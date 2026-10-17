# Northwind Labs synthetic company memory

All people, customers, messages, domains and events here are fictional. This is
synthetic evaluation data, not a record of a real company. Northwind Labs is a
60-person JAPAC logistics SaaS company. Its working archive spans January 2025
through October 2026. Source metadata sets `synthetic: true` and `workspace: acme`.
Every link uses a reserved `.example` domain and does not resolve to a real record.

The corpus has 159 sources across Slack, meetings, wiki, PRs, commits and email.
Twenty named colleagues include three departed people. Anika Rao is the departed
platform expert. Her notes explain event identity, cursors, retry behavior,
replays, restore drills, idempotency and release safety. Mei Tan takes over her
platform responsibilities. Use `anika-rao` for the expert persona.

## Run the checks

From the repository root, using Python 3.10 or later:

```sh
python3 data/validate.py
python3 -m unittest discover -s data -p 'test_*.py' -v
```

No packages, credentials, cloud access or Gemini calls are needed. To reproduce
the JSON artifacts from the hand-authored content:

```sh
python3 data/build_corpus.py
python3 data/validate.py
```

`build_corpus.py` is a deterministic serializer of authored content. It does not
sample, call a model, or access the network. Commit the resulting artifacts so
consumers do not need to run it. For ingestion, read all `corpus/*.jsonl`, combine
the rows, and sort by `(ts, title)`. Do not ingest one kind at a time: chronology
matters to supersession and stale-document detection. Keep the source titles and
quotes intact. No source has an `id`; ingestion assigns runtime IDs. `people.json`
is a JSON array of `Person` objects, not JSONL. Do not ingest gold or samples as
base-workspace sources.

## Demo paths

1. Open **Release process**. Its Friday afternoon window predates the incident.
2. Read **INC-042 live dispatch thread**, on Friday 6 March 2026. The rollback
   restores dispatch acknowledgements after 47 minutes.
3. Read **INC-042 review: the Friday release**, on Monday 9 March. The production
   ban covers scheduled jobs and config-only releases. Emergency mitigation has
   a narrow approval and staffing exception. Tuesday and Thursday morning slots
   replace the ordinary Friday window.
4. Check the intent to deploy production on Friday. Expect `block`.
5. Open **PR 684: unattended dispatch refresh**. Its numeric cron and local-time
   description conflict with the review despite describing the change as routine.

For the PM persona, use a briefing since `2026-03-01T00:00:00Z`. Route Lens changes
from USD 99 to USD 149 for new subscriptions after a second inference pass raises
cost. Signed pilot order forms have an explicit six-month exception. GA moves
from 15 April to 2 June because the three-week accuracy gate is not met. A newer
customer email still promises each old term. The sales FAQ and launch brief are
also stale. These are two separate changes, not one generic launch disagreement.

Useful questions:

- Why can we no longer deploy production on Fridays?
- What should we quote a new Route Lens customer, and why did the price change?
- When did Route Lens GA move, and what gate held it up?
- Why did Anika choose ingestion sequence for tracking cursors?
- Can Sakura backups live outside Japan?

The archive intentionally has no approved replacement cache interval or serving
model after two assumptions fail. The correct answer to those questions is an
explicit refusal to invent a replacement. A premise alert does not itself set a
new policy. Three departed people are Anika Rao, Ravi Perera and Tomoko Ito.
Their authored sources predate their departures.

## Gold format

`gold/gold.json` has `schema_version: 1`, synthetic metadata and four collections:

- `items`: every planted decision, update, contradiction, stale document and
  premise change. `key` is a unique stable label. `type` is one of `decision`,
  `update`, `contradiction`, `stale_doc`, `premise_change`. `decision_key` points
  to the relevant decision item. Each `evidence` entry has an exact `source_title`
  and an exact substring `quote`. Decision items also have `owner` and `statement`.
  Non-decision items include the deciding evidence as well as the new evidence.
  The first evidence is the item being evaluated. For stale documents it is the
  old wiki; the second is its newer correction. Updates use
  `related_decision_key` for the prior decision and `decision_key` for its
  replacement. New statements in updates also have their own decision items.
- `check_intent`: 15 cases with `intent`, `expected_verdict`, `decision_key` and
  a short `reason`. These cover blocks, allowed actions, scope exceptions and
  warnings when assumptions fail without an approved replacement.
- `answerable_questions`: ten questions and their `expected_decision_keys`.
  These are required supporting decisions, not a required verbatim answer.
- `unanswerable_questions`: five questions with `expected_refused: true`.
  Some mention known topics but ask for facts absent from the archive.

Stable keys are benchmark labels, not Firestore decision IDs. Resolve source
names to assigned source IDs, then match extracted decisions using their quoted
evidence and meaning. Gold deliberately does not preseed extracted decisions or
claims about actual model performance. `premise_change` is the gold label; the
API alert enum spells the corresponding kind `premise_changed`.

The label counts are 38 decision statements, 17 contradictions/updates, eight
stale wiki snapshots and five premise changes. Historical statements remain in
gold even when superseded. Ambient sources supply observational context and
negative examples. For example, a Friday team discussion, a staging dry run, or
a documentation-only commit does not breach a production deployment restriction.

## Judge samples

`samples/live_paste.json` is an array of three entries with a `source` object,
`expected_relation` and the relevant stable `decision_key` when one exists. Paste
`source.text` into the web UI, or submit `source` through `POST /api/ingest` with
the visitor workspace. The placeholder `agents` workspace is for direct MCP demos;
the web client must substitute its visitor workspace. Each sample is independent
against the clean base corpus. Reset the demo workspace between repeated runs to
avoid converting an expected `new` or `update` into `same`.

`samples/agent_playground.json` contains one example for each of the six MCP
tools. Each entry has `tool`, `args`, and a descriptive `expected_outcome`, plus
expected keys or verdicts where applicable. The calls use the SPEC argument
names. Read calls need no actor argument except `check_intent`; write calls
include one. These outcomes describe the intended behavior, not measured results.

The validator checks JSONL parsing, source fields and date bounds, fake URLs,
unique titles, known authors, people and departure counts, all exact gold quotes,
decision references, stale-page chronology, minimum planted counts and example
coverage. Mutation tests verify that broken quotes, dangling keys, malformed
JSONL, missing minimums and future-dated stale pages fail validation.
