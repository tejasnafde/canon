"""W14 live Discord connector: sync grouping, cursors, skips, limits, replies. No network."""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from nacl.signing import SigningKey

from canon import core, discord
from canon.connectors import discord_sync as ds, state
from canon.models import Alert, IngestResult, Quote

T0 = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
CHAN = {"id": "c1", "name": "eng", "guild_id": "g1", "type": 0}


def msg(i, text, minutes=0, user="ishank", bot=False):
    return {"id": str(i), "content": text, "type": 0, "timestamp": (T0 + timedelta(minutes=minutes)).isoformat(),
            "author": {"username": user, **({"bot": True} if bot else {})}}


class FakeDiscord:
    def __init__(self, msgs):
        self.msgs, self.posts, self.params = msgs, [], []

    async def get(self, path, params=None):
        if path == "/channels/c1":
            return CHAN
        self.params.append(params)
        after = int((params or {}).get("after", 0))
        return [m for m in reversed(self.msgs) if int(m["id"]) > after]  # Discord returns newest first

    async def post(self, path, json):
        self.posts.append((path, json))
        return {}


@pytest.fixture
def ingested(monkeypatch, fresh):
    """Fake core.ingest: any text mentioning Friday contradicts the seeded Friday decision."""
    calls = []
    fresh.db["decisions"]["d-friday"] = {
        "id": "d-friday", "workspace": "acme", "statement": "No production deploys on Fridays",
        "owner": "Priya Rao", "ts": datetime(2026, 3, 14, tzinfo=timezone.utc), "created_at": T0}

    async def ingest(req, ws):
        calls.append((req, ws))
        alerts = []
        if "friday" in req.source.text.lower():
            alerts = [Alert(id="a1", workspace="discord", kind="contradiction", severity="high", decision_id="d-new",
                            related_decision_id="d-friday", explanation="x", created_at=T0,
                            quotes=[Quote(source_id="s", quote="ship the  release on Friday")])]
        return IngestResult(source=req.source, decisions=[], alerts=alerts, latency_ms=1)

    monkeypatch.setattr(core, "ingest", ingest)
    monkeypatch.setenv("CANON_DISCORD_CHANNELS", "c1")
    monkeypatch.setenv("CANON_PUBLIC_URL", "https://canon.tn07.dev/")
    return calls


async def test_sync_groups_skips_replies_and_advances_cursor(ingested, monkeypatch):
    from canon.models import AskResult

    async def ask(req, ws):  # the projector question is unanswerable, so Canon stays silent
        return AskResult(answer="I do not know.", citations=[], refused=True, latency_ms=1)
    monkeypatch.setattr(core, "ask", ask)
    fake = FakeDiscord([
        msg(1, "We should move the billing service to Postgres."),
        msg(2, "ok"),  # too short
        msg(3, "Deploy bot finished release 4.2 successfully.", bot=True),
        msg(4, "Agreed, and let us ship the release on Friday.", minutes=3, user="mitushi"),
        msg(5, "Unrelated: who has the projector key for room B?", minutes=30),
    ])
    out = await ds.sync(fake)
    assert out["channels"][0] == {"channel": "eng", "fetched": 5, "ingested": 3, "replies": 1}
    assert len(ingested) == 2  # 1+4 in one 10-minute window, 5 alone
    req, ws = ingested[0]
    assert ws == ["acme", "discord"] and req.source.workspace == "discord"
    assert req.source.kind == "paste" and req.source.title == "Discord #eng" and not req.source.synthetic
    assert req.source.url == "https://discord.com/channels/g1/c1/1" and req.actor == "human:discord/ishank"
    assert "mitushi: Agreed" in req.source.text
    # reply goes to the quoted message, once, plain text
    path, body = fake.posts[0]
    assert path == "/channels/c1/messages" and body["message_reference"] == {"message_id": "4"}
    assert body["content"] == ("This goes against: No production deploys on Fridays (decided by Priya Rao on "
                               "2026-03-14). https://canon.tn07.dev/decisions/d-friday")
    assert (await state.get("discord-c1"))["last_id"] == "5"
    # next run asks only for newer messages and ingests nothing
    out = await ds.sync(fake)
    assert fake.params[-1]["after"] == "5" and out["channels"][0]["fetched"] == 0 and len(ingested) == 2


async def test_thread_is_one_group(ingested):
    msgs = [msg(1, "Thread start about the deploy policy.", 0), msg(2, "Second reply much later in thread.", 90)]
    assert len(ds.group(msgs, is_thread=True)) == 1 and len(ds.group(msgs, is_thread=False)) == 2


async def test_daily_and_user_limits(ingested, monkeypatch, caplog):
    monkeypatch.setenv("CANON_DISCORD_DAILY_LIMIT", "22")
    assert all([await ds.allow("a") for _ in range(20)])
    assert not await ds.allow("a")  # per-user cap 20
    assert await ds.allow("b") and await ds.allow("b")
    assert not await ds.allow("c") and not await ds.allow("c")  # total cap 22
    assert sum("daily limit" in r.message for r in caplog.records) == 1  # warn once


async def test_sync_token(monkeypatch):
    monkeypatch.setenv("CANON_SYNC_TOKEN", "s3cret")
    for bad in (None, "", "nope"):
        with pytest.raises(HTTPException):
            await discord.sync(bad)
    monkeypatch.delenv("CANON_SYNC_TOKEN")
    with pytest.raises(HTTPException):  # unset token never matches
        await discord.sync("")


def test_signature():
    key = SigningKey.generate()
    pub, body, t = key.verify_key.encode().hex(), b'{"type":1}', "1700000000"
    sig = key.sign(t.encode() + body).signature.hex()
    assert discord.verify(pub, body, sig, t)
    assert not discord.verify(pub, body + b" ", sig, t)
    assert not discord.verify(pub, body, "zz", t) and not discord.verify("", body, sig, t)


async def test_remember_and_catchup_role(ingested, monkeypatch):
    out = await discord.answer("remember", {"text": "We will ship the release on Friday from now on."}, "tejas")
    assert out.startswith("Remembered: 0 decisions, 1 alerts.") and "No production deploys on Fridays" in out
    req, ws = ingested[-1]
    assert req.source.workspace == "discord" and req.actor == "human:discord/tejas" and ws == ["acme", "discord"]
    seen = []

    async def briefing(req, ws):
        seen.append(req.persona)
        raise RuntimeError("stop")

    monkeypatch.setattr(core, "briefing", briefing)
    with pytest.raises(RuntimeError):
        await discord.answer("catchup", {"role": "legal"}, "tejas")
    assert seen == ["legal"]


def test_register_lists_every_persona():
    from typing import get_args

    from canon.models import Persona
    from scripts.register_discord import COMMAND
    sub = {o["name"]: o for o in COMMAND["options"]}
    assert set(sub) == {"ask", "check", "catchup", "remember"}
    assert [c["value"] for c in sub["catchup"]["options"][0]["choices"]] == list(get_args(Persona))


async def test_questions_get_answers(ingested, monkeypatch):
    from canon.connectors import discord_sync as ds
    from canon.models import AskResult, CheckResult
    assert ds.question_of(msg(1, "Can i migrate my service to convex")) == ("Can i migrate my service to convex", False)
    assert ds.question_of(msg(2, "what is our tech stack")) and ds.question_of(msg(3, "lunch is here")) is None
    monkeypatch.setenv("CANON_DISCORD_APP_ID", "99")
    assert ds.question_of(msg(4, "<@99> tech stack please")) == ("tech stack please", True)

    async def check(req, ws):
        return CheckResult(verdict="warn", explanation="No decision covers Convex yet.", decisions=[], citations=[], latency_ms=1)

    async def ask(req, ws):
        return AskResult(answer="Python and Postgres.", citations=[], refused=False, latency_ms=1)
    monkeypatch.setattr(core, "check", check)
    monkeypatch.setattr(core, "ask", ask)
    fake = FakeDiscord([msg(10, "Can i migrate my service to convex"), msg(11, "lunch is here today folks")])
    sent = await ds.ingest_group(fake.msgs, CHAN, fake)
    assert sent == ["Warn: No decision covers Convex yet."]
    assert fake.posts[-1][1]["message_reference"] == {"message_id": "10"}
