"""W17 Discord sync v2: threads (active and archived), attachments, per-thread cursors, skips. No network."""
import base64
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from canon import core
from canon.connectors import discord_sync as ds, state
from canon.models import Alert, IngestResult, Quote

T0 = datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc)
NOW = datetime.now(timezone.utc)
ENG = {"id": "100", "name": "engineering", "guild_id": "g1", "type": 0}
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32


def msg(i, text, minutes=0, user="ishank", **kw):
    return {"id": str(i), "content": text, "type": 0, "timestamp": (T0 + timedelta(minutes=minutes)).isoformat(),
            "author": {"username": user}, **kw}


def thread(tid, name, archived_days=None, last=None):
    meta = {"archive_timestamp": (NOW - timedelta(days=archived_days)).isoformat()} if archived_days else {}
    return {"id": str(tid), "name": name, "type": 11, "parent_id": "100", "guild_id": "g1",
            "thread_metadata": meta, **({"last_message_id": str(last)} if last else {})}


def att(name, size=100, url=None):
    return {"filename": name, "size": size, "url": url or f"https://cdn/{name}"}


class FakeDiscord:
    """Channel 100 with one active thread 200 and one archived thread 300 (plus one too old to read)."""

    def __init__(self):
        self.msgs = {
            "100": [msg(200, "Starting a thread about the Friday release window here.", thread={"id": "200"}),
                    msg(150, "Lunch is on the third floor today, bring a mug.")],
            "200": [msg(201, "I think we should ship the release on Friday again.", 1, "mitushi"),
                    msg(202, "Deploy bot finished 4.2", 2, author={"username": "ci", "bot": True}),
                    msg(203, "Archive repost from the old Slack thread.", 3, webhook_id="w1")],
            "300": [msg(301, "here is the release doc pls read before friday", 0, "tejas",
                        attachments=[att("Release process.md"), att("huge.md", size=300_000), att("x.zip")]),
                    msg(302, "", 5, "tejas", attachments=[att("latency.png")])],
            "400": [msg(401, "Too old to read again, this thread was archived long ago.")],
        }
        self.files = {"https://cdn/Release process.md": b"# Release process\nFriday 14:00 to 16:00 SGT is the window.",
                      "https://cdn/latency.png": PNG}
        self.posts, self.calls = [], []

    async def get(self, path, params=None):
        self.calls.append(path)
        if path == "/guilds/g1/channels":
            return [ENG, {"id": "999", "name": "voice", "type": 2}]
        if path == "/guilds/g1/threads/active":
            return {"threads": [thread(200, "Release window", last=self.msgs["200"][-1]["id"])]}
        if path == "/channels/100/threads/archived/public":
            return {"threads": [thread(300, "Release doc", archived_days=2), thread(400, "Ancient", archived_days=40)]}
        if path == "/channels/100/messages/200":
            return self.msgs["100"][0]
        if path.startswith("/channels/100/messages/"):
            raise httpx.HTTPError("404 thread not started from a message")
        cid = path.split("/")[2]
        after = int((params or {}).get("after", 0))
        return [m for m in reversed(self.msgs[cid]) if int(m["id"]) > after]

    async def post(self, path, json):
        self.posts.append((path, json))
        return {}

    async def download(self, url, limit):
        return self.files[url][:limit]


@pytest.fixture
def ingested(monkeypatch, fresh):
    calls = []
    fresh.db["decisions"]["d-friday"] = {
        "id": "d-friday", "workspace": "acme", "statement": "No production deploys on Fridays",
        "owner": "Anika Rao", "ts": datetime(2026, 3, 9, tzinfo=timezone.utc), "created_at": T0}

    async def ingest(req, ws):
        calls.append(req.source)
        alerts = []
        if "ship the release on friday" in req.source.text.lower():
            alerts = [Alert(id="a1", workspace="discord", kind="contradiction", severity="high", decision_id="d-new",
                            related_decision_id="d-friday", explanation="x", created_at=T0,
                            quotes=[Quote(source_id="s", quote="ship the release on Friday")])]
        return IngestResult(source=req.source, decisions=[], alerts=alerts, latency_ms=1)

    monkeypatch.setattr(core, "ingest", ingest)
    monkeypatch.delenv("CANON_DISCORD_CHANNELS", raising=False)
    monkeypatch.setenv("CANON_DISCORD_GUILD_ID", "g1")
    return calls


async def test_threads_are_found_with_parent_name(ingested):
    found = await ds.channels(FakeDiscord())
    assert [c["id"] for c in found] == ["100", "200", "300"]  # voice channel and 40-day-old thread left out
    assert found[1]["parent_name"] == "engineering" and ds.title_of(found[1]) == "Discord #engineering / Release window"
    assert ds.title_of(found[0]) == "Discord #engineering"


async def test_thread_is_one_source_with_its_starter_and_reply_lands_in_thread(ingested):
    fake = FakeDiscord()
    out = await ds.sync(fake)
    by_title = {s.title: s for s in ingested}
    # the thread starter is not ingested with the channel window, only with its thread
    assert by_title["Discord #engineering"].text == "ishank: Lunch is on the third floor today, bring a mug."
    t = by_title["Discord #engineering / Release window"]
    assert t.text.splitlines() == ["ishank: Starting a thread about the Friday release window here.",
                                   "mitushi: I think we should ship the release on Friday again."]  # bot, webhook skipped
    assert t.url == "https://discord.com/channels/g1/200/200"
    path, body = fake.posts[0]
    assert path == "/channels/200/messages" and body["message_reference"] == {"message_id": "201"}
    rows = {r["channel"]: r for r in out["channels"]}
    assert rows["engineering/Release window"] == {"channel": "engineering/Release window", "fetched": 4,
                                                  "ingested": 2, "replies": 1}


async def test_text_and_image_attachments(ingested):
    await ds.sync(FakeDiscord())
    doc = next(s for s in ingested if s.title == "Discord #engineering / Release doc")
    assert "tejas attached Release process.md:\n# Release process\nFriday 14:00" in doc.text
    assert "huge.md" not in doc.text and "x.zip" not in doc.text and doc.image_b64 is None
    img = next(s for s in ingested if s.title == "Discord #engineering / Release doc / latency.png")
    assert base64.b64decode(img.image_b64) == PNG and img.url.endswith("/300/302")
    assert img.text == "tejas: Image shared by tejas in Discord #engineering / Release doc."
    assert ds.file_kind(att("a.csv")) == "text" and ds.file_kind(att("b.webp", 6_000_000)) is None


async def test_cursor_per_thread_and_idle_skip(ingested):
    fake = FakeDiscord()
    await ds.sync(fake)
    assert (await state.get("discord-200"))["last_id"] == "203"
    assert (await state.get("discord-300"))["last_id"] == "302"
    n = len(ingested)
    fake.calls.clear()
    await ds.sync(fake)
    assert len(ingested) == n  # nothing new anywhere
    assert "/channels/200/messages" not in fake.calls  # last_message_id == cursor, no fetch
    fake.msgs["200"].append(msg(204, "Follow-up in the thread about the rollback buddy.", 9, "ishank"))
    await ds.sync(fake)
    assert ingested[-1].title == "Discord #engineering / Release window"
    assert ingested[-1].text == "ishank: Follow-up in the thread about the rollback buddy."  # starter not repeated
