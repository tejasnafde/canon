"""W3 agent layer: HTTP app, MCP end to end, GitHub hook, Discord, A2A card. No network."""
import asyncio
import hashlib
import hmac
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx2
import pytest
import pytest_asyncio
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from nacl.signing import SigningKey

from canon import app as app_mod, core, discord, hooks, llm
from canon.models import AskResult, CheckResult, Decision, IngestResult, Quote

NOW = datetime(2026, 10, 17, tzinfo=timezone.utc)
FRIDAY = Decision(id="d-friday", workspace="acme", statement="No production deploys on Fridays",
                  rationale="Friday deploy caused the March outage", owner="Priya Rao", ts=NOW,
                  topic="deploys", quotes=[Quote(source_id="s-1", quote="no more Friday deploys")])


@pytest.fixture
def calls(monkeypatch):
    """Replace every core function used by W3 with a fake that records its calls."""
    log = []

    async def check(req, ws):
        log.append(("check", req.actor, ws))
        verdict = "block" if "friday" in req.intent.lower() else "allow"
        return CheckResult(verdict=verdict, explanation="Friday deploys are banned.",
                           decisions=[FRIDAY] if verdict == "block" else [], citations=[], latency_ms=5)

    async def ask(req, ws):
        log.append(("ask", req.actor, ws))
        return AskResult(answer="Because of the March outage.", citations=[], latency_ms=5)

    async def search_decisions(query, ws, limit=5):
        log.append(("search", query, ws))
        return [FRIDAY]

    async def ingest(req, ws):
        log.append(("ingest", req.actor, ws, req.source.workspace))
        return IngestResult(source=req.source, decisions=[], alerts=[], latency_ms=5)

    async def log_activity(workspace, actor, action, summary, ref_ids=None, verdict=None):
        log.append(("activity", workspace, actor, action, verdict))

    async def get_source(source_id, ws):
        raise KeyError(source_id)

    async def list_people(ws):
        raise RuntimeError("boom")

    for f in (check, ask, search_decisions, ingest, log_activity, get_source, list_people):
        monkeypatch.setattr(core, f.__name__, f)
    app_mod._hits.clear()
    return log


pytestmark = pytest.mark.asyncio(loop_scope="module")


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def running_app():
    # The MCP session manager can start only once per process, so one lifespan per module.
    # Hold the lifespan in its own task: anyio cancel scopes must exit in the task that entered them.
    started, stop = asyncio.Event(), asyncio.Event()

    async def hold():
        async with app_mod.app.router.lifespan_context(app_mod.app):
            started.set()
            await stop.wait()

    task = asyncio.create_task(hold())
    await started.wait()
    yield app_mod.app
    stop.set()
    await task


@pytest_asyncio.fixture(loop_scope="module")
async def client(running_app, calls):
    transport = httpx2.ASGITransport(app=running_app, raise_app_exceptions=False)
    async with httpx2.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---- app ----

async def test_health(client):
    assert (await client.get("/health")).json()["ok"] is True


async def test_workspace_scope(client, calls):
    await client.post("/api/check", json={"intent": "x"}, headers={"X-Canon-Workspace": "v-abc"})
    await client.post("/api/check", json={"intent": "x"}, headers={"X-Canon-Workspace": "acme"})
    await client.post("/api/check", json={"intent": "x"})
    assert [c[2] for c in calls] == [["acme", "v-abc"], ["acme", "agents"], ["acme", "agents"]]


async def test_ingest_writes_to_visitor_workspace(client, calls):
    src = {"kind": "paste", "title": "t", "author": "a", "ts": NOW.isoformat(), "text": "x", "workspace": "acme"}
    await client.post("/api/ingest", json={"source": src}, headers={"X-Canon-Workspace": "v-1"})
    assert calls[-1][3] == "v-1"


async def test_errors_are_json(client):
    r = await client.get("/api/sources/nope")
    assert r.status_code == 404 and r.json()["error"] == "not_found"
    r = await client.get("/api/people")
    assert r.status_code == 500 and r.json()["error"] == "internal"


async def test_rate_limit(client, monkeypatch):
    monkeypatch.setattr(app_mod, "RATE_LIMIT", 3)
    codes = [(await client.post("/api/ask", json={"question": "q"})).status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]


# ---- MCP end to end over streamable HTTP with the official client ----

@asynccontextmanager
async def mcp_session(app, headers):
    http = httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app), base_url="http://test", headers=headers)
    async with http, streamable_http_client("http://test/mcp", http_client=http) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def test_mcp_tools_end_to_end(running_app, calls):
    async with mcp_session(running_app, {"X-Canon-Workspace": "v-judge", "User-Agent": "codex/1.0"}) as s:
        names = {t.name for t in (await s.list_tools()).tools}
        assert names == {"search_decisions", "check_intent", "ask_why", "catch_me_up",
                         "record_decision", "flag_conflict"}
        r = await s.call_tool("check_intent", {"intent": "Add a Friday 17:00 cron deploy", "actor": "claude-code"})
        assert not r.is_error, r.content
        assert r.structured_content["verdict"] == "block"
        assert calls[-1] == ("check", "agent:claude-code", ["acme", "v-judge"])
        await s.call_tool("search_decisions", {"query": "deploys"})
        assert calls[-1][:4] == ("activity", "v-judge", "agent:codex", "search")  # User-Agent fallback
        await s.call_tool("record_decision", {"statement": "Use Postgres", "rationale": "joins",
                                              "source_text": "We agreed on Postgres.", "actor": "pm-bot"})
        assert calls[-1] == ("ingest", "agent:pm-bot", ["acme", "v-judge"], "v-judge")


# ---- GitHub hook ----

PR_PAYLOAD = {
    "action": "opened",
    "number": 7,
    "pull_request": {"number": 7, "title": "Add Friday deploy cron", "body": "Ship weekly on Friday 5pm",
                     "url": "https://api.github.com/repos/tejasnafde/canon/pulls/7",
                     "base": {"ref": "main"}},
    "repository": {"full_name": "tejasnafde/canon"},
}


async def _gh_post(client, payload, secret="s3cret"):
    body = json.dumps(payload).encode()
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return await client.post("/hooks/github", content=body,
                       headers={"X-Hub-Signature-256": sig, "X-GitHub-Event": "pull_request"})


async def test_github_hook(client, calls, monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "s3cret")
    monkeypatch.setenv("GITHUB_TOKEN", "t")
    posted = []

    async def fake_diff(pr):
        return "+  schedule: cron('0 17 * * FRI')"

    async def fake_comment(repo, number, body):
        posted.append((repo, number, body))

    monkeypatch.setattr(hooks, "fetch_diff", fake_diff)
    monkeypatch.setattr(hooks, "post_comment", fake_comment)
    assert (await _gh_post(client, PR_PAYLOAD, secret="wrong")).status_code == 401
    r = await _gh_post(client, PR_PAYLOAD)
    assert r.json() == {"ok": True, "verdict": "block", "commented": True}
    assert posted[0][:2] == ("tejasnafde/canon", 7) and "No production deploys on Fridays" in posted[0][2]
    # core.check (faked here) logs the activity itself; the hook no longer logs a second row.
    assert not [c for c in calls if c[0] == "activity"]


# ---- Discord ----

async def _discord_post(client, key, payload):
    body = json.dumps(payload).encode()
    ts = "1700000000"
    sig = key.sign(ts.encode() + body).signature.hex()
    return await client.post("/discord/interactions", content=body,
                       headers={"X-Signature-Ed25519": sig, "X-Signature-Timestamp": ts})


async def test_discord(client, monkeypatch):
    key = SigningKey.generate()
    monkeypatch.setenv("DISCORD_PUBLIC_KEY", key.verify_key.encode().hex())
    assert (await _discord_post(client, key, {"type": 1})).json() == {"type": 1}
    assert (await _discord_post(client, SigningKey.generate(), {"type": 1})).status_code == 401
    cmd = {"type": 2, "application_id": "a", "token": "t", "member": {"user": {"username": "ishank"}},
           "data": {"name": "canon", "options": [{"name": "check", "type": 1,
                                                  "options": [{"name": "intent", "value": "deploy on Friday"}]}]}}
    r = (await _discord_post(client, key, cmd)).json()
    assert r["type"] == 4 and r["data"]["content"].startswith("**BLOCK**")


async def test_discord_slow_defers(client, monkeypatch):
    key = SigningKey.generate()
    monkeypatch.setenv("DISCORD_PUBLIC_KEY", key.verify_key.encode().hex())
    monkeypatch.setattr(discord, "INLINE_SECONDS", 0.01)
    followed = []

    async def slow(*a):
        await asyncio.sleep(0.1)
        return "late answer"

    async def fake_follow_up(app_id, token, task):
        followed.append(await task)

    monkeypatch.setattr(discord, "answer", slow)
    monkeypatch.setattr(discord, "follow_up", fake_follow_up)
    cmd = {"type": 2, "application_id": "a", "token": "t", "user": {"username": "u"},
           "data": {"name": "canon", "options": [{"name": "ask", "type": 1,
                                                  "options": [{"name": "question", "value": "why?"}]}]}}
    assert (await _discord_post(client, key, cmd)).json() == {"type": 5}
    assert followed == ["late answer"]


# ---- A2A ----

async def test_agent_card(client):
    card = (await client.get("/.well-known/agent-card.json")).json()
    assert card["name"] == "canon"
    assert {s["name"] for s in card["skills"]} >= {"check_intent"} or card["skills"]


# ---- W25 QA: edge cases found against the live API ----

QA_WS = {"X-Canon-Workspace": "v-qa"}


@pytest.mark.parametrize("path,body", [
    ("/api/ask", {"question": ""}), ("/api/ask", {"question": "   "}), ("/api/check", {"intent": "\n"}),
    ("/api/expert", {"person_id": "p", "question": ""}),
])
async def test_blank_text_is_422_not_500(client, calls, path, body):
    r = await client.post(path, json=body, headers=QA_WS)
    assert r.status_code == 422 and r.json()["error"] == "validation"
    assert not [c for c in calls if c[0] in ("ask", "check")]  # no Gemini/embed spent


async def test_activity_bad_since_is_422(client):
    r = await client.get("/api/activity?since=garbage", headers=QA_WS)
    assert r.status_code == 422 and r.json()["field"] == "since"


async def test_budget_cap_says_so(client, monkeypatch):

    async def broke(req, ws):
        raise llm.BudgetExceeded("cap")
    monkeypatch.setattr(core, "ask", broke)
    r = await client.post("/api/ask", json={"question": "why?"}, headers=QA_WS)
    assert r.status_code == 503 and r.json()["error"] == "budget_exceeded"


async def test_mcp_blank_and_unknown_tool(running_app, calls):
    async with mcp_session(running_app, QA_WS) as s:
        r = await s.call_tool("ask_why", {"question": "  "})
        assert r.is_error and "must not be empty" in r.content[0].text
        r = await s.call_tool("ask_why", {"question": "a" * 1001})
        assert r.is_error and "longer than 1000" in r.content[0].text
        r = await s.call_tool("catch_me_up", {"since": "yesterday"})
        assert r.is_error and "ISO date" in r.content[0].text
        r = await s.call_tool("no_such_tool", {})
        assert r.is_error
        r = await s.call_tool("check_intent", {})  # missing required arg
        assert r.is_error
        tools = {t.name: t for t in (await s.list_tools()).tools}
        assert "security" in json.dumps(tools["catch_me_up"].input_schema)  # all 14 roles, as in the API


async def test_discord_missing_option_and_failure_answer_inline(client, monkeypatch):
    key = SigningKey.generate()
    monkeypatch.setenv("DISCORD_PUBLIC_KEY", key.verify_key.encode().hex())

    def cmd(sub, opts):
        return {"type": 2, "application_id": "a", "token": "t", "user": {"username": "u"},
                "data": {"name": "canon", "options": [{"name": sub, "type": 1, "options": opts}]}}
    r = (await _discord_post(client, key, cmd("ask", []))).json()
    assert r["type"] == 4 and r["data"]["content"].startswith("Usage: /canon ask")
    r = (await _discord_post(client, key, cmd("catchup", [{"name": "days", "value": "x"}]))).json()
    assert r["data"]["content"].startswith("Usage: /canon catchup")
    r = (await _discord_post(client, key, cmd("dance", []))).json()
    assert r["data"]["content"] == "Unknown subcommand dance"

    async def boom(*a):
        raise RuntimeError("x")
    monkeypatch.setattr(discord, "answer", boom)
    r = (await _discord_post(client, key, cmd("ask", [{"name": "question", "value": "why?"}]))).json()
    assert r["type"] == 4 and r["data"]["content"] == "Canon failed: RuntimeError"
