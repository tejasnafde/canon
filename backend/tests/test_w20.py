"""W20: authority, effective dates and outdated copies, unverified claims, premise rule, stats, cheap Discord sync."""
import json
from datetime import datetime, timezone
from pathlib import Path

from canon import core, llm, store
from canon.authority import TOPICS, Org, authority, org_topic
from canon.connectors import discord_sync as ds
from canon.ingest import effective_at
from canon.models import IngestRequest, Source
from canon.reconcile import premise_holds

ROOT = Path(__file__).resolve().parents[2]
PEOPLE = json.loads((ROOT / "data" / "people.json").read_text())


def test_bundled_org_files_match_data():
    for f in ("topics.json", "channels.json"):
        assert json.loads((ROOT / "data/org" / f).read_text()) == \
            json.loads((ROOT / "backend/canon/org" / f).read_text()), f"copy data/org/{f} to backend/canon/org/"


def org():
    return Org([{**p, "id": f"w-{p['id']}", "workspace": "w", "discord_username": {"pranav-menon": "pranav"}.get(p["id"])}
                for p in PEOPLE])


def auth(author, topic, kind="slack", title="t", approved=False, statement=""):
    return authority({"topic": topic, "statement": statement, "owner": author},
                     {"author": author, "kind": kind, "title": title, "url": None}, org(), approved)


def test_authority_rules():
    assert org_topic("leave policy") == "leave/notice/handbook/hiring/reviews"
    assert org_topic("deploys") == "deploys/release" and org_topic("pricing") == "pricing"
    assert auth("Amina Yusuf", "leave policy") == "official"            # People head owns leave
    assert auth("Pranav Menon", "leave policy") == "claim"              # engineer posting a leave policy
    assert auth("Pranav Menon", "deploys") == "proposed"                # IC in area, no approval
    assert auth("Pranav Menon", "deploys", approved=True) == "official"
    assert auth("Pranav Menon", "deploys", kind="meeting") == "official"
    assert auth("Hana Okafor", "pricing") == "official"                 # CEO
    assert auth("someguest", "pricing", title="Discord #sales") == "claim"
    assert auth("pranav", "deploys", title="Discord #general", approved=True) == "official"
    assert auth("Mei Tan", "deploys", title="Discord #general") == "claim"  # Discord maps by username only
    assert auth("Arjun Desai", "leave policy") == "proposed"            # a head outside their area
    assert authority({"topic": "x", "statement": "", "owner": "a"}, {"author": "a", "kind": "slack", "title": ""},
                     Org([])) == "official"                             # no org data: pre-W20 behaviour


def test_cross_team_decider_is_lowest_common_manager():
    from canon.authority import decider
    o = org()
    who = decider({"owner": "Pranav Menon"}, {"owner": "Linh Nguyen", "topic": "x", "statement": ""},
                  {"author": "Pranav Menon", "title": ""}, o)
    assert who["id"] == "mei-tan"  # Platform vs Data, both under Mei Tan
    assert TOPICS["pricing"]["owner"] == "aisha-rahman"


def test_effective_date():
    assert effective_at("", "Leave policy v4. Effective 1 November 2026.") == datetime(2026, 11, 1, tzinfo=timezone.utc)
    assert effective_at("2026-03-01", "Effective from 1 Mar 2026, staff get 20 days.").month == 3
    assert effective_at("2026-10-17", "Lunch is at noon.") is None  # a guessed upload date is ignored


def test_premise_rule_rejects_trivial_and_restated():
    d = {"statement": "Use Twilio for SMS alerts.", "rationale": "", "assumptions": ["Twilio costs 2k per month"]}
    good = {"assumption_quote": "Twilio costs 2k per month", "evidence_quote": "now cost 6k", "contradicts": True,
            "trivial": False}
    assert premise_holds(good, d)
    assert not premise_holds({**good, "trivial": True}, d)
    assert not premise_holds({**good, "contradicts": False}, d)
    assert not premise_holds({**good, "assumption_quote": "the faulty cable has a paper tag"}, d)  # not stated
    assert not premise_holds({**good, "evidence_quote": "Twilio costs 2k per month"}, d)  # restates it


def ex(statement, quote, topic, joke=False, effective=""):
    return {"transcript": "", "facts": [], "effective_date": effective, "approval_quote": "", "decisions": [
        {"kind": "rule", "statement": statement, "rationale": "", "assumptions": [], "owner": "", "topic": topic,
         "quotes": [quote], "is_joke_or_hypothetical": joke}]}


def judge(conflicts=True, supersede=True):
    return {"assessments": [{"decision": "D1", "restates": False, "conflicts": conflicts,
                             "explicit_supersede": supersede, "why": "They set different leave."}],
            "authority_evidence": ""}


async def put_people(fresh):
    for p in PEOPLE:
        await fresh.put("people", {**p, "id": f"acme-{p['id']}", "workspace": "acme"})


def src(text, author, ts, title="Leave policy", kind="doc"):
    return Source(kind=kind, title=title, author=author, ts=ts, text=text)


async def ing(s):
    return await core.ingest(IngestRequest(source=s), ["acme"])


async def test_versions_by_date_and_claims(fresh):
    await put_people(fresh)
    llm.FAKE_RESPONSES.update({"PremiseCheck": {"broken": []}, "StaleCheck": {"stale": []}})
    llm.FAKE_RESPONSES["Extraction"] = ex("Staff get 22 days of leave.", "22 days of leave", "leave policy",
                                          effective="2026-11-01")
    v4 = await ing(src("Leave policy v4. Effective 1 November 2026. Staff get 22 days of leave.", "Amina Yusuf",
                       "2026-10-01T00:00:00Z"))
    assert v4.decisions[0].decision.authority == "official"
    assert v4.decisions[0].decision.effective_at == datetime(2026, 11, 1, tzinfo=timezone.utc)

    # the old v2 arrives later but is dated earlier: an outdated copy, never an update
    llm.FAKE_RESPONSES["Extraction"] = ex("Staff get 18 days of leave.", "18 days of leave", "leave policy")
    llm.FAKE_RESPONSES["Judgement"] = judge()
    v2 = await ing(src("Leave policy v2. Effective 1 March 2026. Staff get 18 days of leave.", "Amina Yusuf",
                       "2026-10-15T00:00:00Z"))
    d = v2.decisions[0]
    assert d.decision.status == "superseded" and d.decision.superseded_by == v4.decisions[0].decision.id
    assert [(a.kind, a.severity) for a in v2.alerts] == [("stale_doc", "low")]
    assert v2.alerts[0].explanation.startswith("Outdated copy:")
    assert (await fresh.get("decisions", v4.decisions[0].decision.id))["status"] == "active"

    # an engineer posting a leave policy is a claim: unverified, addressed to the topic owner, no supersede
    llm.FAKE_RESPONSES["Extraction"] = ex("Staff get 30 days of leave.", "30 days of leave", "leave policy")
    c = await ing(src("New rule: staff get 30 days of leave.", "Pranav Menon", "2026-10-16T00:00:00Z", "chat", "slack"))
    a = c.alerts[0]
    assert c.decisions[0].decision.authority == "claim" and (a.kind, a.severity) == ("contradiction", "low")
    assert a.explanation.startswith("Unverified:") and "Amina Yusuf (People operations partner) should confirm" in a.explanation
    assert (await fresh.get("decisions", v4.decisions[0].decision.id))["status"] == "active"

    # a joke is never stored
    llm.FAKE_RESPONSES["Extraction"] = ex("Leave is unlimited on Fridays.", "unlimited on Fridays", "leave", joke=True)
    j = await ing(src("lol leave is unlimited on Fridays", "Pranav Menon", "2026-10-16T01:00:00Z", "chat", "slack"))
    assert j.decisions == [] and j.alerts == []

    stats = await store.stats(["acme"])
    assert stats == {"sources": 4, "decisions": 3, "decisions_official": 2, "stale_docs": 1, "open_alerts": 2,
                     "people": len(PEOPLE)}


async def test_archived_threads_listed_at_most_every_30_minutes(monkeypatch, fresh):
    from tests.test_w17_discord import FakeDiscord
    monkeypatch.setenv("CANON_DISCORD_GUILD_ID", "g1")
    monkeypatch.delenv("CANON_DISCORD_CHANNELS", raising=False)
    fake = FakeDiscord()
    assert "300" in [c["id"] for c in await ds.channels(fake)]
    fake.calls.clear()
    found = await ds.channels(fake)
    assert "/channels/100/threads/archived/public" not in fake.calls and "300" not in [c["id"] for c in found]
