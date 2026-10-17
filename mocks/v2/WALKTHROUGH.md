# Canon UI mocks v2: walkthrough

Static HTML for review. Open `index.html` in a browser. Screenshots are in `shots/`
(`<page>.png` is the 1280x800 viewport, `<page>-full.png` is the full page,
`*-phone.png` is a 390 px wide phone). Retake them with
`/tmp/pwvenv/bin/python shoot.py`. All content comes from the corpus, the gold file
and `backend/canon/eval_report.json`. Northwind Labs is made up.

## Visual language (revised after the "less chips" review)

- Hierarchy comes from type and space. Fraunces for headings, figures and quotes;
  IBM Plex Sans for everything else. No mono caps labels, no eyebrows, no pills.
- No cards. Items sit in hairline-separated lists. The only boxed surface is the
  dark terminal on the agents page.
- One accent, vermilion, and it has one meaning: something breaks a decision. It
  appears as a small dot, a word, or a left rule. A hollow dot marks a document
  that is out of date. Everything else is ink or grey, including Allow and Warn.
- Sources are one plain line under the item: "Meeting, INC-042 review, 9 Mar 2026".
- Choices (roles, filters, samples) are text; the chosen one carries a rule beneath.
- The header has five text links: Home, Ask why, Decisions, For agents, and
  "How well does it work?" on the right. The footer says the company is made up.

## 1. Home (`home.html`)
One sentence on what Canon is, with three figures beside it (259 items read, 36 decisions found, 8 documents out of date) and a line that says Northwind Labs is made up.
Below, four stories as a list: I am new here, What changed while I was away, Watch an AI agent get stopped, Paste a new message. The first story is visible at the fold.
It proves to a judge, in 10 seconds, what the product does and that the data is honest demo data.

## 2. I am new here (`new-hire.html`)
A vermilion-ruled warning first: the Release process wiki page is out of date, so do not release on a Friday.
Then the five decisions a new person must know, each with one line of why and its source.
On the right, people to ask, and two people who left with what Canon kept from them (13 decisions from Anika Rao).
It proves Canon turns two years of chat into a two-minute onboarding, and keeps knowledge when people leave.

## 3. What changed while I was away (`catch-up.html`, `catch-up-sales.html`)
The user picks a role and a time span. Three roles are featured (Engineer, Product, Sales) and a "More roles" select holds the other eleven, grouped: Build (Design, Data, Security), Customers (Support, Marketing), Company (Finance, Operations, People and HR, Legal, Leadership), Just joined (New hire).
Time span is "1 week, 1 month, 3 months". Both mocks show 3 months. Open conflicts stay on the list however old, and the page says so.
They see a two-sentence summary in large serif, then a to-do list with an urgency number (0 to 100) on the right, vermilion when above 80.
The Sales version shows the Meridian email that still says USD 99, the Sakura email with the old 15 April date, and the 30-minute outage notice rule.
It proves the same record gives each role a different, useful answer.

## 4. Watch an AI agent get stopped (`agent.html`)
Above the fold at 1280x800: the four steps in plain words on the left, and the result on the right, the word "Block" in vermilion with the rule, owner, date and the outage behind it.
Below, the same exchange as the agent saw it, in a terminal: the developer's request, the `check_intent` call, Canon's BLOCK, and the agent offering Tuesday or Thursday.
"Try it yourself" lets them type any action and get Allow, Warn or Block (the mock shows "Check with a person first").
"Connect your own agent" gives the one-line commands for Claude Code and Codex, and explains MCP in one sentence.
It proves Canon works for AI agents, not only for people, and that it is a real tool they can plug in.

## 5. Paste a new message (`paste.html`)
The user picks a sample or pastes text, then clicks "Check this message". One line reports the steps and the time (3.4 s, the measured median).
The result shows the conflict with both quotes side by side under a vermilion rule, the wiki page that is now out of date, and what Canon understood.
It proves Canon checks new information as it arrives, and that every quote is real.

## 6. Ask why (`ask.html`)
The user types a question or picks an example. The answer has small numbered citations with the exact quotes beneath.
Next to it is a timeline of how the Friday rule changed, from trial slot to ban to the PR that breaks it.
Below is an honest "I do not know" answer to a question the record cannot answer.
It proves answers are grounded, and that Canon does not make things up.

## 7. Decisions (`decisions.html`, `decision.html`)
The list shows each decision with owner, team, date and a plain status. Broken decisions come first, the Friday decision at the top, then the rest newest first. "Broken by N" is vermilion with a dot; Active is plain; Replaced is grey.
Team and status filters are text rows above it. Clicking "No production deploys on Fridays" opens the decision page.
That page reads "Active, but 2 things break it", then the rule in big type, owner, date, where and what it replaces, why, what breaks it now (PR 684 and the wiki page), and a timeline.
The "Agents that checked it" example was removed; a line says agent checks will appear there once the API logs them.
It proves Canon is a real record, not a chat window.

## 8. How well does it work? (`benchmark.html`)
Reached from the header on every page. Seven results as large figures in a list, such as "Found 36 of 38 decisions" and "Said I do not know to all 5 questions it could not answer", each with one line on what it means, including the one miss and the 3 false alarms.
Every figure carries a `data-key` naming its field in `eval_report.json`, so a new run is a find-and-replace.
It proves the team measured the product against a labelled test set and reports the misses too.

## Open questions for the reviewer
- The catch-up mocks show "3 months". Some items on the list are older than that (June and July conflicts), kept because they are still open. If that reads wrong, the list can be cut to the window.
- The "More roles" select is a native control styled as text. In the build it should filter the list; here it is static.
- The decisions list shows 16 of 36, generated from the gold file (38 planted; the real list will come from the API).
