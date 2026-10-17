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

## Product: Canon (draft scope, Future of Work track)

Canon is the company brain that knows what the company actually decided, not what
the wiki still says.

- Core: knowledge drift. On ingest, Gemini extracts decisions and flags older docs
  that a newer decision contradicts ("contradicted by" banner with source link).
- Live paste box: judge pastes a new message/doc, Canon ingests it and flags what it
  contradicts in seconds. Three sample pastes ship next to the box.
- Supporting: "Catch me up" (persona + last-seen date gives briefing and ranked next
  actions; onboarding = last-seen at company day one) and "Ask why" (cited answers,
  says "I do not know" when the corpus has no answer).
- Data: synthetic company corpus (clearly labelled) with planted decisions and
  contradictions, plus this repo's own README/PRs/commits as real data.
- Benchmark: planted vs found contradictions, false positives, median latency.
- Stretch: Discord slash command over HTTP for a video clip only.

## GCP isolation (teejayproject is shared with live apps)

- New named Firestore database `canon`. Never write to `(default)` or `hinge`.
- New Firebase Hosting site, not the default `teejayproject` site.
- New Cloud Run service `canon`, label `app=canon`, scale to zero, no min instances.
- Model: Gemini Flash-Lite on Vertex, label `app=canon` on every call.
- No per-hour resources (no Vertex Vector Search endpoints, AlloyDB, min instances).
- Ask Tejas before any project-wide toggle (for example Firebase Anonymous Auth).
