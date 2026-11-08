"""What a person sees when they open the MCP endpoint in a browser (an MCP client never gets this:
it sends Accept: text/event-stream or POSTs JSON-RPC). Before this page, a browser got a bare 406."""
import html

CLIENTS = [  # (client, where, snippet)
    ("Claude Code", "terminal", "claude mcp add --transport http canon {url}"),
    ("Codex CLI", "terminal", "codex mcp add canon --url {url}"),
    ("Cursor", "~/.cursor/mcp.json", '{{"mcpServers": {{"canon": {{"url": "{url}"}}}}}}'),
    ("VS Code (GitHub Copilot agent mode)", ".vscode/mcp.json",
     '{{"servers": {{"canon": {{"type": "http", "url": "{url}"}}}}}}'),
    ("Windsurf", "~/.codeium/windsurf/mcp_config.json", '{{"mcpServers": {{"canon": {{"serverUrl": "{url}"}}}}}}'),
    ("Gemini CLI", "~/.gemini/settings.json", '{{"mcpServers": {{"canon": {{"httpUrl": "{url}"}}}}}}'),
    ("Claude Desktop / claude.ai", "Settings, Connectors", "Add custom connector, URL: {url}"),
    ("Any other MCP client", "its MCP settings", "Streamable HTTP server, no auth: {url}"),
]


def page(url: str) -> str:
    rows = "".join(
        f"<h3>{html.escape(c)}</h3><p class=w>{html.escape(w)}</p><pre>{html.escape(s.format(url=url))}</pre>"
        for c, w, s in CLIENTS)
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Canon MCP endpoint</title>
<style>body{{font:16px/1.55 system-ui,sans-serif;background:#f6f1e7;color:#1c1a17;max-width:760px;margin:48px auto;padding:0 20px}}
h1{{font:600 34px Georgia,serif;margin:0 0 8px}}h3{{margin:28px 0 2px;font-size:17px}}.w{{margin:0;color:#5f5a52;font-size:14px}}
pre{{background:#fffdf8;border:1px solid #e3dccd;padding:12px 14px;overflow-x:auto;font-size:14px;margin:8px 0 0}}a{{color:#1c1a17}}</style></head>
<body><h1>This is Canon's MCP endpoint.</h1>
<p>It is for AI agents, not browsers. Connect your coding agent or assistant with one of the setups below.
It needs no key. Your agent gets six tools: search decisions, ask why, catch me up, check an action
(allow, warn or block), record a decision, and flag a conflict.</p>
<p>Try it after connecting: ask your agent to <i>"add a job that deploys to production every Friday at 15:00"</i>.
It should check with Canon first and be blocked.</p>
{rows}
<p style="margin-top:36px"><a href="/agent">See it in the web app</a> &middot; <a href="/llms.txt">Brief for AI readers</a></p>
</body></html>"""
