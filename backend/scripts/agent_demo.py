"""Video moment: two agents use Canon over MCP.

1. An engineering agent is asked to add a Friday cron deploy. It calls check_intent
   first, gets BLOCK with the deciding decision, and stops.
2. A PM bot catches up on the week and asks why.

Usage: uv run python scripts/agent_demo.py [http://localhost:8000/mcp]
"""
import asyncio
import json
import sys
import textwrap
from datetime import datetime, timedelta, timezone

import httpx2
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/mcp"


def say(who: str, text: str) -> None:
    print(textwrap.fill(text, 96, initial_indent=f"{who:>14} | ", subsequent_indent=" " * 14 + " | "))


async def call(s: ClientSession, tool: str, args: dict) -> dict:
    say("-> canon", f"{tool}({json.dumps(args)})")
    r = await s.call_tool(tool, args)
    if r.is_error:
        raise SystemExit(f"{tool} failed: {r.content}")
    return r.structured_content


async def main() -> None:
    http = httpx2.AsyncClient(headers={"X-Canon-Workspace": "agents"}, timeout=60)
    async with http, streamable_http_client(URL, http_client=http) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()

            print("\n=== Engineering agent ===")
            say("user", "Add a GitHub Actions cron that deploys main to production every Friday at 17:00.")
            say("claude-code", "This changes the deploy schedule. Checking Canon before I touch CI.")
            res = await call(s, "check_intent", {
                "intent": "Add a GitHub Actions cron that deploys main to production every Friday at 17:00 IST",
                "actor": "claude-code"})
            say("canon", f"{res['verdict'].upper()}: {res['explanation']}")
            for d in res["decisions"]:
                quote = d["quotes"][0]["quote"] if d["quotes"] else ""
                say("", f"- {d['statement']} ({d['owner']}, {d['ts'][:10]}) \"{quote}\"")
            if res["verdict"] == "block":
                say("claude-code", "I did not add the cron. The decision above bans it. "
                                   "Ask its owner to change it if Friday deploys are needed.")
            else:
                say("claude-code", f"Verdict {res['verdict']}, proceeding with care.")

            print("\n=== PM bot ===")
            since = (datetime.now(timezone.utc) - timedelta(days=30)).date().isoformat()
            brief = await call(s, "catch_me_up", {"persona": "pm", "since": since, "actor": "pm-bot"})
            say("canon", brief["summary"])
            for a in brief["actions"][:3]:
                say("", f"[{a['priority']}] {a['title']}: {a['why']}")
            why = await call(s, "ask_why", {"question": "Why do we not deploy on Fridays?", "actor": "pm-bot"})
            say("canon", "I do not know." if why["refused"] else why["answer"])
            for c in why["citations"][:3]:
                say("", f"- {c['title']} ({c['ts'][:10]}): \"{c['quote']}\"")
            print("\nEvery call above is in the Canon activity feed.")


if __name__ == "__main__":
    asyncio.run(main())
