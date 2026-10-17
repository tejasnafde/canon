# Canon build spec

Canon is the shared memory of a company, for its people and for its AI agents.
One record of decisions. People and agents both read it and write to it. Canon
checks everything that comes in against that record and flags drift.

Track: Future of Work & Enterprise Productivity. Deadline 2026-10-18 night IST.

## Feature set (union of every competitor, done better, plus the agent layer)

P0 = must ship and be in the video. P1 = ship if P0 is green by 2026-10-18 10:00 IST.

| # | Feature | Pri | Beats |
|---|---|---|---|
| F1 | Ingest any source (Slack thread, meeting transcript, wiki page, PR, commit, email, free paste) | P0 | all |
| F2 | Decision extraction: statement, rationale, assumptions, owner, date, each backed by a quote that is checked word for word against the source (reject unverified) | P0 | Mnemo, Decision Ledger |
| F3 | Reconciliation: new decision is `same`, `update` (supersedes), or `contradiction` of an existing one | P0 | Decision Ledger |
| F4 | Drift: docs/wiki pages contradicted by a newer decision get a "contradicted by" alert with both quotes | P0 | Mnemo |
| F5 | Ask why: cited answer with a decision timeline; says "I do not know" when the record has no answer | P0 | Mnemo |
| F6 | Catch me up: persona (any of the 14 roles in models.Persona) + since date gives a briefing and a ranked next-best-action list (score 0-100 with reasons) | P0 | SyncStream, WorkWeave |
| F7 | Agent guard: `check` an intended action against the record, verdict allow/warn/block with the deciding decisions | P0 | nobody |
| F8 | MCP server at `/mcp` (streamable HTTP) exposing the tools below; works from Claude Code and Codex | P0 | nobody |
| F9 | Agent activity feed: every agent read/write/check shows live in the web app | P0 | nobody |
| F10 | Agent playground in the web app: judges call the MCP tools from the browser | P0 | nobody |
| F11 | Benchmark: planted contradictions vs found, false positives, refusal accuracy, p50/p95 latency, on a labelled gold set | P0 | Decision Ledger |
| F12 | Onboarding = catch me up with persona new_hire and since = company day one, plus "who to ask" | P0 | WorkWeave |
| F13 | Premise watch: new info that breaks an assumption behind an active decision raises `premise_changed` | P1 | Mnemo, Decision Ledger |
| F14 | PR deviation check: GitHub webhook on this repo, PR diff checked against decisions, draft review comment | P1 | Decision Ledger, Spec Keeper |
| F15 | Ask the departed expert: answer in the voice of a person who left, only from their recorded decisions and quotes | P1 | Mnemo |
| F16 | Human in the loop: alerts are open until a person resolves them (accept update, dismiss, retire decision) | P1 | Spec Keeper, Decision Ledger |
| F17 | Multimodal ingest: image or PDF paste (Gemini reads it) | P1 | Mnemo |
| F18 | A2A agent card at `/.well-known/agent-card.json` and ADK agent at `/a2a` | P1 | nobody |
| F19 | Discord slash command `/canon ask|check|catchup` over HTTP interactions | P1 | nobody |
| F20 | Self-ingest: this repo's README, PRs and commits as real (non-synthetic) data | P1 | nobody |

## Stack

- Backend: Python 3.12, `uv`, FastAPI, `google-genai` (Vertex mode), `google-cloud-firestore`,
  `mcp` (FastMCP, streamable HTTP mounted into the FastAPI app), `google-adk` for the agent.
- Frontend: Vite + React + TypeScript + Tailwind, static build.
- Deploy: one Cloud Run service `canon` (API, MCP, A2A, hooks). Firebase Hosting site
  `canon-tn07` serves the static web app and rewrites `/api/**`, `/mcp/**`, `/a2a/**`,
  `/hooks/**`, `/discord/**`, `/.well-known/**` to Cloud Run. `canon.tn07.dev` is a
  Cloudflare Worker that proxies to `canon-tn07.web.app`.

## Workspaces (no login, judges never pollute each other)

- Base workspace `acme` holds the seeded synthetic corpus. Read-only for visitors.
- Each browser gets `v-<uuid>` (localStorage) and sends it as header `X-Canon-Workspace`.
  Reads cover `acme` plus the visitor workspace. Writes go to the visitor workspace.
- `POST /api/workspace/reset` deletes the visitor workspace.
- MCP/agent calls without a header use workspace `agents` (a shared, resettable demo space).

## Firestore data model (database `canon`)

All docs carry `workspace: str` and `created_at: timestamp`.

- `sources/{id}`: `kind` (slack|meeting|wiki|pr|commit|email|doc|paste|agent), `title`,
  `author`, `ts` (when it happened), `url`, `text`, `synthetic: bool`.
- `chunks/{id}`: `source_id`, `text`, `embedding` (Vector 768), `ts`.
- `decisions/{id}`: `statement`, `rationale`, `assumptions: [str]`, `owner`, `ts`, `topic`,
  `status` (active|superseded|retired), `supersedes: [id]`, `superseded_by: id|null`,
  `quotes: [{source_id, quote}]`, `embedding` (Vector 768), `created_by` (human|agent:<name>).
- `alerts/{id}`: `kind` (contradiction|stale_doc|premise_changed|agent_violation|pr_deviation),
  `severity` (high|medium|low), `decision_id`, `source_id`, `explanation`,
  `quotes: [{source_id, quote}]`, `status` (open|resolved), `resolution`, `created_by`.
- `activity/{id}`: `actor` (e.g. `human:web`, `agent:claude-code`, `agent:pm-bot`),
  `action` (ingest|ask|check|record|briefing|resolve), `summary`, `ref_ids: [id]`, `verdict`.
- `people/{id}`: `name`, `role`, `team`, `status` (active|left), `left_at`.

Vector indexes: `chunks.embedding` and `decisions.embedding`, 768 dims, COSINE, with
`workspace` as a prefilter field.

## HTTP API (all JSON, all under Cloud Run)

Pydantic models live in `backend/canon/models.py` (the code is the exact contract).

| Method & path | Body | Returns |
|---|---|---|
| POST `/api/ingest` | `IngestRequest` | `IngestResult` (source, decisions, alerts, latency_ms) |
| POST `/api/ask` | `AskRequest` | `AskResult` (answer, citations, timeline, refused, latency_ms) |
| POST `/api/briefing` | `BriefingRequest` | `Briefing` (summary, highlights, actions ranked) |
| POST `/api/check` | `CheckRequest` | `CheckResult` (verdict, decisions, explanation) |
| POST `/api/expert` | `ExpertRequest` | `AskResult` |
| GET `/api/decisions` | `?status=&topic=` | `[Decision]` |
| GET `/api/decisions/{id}` | | `DecisionDetail` (decision, timeline, sources, alerts) |
| GET `/api/alerts` | `?status=open` | `[Alert]` |
| POST `/api/alerts/{id}/resolve` | `ResolveRequest` | `Alert` |
| GET `/api/sources/{id}` | | `Source` |
| GET `/api/activity` | `?since=` | `[Activity]` (web polls every 2 s) |
| GET `/api/people` | | `[Person]` |
| GET `/api/eval` | | `EvalReport` (from the last committed run) |
| POST `/api/workspace/reset` | | `{ok}` |
| GET `/health` | | `{ok, model}` (cheap, no Gemini) |
| GET `/health/deep` | | Firestore read + one embed, manual checks only |
| POST `/api/client-error` | `{message, stack?, url, userAgent?, release?}` | 204; logged at ERROR, source web |

## MCP tools (`/mcp`, streamable HTTP, no auth, rate limited)

| Tool | Args | Does |
|---|---|---|
| `search_decisions` | query, limit=5 | semantic search over active decisions |
| `check_intent` | intent, actor | F7 guard: allow/warn/block with deciding decisions and links |
| `ask_why` | question | F5 |
| `catch_me_up` | persona, since | F6 |
| `record_decision` | statement, rationale, source_text, actor | F1+F2+F3 from an agent; returns reconciliation |
| `flag_conflict` | description, source_text, actor | agent-raised alert (returns `Alert`, kind agent_violation) |

Every tool call writes an `activity` row with `actor = agent:<actor or client name>`.

## Gemini usage

- Model `gemini-3.5-flash-lite`, Vertex, location `asia-south1`, `labels={"app":"canon"}`,
  structured output via `response_schema` for every extraction/judgement call.
- Embeddings `gemini-embedding-001`, `output_dimensionality=768`.
- All Gemini access goes through `backend/canon/llm.py` (`generate_json`, `embed`). Tests
  swap in `FakeLLM` that replays fixtures from `backend/tests/fixtures/llm/`.
- Guardrails: answers only from retrieved decisions/chunks; every claim cites a source
  id; quotes are verified by exact substring match after whitespace normalisation;
  refuse when top retrieval score is below threshold.

## Synthetic corpus (`data/`)

Company: "Northwind Labs", a 60-person B2B SaaS (logistics software), Jan 2025 to Oct 2026.
Clearly labelled synthetic. Files are JSONL, one source per line, matching `Source`.

- `data/corpus/*.jsonl`: 380-460 sources (about 100 are pure noise), covering all 14 personas across slack, meeting, wiki, pr, commit, email.
- At least 25 decisions planted, 12 contradictions/updates, 8 stale wiki pages,
  5 premise changes, 3 people who left (one is the "departed expert"), and the hero
  storyline: "no Friday deploys" after an incident (the video moment).
- `data/gold/gold.json`: labelled answers for every planted item (decision ids, which
  source contradicts which, expected verdicts for 15 `check_intent` cases, 10 answerable
  and 5 unanswerable questions). This is the benchmark test set.
- `data/samples/`: 3 live-paste samples and 6 agent-playground examples for judges.

## Directory ownership (one workstream per directory)

| Dir | Owner | Branch |
|---|---|---|
| `data/` | W1 corpus (Codex) | `w1-data` |
| `backend/canon/{llm,store,ingest,reconcile,ask,briefing,check,expert,eval}.py`, `backend/tests/` | W2 core (Claude) | `w2-core` |
| `backend/canon/{app,mcp_server,a2a,hooks,discord}.py` | W3 agent layer (Claude) | `w3-agents` |
| `web/`, `mocks/` | W4 frontend (Claude) | `w4-web` |
| `deploy/`, `firebase.json`, `Dockerfile`, `.github/` | W5 deploy (lead) | `main` |
| `SPEC.md`, `AGENTS.md`, `backend/canon/models.py` | lead only | `main` |

W3 calls W2 only through the functions declared in `backend/canon/core.py`.
