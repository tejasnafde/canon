# W25 QA plan

Target: https://canon.tn07.dev (base workspace `acme4`, shared `agents` and `discord`).
Suites: `qa/api` (live HTTP, MCP, A2A), `qa/e2e/run.py` (live web, Playwright), `qa/discord/run.py`
(real Discord API, in-process sync, throwaway workspace), `backend/tests` (offline, FakeLLM + memory store).
Columns: + positive path, - negative path, e edge case. "auto" names the suite that covers it.

## Web flows

| Flow | Cases | Auto |
|---|---|---|
| Every route (/, /new-hire, /catch-up, /agent, /paste, /ask, /decisions, /org, /benchmark) | + renders with no console error, page error or 4xx/5xx API call, desktop 1440 and mobile 390; e no horizontal scroll at 390 | e2e |
| Unknown route | - "Not on record" page | e2e |
| /decisions/:id | + opens from the list; - unknown id shows "did not load / Not on record" | e2e |
| Ask | + hero question answers with citations; - blank input cannot submit; e double click sends one request; e prompt injection and RTL/emoji text not obeyed | e2e, api |
| Agent check | + Friday deploy is blocked; e double submit sends one request | e2e |
| Catch up / new hire | + briefing renders (Gemini, loaded on page open) | e2e |
| Paste | + renders; ingest itself covered via API (PastePage.tsx owned by another worker) | e2e, api |
| Keyboard only | + Tab reaches links and buttons with a visible focus style | e2e |
| Back / forward | + history returns to the right page | e2e |
| Slow network | e 400 ms delay on every API call, page still renders | e2e |
| XSS on render | e `<script>` and `onerror` in ingested title and text; the web has no `innerHTML` or source-URL links, React escapes text | api + code review |

## HTTP API

| Route | Cases | Auto |
|---|---|---|
| /health, /api/stats, /api/decisions, /api/people, /api/alerts, /api/activity, /api/eval | + shape and non-empty | api |
| /api/ask, /api/check, /api/expert | - empty or whitespace text gives 422; - over limits.py cap gives 422 with field; - malformed JSON 422 | api, unit |
| /api/briefing | - unknown persona, bad since, empty body give 422 | api |
| /api/activity?since= | - garbage since gives 422 | api, unit |
| /api/decisions/{id}, /api/sources/{id}, /api/alerts/{id}/resolve | - unknown id gives 404 | api |
| X-Canon-Workspace | - missing or invalid header falls back to `agents`, never writes `acme` | api, unit |
| /api/workspace/reset | + resets the QA workspace | api, e2e |
| /api/client-error | + 204; - bad body 422; - over 8 KB 413 | api |
| Rate limit | - 429 after the cap | unit (live would hit judges sharing the IP) |
| Budget cap | - 503 `budget_exceeded`, not a misleading timeout | unit |
| Model timeout | - 503 `model_timeout` with Retry-After | unit (existing) |
| Cold start | e first request after idle answers (health retried by the web) | manual |
| SPA deep links and 404 | + serve index.html | api |

## MCP and A2A

| Case | Auto |
|---|---|
| tools/list has all six tools; catch_me_up accepts all 14 roles | api, unit |
| Unknown tool, missing args, wrong arg type, JSON parse error | api, unit |
| Blank question, over-length question, bad since: readable error text | api, unit |
| search_decisions (embed only), check_intent (Gemini) | api |
| A2A agent card at /.well-known/agent-card.json | api |

## Discord

| Case | Auto |
|---|---|
| Interactions: bad signature 401; PING; unknown subcommand; empty /canon ask; bad days; answer raises | api, unit |
| Sync hook without token 401 | api |
| Webhook skipped without QA mode | discord |
| Guest contradiction: reply in channel, stored as claim, low "Unverified:" alert, nothing superseded | discord |
| Casual channel: a head's rule is only proposed | discord |
| Joke not stored | discord |
| Thread reply lands inside the thread | discord |
| Text file, PDF, image attachments | discord |
| Duplicate (re-sync), 2000-char message, daily limit | discord |
