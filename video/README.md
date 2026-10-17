# Demo video clips

Every clip is 1920x1080, H.264, 30 fps, silent. Tejas narrates and cuts them together.
The clips are in `video/clips/` (gitignored). Rebuild them with the commands below.
The script is `docs/video-script.md`, and the scene numbers match the clip numbers.

| Clip | Scene | Length | What it shows | Source |
|---|---|---|---|---|
| `clip-01-title.mp4` | 01 title | 5.0 s | Ribbon mark, "Canon", the tagline | `motion/title.html` |
| `clip-02-home.mp4` | 02 home | 25.8 s | Home: the headline, the counts, a hover over each story | `record.py home` |
| `clip-03-new-hire.mp4` | 03 new hire | 37.2 s | Welcome page, 5 things to know, people to ask, people who left | `record.py new-hire` |
| `clip-04-catch-up.mp4` | 04 catch-up | 51.4 s | Engineer summary and to-do list, urgency tooltip, then Sales | `record.py catch-up` |
| `clip-05-agent.mp4` | 05 agent | 54.3 s | The Block replay and the agent exchange, then "Try it yourself" with the Friday cron and a live Block | `record.py agent` |
| `clip-05b-agent-terminal.mp4` | 05b agent, terminal | 18.1 s | Terminal-style replay of a real `check_intent` MCP call and its JSON answer | `terminal/agent.html` |
| `clip-06-paste.mp4` | 06 paste | 40.0 s | Friday sample, staged progress, both quotes side by side, Release process wiki out of date | `record.py paste` |
| `clip-07-discord.mp4` | 07 Discord | 18.4 s | Illustration: post in #engineering, Canon sync, conflict, reply in the thread | `motion/discord.html` |
| `clip-08-ask.mp4` | 08 ask why | 36.9 s | "Why do we not deploy on Fridays?" with its answer, quote and timeline, then the refusal | `record.py ask` |
| `clip-09-decisions.mp4` | 09 decisions and people | 40.5 s | Decision list, the Friday decision, the People page, Mei Tan | `record.py decisions` |
| `clip-10-architecture.mp4` | 10 architecture | 15.0 s | Sources, Cloud Run (FastAPI, MCP, ADK A2A), Gemini, Firestore, Firebase Hosting, built up one piece at a time | `motion/architecture.html` |
| `clip-11-benchmark.mp4` | 11 benchmark | 28.1 s | "How well does it work?" page, scrolled slowly | `record.py benchmark` |
| `clip-12-close.mp4` | 12 close | 6.0 s | canon.tn07.dev, the GitHub repo, "Built on Google Cloud" | `motion/close.html` |

The screen clips are deliberately slow (12 characters per second, long holds on results).
Cut or speed them up in the edit. Notes for the cut:

- `clip-04`: the Sales briefing takes a few seconds to load after the click. Cut the skeleton.
- `clip-05`: Canon answers "Try it yourself" in about 1 s. The typing is about 7 s, so speed it up 2x if you need time.
- `clip-07`: this is an illustration. Also record the real Discord exchange; see `clips/clip-07-README.md`.
- `clip-05b`: the JSON is real (`terminal/exchange.json`, fetched from canon.tn07.dev/mcp). Only the two "agent" lines are narration, and the on-screen note says so.

## Rebuild

```sh
# screen clips from the live app (Chromium + Playwright in /tmp/pwvenv)
/tmp/pwvenv/bin/python video/record.py                 # all of them
/tmp/pwvenv/bin/python video/record.py agent paste     # only these
CANON_BASE=http://localhost:5181 /tmp/pwvenv/bin/python video/record.py decisions   # a local build

# motion clips (frame-exact: GSAP timeline, seeked and screenshotted per frame)
/tmp/pwvenv/bin/python video/motion/render.py video/motion/title.html        video/clips/clip-01-title.mp4
/tmp/pwvenv/bin/python video/motion/render.py video/motion/discord.html      video/clips/clip-07-discord.mp4
/tmp/pwvenv/bin/python video/motion/render.py video/motion/architecture.html video/clips/clip-10-architecture.mp4
/tmp/pwvenv/bin/python video/motion/render.py video/motion/close.html        video/clips/clip-12-close.mp4
/tmp/pwvenv/bin/python video/motion/render.py video/terminal/agent.html      video/clips/clip-05b-agent-terminal.mp4

# refresh the real MCP exchange (one Gemini call, throwaway workspace, reset after)
~/Desktop/projects/google-hackathon/canon/backend/.venv/bin/python video/terminal/fetch_mcp.py
```

How `record.py` works:

- Frames come from the DevTools screencast (JPEG q92), not Playwright's 1 Mbit/s recorder, so small text stays sharp.
- A cursor is drawn on the page (ink arrow, vermilion ring on click), so viewers can follow it.
- Capture starts after the first page has settled, so a clip has no blank start.
- Each clip uses a fresh browser context, so it gets a fresh visitor workspace (localStorage `canon-ws`). The workspace is reset at the end.

Gemini cost: one full `record.py` run makes about 10 to 15 live calls (catch-up 2 briefings, agent 2 checks, paste 1 ingest, ask 3 questions). Do not loop it.

Fonts (Fraunces, IBM Plex, OFL) and GSAP are vendored in `motion/vendor/`, so motion renders need no network.
