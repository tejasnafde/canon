"""Fetch one real check_intent exchange from the live MCP server and save it for agent.html.

  ../canon/backend/.venv/bin/python video/terminal/fetch_mcp.py   (any venv with the mcp client)

Uses a throwaway visitor workspace and resets it afterwards. One Gemini call.
"""
import asyncio
import json
import time
import uuid
from pathlib import Path

import httpx
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

BASE = "https://canon.tn07.dev"
INTENT = "Add a cron job that deploys the dispatch service to production every Friday at 15:00"
OUT = Path(__file__).resolve().parent / "exchange.json"  # agent.html loads exchange.js, the same data


async def main() -> None:
    ws = "v-" + str(uuid.uuid4())
    try:
        await exchange(ws)
    finally:
        async with httpx.AsyncClient(timeout=30) as c:
            await c.post(BASE + "/api/workspace/reset", headers={"X-Canon-Workspace": ws})


async def exchange(ws: str) -> None:
    http = httpx.AsyncClient(headers={"X-Canon-Workspace": ws}, timeout=90)
    async with http, streamable_http_client(BASE + "/mcp", http_client=http) as (read, write):
        async with ClientSession(read, write) as s:
            init = await s.initialize()
            tools = await s.list_tools()
            args = {"intent": INTENT, "actor": "claude-code"}
            t = time.monotonic()
            r = await s.call_tool("check_intent", args)
            ms = round((time.monotonic() - t) * 1000)
    tool = next(x for x in tools.tools if x.name == "check_intent")
    OUT.write_text(json.dumps({
        "server": init.server_info.model_dump(mode="json"),
        "tools": [x.name for x in tools.tools],
        "tool": tool.model_dump(mode="json", exclude_none=True),
        "request": {"method": "tools/call", "params": {"name": "check_intent", "arguments": args}},
        "result": r.structured_content,
        "is_error": r.is_error,
        "roundtrip_ms": ms,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }, indent=2))
    OUT.with_suffix(".js").write_text("window.EXCHANGE = " + OUT.read_text() + ";\n")
    print("saved", OUT, r.structured_content.get("verdict") if r.structured_content else r.content, ms, "ms")


asyncio.run(main())
