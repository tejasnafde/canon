"""W14: pull sync from Discord. No gateway, so Cloud Run can scale to zero.

A scheduler POSTs /hooks/discord/sync every minute. For each channel we fetch messages after the
last seen id, group them (a thread is one group, a channel is split into 10-minute windows),
ingest each group into workspace "discord", and reply to the message that breaks a decision.
"""
import asyncio
import logging
import os
import time
from datetime import datetime, timedelta, timezone

import httpx

from canon import core, llm, store
from canon.connectors import state
from canon.models import IngestRequest, Source

log = logging.getLogger("canon.discord_sync")
API = "https://discord.com/api/v10"
WS = "discord"
BASE = os.environ.get("CANON_BASE_WS", "acme")
SCOPE = [BASE, WS]
MIN_CHARS = 15
WINDOW = timedelta(minutes=10)
PAGE = 50  # messages per channel per sync; the rest arrive on the next run
USER_DAILY_LIMIT = 20
TEXT, THREADS = {0, 5}, {10, 11, 12}  # text/announcement channels, thread channels
_lock = asyncio.Lock()  # ponytail: per instance; overlapping syncs on 2+ instances could double ingest


class DiscordClient:
    def __init__(self, token: str):
        self.h = {"Authorization": f"Bot {token}"}

    async def get(self, path: str, params: dict | None = None):
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(API + path, params=params, headers=self.h)
            r.raise_for_status()
            return r.json()

    async def post(self, path: str, json: dict):
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(API + path, json=json, headers=self.h)
            r.raise_for_status()
            return r.json()


def ts(m: dict) -> datetime:
    return datetime.fromisoformat(m["timestamp"])


def eligible(m: dict) -> bool:
    return (not m["author"].get("bot") and not m.get("webhook_id") and m.get("type", 0) in (0, 19)
            and len(m.get("content", "").strip()) >= MIN_CHARS)


def group(msgs: list[dict], is_thread: bool) -> list[list[dict]]:
    """Messages sorted oldest first. A thread is one group; a channel is split into 10-minute windows."""
    if is_thread:
        return [msgs] if msgs else []
    out: list[list[dict]] = []
    for m in msgs:
        if out and ts(m) - ts(out[-1][0]) <= WINDOW:
            out[-1].append(m)
        else:
            out.append([m])
    return out


def jump(guild: str, channel: str, msg: str) -> str:
    return f"https://discord.com/channels/{guild}/{channel}/{msg}"


def day_key() -> str:
    return f"discord-daily-{datetime.now(timezone.utc):%Y-%m-%d}"


async def allow(user: str) -> bool:
    """Daily cost guard: total and per-user message budget, counted in connector_state."""
    limit = int(os.environ.get("CANON_DISCORD_DAILY_LIMIT", "200"))
    key = day_key()
    d = await state.get(key)
    users = d.get("users", {})
    if d.get("total", 0) >= limit:
        if not d.get("warned"):
            log.warning("discord daily limit %d reached, skipping messages until 00:00 UTC", limit)
            await state.merge(key, {"warned": True})
        return False
    if users.get(user, 0) >= USER_DAILY_LIMIT:
        return False
    await state.merge(key, {"total": d.get("total", 0) + 1, "users": {**users, user: users.get(user, 0) + 1}})
    return True


async def decision_line(alert) -> str | None:
    """'This goes against: ...' for the decision an alert says was broken."""
    did = alert.related_decision_id if alert.kind == "contradiction" and alert.related_decision_id \
        else alert.decision_id
    d = await store.get_store().get("decisions", did) if did else None
    if not d:
        return None
    url = os.environ.get("CANON_PUBLIC_URL", "https://canon.tn07.dev").rstrip("/")
    when = store.utc(d["ts"]).strftime("%Y-%m-%d")
    return f"This goes against: {d['statement']} (decided by {d['owner']} on {when}). {url}/decisions/{d['id']}"


def _norm(s: str) -> str:
    return " ".join(s.split()).lower()


def target(msgs: list[dict], alert) -> dict:
    """The message an alert quotes, else the last message of the group."""
    for q in alert.quotes:
        for m in msgs:
            if q.quote and _norm(q.quote) in _norm(m["content"]):
                return m
    return msgs[-1]


async def ingest_group(msgs: list[dict], channel: dict, client) -> list[str]:
    """Ingest one group as a Source; reply once per message that breaks a decision. Returns replies."""
    first = msgs[0]
    user = first["author"]["username"]
    src = Source(workspace=WS, kind="paste", title=f"Discord #{channel['name']}"[:300], author=user,
                 ts=ts(first), url=jump(channel["guild_id"], channel["id"], first["id"]), synthetic=False,
                 text="\n".join(f"{m['author']['username']}: {m['content']}" for m in msgs)[:50_000])
    llm.deadline.set(time.monotonic() + 60)  # each group gets its own model budget
    r = await core.ingest(IngestRequest(source=src, actor=f"human:discord/{user}"[:100]), SCOPE)
    replied: set[str] = set()
    sent = []
    for a in r.alerts:
        if a.kind not in ("contradiction", "agent_violation"):
            continue
        m = target(msgs, a)
        if m["id"] in replied or not (line := await decision_line(a)):
            continue
        replied.add(m["id"])
        await client.post(f"/channels/{channel['id']}/messages",
                          {"content": line[:2000], "message_reference": {"message_id": m["id"]},
                           "allowed_mentions": {"parse": []}})
        sent.append(line)
    return sent


async def channels(client) -> list[dict]:
    """Configured channel ids, or every text channel plus active thread in the guild."""
    ids = [c.strip() for c in os.environ.get("CANON_DISCORD_CHANNELS", "").split(",") if c.strip()]
    if ids:
        return list(await asyncio.gather(*(client.get(f"/channels/{i}") for i in ids)))
    gid = os.environ.get("CANON_DISCORD_GUILD_ID", "")
    if not gid:
        return []
    chans = [c for c in await client.get(f"/guilds/{gid}/channels") if c["type"] in TEXT]
    threads = (await client.get(f"/guilds/{gid}/threads/active")).get("threads", [])
    return chans + [t for t in threads if t["type"] in THREADS]


async def sync_channel(channel: dict, client) -> dict:
    key = f"discord-{channel['id']}"
    cursor = (await state.get(key)).get("last_id")
    params = {"limit": PAGE, **({"after": cursor} if cursor else {})}  # first run: latest PAGE only
    msgs = sorted(await client.get(f"/channels/{channel['id']}/messages", params), key=lambda m: int(m["id"]))
    if not msgs:
        return {"channel": channel["name"], "fetched": 0, "ingested": 0, "replies": 0}
    keep = [m for m in msgs if eligible(m) and await allow(m["author"]["username"])]
    replies = 0
    for g in group(keep, channel["type"] in THREADS):
        try:
            replies += len(await ingest_group(g, channel, client))
        except Exception:  # one bad group must not block the channel; its cursor still advances
            log.exception("discord ingest failed for #%s", channel.get("name"))
    await state.merge(key, {"last_id": msgs[-1]["id"], "channel": channel.get("name"), "synced_at": store.now()})
    return {"channel": channel["name"], "fetched": len(msgs), "ingested": len(keep), "replies": replies}


async def sync(client=None) -> dict:
    if _lock.locked():
        return {"busy": True}
    async with _lock:
        client = client or DiscordClient(os.environ["CANON_DISCORD_BOT_TOKEN"])
        out = []
        for c in await channels(client):
            try:
                out.append(await sync_channel(c, client))
            except httpx.HTTPError as e:  # e.g. no access to one channel; keep going
                log.warning("discord sync of %s failed: %s", c.get("id"), e)
        return {"channels": out}
