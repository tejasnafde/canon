# W25 QA report (2026-10-18)

Live target https://canon.tn07.dev, revision deployed before this branch. Fixes below are on branch
`w25-qa` and are NOT deployed, so the live suites still show them as failures until the next deploy.

## Results

| Suite | Result |
|---|---|
| `backend` offline (`CANON_FAKE_LLM=1 CANON_MEMORY_STORE=1 uv run pytest -q`) | 93 passed (8 new W25 cases in `tests/test_w3_agents.py`) |
| `web` typecheck, lint, vitest (26), build | clean |
| `qa/api` live, no Gemini | 33 passed, 5 failed: all 5 are bugs 1 to 3 below, fixed on the branch |
| `qa/api` live, Gemini (`QA_GEMINI=1`) | 7 passed: hero ask cites, unanswerable refuses, prompt injection ignored, Friday check blocks, XSS/injection ingest stored as data, MCP check_intent blocks |
| `qa/e2e/run.py` live (`QA_GEMINI=1`) | 38 passed, 1 failed: bug 4, fixed on the branch (verified by injecting the CSS on the live page) |
| `qa/discord/run.py` (real Discord API, in-process sync) | 17 of 17 cases passed (first run used base `acme` by mistake; authority cases re-run on `acme4`) |

Cleanup: every `qa-canon` channel deleted (guild checked: none left), QA workspaces reset, QA connector
state keys deleted. Live `discord` workspace, cursors and daily counters untouched (harness prefixes them).

## Bugs fixed (each with a test)

1. High. `POST /api/ask` (and `/api/expert`) with an empty or whitespace question: 500. `/api/check` with a blank intent spent an embed and said allow. Now 422 `validation` (app.py, `require`).
2. Medium. `GET /api/activity?since=garbage`: 500. Now 422.
3. Medium. MCP tool errors were opaque ("Error executing tool ask_why") and logged as crashes for blank, over-length, or bad-date input. Now readable `ToolError` text. MCP `catch_me_up` accepted only 3 of the 14 roles the API accepts; now all.
4. Low. `/org` scrolls sideways by 38 px at 390 px width. The decision count now wraps under the name on phones (index.css).
5. Low. Daily Gemini cap returned "model did not answer in time". Now 503 `budget_exceeded` with a clear message.
6. Low. Discord `/canon ask` with no question, or a non-numeric `days`, failed the interaction (KeyError became a 404). Now a usage line; an exception inside an inline answer now says "Canon failed: <type>".

## Open issues (not fixed: owned by another worker, or not mine to change)

- Medium, ingest.py: a Discord guest's claim also raises a `premise_changed` alert ("Assumption ... may no longer hold") against the official Friday rule. An unverified claim should not move premise watch.
- Low, authority.py: when the read scope has no people (e.g. base `acme`), every author is `official`, so a guest could supersede. Fails open; live uses `acme4`, which has people.
- Low, cost: every /ask page view asks two sample questions, and /catch-up and /new-hire load a briefing on open. Each judge visit spends Gemini calls before any input. Client cache is per tab only.
- Info, connectors/discord_sync.py: QA mode lives in the harness (`qa/discord/run.py` patches `eligible`), because connectors/ was frozen for me. Product change if wanted: in `eligible`, treat `webhook_id` messages as human when `channel_id` (or the thread's parent) equals env `CANON_QA_CHANNEL`.
- Info: mapped Discord users are not tested live; no person in `acme4` has a `discord_username`. The harness maps `mei-qa` to Mei Tan in-process for the casual-channel case.

## Gemini generate calls used

About 71 of 80: live API 8, Playwright runs about 30 (page-open briefings and sample asks, 3 runs), Discord 25 + 8
(counted in-process). Embeddings are not counted.
