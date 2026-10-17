# Canon demo video script (3:30)

Target length 3:30, hard limit 4:00. Narration is about 480 words, at about 140 words per minute.
Record at 1280x800 or larger. Use a clean browser profile and a fresh workspace (Ingest, then "Reset my workspace").

Before you record:

- Warm the service: open https://canon-tn07.web.app and wait for "Online" in the header. Cloud Run scales to zero, so the first call is slower.
- In a terminal, run `claude mcp add --transport http canon https://canon.tn07.dev/mcp` and start Claude Code in a scratch repo that has a `.github/workflows/` folder.
- Have `backend/scripts/agent_demo.py` ready in a second terminal tab.
- Copy the Friday paste text (below) to the clipboard.

| Time | On screen | Narration |
|---|---|---|
| 0:00 - 0:15 | Home page of https://canon-tn07.web.app, Engineer persona. Slowly scroll past the briefing and "Next best actions". | "This is Canon, the shared memory of a company. It keeps one record of decisions, for people and for AI agents. And it flags the moment anyone, or anything, drifts from it." |
| 0:15 - 0:30 | Cut to the Claude Code terminal. Type: `Add a GitHub Actions cron that deploys to production every Friday.` | "Here is the problem. Coding agents now change real systems. They read the code, but they never read the incident review where the team decided something." |
| 0:30 - 0:55 | Claude Code calls the `check_intent` tool. Show the tool result: verdict `block`, the decision "no production deploys on Fridays, including scheduled jobs and configuration-only releases", owner Mei Tan. Claude Code stops and explains. | "Claude Code has Canon as an MCP server. Before it writes the workflow, it calls check intent. Canon finds the decision from the March incident review: no production deploys on Fridays, scheduled jobs included. The verdict is block, with the quote and the owner. The agent stops and tells me why." |
| 0:55 - 1:05 | Switch to the browser, Home page. The red "Agent blocked" card and the live Agent activity feed show the call. | "Every agent call lands in the live activity feed. The team sees what their agents tried, and what Canon said." |
| 1:05 - 1:25 | Second terminal: run `uv run python scripts/agent_demo.py https://canon.tn07.dev/mcp`. The script first repeats the blocked check, then the PM bot runs `catch_me_up` (persona pm, last 30 days) and `ask_why` ("Why do we not deploy on Fridays?"). Let that part scroll. | "Agents also read the record. This product manager bot asks Canon to catch it up on the last thirty days, then asks why we stopped Friday deploys. It gets a briefing and a cited answer, in seconds." |
| 1:25 - 1:35 | Browser: Home, switch the persona to PM. Set Since to the widest range. Show the ranked actions with scores and reasons (Route Lens price and GA date items). | "People get the same briefing, ranked by what to do next, with a score and the reasons behind it." |
| 1:35 - 2:05 | Go to Ingest. Kind `paste`, author `Pranav Menon`, title `Dispatch cron review`. Paste the Friday text and click "Ingest and reconcile". Show the extracted decision with its verified quote and the alert. Then go to Home and open the alert on the **Release process** wiki: "contradicted by a newer decision", with both quotes. | "Now a human makes the same mistake. Pranav pastes a note: a Friday refresh, taken from the Release process wiki. Canon extracts the decision, checks the quote word for word, and raises an alert against the record. It also shows the real cause. The Release process wiki still lists the old Friday window. Canon marks it as contradicted by the newer decision, with both quotes side by side." |
| 2:05 - 2:30 | Home, switch the persona to New hire, since company day one. Scroll to "Who to ask". Then Ask why: type `Which company acquired Northwind Labs?` and show the refusal. | "A new hire gets onboarding from the same record, plus who to ask. And when the record has no answer, Canon says I do not know. It does not invent one." |
| 2:30 - 3:00 | Architecture slide from the deck (or the README mermaid diagram). Point to each box as you name it. | "Under the hood. Firebase Hosting serves the web app. One Cloud Run service runs the API, the MCP server, and an ADK agent over A2A. Gemini 3.5 Flash-Lite on Vertex AI does extraction, reconciliation and verdicts, all with structured output. Gemini embeddings and Firestore vector search, filtered by workspace, find the right decisions. Every quote is checked against its source, and source text is fenced off from instructions." |
| 3:00 - 3:20 | Benchmark page in the app (or the benchmark slide). Highlight decisions found, refusals, latency. | "We planted the problems in a synthetic company archive, then measured. Canon found 37 of 38 decisions, refused all 5 unanswerable questions, and got 13 of 15 agent checks right, at a median of about one second. We show the misses too." |
| 3:20 - 3:30 | Back to the Home page. Show the URL `canon-tn07.web.app` and the MCP command. | "Canon. One record of decisions, for your people and your agents. Try it now, and connect your own agent in one line." |

## Friday paste text

From `data/samples/live_paste.json`, key `friday-contradiction`:

```
Pranav: I have scheduled the production dispatch image refresh for every Friday at 15:00 Singapore time. It runs unattended, including configuration changes. I used the slot from the Release process wiki. This is routine housekeeping, not incident mitigation.
```

## Notes for the recording

- The numbers in the narration come from `backend/canon/eval_report.json` (run 2026-10-17 12:47 UTC). If a newer run is committed, update the 3:00 line to match it.
- Model output varies between runs. On one live probe the Friday paste was classed as an update with a premise alert, not a contradiction. Record the Ingest step until it shows a clear alert, and keep the Release process stale-doc alert on screen either way: it is part of the seeded record.
- If Claude Code does not call `check_intent` on its own, add "Check with Canon first." to the prompt. Do not edit the tool output.
- Speak slowly and keep the microphone close. Judges asked for clear, loud audio.
