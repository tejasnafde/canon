# Canon demo video script (3:30)

Target 3:30, hard limit 4:00. Tejas narrates in his own voice, about 140 words per minute (about 480 words).
Every scene is one clip file, recorded at 1920x1080. Screen clips come from Playwright against https://canon.tn07.dev; motion clips (01, 10, 12) are built separately. The editor lays the clips end to end in this order and cuts each to its slot.

Before recording:

- Warm the service: open https://canon.tn07.dev and wait for the counts on Home. Cloud Run scales to zero.
- Use a fresh browser workspace (no earlier pastes).
- Terminal for clip 05: `claude mcp add --transport http canon https://canon.tn07.dev/mcp`, then start Claude Code in a scratch repo that has `.github/workflows/`.
- Discord for clip 07: join https://discord.gg/HwSgjmcgF5 with a test account. Have the web app open on Decisions in a second window.

| Clip | Time | On screen | Narration |
|---|---|---|---|
| `clip-01-title.mp4` (motion) | 0:00 - 0:07 | Ribbon logo draws in on paper. "Canon. The shared memory of a company, for its people and its AI agents." Team Localhost. | "Companies decide things every day. Then they forget. Canon remembers." |
| `clip-02-home.mp4` | 0:07 - 0:20 | Home. Hold on the headline and the counts: 380 items read, 345 official decisions, 27 documents now out of date. Scroll slowly to "Pick a story". | "Canon read two years of a made-up company, Northwind Labs. Three hundred eighty sources. It found three hundred forty-five decisions, and twenty-seven documents that are now wrong." |
| `clip-03-new-hire.mp4` | 0:20 - 0:38 | Click "I am new here". Hold on the red warning: the Priority support routing page is out of date, old line and new decision side by side. Scroll to "5 things you must know" and "People to ask". | "A new hire gets the five things that will get them in trouble. And a warning: this handbook page is out of date, do not follow it. Here is the old line, and the decision that replaced it. Plus who to ask, by topic." |
| `clip-04-catch-up.mp4` | 0:38 - 0:55 | "What changed while I was away?" Pick Engineer: summary and ranked to-do list with scores. Switch to Sales: the list changes. | "Back from leave? Pick your role. An engineer gets deploy and incident changes, ranked by urgency. Switch to sales, and it is pricing and promises to customers. Fourteen roles, one record." |
| `clip-05-agent-blocked.mp4` | 0:55 - 1:30 | "Watch an AI agent get stopped": the four steps and the red Block with the rule, owner Mei Tan, 9 March 2026. Cut to the real Claude Code terminal: prompt "Add a GitHub Actions cron that deploys the dispatch service to production every Friday." Claude Code calls `canon.check_intent`, gets block, stops and offers Tuesday or Thursday morning. | "Now the part nobody else does. Coding agents ship code on their own. They never read the incident review. So Claude Code asks Canon first, over MCP. A real tool call. Canon finds the rule: no production deploys on Fridays, scheduled jobs included. Who made it, when, and the outage behind it. The verdict is block. The agent does not write the job. It explains why, and offers Tuesday instead." |
| `clip-06-paste-drift.mp4` | 1:30 - 1:48 | "Paste a new message". Sample "Friday deploy job", click "Check this message". Show the extracted decision with its verified quote, and what it goes against: the Friday ban and the old Release process wiki. | "People make the same mistake. Pranav schedules a Friday job, from a slot in the wiki. Canon checks the quote word for word, flags the clash with the Friday ban, and shows the real cause: the wiki is out of date." |
| `clip-07-discord-live.mp4` | 1:48 - 2:15 | Discord #engineering: post "lets ship the dispatch cron this friday". Speed up the wait (label "about a minute"). Canon replies under the message with the rule and a link. Cut to the web app: the new alert, marked from Discord. | "This also runs live, on a public Discord server. Every minute, Canon reads new messages, threads, files and screenshots. I post: let's ship the dispatch cron this Friday. Canon replies under my message with the rule it breaks. The alert lands in the web app. And a guest cannot change a rule: Canon marks it unverified and asks the right lead." |
| `clip-08-ask-why.mp4` | 2:15 - 2:32 | Ask why: "Why can we no longer deploy production on Fridays?" Show the answer, timeline and verified quotes. Then "Which company acquired Northwind Labs?" and the refusal. | "Ask why, and you get a cited answer with the timeline. Ask something the record does not hold, and Canon says: I do not know. It does not invent an answer." |
| `clip-09-decisions-org.mp4` | 2:32 - 2:47 | Decisions list: official, proposed, out-of-date copies. Open People: the org tree, someone who left, their successor. | "Every decision shows its authority and its effective date. Old copies are marked outdated. The org tree says who owns what, who left, and who took over." |
| `clip-10-architecture.mp4` (motion) | 2:47 - 3:05 | Architecture diagram builds box by box: Firebase Hosting, Cloud Run (API, MCP, ADK agent over A2A, Discord sync), Cloud Scheduler, Gemini on Vertex AI, embeddings, Firestore vector search. | "Firebase Hosting serves the app. One Cloud Run service runs the API, MCP, and an ADK agent over A2A. Gemini Flash-Lite on Vertex judges with structured output, and reads PDFs and images. Firestore holds the record, with vector search." |
| `clip-11-benchmark.mp4` | 3:05 - 3:20 | "How well does it work?": 82 of 82, 35 of 39, 18 of 19, 32 of 37, 5 of 5. Scroll to memory health. | "We planted problems in the archive and measured. Eighty-two of eighty-two decisions found. Thirty-five of thirty-nine changes caught. All five unanswerable questions refused. The misses are on the page too." |
| `clip-12-close.mp4` (motion) | 3:20 - 3:30 | Logo, canon.tn07.dev, the one-line MCP command, the Discord invite. | "Canon. One memory, for your people and your agents. Try it, and connect your agent in one line." |

## Text to type

- Clip 05, Claude Code: `Add a GitHub Actions cron that deploys the dispatch service to production every Friday.`
- Clip 06: the "Friday deploy job" sample (`web/src/samples/live_paste.json`, key `friday-contradiction`).
- Clip 07, Discord #engineering: `lets ship the dispatch cron this friday`
- Clip 08: `Why can we no longer deploy production on Fridays?` then `Which company acquired Northwind Labs?`

## Notes

- Numbers come from `backend/canon/eval_report.json` (dataset acme4, run 2026-10-17, check score re-measured 2026-10-18) and `/api/stats` on 2026-10-18. If either changes, update clips 02 and 11 and their lines.
- Model output varies. Record clips 06 and 07 until they show a clear alert. Do not edit tool output.
- If Claude Code does not call `check_intent` on its own, add "Check with Canon first." to the prompt.
- Speak slowly, microphone close. Judges asked for clear, loud audio.
