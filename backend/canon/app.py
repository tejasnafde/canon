"""Canon HTTP app: API, MCP (/mcp), A2A (/a2a), GitHub hook, Discord interactions.

Run: uvicorn canon.app:app
CORS is off on purpose: the web app is same-origin through Firebase Hosting.
"""
import json
import logging
import os
import sys
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse

from canon import a2a, core, discord, hooks
from canon.mcp_server import mcp, scope
from canon.models import (
    Activity, Alert, AskRequest, AskResult, Briefing, BriefingRequest, CheckRequest,
    CheckResult, Decision, DecisionDetail, EvalReport, ExpertRequest, IngestRequest,
    IngestResult, Person, ResolveRequest, Source,
)

MODEL = os.environ.get("CANON_MODEL", "gemini-3.5-flash-lite")
RATE_LIMIT = int(os.environ.get("CANON_RATE_LIMIT", "30"))  # POSTs per IP per minute


class _JsonFormatter(logging.Formatter):
    """One JSON object per line; Cloud Run reads `severity` and `message`."""

    def format(self, record):
        out = {"severity": record.levelname, "message": record.getMessage(), "logger": record.name}
        out.update(getattr(record, "fields", {}))
        if record.exc_info:
            out["exception"] = self.formatException(record.exc_info)
        return json.dumps(out, default=str)


_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(_JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[_handler], force=True)
log = logging.getLogger("canon")

mcp_app = mcp.streamable_http_app(
    streamable_http_path="/mcp", stateless_http=True, json_response=True,
    host="0.0.0.0",  # behind Cloud Run: the localhost-only Host check would reject real traffic
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        await a2a.mount(app)
        yield


app = FastAPI(title="Canon", lifespan=lifespan)
app.router.routes.extend(mcp_app.routes)
app.include_router(hooks.router)
app.include_router(discord.router)

# ponytail: in-process limiter, per instance; move to Firestore/Redis if instances > 1 matter.
_hits: dict[str, deque] = defaultdict(deque)
_EXEMPT = ("/hooks/", "/discord/")  # signature-verified, and come from shared provider IPs


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    return fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "?")


def _limited(ip: str) -> bool:
    now = time.monotonic()
    q = _hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        return True
    q.append(now)
    return False


@app.middleware("http")
async def access_log_and_limit(request: Request, call_next):
    start = time.perf_counter()
    ip = _client_ip(request)
    path = request.url.path
    if request.method == "POST" and not path.startswith(_EXEMPT) and _limited(ip):
        resp = JSONResponse({"error": "rate_limited", "detail": f"max {RATE_LIMIT} POST/min"},
                            status_code=429, headers={"Retry-After": "60"})
    else:
        resp = await call_next(request)
    log.info("request", extra={"fields": {
        "method": request.method, "path": path, "status": resp.status_code, "ip": ip,
        "workspace": request.headers.get("x-canon-workspace"),
        "ms": round((time.perf_counter() - start) * 1000)}})
    return resp


@app.exception_handler(LookupError)  # KeyError included: core signals "not found" this way
async def _not_found(request: Request, exc: LookupError):
    return JSONResponse({"error": "not_found", "detail": str(exc)}, status_code=404)


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception):
    log.exception("unhandled", extra={"fields": {"path": request.url.path}})
    return JSONResponse({"error": "internal", "detail": type(exc).__name__}, status_code=500)


Ws = Header(default=None, alias="X-Canon-Workspace")




@app.get("/health")
async def health():
    return {"ok": True, "model": MODEL}


@app.post("/api/ingest", response_model=IngestResult)
async def ingest(req: IngestRequest, x: str | None = Ws):
    ws = scope(x)
    req.source.workspace = ws[-1]
    return await core.ingest(req, ws)


@app.post("/api/ask", response_model=AskResult)
async def ask(req: AskRequest, x: str | None = Ws):
    return await core.ask(req, scope(x))


@app.post("/api/briefing", response_model=Briefing)
async def briefing(req: BriefingRequest, x: str | None = Ws):
    return await core.briefing(req, scope(x))


@app.post("/api/check", response_model=CheckResult)
async def check(req: CheckRequest, x: str | None = Ws):
    return await core.check(req, scope(x))


@app.post("/api/expert", response_model=AskResult)
async def expert(req: ExpertRequest, x: str | None = Ws):
    return await core.expert(req, scope(x))


@app.get("/api/decisions", response_model=list[Decision])
async def decisions(status: str | None = None, topic: str | None = None, x: str | None = Ws):
    return await core.list_decisions(scope(x), status=status or None, topic=topic or None)


@app.get("/api/decisions/{decision_id}", response_model=DecisionDetail)
async def decision(decision_id: str, x: str | None = Ws):
    return await core.get_decision(decision_id, scope(x))


@app.get("/api/alerts", response_model=list[Alert])
async def alerts(status: str | None = None, x: str | None = Ws):
    return await core.list_alerts(scope(x), status=status or None)


@app.post("/api/alerts/{alert_id}/resolve", response_model=Alert)
async def resolve(alert_id: str, req: ResolveRequest, x: str | None = Ws):
    return await core.resolve_alert(alert_id, req, scope(x))


@app.get("/api/sources/{source_id}", response_model=Source)
async def source(source_id: str, x: str | None = Ws):
    return await core.get_source(source_id, scope(x))


@app.get("/api/activity", response_model=list[Activity])
async def activity(since: str | None = None, x: str | None = Ws):
    return await core.list_activity(scope(x), since_iso=since or None)


@app.get("/api/people", response_model=list[Person])
async def people(x: str | None = Ws):
    return await core.list_people(scope(x))


@app.get("/api/eval", response_model=EvalReport)
async def eval_report():
    return await core.eval_report()


@app.post("/api/workspace/reset")
async def reset(x: str | None = Ws):
    await core.reset_workspace(scope(x)[-1])
    return {"ok": True}
