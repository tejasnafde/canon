"""W14/W17: pull sync from Discord. No gateway, so Cloud Run can scale to zero.

A scheduler POSTs /hooks/discord/sync every minute. For each text channel, active thread and recently
archived public thread we fetch messages after the last seen id (one cursor per channel or thread),
group them (a thread is one group, a channel is split into 10-minute windows), ingest each group into
workspace "discord", and reply to the message that breaks a decision (inside the thread if it is one).
Text attachments (.md .txt .csv) join the group text; each image goes through multimodal ingest alone.
"""
import asyncio
import base64
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
TEXT_FILES, TEXT_MAX = (".md", ".txt", ".csv"), 200_000
IMAGE_FILES, IMAGE_MAX = (".png", ".jpg", ".jpeg", ".webp", ".pdf"), 10_000_000  # Gemini reads PDFs natively
ARCHIVED_DAYS = 14  # archived threads older than this are not read again
ARCHIVED_EVERY = timedelta(minutes=30)  # archived threads are listed at most this often (one call per channel)
_lock = asyncio.Lock()  # ponytail: per instance; overlapping syncs on 2+ instances could double ingest


class DiscordClient:
    def __init__(self, token: str):
        self.h = {"Authorization": f"Bot {token}"}
        self._c: httpx.AsyncClient | None = None

    async def get(self, path: str, params: dict | None = None):
        # One kept-alive connection for the whole sync: a fresh TLS handshake per call was most of a quiet run.
        if self._c is None:
            self._c = httpx.AsyncClient(timeout=10)
        for _ in range(3):
            r = await self._c.get(API + path, params=params, headers=self.h)
            if r.status_code != 429:
                break
            await asyncio.sleep(min(float(r.json().get("retry_after", 1)), 5))
        r.raise_for_status()
        return r.json()

    async def aclose(self):
        if self._c is not None:
            await self._c.aclose()

    async def download(self, url: str, limit: int) -> bytes:
        """Attachment bytes from the CDN (signed URL, no auth header), at most `limit` bytes."""
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as c:
            r = await c.get(url)
            r.raise_for_status()
            return r.content[:limit]

    async def post(self, path: str, json: dict):
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(API + path, json=json, headers=self.h)
            r.raise_for_status()
            return r.json()


def ts(m: dict) -> datetime:
    return datetime.fromisoformat(m["timestamp"])


def file_kind(a: dict) -> str | None:
    """'text' or 'image' for an attachment we read, None for anything else or anything too big."""
    name, size = a.get("filename", "").lower(), a.get("size", 0)
    if name.endswith(TEXT_FILES) and size <= TEXT_MAX:
        return "text"
    if name.endswith(IMAGE_FILES) and size <= IMAGE_MAX:
        return "image"
    return None


def eligible(m: dict) -> bool:
    return (not m["author"].get("bot") and not m.get("webhook_id") and m.get("type", 0) in (0, 19)
            and (len(m.get("content", "").strip()) >= MIN_CHARS
                 or any(file_kind(a) for a in m.get("attachments", []))))


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


def title_of(channel: dict) -> str:
    if channel.get("parent_name"):
        return f"Discord #{channel['parent_name']} / {channel['name']}"[:300]
    return f"Discord #{channel['name']}"[:300]


async def ingest_source(src: Source, msgs: list[dict], channel: dict, client, replied: set[str]) -> list[str]:
    """Ingest one Source; reply once per message that breaks a decision. Returns the replies sent."""
    user = src.author
    llm.deadline.set(time.monotonic() + 60)  # each source gets its own model budget
    r = await core.ingest(IngestRequest(source=src, actor=f"human:discord/{user}"[:100]), SCOPE)
    sent = []
    for a in r.alerts:
        if a.kind not in ("contradiction", "agent_violation"):
            continue
        m = target(msgs, a)
        if m["id"] in replied or not (line := await decision_line(a)):
            continue
        replied.add(m["id"])
        # channel["id"] is the thread id for a thread, so the reply lands inside the thread
        await client.post(f"/channels/{channel['id']}/messages",
                          {"content": line[:2000], "message_reference": {"message_id": m["id"]},
                           "allowed_mentions": {"parse": []}})
        sent.append(line)
    return sent


async def ingest_group(msgs: list[dict], channel: dict, client) -> list[str]:
    """One text Source for the group (with text attachments inlined), plus one Source per image."""
    first, title = msgs[0], title_of(channel)
    lines, images, docs = [], [], 0
    for m in msgs:
        who = m["author"]["username"]
        parts = [f"{who}: {m['content']}"] if m.get("content", "").strip() else []
        for a in m.get("attachments", []):
            kind = file_kind(a)
            try:
                if kind == "text":
                    body = (await client.download(a["url"], TEXT_MAX)).decode("utf-8", "replace")
                    parts.append(f"{who} attached {a['filename']}:\n{body}")
                    docs += 1
                elif kind == "image":
                    images.append((m, a, await client.download(a["url"], IMAGE_MAX)))
            except httpx.HTTPError as e:
                log.warning("discord attachment %s unreadable: %s", a.get("filename"), e)
        lines += parts
    replied: set[str] = set()
    sent = []
    text = "\n".join(lines)
    if any(len(m.get("content", "").strip()) >= MIN_CHARS for m in msgs) or docs:
        src = Source(workspace=WS, kind="paste", title=title, author=first["author"]["username"], ts=ts(first),
                     url=jump(channel["guild_id"], channel["id"], first["id"]), synthetic=False, text=text[:50_000])
        sent += await ingest_source(src, msgs, channel, client, replied)
    for m, a, data in images:
        who = m["author"]["username"]
        context = m.get("content", "").strip() or f"Image shared by {who} in {title}."
        src = Source(workspace=WS, kind="paste", title=f"{title} / {a['filename']}"[:300], author=who, ts=ts(m),
                     url=jump(channel["guild_id"], channel["id"], m["id"]), synthetic=False,
                     text=f"{who}: {context}", image_b64=base64.b64encode(data).decode())
        try:
            sent += await ingest_source(src, [m], channel, client, replied)
        except Exception:  # one unreadable image must not drop the rest of the group
            log.exception("discord image ingest failed for %s", a.get("filename"))
    return sent


def archived_at(t: dict) -> datetime:
    raw = (t.get("thread_metadata") or {}).get("archive_timestamp")
    return datetime.fromisoformat(raw) if raw else datetime.now(timezone.utc)


async def channels(client) -> list[dict]:
    """Configured channel ids (or every text channel in the guild), then their active threads and
    their public threads archived in the last ARCHIVED_DAYS. Threads carry `parent_name`."""
    ids = [c.strip() for c in os.environ.get("CANON_DISCORD_CHANNELS", "").split(",") if c.strip()]
    gid = os.environ.get("CANON_DISCORD_GUILD_ID", "")
    active = client.get(f"/guilds/{gid}/threads/active") if gid else asyncio.sleep(0, {})
    if ids:
        *chans, act = await asyncio.gather(*(client.get(f"/channels/{i}") for i in ids), active)
    elif gid:
        listed, act = await asyncio.gather(client.get(f"/guilds/{gid}/channels"), active)
        chans = [c for c in listed if c["type"] in TEXT]
    else:
        return []
    names = {c["id"]: c["name"] for c in chans if c["type"] in TEXT}
    found = list(act.get("threads", []))
    cutoff = datetime.now(timezone.utc) - timedelta(days=ARCHIVED_DAYS)
    scan = (await state.get("discord-archived-scan")).get("at")
    if scan and datetime.now(timezone.utc) - store.utc(scan) < ARCHIVED_EVERY:
        names_to_scan = []  # a thread that gets a new message is unarchived, so it shows up as active anyway
    else:
        names_to_scan = list(names)
        await state.merge("discord-archived-scan", {"at": store.now()})
    async def archived(cid):
        try:
            return await client.get(f"/channels/{cid}/threads/archived/public", {"limit": 50})
        except httpx.HTTPError as e:
            log.warning("discord archived threads of %s unreadable: %s", cid, e)
            return None
    for old in await asyncio.gather(*(archived(c) for c in names_to_scan)):
        if isinstance(old, dict):
            found += [t for t in old.get("threads", []) if archived_at(t) >= cutoff]
    out, seen = list(chans), {c["id"] for c in chans}
    for t in found:
        if t["type"] in THREADS and t.get("parent_id") in names and t["id"] not in seen:
            seen.add(t["id"])
            out.append({**t, "parent_name": names[t["parent_id"]]})
    return out


async def starter(thread: dict, client) -> dict | None:
    """The channel message a thread was started from (it lives in the parent, not in the thread)."""
    try:
        return await client.get(f"/channels/{thread['parent_id']}/messages/{thread['id']}")
    except httpx.HTTPError:  # thread not started from a message, or the message is gone
        return None


async def sync_channel(channel: dict, client, cursor: str | None = None, read: bool = True) -> dict:
    key = f"discord-{channel['id']}"
    if read:
        cursor = (await state.get(key)).get("last_id")
    name = channel.get("parent_name", "") + "/" * bool(channel.get("parent_name")) + channel["name"]
    idle = {"channel": name, "fetched": 0, "ingested": 0, "replies": 0}
    last = channel.get("last_message_id")
    if cursor and last and int(last) <= int(cursor):
        return idle  # nothing new since the last run; saves one API call per idle channel
    is_thread = channel["type"] in THREADS
    params = {"limit": PAGE, **({"after": cursor} if cursor else {})}  # first run: latest PAGE only
    msgs = sorted(await client.get(f"/channels/{channel['id']}/messages", params), key=lambda m: int(m["id"]))
    if is_thread and not cursor and channel.get("parent_id") and (first := await starter(channel, client)):
        msgs = [first, *[m for m in msgs if m["id"] != first["id"]]]
    if not msgs:
        return idle
    # a message that started a thread is ingested with its thread, not with the channel window
    keep = [m for m in msgs if eligible(m) and not (not is_thread and m.get("thread"))
            and await allow(m["author"]["username"])]
    replies = 0
    for g in group(keep, is_thread):
        try:
            replies += len(await ingest_group(g, channel, client))
        except Exception:  # one bad group must not block the channel; its cursor still advances
            log.exception("discord ingest failed for #%s", name)
    newest = max(msgs, key=lambda m: int(m["id"]))["id"]
    await state.merge(key, {"last_id": newest, "channel": name, "synced_at": store.now()})
    return {"channel": name, "fetched": len(msgs), "ingested": len(keep), "replies": replies}


async def sync(client=None) -> dict:
    if _lock.locked():
        return {"busy": True}
    async with _lock:
        own = client is None
        client = client or DiscordClient(os.environ["CANON_DISCORD_BOT_TOKEN"])
        out = []
        chans = await channels(client)
        cursors = await state.get_many([f"discord-{c['id']}" for c in chans])  # one read, not one per channel
        for c in chans:
            try:
                out.append(await sync_channel(c, client, cursors.get(f"discord-{c['id']}", {}).get("last_id"), False))
            except httpx.HTTPError as e:  # e.g. no access to one channel; keep going
                log.warning("discord sync of %s failed: %s", c.get("id"), e)
        if own:
            await client.aclose()
        return {"channels": out}
