# Canon UI mocks v2: walkthrough

Static HTML for review. Open `index.html` in a browser. Screenshots are in `shots/`
(`<page>.png` is the 1280x800 viewport, `<page>-full.png` is the full page,
`*-phone.png` is a 390 px wide phone). All content comes from the corpus, the
gold file and `backend/canon/eval_report.json`. Northwind Labs is made up.

Menu: Home, Ask why, Decisions, For agents. "How well does it work?" sits in the footer.
A "Demo company: Northwind Labs (made up)" tag is on every page.

## 1. Home (`home.html`)
The user sees one sentence on what Canon is, and a card that says Northwind Labs is a made-up company and what Canon read (259 items, 36 decisions, 8 out-of-date documents).
Below it are three big story doors and one smaller "paste a message" door.
The user clicks the story they care about. Nobody needs to learn a menu first.
It proves to a judge, in 10 seconds, what the product does and that the data is honest demo data.

## 2. I am new here (`new-hire.html`)
The user sees a red warning first: the Release process wiki page is out of date, so do not release on a Friday.
Then the 5 decisions a new person must know, each with one line of why and the source it came from.
On the right are people to ask, and two people who left, with what Canon kept from them (13 decisions from Anika Rao).
It proves Canon turns 2 years of chat into a 2-minute onboarding, and that it keeps knowledge when people leave.

## 3. What changed while I was away (`catch-up.html`, `catch-up-sales.html`)
The user picks a role (6 roles) and a time span. The mock shows "Engineer, since I joined".
They see a two-sentence summary, then a to-do list ranked by a 0 to 100 urgency bar, each with "why this is high" and sources.
The Sales & Support version shows the Meridian email that still says USD 99, the Sakura email with the old 15 April date, and the 30-minute outage notice rule.
It proves the same record gives each role a different, useful answer.

## 4. Watch an AI agent get stopped (`agent.html`)
The user sees a 4-step replay in a terminal: a developer asks for a Friday deploy job, the agent asks Canon, Canon says BLOCK with the rule, owner, date and outage, and the agent offers Tuesday or Thursday.
Below, "Try it yourself" lets them type any action and get Allow, Warn or Block (the mock shows a Warn).
"Connect your own agent" gives the one-line commands for Claude Code and Codex, and explains MCP in one sentence.
It proves Canon works for AI agents, not only for people, and that it is a real tool they can plug in.

## 5. Paste a new message (`paste.html`)
The user picks a sample or pastes text, then clicks "Check this message". A short progress line shows the steps and the time (3.4 s, the measured median).
The result shows what Canon understood, the conflict with both quotes side by side, and the wiki page that is now out of date.
It proves Canon checks new information as it arrives, and that every quote is real.

## 6. Ask why (`ask.html`)
The user types a question or clicks an example. The answer has numbered citations with the exact quotes.
Next to it is a small timeline of how the Friday rule changed, from trial slot to ban to the PR that breaks it.
Below is an honest "I do not know" answer to a question the record cannot answer.
It proves answers are grounded, and that Canon does not make things up.

## 7. Decisions (`decisions.html`, `decision.html`)
The list shows each decision with owner, team, date and a plain status: Active, Replaced, or Broken by N.
Team and status filters sit above it. Clicking "No production deploys on Fridays" opens the decision page.
That page shows the rule in big type, why, who and when, a timeline, what breaks it now (PR 684 and the wiki page), and which agents checked it.
It proves Canon is a real record, not a chat window.

## 8. How well does it work? (`benchmark.html`)
The user sees seven results in plain words, such as "Found 36 of 38 decisions" and "Said I do not know to all 5 questions it could not answer".
Each result has one line on what it means, including the one miss and the 3 false alarms.
It proves the team measured the product against a labelled test set and reports the misses too.

## Open questions for the reviewer
- The catch-up mocks use "since I joined" with a join date, because the demo history ends in October 2026 and "1 week" has little in it.
- "Agents that checked it" on the decision page is example activity, labelled as such.
- The decisions list shows the 16 newest of 36, generated from the gold file (38 planted; the real list will come from the API).
