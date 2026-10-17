# AI Builder Cup 2026 (Google Cloud x Hack2Skill)

Team: Tejas Nafde (leader), Ishank Giri, Mitushi.
Deadline: submission closes 2026-10-18 night (IST). Treat that as final, no extension.

## Shared conventions (read first)

Cross-project rules live in `~/Desktop/projects/CLAUDE.local.md` (Tejas's Mac only):
GCP identities (`--configuration=personal`, project `teejayproject`), the ADC trap,
Secret Manager, Cloudflare/tn07.dev, Cloud Run gotchas, labels (`app=<repo>`),
and writing style. Read it before touching gcloud, secrets, DNS or deploys.
Teammates without that file: ask Tejas before creating any cloud resource.

Writing style, short form: no em dashes (U+2014) anywhere, no emoji in UI or code.

## Hard submission requirements (miss one = disqualified)

1. Pitch deck in the prescribed template, exported to PDF, max 5 MB.
   Template: `Submission Template _ AI Builder Cup.pptx` (slides: brief, opportunities/USP,
   features, process flow, wireframes, architecture, tech, cost, snapshots,
   benchmarks, future, links).
2. Demo video, 3 to 4 minutes. Over time = penalty. Must show working functionality.
   Clear, loud audio. Open with the live product.
3. Deployed prototype link on Cloud Run or Firebase Hosting (use the `run.app` or
   `web.app` URL, not a custom domain). Must stay up through judging.
   No login wall for judges. Scale to zero is fine.
4. GitHub repo, PUBLIC at submission time (it starts private).
5. Description, max 1024 chars, naming how we use Firebase, Firestore, Cloud Run, Gemini.

## Judging signals (from the "Ask the Expert" session)

- Must use Gemini (Vertex / Agent Platform). ADK 2.0 is a plus, not required.
- Synthetic, clearly labelled data is fine.
- Ship sample questions and test data in the README so judges hit the happy path.
- Write down real technical wins (latency, grounding, guardrails). Do not make any up.
- Lose points on: feasibility doubts, "too basic", unclear presentation.
- NO secrets in the repo, deck, video or deploy commands. Secret Manager or env vars only.
- After the deadline: critical fixes only, never redeploy something risky.

## Repo rules

- Label every GCP resource `app=canon` (Vertex calls too).
- Keep it boring: one Cloud Run service, Firestore, Firebase Hosting in front.

## Product and build contract

See `SPEC.md`. It is the single source of truth for the data model, API, MCP tools,
and who owns which directory. Change the contract only by editing SPEC.md in the
same commit as the code.

## GCP resources (all new, isolated from the live apps in teejayproject)

- Firestore database `canon` (asia-south1). Never touch `(default)` or `hinge`.
- Service account `canon-run@teejayproject.iam.gserviceaccount.com`: Vertex user,
  and datastore.user conditioned to the `canon` database only.
  Local dev key: `.secrets/sa-canon.json` (gitignored). Use it via
  `GOOGLE_APPLICATION_CREDENTIALS`, never ADC (ADC on this Mac is the work identity).
- Firebase Hosting site `canon-tn07` (https://canon-tn07.web.app).
- Cloud Run service `canon` (asia-south1), runs as `canon-run`, label `app=canon`,
  min instances 0.
- Public hostname `canon.tn07.dev` via a Cloudflare Worker (see CLAUDE.local.md).
- Models: `gemini-3.5-flash-lite` (location asia-south1) for everything; embeddings
  `gemini-embedding-001` at 768 dims. Every call carries `labels={"app": "canon"}`.
- No per-hour resources. No project-wide toggles without asking Tejas.

## Working rules for agents

- Work only inside the directories SPEC.md assigns to you, in your own git worktree
  and branch. Do not edit another workstream's files; leave a note in your report.
- Commit small and often. End commit messages with the co-author line you were given.
- Every non-trivial logic path leaves one runnable test (`pytest` for backend).
- Gemini calls in tests use the recorded-fixture fake (see SPEC.md), never the network.
