"""Canon HTTP app: API, MCP (/mcp), A2A (/a2a), GitHub hook, Discord interactions.

Run: uvicorn canon.app:app
CORS is off on purpose: the web app is same-origin through Firebase Hosting.
"""
import asyncio
import contextvars
import json
import logging
import os
import re
import sys
import time
import traceback
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse, Response

from canon import a2a, core, discord, hooks, llm, store
from canon.limits import TooLong, enforce
from canon.mcp_server import AGENTS, BASE, Blank, mcp, require, scope
from canon.models import (
    Activity, Alert, AskRequest, AskResult, Briefing, BriefingRequest, CheckRequest,
    CheckResult, Decision, DecisionDetail, EvalReport, ExpertRequest, IngestRequest,
    IngestResult, Person, ResolveRequest, Source,
)

MODEL = os.environ.get("CANON_MODEL", "gemini-3.5-flash-lite")
RATE_LIMIT = int(os.environ.get("CANON_RATE_LIMIT", "120"))  # POSTs per IP per minute; judges share networks
CLIENT_ERROR_LIMIT = int(os.environ.get("CANON_CLIENT_ERROR_LIMIT", "10"))  # web error reports per IP per minute
REQUEST_DEADLINE = float(os.environ.get("CANON_REQUEST_DEADLINE", "90"))  # seconds of model time per request
PROJECT = os.environ.get("CANON_PROJECT", "teejayproject")
SERVICE = {"service": "canon", "version": os.environ.get("K_REVISION", "local")}
ERROR_TYPE = "type.googleapis.com/google.devtools.clouderrorreporting.v1beta1.ReportedErrorEvent"

request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
trace: contextvars.ContextVar[dict] = contextvars.ContextVar("trace", default={})


class _JsonFormatter(logging.Formatter):
    """One JSON object per line; Cloud Run reads `severity` and `message`.

    Tracebacks go into `message` with the ReportedErrorEvent @type, so Error Reporting groups them.
    Every line carries the request id and trace of the request that produced it.
    """

    def format(self, record):
        out = {"severity": record.levelname, "message": record.getMessage(), "logger": record.name}
        if rid := request_id.get():
            out["request_id"] = rid
        out.update(trace.get())
        out.update(getattr(record, "fields", {}))
        if record.exc_info:
            out["message"] = f"{out['message']}\n{self.formatException(record.exc_info)}"
            out["@type"], out["serviceContext"] = ERROR_TYPE, SERVICE
        return json.dumps(out, default=str)


_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(_JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[_handler], force=True)
log = logging.getLogger("canon")

mcp_app = mcp.streamable_http_app(
    streamable_http_path="/mcp", stateless_http=True, json_response=True,
    host="0.0.0.0",  # behind Cloud Run: the localhost-only Host check would reject real traffic
)


async def _startup_check():
    """Fail fast with one clear log line if credentials or Firestore are unreachable."""
    if os.environ.get("CANON_MEMORY_STORE") == "1":
        return
    try:
        import google.auth
        google.auth.default()
        await asyncio.wait_for(store.get_store().get("people", "canon-startup-probe"), 15)
    except Exception as e:
        log.critical("startup check failed: cannot reach Firestore database canon with the current credentials "
                     "(%s: %s). Set GOOGLE_APPLICATION_CREDENTIALS or the Cloud Run service account.",
                     type(e).__name__, e)
        raise SystemExit(1) from e


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _startup_check()
    async with mcp.session_manager.run():
        await a2a.mount(app)
        yield


app = FastAPI(title="Canon", lifespan=lifespan)
app.router.routes.extend(mcp_app.routes)
app.include_router(hooks.router)
app.include_router(discord.router)

# ponytail: in-process limiter, per instance; move to Firestore/Redis if instances > 1 matter.
_hits: dict[str, deque] = defaultdict(deque)
_err_hits: dict[str, deque] = defaultdict(deque)
_EXEMPT = ("/hooks/", "/discord/", "/api/client-error")  # signature-verified / own limit
_RID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    return fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "?")


def _limited(ip: str, hits: dict[str, deque] = _hits, limit: int | None = None) -> bool:
    limit = RATE_LIMIT if limit is None else limit
    now = time.monotonic()
    q = hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= limit:
        return True
    q.append(now)
    return False


def _trace_fields(header: str | None) -> dict:
    """X-Cloud-Trace-Context `TRACE_ID/SPAN_ID;o=1` to Cloud Logging trace correlation fields."""
    m = re.match(r"^([0-9a-fA-F]{32})(?:/(\d+))?", header or "")
    if not m:
        return {}
    out = {"logging.googleapis.com/trace": f"projects/{PROJECT}/traces/{m.group(1)}"}
    if m.group(2):
        out["logging.googleapis.com/spanId"] = format(int(m.group(2)), "016x")
    return out


def _err(error: str, status: int, **extra) -> JSONResponse:
    return JSONResponse({"error": error, **extra, "request_id": request_id.get()}, status_code=status)


@app.middleware("http")
async def access_log_and_limit(request: Request, call_next):
    start = time.perf_counter()
    rid = request.headers.get("x-request-id", "")
    request_id.set(rid if _RID.match(rid) else uuid.uuid4().hex)
    trace.set(_trace_fields(request.headers.get("x-cloud-trace-context")))
    llm.deadline.set(time.monotonic() + REQUEST_DEADLINE)
    ip = _client_ip(request)
    path = request.url.path
    if (request.method == "POST" or path == "/health/deep") and not path.startswith(_EXEMPT) and _limited(ip):
        resp = _err("rate_limited", 429, detail=f"max {RATE_LIMIT} POST/min")
        resp.headers["Retry-After"] = "60"
    else:
        try:
            resp = await call_next(request)
        except Exception:
            log.exception("unhandled", extra={"fields": {"path": path, "method": request.method}})
            resp = _err("internal", 500)
    resp.headers["X-Request-Id"] = request_id.get()
    log.info("request", extra={"fields": {
        "method": request.method, "path": path, "status": resp.status_code, "ip": ip,
        "workspace": request.headers.get("x-canon-workspace"),
        "ms": round((time.perf_counter() - start) * 1000)}})
    return resp


@app.exception_handler(LookupError)  # KeyError included: core signals "not found" this way
async def _not_found(request: Request, exc: LookupError):
    return _err("not_found", 404, detail=str(exc))


@app.exception_handler(FileNotFoundError)  # e.g. no committed eval report
async def _missing(request: Request, exc: FileNotFoundError):
    return _err("not_found", 404, detail="not available")


@app.exception_handler(llm.ModelTimeout)
async def _model_timeout(request: Request, exc: llm.ModelTimeout):
    log.error("model_timeout: %s", exc, extra={"fields": {"path": request.url.path}})
    if isinstance(exc, llm.BudgetExceeded):
        return _err("budget_exceeded", 503, detail="Canon has used today's Gemini budget, try again tomorrow")
    resp = _err("model_timeout", 503, detail="the model did not answer in time, try again")
    resp.headers["Retry-After"] = "5"
    return resp


@app.exception_handler(TooLong)
async def _too_long(request: Request, exc: TooLong):
    return _err("validation", 422, field=exc.field, max=exc.limit, detail=str(exc))


@app.exception_handler(Blank)
async def _blank(request: Request, exc: Blank):
    return _err("validation", 422, field=exc.field, detail=str(exc))


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):  # fallback; the middleware normally catches first
    log.exception("unhandled", extra={"fields": {"path": request.url.path}})
    return _err("internal", 500)


Ws = Header(default=None, alias="X-Canon-Workspace")
DISCORD = "discord"


def view(x: str | None) -> list[str]:
    """Read scope for the record pages: also the live Discord workspace, so judges see their message land.
    The visitor workspace stays last, so writes (alert resolution) still go there."""
    ws = scope(x)
    return list(dict.fromkeys([ws[0], DISCORD, ws[-1]]))


@app.get("/health")
async def health():
    return {"ok": True, "model": MODEL}


@app.get("/health/deep")
async def health_deep():
    """Manual check only (Firestore read + one tiny embed). Not for probes: it costs a Gemini call."""
    out, ok = {"model": MODEL}, True
    for name, fn in (("firestore", lambda: store.get_store().get("people", "canon-health-probe")),
                     ("embed", lambda: llm.embed(["canon health check"]))):
        t = time.perf_counter()
        try:
            await asyncio.wait_for(fn(), 15)
            out[name] = {"ok": True, "ms": round((time.perf_counter() - t) * 1000)}
        except Exception as e:
            ok = False
            log.error("health/deep %s failed: %s: %s", name, type(e).__name__, e)
            out[name] = {"ok": False, "error": type(e).__name__}
    return JSONResponse({"ok": ok, **out, "request_id": request_id.get()}, status_code=200 if ok else 503)


@app.post("/api/client-error", status_code=204)
async def client_error(request: Request):
    """Browser error reports. Logged at ERROR with source "web"; nothing is echoed back."""
    if _limited(_client_ip(request), _err_hits, CLIENT_ERROR_LIMIT):
        return _err("rate_limited", 429)
    if int(request.headers.get("content-length") or 0) > 8192:
        return _err("too_large", 413)
    body = await request.body()
    try:
        r = json.loads(body) if len(body) <= 8192 else None
    except ValueError:
        r = None
    if isinstance(r, dict) and not r.get("url") and isinstance(r.get("path"), str):
        r["url"] = r["path"]  # the web client sends {message, stack, source, path}
    if not isinstance(r, dict) or not isinstance(r.get("message"), str) or not isinstance(r.get("url"), str):
        return _err("validation", 422 if len(body) <= 8192 else 413, detail="need {message, url} under 8 KB")
    f = {k: str(r[k])[:4000] for k in ("stack", "url", "userAgent", "release") if r.get(k)}
    msg = r["message"][:2000] + (f"\n{f['stack']}" if f.get("stack") else "")
    log.error(msg, extra={"fields": {"source": "web", "@type": ERROR_TYPE, **f,
                                     "serviceContext": {"service": "canon-web", "version": f.get("release", "unknown")},
                                     "context": {"httpRequest": {"url": f.get("url", ""),
                                                                 "userAgent": f.get("userAgent", "")}}}})
    return Response(status_code=204)


@app.post("/api/ingest", response_model=IngestResult)
async def ingest(req: IngestRequest, x: str | None = Ws):
    enforce(req)
    ws = scope(x)
    req.source.workspace = ws[-1]
    return await core.ingest(req, ws)


@app.post("/api/ask", response_model=AskResult)
async def ask(req: AskRequest, x: str | None = Ws):
    enforce(req)
    require(question=req.question)
    return await core.ask(req, scope(x))


@app.post("/api/briefing", response_model=Briefing)
async def briefing(req: BriefingRequest, x: str | None = Ws):
    enforce(req)
    return await core.briefing(req, scope(x))


@app.post("/api/check", response_model=CheckResult)
async def check(req: CheckRequest, x: str | None = Ws):
    enforce(req)
    require(intent=req.intent)
    return await core.check(req, scope(x))


@app.post("/api/expert", response_model=AskResult)
async def expert(req: ExpertRequest, x: str | None = Ws):
    enforce(req)
    require(question=req.question)
    return await core.expert(req, scope(x))


@app.get("/api/decisions", response_model=list[Decision])
async def decisions(status: str | None = None, topic: str | None = None, x: str | None = Ws):
    return await core.list_decisions(view(x), status=status or None, topic=topic or None)


@app.get("/api/decisions/{decision_id}", response_model=DecisionDetail)
async def decision(decision_id: str, x: str | None = Ws):
    return await core.get_decision(decision_id, view(x))


@app.get("/api/alerts", response_model=list[Alert])
async def alerts(status: str | None = None, x: str | None = Ws):
    return await core.list_alerts(view(x), status=status or None)


@app.post("/api/alerts/{alert_id}/resolve", response_model=Alert)
async def resolve(alert_id: str, req: ResolveRequest, x: str | None = Ws):
    enforce(req)
    return await core.resolve_alert(alert_id, req, view(x))


@app.get("/api/sources/{source_id}", response_model=Source)
async def source(source_id: str, x: str | None = Ws):
    return await core.get_source(source_id, view(x))


@app.get("/api/activity", response_model=list[Activity])
async def activity(since: str | None = None, x: str | None = Ws):
    try:
        if since:
            datetime.fromisoformat(since.replace("Z", "+00:00"))
    except ValueError:
        return _err("validation", 422, field="since", detail="since must be an ISO 8601 timestamp")
    # Visitors also see agent traffic (MCP/A2A write to "agents") and Discord, so the feed shows both live.
    return await core.list_activity(list(dict.fromkeys([BASE, AGENTS, DISCORD, *scope(x)])), since_iso=since or None)


@app.get("/api/people", response_model=list[Person])
async def people(x: str | None = Ws):
    return await core.list_people(scope(x))


@app.get("/api/stats")
async def stats(x: str | None = Ws):
    return await store.stats(view(x))


@app.get("/api/eval", response_model=EvalReport)
async def eval_report():
    return await core.eval_report()


@app.post("/api/workspace/reset")
async def reset(x: str | None = Ws):
    await core.reset_workspace(scope(x)[-1])
    return {"ok": True}
