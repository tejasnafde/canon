# Canon over MCP and A2A

Canon serves an MCP server (streamable HTTP, no auth, rate limited to 30 POST per minute
per IP) at `/mcp`. Base URL in production: `https://canon-tn07.web.app`.
Locally: `uv run uvicorn canon.app:app` and use `http://localhost:8000`.

## Tools

| Tool | Use it when |
|---|---|
| `check_intent(intent, actor)` | BEFORE changing deploys, infra, APIs, pricing, retention, process. Returns allow, warn or block with the deciding decisions. |
| `search_decisions(query, limit=5)` | Find what was decided about a topic. |
| `ask_why(question, actor)` | "Why do we do X?" Cited answer, or `refused: true`. |
| `catch_me_up(persona, since, actor)` | Briefing since an ISO date for engineer, pm or new_hire. |
| `record_decision(statement, rationale, source_text, actor)` | Store a decision. Returns new, same, update or contradiction. |
| `flag_conflict(description, source_text, actor)` | Report text that disagrees with the record. |

Every call appears in the activity feed as `agent:<actor>`. Without `actor`, Canon uses the
MCP client name, then the User-Agent product name.

## Workspaces

Agents without a header read the seeded `acme` corpus and write to the shared `agents`
workspace. To act inside your browser's workspace, send `X-Canon-Workspace: v-<id>`.

## Claude Code

```sh
claude mcp add --transport http canon https://canon-tn07.web.app/mcp
# with your browser workspace:
claude mcp add --transport http canon https://canon-tn07.web.app/mcp --header "X-Canon-Workspace: v-<id>"
```

Then ask: "Add a GitHub Actions cron that deploys to production every Friday." Claude Code
calls `check_intent` first and gets `block`.

## Codex

In `~/.codex/config.toml`:

```toml
[mcp_servers.canon]
url = "https://canon-tn07.web.app/mcp"
# http_headers = { "X-Canon-Workspace" = "v-<id>" }
```

Or `codex mcp add canon --url https://canon-tn07.web.app/mcp`.

## Scripted demo

```sh
uv run python scripts/agent_demo.py https://canon-tn07.web.app/mcp
```

An engineering agent tries a Friday cron deploy and is blocked. A PM bot catches up and asks why.

## A2A

Agent card: `GET /.well-known/agent-card.json`. JSON-RPC endpoint: `POST /a2a`.
The agent is an ADK `LlmAgent` on `gemini-3.5-flash-lite` (Vertex) with tools
`check_intent`, `ask_why`, `search_decisions` and `catch_me_up`. Set `CANON_PUBLIC_URL`
so the card advertises the right endpoint.

## GitHub and Discord

- `POST /hooks/github`: set a repo webhook (content type JSON, event "Pull requests") with
  secret `GITHUB_WEBHOOK_SECRET`. With `GITHUB_TOKEN` set, Canon comments on PRs that
  get warn or block.
- `POST /discord/interactions`: set `DISCORD_PUBLIC_KEY`, register the command with
  `scripts/register_discord.py`, and set the app's Interactions Endpoint URL.
