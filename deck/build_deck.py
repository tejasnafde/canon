"""Fill the AI Builder Cup template with Canon's pitch deck.

  python3 deck/build_deck.py [--shots web/shots] [--mocks mocks/shots] [--out deck/canon-deck.pptx]

Images are read from folders, so the lead can drop final screenshots in and rebuild.
Snapshot slide uses SNAPSHOTS (file names inside --shots); missing files are skipped.
Needs python-pptx and Pillow. Export to PDF with deck/export_pdf.sh (Keynote).
"""
import argparse
import json
import tempfile
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
TEAM_NAME = "Canon"  # to be confirmed by the lead
LEADER = "Tejas Nafde"
PROBLEM = "Future of Work & Enterprise Productivity"
APP_URL = "https://canon-tn07.web.app"
REPO_URL = "https://github.com/tejasnafde/canon"
VIDEO_URL = "(add the video link)"
SNAPSHOTS = ["home-block.png", "ingest-result.png", "ask.png", "agents.png"]
WIREFRAMES = ["home.png", "ingest.png", "agents.png"]

FONT = "Google Sans Flex"
INK, MUTED, ACCENT, RED = RGBColor(0x20, 0x21, 0x24), RGBColor(0x5F, 0x63, 0x68), RGBColor(0x1A, 0x73, 0xE8), RGBColor(0xC5, 0x22, 0x1F)
FILL, LINE = RGBColor(0xF1, 0xF3, 0xF4), RGBColor(0xDA, 0xDC, 0xE0)
X0, Y0, W, H = Inches(0.35), Inches(1.3), Inches(9.3), Inches(4.05)  # content area under the title


def drop_slide(prs, index):
    ids = prs.slides._sldIdLst
    sid = ids[index]
    prs.part.drop_rel(sid.get(qn("r:id")))
    ids.remove(sid)


def style(run, size, bold=False, color=INK):
    run.font.name, run.font.size, run.font.bold, run.font.color.rgb = FONT, Pt(size), bold, color


def set_title(slide, text):
    box = next(s for s in slide.shapes if s.has_text_frame and s.text_frame.text.strip())
    tf = box.text_frame
    p = tf.paragraphs[0] if tf.paragraphs[0].text.strip() else next(p for p in tf.paragraphs if p.text.strip())
    for extra in [x for x in tf.paragraphs if x._p is not p._p]:
        extra._p.getparent().remove(extra._p)
    for r in p.runs[1:]:
        r._r.getparent().remove(r._r)
    p.runs[0].text = text
    box.height = Inches(0.6)


def text(slide, x, y, w, h, items, size=12, color=INK, gap=4, align=None, anchor=MSO_ANCHOR.TOP):
    """items: str or (bold_head, rest). A leading '- ' makes a bullet-like indent."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap, tf.vertical_anchor = True, anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    for i, it in enumerate(items if isinstance(items, list) else [items]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        if align:
            p.alignment = align
        head, rest = it if isinstance(it, tuple) else (None, it)
        if head:
            style(p.add_run(), size, True, color)
            p.runs[-1].text = head + (" " if rest else "")
        if rest:
            r = p.add_run()
            style(r, size, False, color)
            r.text = rest
    return tb


def box(slide, x, y, w, h, label, size=10, fill=FILL, color=INK, bold=False, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    s = slide.shapes.add_shape(shape, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    s.line.color.rgb = LINE
    s.shadow.inherit = False
    tf = s.text_frame
    tf.word_wrap, tf.vertical_anchor = True, MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.05)
    for i, line in enumerate(label.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        style(r, size if i == 0 else size - 2, bold if i == 0 else False, color if i == 0 else MUTED)
        r.text = line
    return s


def arrow(slide, a, b, side="h"):
    """Straight connector from shape a to shape b with an arrowhead at b."""
    if side == "h":
        x1, y1, x2, y2 = a.left + a.width, a.top + a.height // 2, b.left, b.top + b.height // 2
    else:
        x1, y1, x2, y2 = a.left + a.width // 2, a.top + a.height, b.left + b.width // 2, b.top
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    c.line.color.rgb, c.line.width = MUTED, Pt(1.25)
    ln = c.line._get_or_add_ln()
    tail = ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"})
    ln.append(tail)
    return c


def picture(slide, path, x, y, w, h, tmp):
    """Downscale to JPEG (keeps the PDF small), then fit inside the box, centred, with a thin border."""
    im = Image.open(path).convert("RGB")
    im.thumbnail((1400, 1400))
    out = Path(tmp) / (path.stem + ".jpg")
    im.save(out, quality=82)
    r = min(w / im.width, h / im.height)
    pw, ph = int(im.width * r), int(im.height * r)
    pic = slide.shapes.add_picture(str(out), x + (w - pw) // 2, y + (h - ph) // 2, pw, ph)
    pic.line.color.rgb, pic.line.width = LINE, Pt(0.75)
    return pic


def table(slide, x, y, w, rows, widths, size=10, row_h=Inches(0.28)):
    t = slide.shapes.add_table(len(rows), len(rows[0]), x, y, w, row_h * len(rows)).table
    for j, cw in enumerate(widths):
        t.columns[j].width = Emu(int(w * cw))
    for i, row in enumerate(rows):
        t.rows[i].height = row_h
        for j, val in enumerate(row):
            c = t.cell(i, j)
            c.fill.solid()
            c.fill.fore_color.rgb = INK if i == 0 else (FILL if i % 2 else RGBColor(0xFF, 0xFF, 0xFF))
            c.margin_top = c.margin_bottom = Inches(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = c.text_frame.paragraphs[0]
            r = p.add_run()
            style(r, size, i == 0, RGBColor(0xFF, 0xFF, 0xFF) if i == 0 else INK)
            r.text = str(val)
    return t


def caption(slide, x, y, w, s):
    text(slide, x, y, w, Inches(0.3), s, size=9, color=MUTED, align=PP_ALIGN.CENTER)


def build(shots: Path, mocks: Path, out: Path):
    prs = Presentation(str(ROOT / "deck" / "template.pptx"))
    drop_slide(prs, 14)  # empty spare content slide
    drop_slide(prs, 1)   # "Note: Please download this template..." instruction slide
    s = list(prs.slides)
    ev = json.loads((ROOT / "backend" / "canon" / "eval_report.json").read_text())
    tmp = tempfile.mkdtemp()

    # 1. Team details
    tf = next(x for x in s[0].shapes if x.has_text_frame).text_frame
    for p, val in zip([p for p in tf.paragraphs if p.text.strip()][1:], [TEAM_NAME, LEADER, PROBLEM]):
        r = p.add_run()
        style(r, 18, True)
        r.text = val

    # 2. Brief
    set_title(s[1], "Brief about the idea")
    text(s[1], X0, Y0, Inches(4.5), H, [
        ("Canon is the shared memory of a company, for its people and for its AI agents.", ""),
        "Teams decide things in Slack threads, meetings, PRs and email. The wiki goes stale. New hires and AI agents act on old information.",
        "Canon keeps one record of decisions. Each decision has a rationale, an owner, a date and a quote checked word for word against its source.",
        "Every new message, document and agent action is checked against that record. Canon flags drift: a contradiction, a stale wiki page, a broken premise.",
        "Coding agents connect over MCP and call check_intent before they act. A Friday cron deploy is blocked, with the incident review as evidence.",
    ], size=12, gap=7)
    if (shots / "home-block.png").exists():
        picture(s[1], shots / "home-block.png", Inches(5.0), Y0, Inches(4.65), H, tmp)

    # 3. Opportunities
    set_title(s[2], "Opportunities")
    cols = [
        ("How is it different?", [
            "Meeting-memory tools (Mnemo style) summarise. Decision logs (Decision Ledger style) store. Spec checkers (Spec Keeper style) review code.",
            "Canon does all three on one record, and its first-class users include AI agents, not only people."]),
        ("How does it solve the problem?", [
            "Extracts decisions with verified quotes from any source.",
            "Reconciles each one: same, update or contradiction.",
            "Raises alerts on stale docs and broken premises.",
            "Answers why, with citations, or says I do not know."]),
        ("USP: agent-native", [
            "An MCP server any agent can call: check_intent returns allow, warn or block with the deciding decision.",
            "Every agent read, write and check shows in a live feed.",
            "Also an ADK agent over A2A."]),
    ]
    cw = Inches(3.0)
    for i, (head, body) in enumerate(cols):
        x = X0 + i * (cw + Inches(0.15))
        box(s[2], x, Y0, cw, Inches(0.45), head, size=13, fill=INK, color=RGBColor(0xFF, 0xFF, 0xFF), bold=True,
            shape=MSO_SHAPE.RECTANGLE)
        text(s[2], x, Y0 + Inches(0.55), cw, Inches(3.4), ["- " + b for b in body], size=11, gap=6)

    # 4. Features
    set_title(s[3], "List of features offered by the solution")
    left = [("Ingest any source:", "Slack, meeting, wiki, PR, commit, email, free paste, image or PDF."),
            ("Decision extraction:", "statement, rationale, assumptions, owner, date, verified quotes."),
            ("Reconciliation:", "same, update (supersedes) or contradiction."),
            ("Drift alerts:", "stale wiki pages and premise changes, both quotes side by side."),
            ("Ask why:", "cited answer and decision timeline; refuses when the record is silent."),
            ("Catch me up:", "engineer, PM or new-hire briefing with ranked next actions (score 0 to 100 with reasons) and who to ask.")]
    right = [("Agent guard:", "check_intent gives allow, warn or block with the deciding decisions."),
             ("MCP server:", "six tools over streamable HTTP for Claude Code and Codex."),
             ("Live agent activity feed and an agent playground in the browser.", ""),
             ("Ask the departed expert:", "answers in a former colleague's voice, from their quotes only."),
             ("Human in the loop:", "alerts stay open until a person resolves them."),
             ("Integrations:", "A2A agent card, GitHub PR webhook, Discord slash command."),
             ("Benchmark:", "planted problems vs found, on a labelled gold set.")]
    text(s[3], X0, Y0, Inches(4.55), H, left, size=11, gap=7)
    text(s[3], X0 + Inches(4.75), Y0, Inches(4.55), H, right, size=11, gap=7)

    # 5. Process flow
    set_title(s[4], "Process flow diagram")
    bw, bh, gx = Inches(1.38), Inches(0.75), Inches(0.2)
    text(s[4], X0, Y0 - Inches(0.05), Inches(5), Inches(0.3), ("A. A new source arrives (web paste, Slack, PR, agent)", ""), size=11)
    row1 = ["Source\ntext or image", "Chunk + embed\ngemini-embedding-001", "Extract decisions\nGemini, structured", "Verify quotes\nexact substring",
            "Reconcile\nsame / update / contra", "Drift scan\nstale docs, premises"]
    y1 = Y0 + Inches(0.32)
    a = [box(s[4], X0 + i * (bw + gx), y1, bw, bh, t) for i, t in enumerate(row1)]
    for i in range(len(a) - 1):
        arrow(s[4], a[i], a[i + 1])
    rec = box(s[4], X0 + Inches(1.9), y1 + Inches(1.15), Inches(4.3), Inches(0.6),
              "Firestore record: decisions, alerts, activity\nvector search, workspace prefilter", size=11, fill=RGBColor(0xE8, 0xF0, 0xFE), bold=True)
    arrow(s[4], a[4], rec, "v")
    text(s[4], X0, Y0 + Inches(3.5), Inches(6), Inches(0.3), ("B. A person or an agent asks or acts", ""), size=11)
    row2 = ["Question, briefing\nor intended action", "Embed query\nnearest decisions", "Below threshold?\nrefuse / allow, no LLM",
            "Gemini judges\nanswer or verdict", "Cite verified quotes\nallow / warn / block", "Activity feed\nweb, MCP, A2A"]
    y2 = Y0 + Inches(2.67)
    b = [box(s[4], X0 + i * (bw + gx), y2, bw, bh, t) for i, t in enumerate(row2)]
    for i in range(len(b) - 1):
        arrow(s[4], b[i], b[i + 1])
    c = arrow(s[4], rec, b[1], "v")
    c.begin_x = c.end_x = b[1].left + b[1].width // 2  # straight down into "Embed query"

    # 6. Wireframes
    set_title(s[5], "Wireframes / mock diagrams")
    names = [("home.png", "Home: briefing, alerts, agent feed"), ("ingest.png", "Ingest: paste and reconcile"),
             ("agents.png", "Agents: MCP playground")]
    spots = [(X0, Y0, Inches(5.6), Inches(3.5)), (X0 + Inches(5.8), Y0, Inches(3.5), Inches(1.65)),
             (X0 + Inches(5.8), Y0 + Inches(1.95), Inches(3.5), Inches(1.65))]
    for (n, cap), (x, y, w, h) in zip(names, spots):
        if (mocks / n).exists():
            pic = picture(s[5], mocks / n, x, y, w, h, tmp)
            caption(s[5], x, pic.top + pic.height, w, cap)

    # 7. Architecture
    set_title(s[6], "Architecture diagram")
    cx = [box(s[6], X0, Y0 + i * Inches(0.95), Inches(1.9), Inches(0.75), t, size=10) for i, t in enumerate([
        "Web app (React)\nFirebase Hosting", "Claude Code, Codex\nMCP clients", "Other agents\nA2A", "GitHub, Discord\nwebhooks"])]
    run = s[6].shapes.add_shape(MSO_SHAPE.RECTANGLE, X0 + Inches(2.55), Y0 - Inches(0.05), Inches(3.4), H)
    run.fill.solid(); run.fill.fore_color.rgb = RGBColor(0xE8, 0xF0, 0xFE); run.line.color.rgb = ACCENT
    run.shadow.inherit = False
    text(s[6], run.left, run.top + Inches(0.02), run.width, Inches(0.3), ("Cloud Run service canon (asia-south1, min 0)", ""), size=10,
         color=ACCENT, align=PP_ALIGN.CENTER)
    ep = [box(s[6], run.left + Inches(0.2), Y0 + Inches(0.35) + i * Inches(0.62), Inches(1.3), Inches(0.5), t, size=10, fill=RGBColor(0xFF, 0xFF, 0xFF))
          for i, t in enumerate(["FastAPI /api", "MCP /mcp", "ADK agent /a2a", "Hooks"])]
    core = box(s[6], run.left + Inches(1.85), Y0 + Inches(0.35), Inches(1.35), Inches(2.36),
               "Core\ningest, reconcile\nask, briefing\ncheck, expert", size=11, fill=RGBColor(0xFF, 0xFF, 0xFF), bold=True)
    for c, e in zip(cx, ep):
        arrow(s[6], c, e)
    for e in ep:
        arrow(s[6], e, core)
    guard = box(s[6], run.left + Inches(0.2), Y0 + Inches(2.95), Inches(3.0), Inches(0.75),
                "Guardrails\nverified quotes, refusal threshold,\nsource fencing, input limits, timeouts", size=10, fill=RGBColor(0xFF, 0xFF, 0xFF))
    gcp = [box(s[6], X0 + Inches(6.55), Y0 + i * Inches(1.3), Inches(2.75), Inches(1.0), t, size=11) for i, t in enumerate([
        "Vertex AI Gemini\ngemini-3.5-flash-lite\nstructured output, label app=canon", "Embeddings\ngemini-embedding-001, 768 dims",
        "Firestore (database canon)\nvector search (cosine)\nworkspace prefilter"])]
    for g in gcp:
        arrow(s[6], core, g)

    # 8. Technologies
    set_title(s[7], "Technologies used in the solution")
    table(s[7], X0, Y0, W, [
        ["Technology", "What Canon uses it for"],
        ["Gemini 3.5 Flash-Lite on Vertex AI", "Extraction, reconciliation, drift checks, answers, briefings, check_intent verdicts; structured output (response_schema)"],
        ["gemini-embedding-001 (768 dims)", "Embeddings for source chunks, decisions and queries"],
        ["Cloud Firestore, named database canon", "Sources, chunks, decisions, alerts, activity, people; vector search with a workspace prefilter"],
        ["Cloud Run", "One scale-to-zero service: FastAPI API, MCP server, A2A agent, GitHub and Discord hooks"],
        ["Firebase Hosting", "Static web app; rewrites /api, /mcp, /a2a to Cloud Run on one origin"],
        ["Agent Development Kit (ADK) + A2A", "Canon as an LlmAgent with four tools, discoverable by agent card"],
        ["Model Context Protocol (FastMCP)", "Six tools over streamable HTTP for Claude Code, Codex and other clients"],
        ["Python 3.12, FastAPI, uv, pytest", "Backend; tests replay recorded Gemini fixtures, no network"],
        ["React, TypeScript, Vite", "Web app: home, decisions, ask, ingest, agents, benchmark"],
    ], [0.33, 0.67], size=10, row_h=Inches(0.38))

    # 9. Cost
    set_title(s[8], "Estimated implementation cost")
    text(s[8], X0, Y0, Inches(4.55), H, [
        ("Idle cost is near zero.", "Cloud Run scales to zero (min instances 0). There is no per-hour resource."),
        ("Firestore:", "the demo data fits inside the free tier so far."),
        ("Gemini is paid per call.", "An answer is one embedding and one Flash-Lite call. A check is one embedding and one call, or none when no decision is relevant. An ingest is one extraction call plus a few reconcile calls."),
        ("Refusals and irrelevant checks never reach Gemini.", "The similarity threshold stops them first."),
        ("Tracked, not guessed:", "every Gemini call and the Cloud Run service carry the label app=canon, so the billing export splits Canon's spend."),
    ], size=11, gap=7)
    text(s[8], X0 + Inches(4.8), Y0, Inches(4.5), H, [
        ("What we measured (2026-10-17):", ""),
        "- The billing export has no app=canon rows yet. It lags by up to a day.",
        "- All embedding usage on the shared billing project since 2026-10-12: INR 0.16.",
        ("List price (unverified):", "third-party listings quote USD 0.30 per 1M input tokens and USD 2.50 per 1M output tokens for Gemini 3.5 Flash-Lite. Check the Vertex AI pricing page before you rely on it."),
        ("Not measured yet:", "tokens per call, so we do not quote a per-call price."),
    ], size=11, gap=7)

    # 10. Snapshots
    set_title(s[9], "Snapshots of the prototype")
    caps = {"home-block.png": "Agent blocked on a Friday deploy", "ingest-result.png": "Paste raises a contradiction",
            "ask.png": "Ask why: cited answer and timeline", "agents.png": "Agent playground over MCP"}
    found = [n for n in SNAPSHOTS if (shots / n).exists()]
    sw, sh = Inches(4.55), Inches(1.72)
    for i, n in enumerate(found[:4]):
        x, y = X0 + (i % 2) * (sw + Inches(0.2)), Y0 + (i // 2) * (sh + Inches(0.3))
        picture(s[9], shots / n, x, y, sw, sh, tmp)
        caption(s[9], x, y + sh, sw, caps.get(n, n))

    # 11. Benchmark
    set_title(s[10], "Prototype performance report / benchmarking")
    pct = lambda a, b: f"{round(100 * a / b)}%" if b else ""
    table(s[10], X0, Y0, Inches(5.2), [
        ["Task (labelled gold set)", "Planted", "Found", "Score"],
        ["Decisions extracted", ev["decisions_planted"], ev["decisions_found"], pct(ev["decisions_found"], ev["decisions_planted"])],
        ["Contradictions and updates", ev["contradictions_planted"], ev["contradictions_found"], pct(ev["contradictions_found"], ev["contradictions_planted"])],
        ["False positive alerts", "", ev["false_positives"], ""],
        ["check_intent verdicts", ev["check_cases"], ev["check_correct"], pct(ev["check_correct"], ev["check_cases"])],
        ["Unanswerable, refused", ev["unanswerable"], ev["refused_correctly"], pct(ev["refused_correctly"], ev["unanswerable"])],
        ["Latency p50 / p95", "", f"{ev['p50_ms']} / {ev['p95_ms']} ms", ""],
    ], [0.52, 0.15, 0.2, 0.13], size=10, row_h=Inches(0.36))
    text(s[10], X0, Y0 + Inches(2.7), Inches(5.2), Inches(1.3), [
        f"Run {ev['run_at'][:16].replace('T', ' ')} UTC, model {ev['model']}. Corpus: 259 synthetic sources, about 100 of them pure noise.",
        "Reproduce: backend/scripts/seed.py, then backend/scripts/eval.py. The app serves the report at /api/eval."],
        size=9, color=MUTED, gap=4)
    text(s[10], X0 + Inches(5.45), Y0, Inches(3.85), H, [("Notes and misses, in the open", "")] + ["- " + n for n in ev["notes"]],
         size=9, gap=3)

    # 12. Future
    set_title(s[11], "Additional details / future development")
    text(s[11], X0, Y0, Inches(4.55), H, [
        ("Where people already talk:", "Slack, Microsoft Teams and Discord plug-ins that ingest threads and answer in place. A Discord slash command exists today."),
        ("Permissions:", "sign-in, per-team visibility, and decisions that follow the access rules of their source."),
        ("Code review at scale:", "the GitHub webhook already checks PR text; next, check diffs and post review comments for every repo."),
    ], size=12, gap=9)
    text(s[11], X0 + Inches(4.8), Y0, Inches(4.5), H, [
        ("Beyond software:", "manufacturing SOP drift. A line change or a supplier note that contradicts the approved standard operating procedure raises an alert before a shift runs it."),
        ("Better recall:", "the benchmark shows 4 of 17 contradictions missed; we will tune reconciliation against the gold set."),
        ("Real data:", "ingest this repository's own README, PRs and commits next to the synthetic corpus."),
    ], size=12, gap=9)

    # 13. Links
    set_title(s[12], "Links")
    text(s[12], X0, Y0, W, H, [
        ("GitHub public repository:", REPO_URL),
        ("Demo video:", VIDEO_URL),
        ("Final product link:", APP_URL),
        ("Cloud Run API:", "https://canon-ezvux7gqxa-el.a.run.app"),
        ("Connect your agent:", "claude mcp add --transport http canon https://canon.tn07.dev/mcp"),
        ("", "No login needed. All company data is synthetic and labelled as such."),
    ], size=14, gap=12)

    prs.save(str(out))
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--shots", default=str(ROOT / "web" / "shots"))
    ap.add_argument("--mocks", default=str(ROOT / "mocks" / "shots"))
    ap.add_argument("--out", default=str(ROOT / "deck" / "canon-deck.pptx"))
    a = ap.parse_args()
    build(Path(a.shots), Path(a.mocks), Path(a.out))
