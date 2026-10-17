"""F19: Discord slash command /canon ask|check|catchup over HTTP interactions.

Discord POSTs to /discord/interactions, signed with Ed25519 (env DISCORD_PUBLIC_KEY).
Answers within 2.5 s go back inline; slower ones are deferred and sent as a follow-up.
"""
import asyncio
import json
import os
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from canon import core
from canon.models import AskRequest, BriefingRequest, CheckRequest

router = APIRouter()
WORKSPACES = ["acme", "agents"]
INLINE_SECONDS = 2.5  # Discord wants a reply within 3 s
API = "https://discord.com/api/v10"


def verify(public_key: str, body: bytes, signature: str | None, timestamp: str | None) -> bool:
    if not (public_key and signature and timestamp):
        return False
    try:
        VerifyKey(bytes.fromhex(public_key)).verify(timestamp.encode() + body, bytes.fromhex(signature))
        return True
    except (BadSignatureError, ValueError):
        return False


async def answer(sub: str, opts: dict, user: str) -> str:
    actor = f"agent:discord:{user}"
    if sub == "ask":
        r = await core.ask(AskRequest(question=opts["question"], actor=actor), WORKSPACES)
        cites = "\n".join(f"- {c.title} ({c.ts:%Y-%m-%d}): \"{c.quote[:150]}\"" for c in r.citations[:3])
        return f"{r.answer}\n\n{cites}".strip()
    if sub == "check":
        r = await core.check(CheckRequest(intent=opts["intent"], actor=actor), WORKSPACES)
        decs = "\n".join(f"- {d.statement} ({d.owner}, {d.ts:%Y-%m-%d})" for d in r.decisions[:3])
        return f"**{r.verdict.upper()}**: {r.explanation}\n{decs}".strip()
    if sub == "catchup":
        since = datetime.now(timezone.utc) - timedelta(days=int(opts.get("days", 7)))
        r = await core.briefing(BriefingRequest(persona=opts.get("persona", "engineer"), since=since, actor=actor),
                                WORKSPACES)
        acts = "\n".join(f"{a.priority}. {a.title}: {a.why}" for a in r.actions[:3])
        return f"{r.summary}\n\n**Next:**\n{acts}".strip()
    return f"Unknown subcommand {sub}"


async def follow_up(app_id: str, token: str, task: asyncio.Task) -> None:
    try:
        content = await task
    except Exception as e:  # report the failure in Discord instead of leaving "thinking..." forever
        content = f"Canon failed: {type(e).__name__}"
    async with httpx.AsyncClient(timeout=10) as c:
        await c.patch(f"{API}/webhooks/{app_id}/{token}/messages/@original", json={"content": content[:2000]})


@router.post("/discord/interactions")
async def interactions(request: Request, background: BackgroundTasks):
    body = await request.body()
    if not verify(os.environ.get("DISCORD_PUBLIC_KEY", ""), body,
                  request.headers.get("x-signature-ed25519"), request.headers.get("x-signature-timestamp")):
        raise HTTPException(401, "invalid request signature")
    i = json.loads(body)
    if i["type"] == 1:  # PING
        return {"type": 1}
    sub = i["data"]["options"][0]
    opts = {o["name"]: o["value"] for o in sub.get("options", [])}
    user = (i.get("member", {}).get("user") or i.get("user") or {}).get("username", "user")
    task = asyncio.create_task(answer(sub["name"], opts, user))
    done, _ = await asyncio.wait({task}, timeout=INLINE_SECONDS)
    if done:
        return {"type": 4, "data": {"content": task.result()[:2000]}}
    # ponytail: follow-up runs after the response; on Cloud Run use --no-cpu-throttling
    # (or keep min instances) if follow-ups stall.
    background.add_task(follow_up, i["application_id"], i["token"], task)
    return {"type": 5}
