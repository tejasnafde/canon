from datetime import datetime, timedelta, timezone

import pytest

from canon import core, llm
from canon.briefing import deadline_days, rank, score
from canon.models import (AskRequest, BriefingRequest, CheckRequest, IngestRequest, ResolveRequest, Source)
from canon.reconcile import decide, pick, verified

NO_PREMISE = {"broken": []}
NO_STALE = {"stale": []}


def src(text, kind="slack", ts="2026-03-01T10:00:00Z", id=None, title="t"):
    return Source(id=id, kind=kind, title=title, author="Priya Shah", ts=ts, text=text)


def extraction(*decisions, facts=()):
    return {"transcript": "", "facts": list(facts), "decisions": [
        {"statement": s, "rationale": "", "assumptions": a, "owner": "Priya Shah", "topic": "deploys", "quotes": q}
        for s, q, a in decisions]}


def fake(**kw):
    llm.FAKE_RESPONSES.update({"PremiseCheck": NO_PREMISE, "StaleCheck": NO_STALE, **kw})


async def ingest(text, ws=("acme",), **kw):
    return await core.ingest(IngestRequest(source=src(text, **kw)), list(ws))


def test_verified_normalises_whitespace_only():
    assert verified("no  deploys\non Fridays", "We agreed: no deploys on Fridays.")
    assert not verified("no deploys on friday", "We agreed: no deploys on Fridays.")  # case matters
    assert not verified("", "anything")


async def test_unverified_quotes_dropped_and_counted():
    text = "We agreed: no deploys on Fridays, starting now."
    fake(Extraction=extraction(("No deploys on Fridays.", ["no deploys on Fridays", "made up quote"], []),
                               ("Invented decision.", ["not in the text"], [])))
    r = await ingest(text)
    assert [d.decision.statement for d in r.decisions] == ["No deploys on Fridays."]
    assert r.rejected_quotes == 2
    assert r.decisions[0].relation == "new"


@pytest.mark.parametrize("relation", ["same", "update", "contradiction", "new"])
async def test_reconciliation_branches(relation):
    fake(Extraction=extraction(("Deploys run on any weekday including Friday.", ["deploys run on any weekday"], [])))
    first = await ingest("Policy: deploys run on any weekday.", ts="2026-01-01T00:00:00Z")
    old_id = first.decisions[0].decision.id

    flags = {"same": (True, False, False), "update": (False, True, True), "contradiction": (False, True, False),
             "new": (False, False, False)}[relation]
    fake(Extraction=extraction(("Deploys run on any weekday except Friday.", ["deploys run on any weekday except Friday"], [])),
         Judgement={"assessments": [dict(zip(("restates", "conflicts", "explicit_supersede"), flags),
                                         decision="D1", why="x")], "authority_evidence": "From today"})
    r = await ingest("From today deploys run on any weekday except Friday.", ts="2026-03-01T00:00:00Z")
    rd = r.decisions[0]
    assert rd.relation == relation
    old = (await core.get_decision(old_id, ["acme"])).decision
    if relation == "same":
        assert rd.decision.id == old_id and len(old.quotes) == 2
    elif relation == "update":
        assert old.status == "superseded" and old.superseded_by == rd.decision.id
        assert rd.decision.supersedes == [old_id]
        tl = (await core.get_decision(rd.decision.id, ["acme"])).timeline
        assert [e.decision_id for e in tl] == [old_id, rd.decision.id]
    elif relation == "contradiction":
        assert old.status == "active"
        [a] = r.alerts
        assert a.kind == "contradiction" and len(a.quotes) == 2
    else:
        assert rd.related_decision_id is None and old.status == "active"


def test_relation_decided_in_code_from_flags():
    rule = {"id": "d-rule", "owner": "Mei Tan"}
    breach = {"id": "d-breach", "owner": "Pranav Menon"}
    labels = {"D1": breach, "D2": rule}
    a = lambda d, r=False, c=False, s=False: {"decision": d, "restates": r, "conflicts": c,  # noqa: E731
                                             "explicit_supersede": s, "why": ""}
    yes, no = (lambda d: True), (lambda d: False)
    # Restating an earlier breach while breaking the rule: contradiction of the rule, not "same".
    assert decide([a("D1", r=True), a("D2", c=True)], labels, no)[:2] == ("contradiction", rule)
    # Both conflict: the known violator is the last target.
    assert decide([a("D1", c=True), a("D2", c=True)], labels, no, {"d-breach"})[:2] == ("contradiction", rule)
    # Change language without authority is still a contradiction; with authority it is an update.
    assert decide([a("D2", c=True, s=True)], labels, no)[0] == "contradiction"
    assert decide([a("D2", c=True, s=True)], labels, yes)[:2] == ("update", rule)
    assert decide([a("D2", c=True)], labels, yes)[0] == "contradiction"  # authority alone does not supersede
    assert decide([a("D2", s=True)], labels, yes)[0] == "update"
    assert decide([a("D2", s=True)], labels, no)[0] == "new"
    assert decide([a("D9", c=True)], labels, yes)[0] == "new"  # unknown label


async def test_contradiction_flags_the_stale_doc_it_relies_on():
    fake(Extraction=extraction(("Production release window is Friday afternoon.", ["Friday afternoon is our production release window"], [])))
    wiki = await ingest("Release process: Friday afternoon is our production release window.", kind="wiki",
                        ts="2025-02-01T00:00:00Z", title="Release process")
    # Rule replaces it with authority (owner match: same author).
    fake(Extraction=extraction(("No production release window on Friday afternoon.", ["No production deploys on Fridays"], [])),
         Judgement={"assessments": [{"decision": "D1", "restates": False, "conflicts": True,
                                     "explicit_supersede": True, "why": "x"}], "authority_evidence": ""})
    rule = (await ingest("No production deploys on Fridays.", ts="2026-03-01T00:00:00Z")).decisions[0]
    assert rule.relation == "update"
    fake(Extraction=extraction(("Production release window refresh every Friday afternoon.", ["every Friday"], [])),
         Judgement={"assessments": [{"decision": "D1", "restates": False, "conflicts": True,
                                     "explicit_supersede": False, "why": "breaks the Friday ban"}],
                    "authority_evidence": ""})
    r = await ingest("I scheduled the refresh every Friday, using the slot from the Release process wiki.",
                     ts="2026-10-01T00:00:00Z")
    assert r.decisions[0].relation == "contradiction"
    stale = [a for a in r.alerts if a.kind == "stale_doc"]
    assert [(a.source_id, a.decision_id) for a in stale] == [(wiki.source.id, rule.decision.id)]
    assert r.source.id in {q.source_id for q in stale[0].quotes}


async def test_stale_doc_alert_with_both_quotes(monkeypatch):
    monkeypatch.setattr("canon.reconcile.DOC_MIN", 0.3)  # bag-of-words fake vectors score lower than real ones
    fake(Extraction=extraction())
    wiki = await ingest("Deploy guide: deploys run on any weekday, Friday included.", kind="wiki",
                        ts="2025-06-01T00:00:00Z", title="Deploy guide")
    fake(Extraction=extraction(("deploys: no deploys run on Friday.", ["no deploys run on Friday"], [])),
         StaleCheck={"stale": [{"excerpt": "W1", "quote": "deploys run on any weekday, Friday included",
                                "explanation": "Friday is now banned."}]})
    r = await ingest("After the incident: no deploys run on Friday.", ts="2026-03-01T00:00:00Z")
    [a] = r.alerts
    assert a.kind == "stale_doc" and a.source_id == wiki.source.id
    assert {q.source_id for q in a.quotes} == {wiki.source.id, r.source.id}


async def test_premise_changed(monkeypatch):
    monkeypatch.setattr("canon.reconcile.PREMISE_MIN", 0.3)
    fake(Extraction=extraction(("Use Twilio for SMS alerts.", ["use Twilio for SMS alerts"], ["Twilio costs 2k per month"])))
    await ingest("Decision: use Twilio for SMS alerts.", ts="2026-01-01T00:00:00Z")
    fake(Extraction=extraction(facts=[{"statement": "Twilio SMS alerts now cost 6k per month.", "quote": "now cost 6k"}]),
         PremiseCheck={"broken": [{"decision": "D1", "assumption": "Twilio costs 2k per month",
                                   "evidence_quote": "Twilio SMS alerts now cost 6k per month", "explanation": "tripled"}]})
    r = await ingest("FYI Twilio SMS alerts now cost 6k per month.", ts="2026-02-01T00:00:00Z")
    assert [a.kind for a in r.alerts] == ["premise_changed"]


async def test_ask_refuses_without_calling_gemini_when_record_is_empty():
    r = await core.ask(AskRequest(question="Why did we pick Kafka?"), ["acme"])
    assert r.refused and not r.citations  # no fixture registered: a Gemini call would raise


async def test_ask_answers_with_citation_and_refuses_when_model_says_unanswerable():
    fake(Extraction=extraction(("No deploys on Friday.", ["no deploys on Friday"], [])))
    await ingest("Incident review: no deploys on Friday.")
    llm.FAKE_RESPONSES["Answer"] = {"answerable": True, "answer": "Because of the incident [D1].",
                                    "cited": [{"ref": "D1", "quote": "no deploys on Friday"}]}
    r = await core.ask(AskRequest(question="why no deploys on Friday"), ["acme"])
    assert not r.refused and r.citations[0].quote == "no deploys on Friday" and r.timeline
    llm.FAKE_RESPONSES["Answer"] = {"answerable": False, "answer": "", "cited": []}
    r = await core.ask(AskRequest(question="why no deploys on Friday"), ["acme"])
    assert r.refused


async def test_check_verdicts_and_agent_violation():
    r = await core.check(CheckRequest(intent="rename a css class"), ["acme"])
    assert r.verdict == "allow" and not r.decisions
    fake(Extraction=extraction(("No deploys on Friday.", ["no deploys on Friday"], [])))
    await ingest("Incident review: no deploys on Friday.")
    llm.FAKE_RESPONSES["Guard"] = {"verdict": "block", "explanation": "Friday freeze.", "deciding": ["D1"]}
    r = await core.check(CheckRequest(intent="deploys on Friday evening", actor="agent:claude-code"), ["acme", "agents"])
    assert r.verdict == "block" and r.decisions and r.citations
    assert [a.kind for a in await core.list_alerts(["agents"])] == ["agent_violation"]
    acts = await core.list_activity(["agents"])
    assert acts[0].action == "check" and acts[0].verdict == "block"


def test_nba_score_factors():
    today = datetime(2026, 10, 17, tzinfo=timezone.utc)
    s, reasons = score("Ship the billing migration by Oct 19, blocks marketing and sales; deploy urgent",
                       "engineer", "decision", today - timedelta(days=1), today, teams={"marketing", "sales"}, links=1)
    assert "deadline in 2 days" in reasons and any("urgent" in r for r in reasons)
    assert any("cross-team" in r for r in reasons) and "relevant to engineer" in reasons
    low, _ = score("Lunch is at noon.", "engineer", "decision", today - timedelta(days=400), today)
    assert low == 30 < s <= 98
    assert deadline_days("due 2026-10-20", today, today) == 3


def test_rank_puts_persona_heroes_on_top():
    """The demo storyline: each persona sees its own hero item first, scores spread instead of clustering."""
    today = datetime(2026, 10, 17, tzinfo=timezone.utc)
    q = lambda sid: [{"source_id": sid, "quote": "x"}]  # noqa: E731

    def dec(i, ts, statement, sid, topic="misc", **kw):
        return {"id": i, "ts": datetime.fromisoformat(ts), "statement": statement, "rationale": "", "topic": topic,
                "status": "active", "owner": "Mei Tan", "quotes": q(sid), "created_at": today, **kw}

    decs = [
        dec("old", "2025-01-16T00:00:00+00:00", "Release window is Friday afternoon.", "s-cal", "deploys"),
        dec("fri", "2026-03-09T00:00:00+00:00", "There will be no production deploys on Fridays.", "s-inc",
            "deploys", supersedes=["old"]),
        dec("cron", "2026-08-14T00:00:00+00:00", "Run the dispatch workflow on a Friday cron.", "s-pr", "deploys"),
        dec("price", "2026-04-02T00:00:00+00:00", "Route Lens costs USD 149 per workspace.", "s-mtg", "pricing"),
        dec("promise", "2026-04-23T00:00:00+00:00", "Route Lens price is USD 99 per workspace.", "s-mail", "pricing"),
        dec("chip", "2026-10-15T00:00:00+00:00", "Budi moved the route chip label down one pixel.", "s-chat", "ui"),
    ]
    alerts = [
        {"id": "a-wiki", "kind": "stale_doc", "severity": "medium", "decision_id": "fri", "source_id": "s-wiki",
         "explanation": "\"Release process\" still states the superseded decision.", "created_at": today},
        {"id": "a-pr", "kind": "contradiction", "severity": "high", "decision_id": "cron",
         "related_decision_id": "fri", "source_id": "s-pr", "explanation": "The PR schedules a production deploy "
         "on Fridays.", "created_at": today},
        {"id": "a-mail", "kind": "contradiction", "severity": "high", "decision_id": "promise",
         "related_decision_id": "price", "source_id": "s-mail", "explanation": "The customer email promises the "
         "old price.", "created_at": today},
    ]
    kinds = {"s-cal": "meeting", "s-inc": "meeting", "s-pr": "pr", "s-mtg": "meeting", "s-mail": "email",
             "s-chat": "slack", "s-wiki": "wiki"}
    day_one = datetime(2025, 1, 1, tzinfo=timezone.utc)
    top = lambda persona, since: rank(decs, alerts, kinds, persona, since, today, set())  # noqa: E731
    nh = top("new_hire", day_one)
    assert {o["id"] for _, _, _, o in nh[:3]} >= {"fri", "a-wiki"} and all(s > 80 for s, *_ in nh[:2])
    assert top("engineer", today - timedelta(days=30))[0][3]["id"] == "a-pr"
    assert top("pm", today - timedelta(days=30))[0][3]["id"] == "a-mail"
    scores = [s for s, *_ in nh]
    assert min(scores) <= 40 and max(scores) >= 85 and scores == [s for s, *_ in top("new_hire", day_one)]


async def test_briefing_ranks_and_resolve_overlay():
    fake(Extraction=extraction(("Deploys: urgent rollback policy for incident.", ["urgent rollback policy for incident"], [])))
    await ingest("New: urgent rollback policy for incident handling.", ts="2026-10-15T00:00:00Z")
    llm.FAKE_RESPONSES["Prose"] = {"summary": "s", "highlights": ["h"], "titles": ["Read it"], "whys": ["w"]}
    b = await core.briefing(BriefingRequest(persona="engineer", since="2026-10-01T00:00:00Z"), ["acme", "v-1"])
    assert b.actions[0].title == "Read it" and 0 <= b.actions[0].priority <= 100 and b.actions[0].reasons

    # Visitor resolves a base-workspace alert: acme is untouched, the visitor sees it resolved.
    from canon.store import get_store
    await get_store().put("alerts", {"id": "a-1", "workspace": "acme", "kind": "stale_doc", "severity": "low",
                                     "explanation": "x", "quotes": [], "status": "open",
                                     "created_at": datetime.now(timezone.utc)})
    await core.resolve_alert("a-1", ResolveRequest(action="dismiss"), ["acme", "v-1"])
    assert (await core.list_alerts(["acme", "v-1"], "open")) == []
    assert len(await core.list_alerts(["acme"], "open")) == 1
    await core.reset_workspace("v-1")
    assert len(await core.list_alerts(["acme", "v-1"], "open")) == 1


def test_pick_accepts_label_or_echoed_statement():
    labels = {"D1": {"statement": "Cache the dashboard for five minutes."}, "D2": {"statement": "Retry for 24 hours."}}
    assert pick(labels, "[D2]") is labels["D2"] and pick(labels, "D1: cache") is labels["D1"]
    assert pick(labels, "Retry for 24 hours. Why: keys") is labels["D2"]
    assert pick(labels, "D9") is None and pick(labels, "") is None


async def test_check_block_becomes_warn_when_premise_broken():
    fake(Extraction=extraction(("Cache dashboard five minutes.", ["cache dashboard five minutes"], [])))
    r = await ingest("We cache dashboard five minutes.")
    from canon.store import get_store
    await get_store().put("alerts", {"id": "a-p", "workspace": "acme", "kind": "premise_changed", "severity": "medium",
                                     "decision_id": r.decisions[0].decision.id, "explanation": "load grew",
                                     "quotes": [], "status": "open", "created_at": datetime.now(timezone.utc)})
    llm.FAKE_RESPONSES["Guard"] = {"verdict": "block", "explanation": "Over the limit.", "deciding": ["D1"]}
    res = await core.check(CheckRequest(intent="keep cache dashboard five minutes"), ["acme"])
    assert res.verdict == "warn"
