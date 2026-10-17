"""W5 integration: activity scope and titles, raise_alert, label scrubbing, eval 404. Memory store, fake LLM."""
from datetime import datetime, timezone

import httpx2

from canon import app as app_mod, core, llm
from canon.models import CheckRequest, IngestRequest, Source
from canon.reconcile import unlabel
from canon.store import get_store

NOW = datetime(2026, 10, 17, tzinfo=timezone.utc)
FRIDAY = {"id": "d-fri", "workspace": "acme", "statement": "No production deploys on Fridays.", "rationale": "INC-042",
          "assumptions": [], "owner": "Mei Tan", "ts": datetime(2026, 3, 9, tzinfo=timezone.utc), "topic": "deploys",
          "status": "active", "quotes": [{"source_id": "s-inc", "quote": "No production deploys on Fridays"}]}


def client():
    return httpx2.AsyncClient(transport=httpx2.ASGITransport(app=app_mod.app), base_url="http://test")


def test_unlabel_rewrites_leaked_labels():
    labels = {"D1": FRIDAY, "C2": {"title": "Release process", "text": "x"}}
    out = unlabel("This conflicts with the existing decision D1, see [C2]; D1's owner agrees.", labels)
    assert "D1" not in out and "C2" not in out
    assert out.startswith("This conflicts with the decision \"No production deploys on Fridays\" (Mei Tan, 2026-03-09)")
    assert "\"Release process\"" in out
    assert unlabel("Breaks D7.") == "Breaks an earlier decision."
    assert unlabel("Breaks D7.", fallback=FRIDAY).startswith("Breaks the decision \"No production")
    assert unlabel("Version 2 of the API") == "Version 2 of the API"


async def test_activity_reads_agents_and_visitor_only():
    for ws in ("acme", "agents", "v-me", "v-other"):
        await core.log_activity(ws, "agent:x", "search", f"from {ws}")
    async with client() as c:
        rows = (await c.get("/api/activity", headers={"X-Canon-Workspace": "v-me"})).json()
    assert {r["summary"] for r in rows} == {"from acme", "from agents", "from v-me"}


async def test_check_logs_titles_and_explanation_without_labels():
    await get_store().put("decisions", {**FRIDAY, "embedding": llm._fake_vec(FRIDAY["statement"])})
    llm.FAKE_RESPONSES["Guard"] = {"verdict": "block", "explanation": "D1 bans production deploys on Fridays.",
                                   "deciding": ["D1"]}
    res = await core.check(CheckRequest(intent="production deploys on Fridays", actor="agent:claude-code"),
                           ["acme", "agents"])
    assert res.verdict == "block" and "D1" not in res.explanation
    [act] = [a for a in await core.list_activity(["agents"]) if a.action == "check"]
    assert act.explanation == res.explanation and act.ref_titles == [FRIDAY["statement"]]


async def test_flag_conflict_raises_agent_alert():
    await get_store().put("decisions", {**FRIDAY, "embedding": llm._fake_vec(FRIDAY["statement"])})
    a = await core.raise_alert("Wiki still allows production deploys on Fridays",
                               "Deploys may go out any weekday including Fridays.", "agent:codex", ["acme", "agents"])
    assert (a.kind, a.created_by, a.decision_id, a.workspace) == ("agent_violation", "agent:codex", "d-fri", "agents")
    assert [x.id for x in await core.list_alerts(["acme", "agents"], "open")] == [a.id]
    [act] = await core.list_activity(["agents"])
    assert act.action == "flag" and act.actor == "agent:codex" and FRIDAY["statement"] in act.ref_titles


async def test_alert_reads_expose_related_decision_and_scrub_labels():
    await get_store().put("decisions", FRIDAY)
    await get_store().put("alerts", {"id": "a-1", "workspace": "acme", "kind": "contradiction", "severity": "high",
                                     "decision_id": "d-pr", "related_decision_id": "d-fri", "source_id": None,
                                     "explanation": "The PR conflicts with D1's ban.", "quotes": [],
                                     "status": "open", "created_at": NOW})
    [a] = await core.list_alerts(["acme"])
    assert a.related_decision_id == "d-fri" and "D1" not in a.explanation and "Fridays" in a.explanation


async def test_ingest_by_agent_logs_record(monkeypatch):
    llm.FAKE_RESPONSES.update({"PremiseCheck": {"broken": []}, "StaleCheck": {"stale": []}, "Extraction": {
        "transcript": "", "facts": [], "decisions": [{"statement": "Use Postgres.", "rationale": "", "assumptions": [],
                                                     "owner": "Mei Tan", "topic": "db", "quotes": ["Use Postgres"]}]}})
    src = Source(kind="agent", title="Use Postgres", author="agent:pm-bot", ts=NOW, text="Use Postgres for billing.")
    await core.ingest(IngestRequest(source=src, actor="agent:pm-bot"), ["acme", "agents"])
    [act] = await core.list_activity(["agents"])
    assert act.action == "record" and act.ref_titles[:2] == ["Use Postgres", "Use Postgres."]


async def test_eval_missing_is_404(monkeypatch, tmp_path):
    monkeypatch.setattr("canon.eval.REPORT", tmp_path / "nope.json")
    async with client() as c:
        r = await c.get("/api/eval")
    assert r.status_code == 404 and r.json()["error"] == "not_found"
