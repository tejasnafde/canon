"""F14: GitHub PR deviation check.

GitHub posts pull_request events to POST /hooks/github. On opened/synchronize Canon
fetches the diff, checks the change against the decision record, and on warn/block
posts a review comment (when GITHUB_TOKEN is set) or only records the alert.
"""
import hashlib
import hmac
import json
import os

import httpx
from fastapi import APIRouter, HTTPException, Request

from canon import core
from canon.models import CheckRequest

router = APIRouter()
WORKSPACES = ["acme", "agents"]
ACTOR = "agent:github"
MAX_DIFF = 8000


def verify(secret: str, body: bytes, signature: str | None) -> bool:
    if not secret or not signature:
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _gh_headers() -> dict:
    h = {"Accept": "application/vnd.github+json", "User-Agent": "canon"}
    if token := os.environ.get("GITHUB_TOKEN"):
        h["Authorization"] = f"Bearer {token}"
    return h


async def fetch_diff(pr: dict) -> str:
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as c:
        r = await c.get(pr["url"], headers={**_gh_headers(), "Accept": "application/vnd.github.diff"})
        r.raise_for_status()
        return r.text


async def post_comment(repo: str, number: int, body: str) -> None:
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(f"https://api.github.com/repos/{repo}/issues/{number}/comments",
                         headers=_gh_headers(), json={"body": body})
        r.raise_for_status()


def summarize(pr: dict, diff: str) -> str:
    # ponytail: raw truncated diff is the summary; Gemini reads diffs fine at this size.
    return (f"Merge pull request #{pr['number']} \"{pr['title']}\" into {pr['base']['ref']}.\n"
            f"Description: {(pr.get('body') or '')[:1000]}\n\nDiff:\n{diff[:MAX_DIFF]}")


def comment_body(res) -> str:
    lines = [f"**Canon: {res.verdict.upper()}** - this change may deviate from recorded decisions.",
             "", res.explanation, ""]
    for d in res.decisions:
        quote = d.quotes[0].quote if d.quotes else ""
        lines.append(f"- **{d.statement}** ({d.owner}, {d.ts:%Y-%m-%d})" + (f"\n  > {quote}" if quote else ""))
    lines += ["", "_Draft review from Canon. A human decides._"]
    return "\n".join(lines)


@router.post("/hooks/github")
async def github(request: Request):
    body = await request.body()
    if not verify(os.environ.get("GITHUB_WEBHOOK_SECRET", ""), body, request.headers.get("x-hub-signature-256")):
        raise HTTPException(401, "bad signature")
    event = request.headers.get("x-github-event")
    payload = json.loads(body)
    if event != "pull_request" or payload.get("action") not in ("opened", "synchronize", "reopened"):
        return {"ok": True, "skipped": event}
    pr = payload["pull_request"]
    repo = payload["repository"]["full_name"]
    res = await core.check(CheckRequest(intent=summarize(pr, await fetch_diff(pr)), actor=ACTOR), WORKSPACES)
    posted = False
    if res.verdict in ("warn", "block"):
        if os.environ.get("GITHUB_TOKEN"):
            await post_comment(repo, pr["number"], comment_body(res))
            posted = True
    return {"ok": True, "verdict": res.verdict, "commented": posted}
