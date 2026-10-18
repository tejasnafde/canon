# Canon demo video: final narration script (3:46)

Runtime 3:46. Hard limit 4:00, so there is 14 seconds of slack for slow takes.
Narration is about 480 words, about 130 words per minute, so there is room to breathe. Tejas narrates in his own voice.

The video opens on the live product (judges asked for this), so `clip-01-title.mp4` is not used.
The close card (`clip-12-close.mp4`) carries the logo.

Clips: `wt/w23-video/video/clips/` (1920x1080, 30 fps, silent).
Every IN and OUT time below is mm:ss inside that clip. "Program" is the time in the final video.
Every IN/OUT was checked against frames extracted at 1 s. `docs/RECORDING-GUIDE.md` has a script
that cuts all 21 segments for you (measured total: 3:46.1), plus the iMovie steps.

How to read a scene: cut the segments in order, lay them end to end, and read the narration over them.
A `[+8s]` cue means "say this from about 8 s into the scene". Bold words carry the stress.

---

## Scene 1. Home (program 0:00 to 0:18, 18 s)

| Seg | Clip | IN | OUT | Length | On screen |
|---|---|---|---|---|---|
| 1a | `clip-02-home.mp4` | 00:00 | 00:11 | 11 s | Home headline "The shared memory of a company, for its people and its AI agents." Counts: 380 items read, 345 official decisions, 27 documents now out of date. |
| 1b | `clip-02-home.mp4` | 00:13 | 00:20 | 7 s | "Pick a story" list. The cursor hovers "I am new here", "What changed while I was away?", "Watch an AI agent get stopped", "Paste a new message". |

> [+0s] This is Canon, live on Google Cloud. Companies decide things every day, then forget them.
> [+7s] Canon read two years of a made-up company, Northwind Labs. **Three hundred eighty** items. **Three hundred forty-five** official decisions.
> [+15s] And **twenty-seven** documents that are now wrong.

## Scene 2. New hire (program 0:18 to 0:38, 20 s)

| Seg | Clip | IN | OUT | Length | On screen |
|---|---|---|---|---|---|
| 2 | `clip-03-new-hire.mp4` | 00:00 | 00:20 | 20 s | "Welcome to Northwind Labs." Red warning: "The Priority support routing handbook page is out of date. Do not follow it." with the old line and the 8 September decision (0 to 6 s). Scrolls to "5 things you must know", "People to ask", "People who left" (6 s on). |

> [+0s] Day one for a new hire. Canon **warns** first: this handbook page is out of date.
> [+7s] Then the five things that will get you in trouble, each with the reason behind it. Who to ask, by topic. And who has left, with their decisions kept.

## Scene 3. Catch-up by role (program 0:38 to 0:58, 20 s)

| Seg | Clip | IN | OUT | Length | On screen |
|---|---|---|---|---|---|
| 3a | `clip-04-catch-up.mp4` | 00:00 | 00:10 | 10 s | "What changed while you were away?" Engineer, 3 months. Summary, then the to-do list with urgency scores 95, 91, 81, 77, 74. |
| 3b | `clip-04-catch-up.mp4` | 00:19 | 00:22 | 3 s | Tooltip on the 95: "open contradiction alert, relevant to Engineering, evidence in a PR". |
| 3c | `clip-04-catch-up.mp4` | 00:24 | 00:25 | 1 s | Click on "Sales". |
| 3d | `clip-04-catch-up.mp4` | 00:29 | 00:35 | 6 s | Sales summary and list: support routing, discount approval limits, contract review threshold, Route Lens price. (00:25 to 00:29 is a loading skeleton: cut it.) |

> [+0s] Back from three months away? Pick your role. An engineer gets a short summary, and a to-do list ranked by **urgency**.
> [+10s] Each score says why.
> [+12s] Switch to **Sales**, and it's discounts, contract limits and pricing. Same record, a view for every role.

## Scene 4. An AI agent gets stopped (program 0:58 to 1:36, 38 s)

This is the scene for technical merit. Speak it slowly and clearly.

| Seg | Clip | IN | OUT | Length | On screen |
|---|---|---|---|---|---|
| 4a | `clip-05-agent.mp4` | 00:00 | 00:10 | 10 s | "Watch an AI agent get stopped." Four steps and the red **Block** card: the Friday rule, owner Mei Tan, decided 9 March 2026 in the INC-042 review. |
| 4b | `clip-05b-agent-terminal.mp4` | 00:00 | 00:18 (end) | 18 s, then freeze 1 s | Terminal replay of a real MCP call to canon.tn07.dev/mcp. Prompt typed (0 to 7 s), agent line and `tools/call check_intent` (7 to 10 s), result `"verdict": "block"` (11 s), decision, quote, citation, `latency_ms: 1049` (12 to 14 s), agent "BLOCK I did not add the job" (14 s on). Hold the last frame 1 s. |
| 4c | `clip-05-agent.mp4` | 00:32 | 00:40 | 8 s at **2x** = 4 s | "Try it yourself": "Add a cron job that deploys the dispatch service to production every Friday at 15:00" is typed. Beside it, "Connect your own agent" with the Claude Code and Codex one-line commands. |
| 4d | `clip-05-agent.mp4` | 00:40 | 00:45 | 5 s | Click "Check it", "Checking...", then live result: "Block. This deployment on Friday violates the rule established by Mei Tan." |

> [4a, +0s] Now the part nobody else does. AI coding agents ship code, but they never read the incident review. So they ask Canon **first**.
> [4b, +10s] This is a **real MCP call** to Canon. The developer asks for a Friday deploy cron.
> [+17s] The agent calls check intent.
> [+21s] Canon says **block**: no production deploys on Fridays, scheduled jobs included. Owner Mei Tan, from the incident review. About **one second**.
> [4c, +29s] Try it on the page yourself. Same request,
> [4d, +33s] same block, live. Claude Code or Codex connect in **one line**.

## Scene 5. Paste a message (program 1:36 to 1:58, 22 s)

| Seg | Clip | IN | OUT | Length | On screen |
|---|---|---|---|---|---|
| 5 | `clip-06-paste.mp4` | 00:05 | 00:27 | 22 s | "Paste a new message and see what it breaks." Sample "Friday deploy job" from Pranav. Click "Check this message" (6 s in), staged progress (6 to 10 s), result at 10 s: "Goes against" the Friday ban, both quotes side by side, "What Canon understood", then "It also shows the Release process page is out of date." |

> [+0s] Paste a new message: Pranav schedules a **Friday** job, using a slot from the wiki.
> [+7s] Gemini pulls out the decision, and Canon checks every quote **word for word**.
> [+13s] It goes against the Friday ban. Both quotes, side by side. And the real cause: the Release process wiki is **still out of date**.

## Scene 6. Discord, live (program 1:58 to 2:18, 20 s)

Preferred: your own screen recording (steps in `docs/RECORDING-GUIDE.md`, part B). Fallback: the illustration clip.

**Live version** (your recording, cut to 20 s):

| Seg | Source | Length | On screen |
|---|---|---|---|
| 6a | your Discord recording | about 6 s | #engineering. You paste the message and press Return. The message appears. |
| 6b | your Discord recording | about 14 s | Cut the wait. The Canon bot reply appears under your message: "This goes against: There will be no production deployments on Fridays..." with the canon.tn07.dev link. Hold on it. Optional title over the cut: "About a minute later". |

> [+0s] Canon also listens **live**, in a public Discord server. I post the same Friday plan in engineering.
> [+7s] A sync on Cloud Run reads new messages every minute.
> [+11s] About a minute later, Canon replies in the thread, with the rule it breaks, and a link.

**Fallback version** (if the live reply does not come):

| Seg | Clip | IN | OUT | Length | On screen |
|---|---|---|---|---|---|
| 6 | `clip-07-discord.mp4` | 00:00 | 00:18 (end) | 18 s, then freeze 2 s | Illustration: Pranav posts in #engineering (1 to 9 s), Canon reads it, pulls out the decision, checks it against the record, finds a conflict (9 to 12 s), Canon replies in the thread (12 s on). Caption says it is an illustration. |

> [+0s] Canon also listens **live**, in a public Discord server. Someone posts the same Friday plan in engineering.
> [+9s] A sync on Cloud Run reads new messages every minute. It finds the conflict.
> [+15s] Canon replies in the thread, with the rule and a link.

## Scene 7. Ask why (program 2:18 to 2:39, 21 s)

| Seg | Clip | IN | OUT | Length | On screen |
|---|---|---|---|---|---|
| 7a | `clip-08-ask.mp4` | 00:03 | 00:19 | 16 s | "Ask why." "Why do we not deploy on Fridays?" is typed (0 to 5 s), Ask (5 s), answer at 7 s: "Answered in 1.0 seconds, from 1 quote", the verbatim quote, and "How this decision changed" with 16 Jan 2025 and 9 Mar 2026. |
| 7b | `clip-08-ask.mp4` | 00:25 | 00:30 | 5 s | Scroll to "When Canon does not know": "What is Northwind Labs annual recurring revenue for 2026?" "I do not know. The record has no decision or document that answers this." |

> [+0s] Ask why. Why don't we deploy on Fridays?
> [+6s] A **grounded** answer in about a second, with the source quote, and the timeline of how the rule changed.
> [+15s] And when the record has no answer, Canon says: **I do not know**. No guessing.

## Scene 8. Decisions and people (program 2:39 to 2:59, 20 s)

| Seg | Clip | IN | OUT | Length | On screen |
|---|---|---|---|---|---|
| 8a | `clip-09-decisions.mp4` | 00:00 | 00:04 | 4 s | "Decisions." The list with owner, date and status ("Broken by 2", "Official"). |
| 8b | `clip-09-decisions.mp4` | 00:08 | 00:18 | 10 s | The Friday decision: owner Mei Tan, Official, 9 March 2026. Why, the quote, the timeline, then "What breaks it now: Release process still gives the old rule." |
| 8c | `clip-09-decisions.mp4` | 00:26 | 00:32 | 6 s | "People." The org tree. Tomoko Ito, left 19 Dec 2025, Linh Nguyen took over. |

> [+0s] Every decision Canon found, with its owner, date and status.
> [+4s] Open the Friday ban. Who made it, why, and the timeline. And what **still breaks it**: a wiki page that gives the old rule.
> [+14s] The org chart shows who left, and who took over.

## Scene 9. Architecture (program 2:59 to 3:19, 20 s)

| Seg | Clip | IN | OUT | Length | On screen |
|---|---|---|---|---|---|
| 9 | `clip-10-architecture.mp4` | 00:00 | 00:15 (end) | 15 s, then freeze 5 s | "One service, one record, two ways in." Sources (1 to 3 s), Cloud Run box (3 s), FastAPI, MCP server, ADK agent (5 to 8 s), Gemini on Vertex AI (8 s), Firestore vector search (9 s), People and Firebase Hosting (10 to 11 s), footer "Every quote is checked word for word against its source." |

> [+0s] Under the hood, **one Cloud Run** service: FastAPI, an MCP server, and an ADK agent over A2A.
> [+10s] **Gemini** Flash-Lite on Vertex AI extracts and judges, with structured output. **Firestore** holds the record, with vector search.
> [+18s] **Firebase Hosting** serves the app.

## Scene 10. Benchmark (program 3:19 to 3:37, 18 s)

| Seg | Clip | IN | OUT | Length | On screen |
|---|---|---|---|---|---|
| 10 | `clip-11-benchmark.mp4` | 00:00 | 00:18 | 18 s | "How well does it work?" 82 of 82, 35 of 39, 18 of 19, 32 of 37, 5 of 5 (0 to 8 s). Scrolls to 1.2 s typical answer and 579 quotes (8 s), then "Memory health": 10 of 10, 0 stored twice, 3 of 3 (11 s on). |

> [+0s] Does it work? We planted known decisions and conflicts, then measured.
> [+5s] **Eighty-two** of eighty-two decisions found. **Thirty-five** of thirty-nine changes caught. All five unanswerable questions refused.
> [+13s] Typical answer: one point two seconds. No decision stored twice.

## Scene 11. Close (program 3:37 to 3:46, 9 s)

| Seg | Clip | IN | OUT | Length | On screen |
|---|---|---|---|---|---|
| 11 | `clip-12-close.mp4` | 00:00 | 00:06 (end) | 6 s, then freeze 3 s | Canon logo, "TRY IT canon.tn07.dev", "CODE github.com/tejasnafde/canon", "Built on Google Cloud: Gemini, Firestore, Cloud Run, Firebase". |

> [+0s] Canon. One memory, for your people **and** your agents.
> [+4s] Try it, and read the code, at the links on screen.

---

## Runtime check

| Scene | Program | Length |
|---|---|---|
| 1 Home | 0:00 | 18 s |
| 2 New hire | 0:18 | 20 s |
| 3 Catch-up | 0:38 | 20 s |
| 4 Agent | 0:58 | 38 s |
| 5 Paste | 1:36 | 22 s |
| 6 Discord | 1:58 | 20 s |
| 7 Ask why | 2:18 | 21 s |
| 8 Decisions and people | 2:39 | 20 s |
| 9 Architecture | 2:59 | 20 s |
| 10 Benchmark | 3:19 | 18 s |
| 11 Close | 3:37 | 9 s |
| **Total** | | **3:46** |

If a take runs long, the scene can grow by a second or two: hold the last frame (freeze frame).
Do not go past 3:55 in total.

## Text to type or post

- Scene 6, Discord #engineering (paste it exactly, once):
  `I have scheduled the production dispatch image refresh for every Friday at 15:00 SGT. It runs unattended, including configuration changes. I used the slot from the Release process wiki.`
- Everything else is already in the clips. Nothing else needs typing.

## Notes

- Numbers on screen and in the narration come from `backend/canon/eval_report.json` (dataset acme4,
  run 2026-10-17) and `/api/stats` on 2026-10-18. If either changes, re-record clips 02 and 11 and
  update scenes 1 and 10.
- The two "agent" lines in clip 05b are narration around a real call. The JSON in between is the real
  response from canon.tn07.dev/mcp, and the on-screen note says so. Do not describe the agent lines as
  model output.
- Model output varies. Do not edit tool output in the Discord recording. If the reply is unclear, use the fallback.
- Pronunciation: "Canon" like the camera brand. "A2A" is "A to A". "MCP" is "M C P". "tn07" is "T N zero seven".
