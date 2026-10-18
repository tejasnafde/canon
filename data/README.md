# Northwind Labs synthetic company memory

All people, customers, messages, domains and events here are fictional. This is
synthetic evaluation data, not a record of a real company. Northwind Labs is a
60-person JAPAC logistics SaaS company. Its working archive spans January 2025
through October 2026. Source metadata sets `synthetic: true` and `workspace: acme`.
Every link uses a reserved `.example` domain and does not resolve to a real record.

The corpus has 380 sources across Slack, meetings, wiki, PRs, commits and email.
Pass 2 adds 100 unlabelled noise sources about lunch, hiring, hardware, customer
workshops, small UI bugs and rota swaps. They are not new benchmark decisions.
Slack threads have several participants and 4 to 15 replies. All 40 meetings
have 300 to 900 words, with questions, objections and transcript crosstalk. Wiki
pages retain their historical wording. PRs have review comments and short
fictional diff excerpts. Emails include headers, greetings and signatures.
Twenty-three named colleagues include three departed people. Anika Rao is the departed
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
the corpus, gold, samples and original person fields from the hand-authored content
in a scratch checkout:

```sh
python3 data/build_corpus.py
python3 data/validate.py
```

`build_corpus.py` is a deterministic serializer of authored content.
`archive_texture.py`, `meeting_details.py` and `source_context.py` hold the
in-world discussions and page comments. `pr_excerpts.py` holds illustrative
review diffs, and `noise.py` holds the 100 unrelated sources. `roles.py` holds 121 department sources and their gold labels. It does not
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
- `check_intent`: 37 cases with `intent`, `expected_verdict`, `decision_key` and
  a short `reason`. These cover blocks, allowed actions, scope exceptions and
  warnings when assumptions fail without an approved replacement.
- `answerable_questions`: 21 questions and their `expected_decision_keys`.
  These are required supporting decisions, not a required verbatim answer.
- `unanswerable_questions`: five questions with `expected_refused: true`.
  Some mention known topics but ask for facts absent from the archive.

Stable keys are benchmark labels, not Firestore decision IDs. Resolve source
names to assigned source IDs, then match extracted decisions using their quoted
evidence and meaning. Gold deliberately does not preseed extracted decisions or
claims about actual model performance. `premise_change` is the gold label; the
API alert enum spells the corresponding kind `premise_changed`.

The label counts are 82 decision statements, 39 contradictions/updates, 19
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

## Role coverage

The October role pass adds 121 sources: 99 Slack threads, 11 email threads, and
11 historical wiki pages. Each requested department has four new decision
statements: a January baseline, a September replacement, and two further
agreements. Each has one update, one stale page, one contradictory copied
packet, two intent cases, and one answerable question. Historical decisions
remain in gold. The five original refusal questions remain unchanged. No source
specifies parental leave, revenue, an acquisition, partner passwords, or an
approved replacement for the broken cache/model assumptions.

| Persona | Owned decision statements, including history | Example question |
|---|---:|---|
| design | 5 | How must design mark delayed shipments now? |
| data | 5 | What counts as an active workspace in the weekly dashboard? |
| security | 11 | How long may a vendor troubleshooting session remain open? |
| sales | 4 | Who approves a Route Lens discount above 10 percent? |
| support | 5 | Where does support send a priority-one incident first? |
| marketing | 4 | Which product name belongs in new campaign headlines? |
| finance | 8 | What payment terms apply to new customer invoices? |
| operations | 4 | When must operations reorder depot scanner kits? |
| people | 4 | How many interview rounds do permanent hires have now? |
| legal | 4 | Which customer contracts require Legal review before signature? |
| leadership | 4 | Which roles are exempt from the permanent hiring freeze now? |

Engineer and Product keep their original release, platform, launch, and pricing
histories. Every gold item and question now has `teams`, containing persona keys.
All department decisions also matter to `new_hire`. Commercial pricing and launch
items list their affected teams. Metadata describes benchmark relevance; ingestion
still consumes only Source fields. For recent role briefings, use
`since=2026-09-01T00:00:00Z`. For the full decision history, use January 2025.

People adds Devika Fernando (Operations), Nandini Wijaya (Legal), and Hana Okafor
(Leadership). Existing owners now use explicit Design, Finance, Support, and
People team names. Three historical departures remain unchanged.

## Integration and verification

The validator requires 380 to 460 sources, three owned decisions per requested
role, an update and stale page per role, and role-specific intent and question
coverage. Tests also check deterministic rebuilding, exact quotes, missing team
labels, stale-page chronology, document shapes, and departed speakers. The checks
run offline and do not measure Gemini accuracy or retrieval quality.

The lead must update SPEC.md's 250 to 300 source range to 380 to 460, expand F6's
persona list to match models.py, and document the additive gold `teams` field.
The runtime Source schema remains unchanged. Person now includes the org fields described below. Re-ingestion and a fresh
model benchmark are required before the deployed product uses this corpus.
This workstream makes no cloud changes.


## Organization hierarchy

`people.json` is the authoritative roster of 23 named colleagues in the fictional
60-person company, not a full employee census. No new people are added. Existing
names, roles, teams, corpus text and gold evidence are unchanged. `level` describes
organizational authority without rewriting historical role titles. Hana Okafor is
the sole CEO and root. The seven heads report to Hana:

| Head | Function | Direct reports |
|---|---|---|
| Mei Tan | Engineering | Anika Rao, Haruto Sato, Pranav Menon, Linh Nguyen, Jiwon Park, Chen Wei, Kavya Iyer, Budi Santoso |
| Aisha Rahman | Product | Yuki Mori, Thao Tran |
| Arjun Desai | Sales | Farah Khan |
| Siti Nuraini | Customer and Support | Daniel Lim, Ravi Perera |
| Amina Yusuf | People | No other named colleagues |
| Nur Aziz | Finance | Devika Fernando |
| Nandini Wijaya | Legal | No other named colleagues |

Linh leads Data and manages Tomoko Ito. Jiwon, Yuki, Farah and Devika lead Security,
Design, Marketing and Operations respectively. These small functions have no
further named reports. Departed staff retain their historical manager links:
Anika reports to Mei, Ravi to Siti, and Tomoko to Linh. Their successors are Mei,
Siti and Linh respectively. Only Anika's handoff is explicit in the corpus; the
other two handoffs and the reporting structure are synthetic organization metadata.
All `discord_username` values are null because no verified handles are provided.

`org/topics.json` maps each of 14 topic areas to `teams` (existing team display
names) and `owner` (a Person ID). Owners are current escalation contacts, not
rewritten historical gold decision owners. `org/channels.json` maps all 14 existing
Discord channel names, including their leading `#`, to a `weight` and topic keys.
General is casual; all other existing channels are team channels. No official
announcement channel exists, so none is invented.

The offline validator also checks manager references, cycles, the single active
executive root, levels, active successors, topic owners and teams, channel weights
and topic references, and every gold decision owner's display name.

Known integration gap: `build_corpus.py` still serializes the original six Person
fields and overwrites `people.json`. Do not rebuild in the working checkout until
the corpus owner updates that serializer to preserve the authoritative org fields.
The deterministic rebuild test verifies all other artifacts byte-for-byte and the
six original person fields structurally. It does not claim org rebuild support.
The lead should add the new Person fields and org JSON shapes to SPEC.md. This
workstream does not edit the lead-owned contract or the corpus serializer.

## Company basics supplement (W27)

`corpus_basics/basics.jsonl` adds 30 synthetic sources for workspace `acme4`.
It is separate from the 380-source benchmark corpus and does not change gold.
The Northwind product stack described here is fictional company knowledge, not
Canon's implementation stack. Current pages preserve the Friday production ban,
Tuesday/Thursday morning slots, USD 149 new-subscription pricing and the signed
pilot exception, current Kestrel concurrency, and Sakura residency requirements.
The team directory follows `people.json`, including historical departures.

ADR B08 explicitly supersedes B07. The September dispatch settings Slack thread
quietly contradicts B06 without naming that ADR. Both versions remain in the
file so Canon can detect drift. These new cases have no benchmark gold labels.
The supplement excludes all five refusal topics and excluded leave policies.
Benefits content covers enrollment routing, equipment and learning purchases.

Run the offline checks from the repository root:

```sh
python3 data/validate.py
uv run --project backend pytest data/test_validate.py data/corpus_basics -q
```

The validator checks supplement fields, date range and timezone, known authors
and departures, unique titles and URLs, fake deep links, workspace, synthetic
labels, prohibited characters and refusal-topic terms. The topic check is a
conservative text screen; the content also receives manual review.

The lead can append the file to an existing workspace with sources. This command
makes paid Gemini calls and is not part of validation. W27 does not run it.
Use the authorized key directly, never ADC:

```sh
cd backend
GOOGLE_APPLICATION_CREDENTIALS=/Users/tejas/Desktop/projects/google-hackathon/canon/.secrets/sa-canon.json \
  uv run python scripts/add_sources.py ../data/corpus_basics/basics.jsonl --workspace acme4
```

The script validates all input before ingestion, sorts by timestamp and title,
then calls `core.ingest` sequentially. It reads only the target workspace when
checking exact titles. It skips titles already present, including duplicates in
the same input, and prints progress and the process Gemini generate call count
from `llm._spent`. It never resets a workspace or imports people. An empty or
unknown workspace fails before ingestion. Run only one importer per workspace;
title skipping does not provide a distributed lock. If an ingest fails after
saving its source but before completing its decisions, inspect that source
before resuming: a rerun skips any saved title. Embedding calls are not included
in the generate counter. Retrieval and live extraction remain untested here.

Supplement titles:

1. ADR B01: Postgres over MySQL
2. ADR B02: Kafka carrier event log
3. ADR B03: One application monorepo
4. ADR B04: Tenant feature flags
5. ADR B05: Grafana Cloud telemetry
6. ADR B06: Dispatch tuning in environment variables
7. ADR B07: Legacy scanner shell
8. ADR B08: React Native scanner client
9. Architecture overview
10. Tech stack
11. Engineering onboarding guide
12. Product overview
13. Glossary
14. Security and access policy
15. On-call runbook
16. Team directory
17. Benefits FAQ
18. Dispatch settings before the depot rehearsal
19. Local development troubleshooting
20. Carrier connector field guide
21. Data store ownership map
22. Mobile scanner working session
23. Build and release checklist
24. Telemetry field guide
25. Customer demo tenant guide
26. New hire office hours: where things live
27. Architecture review: tenant boundaries
28. Feature flag cleanup thread
29. Database migration rehearsal
30. Stack walkthrough for Support

No runtime Source contract change is needed. The supplement's workspace is
explicitly `acme4` as requested. The lead must select the deployed base workspace
and ingest there before judges can retrieve these sources.
