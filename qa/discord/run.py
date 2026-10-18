"""Discord QA: real Discord API, in-process sync, throwaway workspace. Nothing is redeployed.

Run (from backend/):  uv run python ../qa/discord/run.py
Needs: gcloud personal config (reads secret canon-config) and .secrets/sa-canon.json.

QA mode, harness only: CANON_QA_CHANNEL makes webhook messages in THAT channel eligible as if a human sent
them (author = webhook username). The sync normally skips webhooks. The product change would be one clause in
connectors/discord_sync.eligible(); that file belonged to another workstream, so the harness patches it here.

Isolation: writes go to workspace v-qa-discord-<hex> (reset at the end), connector state keys get a "qa-"
prefix (the live cursors and daily counters are untouched), and only the qa-canon channel is read.
The channel is deleted at the end, also on failure.
"""
import asyncio
import json
import os
import subprocess
import sys
import time
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GCLOUD = "/opt/homebrew/share/google-cloud-sdk/bin/gcloud"
os.environ["CANON_CONFIG"] = subprocess.run(
    [GCLOUD, "--configuration=personal", "secrets", "versions", "access", "latest", "--secret=canon-config",
     "--project=teejayproject"], check=True, capture_output=True, text=True).stdout
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.environ.get("QA_SA_KEY", "/Users/tejas/Desktop/projects/google-hackathon/canon/.secrets/sa-canon.json")
os.environ.setdefault("CANON_BASE_WS", "acme4")  # the live base workspace; "acme" has no people, so all is official
os.environ.pop("CANON_MEMORY_STORE", None)
os.environ.pop("CANON_FAKE_LLM", None)

import httpx  # noqa: E402

from canon import authority, llm, store  # noqa: E402
from canon.connectors import discord_sync as ds, state  # noqa: E402

API = ds.API
WS = f"v-qa-discord-{uuid.uuid4().hex[:8]}"
FILES = "/tmp/canon-qa"
results: list[tuple[str, bool, str]] = []
STEPS = set(os.environ.get("QA_STEPS", "0,1,2,3,4,5,6,7,9,10").split(","))  # QA_STEPS=0,1,4 re-runs a few
spent = {"generate": 0}


def case(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}"[:400], flush=True)


# ---- harness patches ----
_charge = llm._charge


def counted():
    spent["generate"] += 1
    if spent["generate"] > 35:
        raise llm.BudgetExceeded("QA harness cap of 35 generate calls")
    _charge()


llm._charge = counted
_eligible = ds.eligible
QA_THREADS: set[str] = set()  # threads under the QA channel count as the QA channel


def eligible(m):
    qa = os.environ.get("CANON_QA_CHANNEL")
    if qa and m.get("webhook_id") and m.get("channel_id") in {qa, *QA_THREADS}:
        m = {**m, "webhook_id": None, "author": {**m["author"], "bot": False}}
    return _eligible(m)


ds.eligible = eligible
ds.WS, ds.SCOPE = WS, [ds.BASE, WS]


class QAState:  # live cursors and daily counters stay untouched
    get = staticmethod(lambda k: state.get("qa-" + k))
    get_many = staticmethod(lambda ks: _many(ks))
    merge = staticmethod(lambda k, f: state.merge("qa-" + k, f))


async def _many(keys):
    got = await state.get_many(["qa-" + k for k in keys])
    return {k[3:]: v for k, v in got.items()}


ds.state = QAState
MAPPED = {"mei-qa": "mei-tan"}  # webhook username -> person, so one author is a known head, not a guest
_load = authority.load_org


async def load_org(scope):
    org = await _load(scope)
    for user, pid in MAPPED.items():
        if pid in org.by_id:
            org.by_discord[authority._n(user)] = org.by_id[pid]
    return org


authority.load_org = load_org


# ---- Discord helpers ----
class Bot:
    def __init__(self):
        self.c = httpx.AsyncClient(base_url=API, timeout=30,
                                   headers={"Authorization": f"Bot {os.environ['CANON_DISCORD_BOT_TOKEN']}"})

    async def req(self, method, path, **kw):
        for _ in range(4):
            r = await self.c.request(method, path, **kw)
            if r.status_code != 429:
                break
            await asyncio.sleep(float(r.json().get("retry_after", 1)) + 0.2)
        if r.status_code >= 400:
            raise RuntimeError(f"{method} {path} {r.status_code} {r.text[:200]}")
        return r.json() if r.content else {}


async def hook_send(bot, hook, username, content="", files=None, thread_id=None):
    params = {"wait": "true", **({"thread_id": thread_id} if thread_id else {})}
    payload = {"username": username, "content": content}
    if files:
        multipart = [("payload_json", (None, json.dumps(payload), "application/json"))]
        for i, (name, data, mime) in enumerate(files):
            multipart.append((f"files[{i}]", (name, data, mime)))
        return await bot.req("POST", f"/webhooks/{hook['id']}/{hook['token']}", params=params, files=multipart)
    return await bot.req("POST", f"/webhooks/{hook['id']}/{hook['token']}", params=params, json=payload)


async def replies_to(bot, channel_id, msg_id):
    msgs = await bot.req("GET", f"/channels/{channel_id}/messages", params={"limit": 50})
    return [m for m in msgs if (m.get("message_reference") or {}).get("message_id") == msg_id
            and m["author"].get("bot")]


async def decisions_from(source_title_part=None):
    st = store.get_store()
    decs = await st.query("decisions", [WS])
    alerts = await st.query("alerts", [WS])
    return decs, alerts


async def run_sync():
    llm.deadline.set(time.monotonic() + 600)
    out = await ds.sync()
    await asyncio.sleep(1)
    return out


def make_files():
    """A small PDF and PNG with a decision in them, rendered by Playwright (separate venv)."""
    os.makedirs(FILES, exist_ok=True)
    script = f"""
from playwright.sync_api import sync_playwright
html = '<h1>Data retention policy v3</h1><p>Effective 2026-10-18. Decision by Jiwon Park: customer GPS traces are kept for 30 days, then deleted. Owner: Jiwon Park.</p>'
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/Applications/Chromium.app/Contents/MacOS/Chromium')
    pg = b.new_page(viewport={{'width': 800, 'height': 400}})
    pg.set_content(html)
    pg.pdf(path='{FILES}/qa-retention.pdf')
    pg.set_content('<h1 style="font-size:40px">Whiteboard</h1><p style="font-size:30px">DECIDED: on-call handover moves to Mondays 10:00 IST. Owner: Mei Tan</p>')
    pg.screenshot(path='{FILES}/qa-whiteboard.png')
"""
    subprocess.run(["/tmp/pwvenv/bin/python", "-c", script], check=True)


async def main():
    make_files()
    bot = Bot()
    gid = os.environ["CANON_DISCORD_GUILD_ID"]
    chan = await bot.req("POST", f"/guilds/{gid}/channels", json={"name": "qa-canon", "type": 0,
                                                                  "topic": "Temporary Canon QA channel"})
    cid = chan["id"]
    os.environ["CANON_QA_CHANNEL"] = cid
    os.environ["CANON_DISCORD_CHANNELS"] = cid
    print("channel", cid, "workspace", WS, flush=True)
    try:
        # first sync with an empty channel sets nothing; cursor starts at the first message we post
        hook = await bot.req("POST", f"/channels/{cid}/webhooks", json={"name": "canon-qa"})

        # 0. QA mode is off without the env: webhook message skipped
        os.environ.pop("CANON_QA_CHANNEL")
        m0 = await hook_send(bot, hook, "guest-qa", "QA: this message must be skipped because QA mode is off now.")
        r = await run_sync()
        case("webhook message skipped when QA mode is off", r["channels"][0]["ingested"] == 0, json.dumps(r))
        os.environ["CANON_QA_CHANNEL"] = cid

        if "1" in STEPS:
            # 1. guest contradicts the Friday rule: reply in channel, stored as claim, nothing superseded
            m1 = await hook_send(bot, hook, "guest-qa", "Heads up team: we are going back to Friday production "
                                 "deploys starting this week, the Friday deploy freeze is over.")
            r = await run_sync()
            decs, alerts = await decisions_from()
            reps = await replies_to(bot, cid, m1["id"])
            case("guest contradiction gets a reply", bool(reps), reps[0]["content"][:160] if reps else json.dumps(r))
            case("guest message stored as claim, not official", decs and all(d.get("authority") == "claim" for d in decs),
                 str([(d["statement"][:60], d.get("authority")) for d in decs]))
            case("guest cannot supersede", all(d["status"] != "superseded" or d["workspace"] == WS for d in decs)
                 and not any(d.get("supersedes") for d in decs), str([d.get("supersedes") for d in decs]))
            case("alert is low and starts Unverified:", any(a["explanation"].startswith("Unverified:")
                                                             and a["severity"] == "low" for a in alerts),
                 str([a["explanation"][:80] for a in alerts]))

        if "2" in STEPS:
            # 2. duplicate: a second sync with no new message ingests nothing
            r = await run_sync()
            case("re-sync does not re-ingest (cursor)", r["channels"][0]["ingested"] == 0, json.dumps(r))

        if "3" in STEPS:
            # 3. joke is never stored
            before = {d["id"] for d in (await decisions_from())[0]}
            await hook_send(bot, hook, "guest-qa", "lol imagine if we just deployed to prod at 5pm every Friday "
                            "for fun, jk jk, nobody actually do that")
            r = await run_sync()
            decs, _ = await decisions_from()
            new = [d for d in decs if d["id"] not in before]
            case("joke is not stored as a decision", not new, str([d["statement"][:60] for d in new]))

        if "4" in STEPS:
            # 4. casual channel weight: a mapped head in #general is only proposed
            before = {d["id"] for d in (await decisions_from())[0]}
            title = ds.title_of
            ds.title_of = lambda c: "Discord #general"
            await hook_send(bot, hook, "mei-qa", "Decision for the platform team: release notes for every "
                            "production deploy go into the #releases channel within one hour, starting today.")
            r = await run_sync()
            ds.title_of = title
            decs, _ = await decisions_from()
            new = [d for d in decs if d["id"] not in before]
            case("casual channel: head's decision is proposed", new and all(d.get("authority") == "proposed" for d in new),
                 str([(d["statement"][:60], d.get("authority")) for d in new]))

        if "5" in STEPS:
            # 5. thread reply: the contradiction inside a thread gets its reply inside the thread
            top = await hook_send(bot, hook, "guest-qa", "QA thread about the deploy calendar for next week")
            thread = await bot.req("POST", f"/channels/{cid}/messages/{top['id']}/threads",
                                   json={"name": "qa deploy calendar", "auto_archive_duration": 60})
            QA_THREADS.add(thread["id"])
            tm = await hook_send(bot, hook, "guest-qa", "Inside the thread: we will deploy to production on "
                                 "Friday evening this week, no freeze any more.", thread_id=thread["id"])
            r = await run_sync()
            reps = await replies_to(bot, thread["id"], tm["id"])
            case("thread contradiction gets a reply inside the thread", bool(reps),
                 reps[0]["content"][:120] if reps else json.dumps(r)[:300])

        if "6" in STEPS:
            # 6. text file attachment joins the text
            doc = (b"Meeting notes 2026-10-18\nDecision: the support team answers P1 tickets within 30 minutes, "
                   b"24x7, starting November. Owner: Siti Nuraini.\n")
            await hook_send(bot, hook, "guest-qa", "notes attached", files=[("qa-notes.txt", doc, "text/plain")])
            r = await run_sync()
            st = store.get_store()
            srcs = await st.query("sources", [WS])
            case("text file attachment is read", any("qa-notes.txt" in s["text"] and "P1 tickets" in s["text"]
                                                    for s in srcs), str([s["title"] for s in srcs]))

        if "7" in STEPS:
            # 7. PDF and 8. image: one source each, read by Gemini
            pdf = open(f"{FILES}/qa-retention.pdf", "rb").read()
            png = open(f"{FILES}/qa-whiteboard.png", "rb").read()
            await hook_send(bot, hook, "guest-qa", "", files=[("qa-retention.pdf", pdf, "application/pdf")])
            await hook_send(bot, hook, "guest-qa", "", files=[("qa-whiteboard.png", png, "image/png")])
            r = await run_sync()
            srcs = await st.query("sources", [WS])
            decs, _ = await decisions_from()
            titles = [s["title"] for s in srcs]
            case("PDF attachment ingested as its own source", any("qa-retention.pdf" in t for t in titles), str(titles))
            case("image attachment ingested as its own source", any("qa-whiteboard.png" in t for t in titles), str(titles))
            case("PDF content became a decision", any("30 days" in d["statement"] or "GPS" in d["statement"] for d in decs),
                 str([d["statement"][:60] for d in decs]))
            case("image content became a decision", any("Monday" in d["statement"] for d in decs),
                 str([d["statement"][:60] for d in decs]))

        if "9" in STEPS:
            # 9. very long message (Discord max 2000 chars) is ingested without error
            await hook_send(bot, hook, "guest-qa", ("QA long message. " * 120)[:1990])
            r = await run_sync()
            case("2000-char message syncs without error", r["channels"][0]["ingested"] >= 1, json.dumps(r)[:200])

        if "10" in STEPS:
            # 10. daily limit: with the limit reached the message is skipped
            os.environ["CANON_DISCORD_DAILY_LIMIT"] = "0"
            await hook_send(bot, hook, "guest-qa", "QA: this one is over the daily limit and must be skipped.")
            r = await run_sync()
            os.environ.pop("CANON_DISCORD_DAILY_LIMIT")
            case("daily limit skips messages", r["channels"][0]["ingested"] == 0, json.dumps(r))
    finally:
        try:
            await bot.req("DELETE", f"/channels/{cid}")
            case("qa-canon channel deleted", True)
        except Exception as e:
            case("qa-canon channel deleted", False, str(e))
        from canon import core
        await core.reset_workspace(WS)
        for k in [f"qa-discord-{cid}", f"qa-{ds.day_key()}", "qa-discord-archived-scan",
                  *[f"qa-discord-{t}" for t in QA_THREADS]]:
            await store.get_store().client.collection(state.COLL).document(k).delete()
        print("workspace reset", WS, "generate calls", spent["generate"], flush=True)
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)} passed, {len(failed)} failed; Gemini generate calls: {spent['generate']}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
