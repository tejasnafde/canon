"""F6 catch me up and F12 onboarding. Scores are computed in code; Gemini only writes the prose."""
import asyncio
import re
import time
from datetime import datetime

from pydantic import BaseModel

from canon import llm
from canon.ask import citations
from canon.models import Action, Briefing, BriefingRequest, Person
from canon.store import get_store, now, scrub_alerts, utc

URGENT = re.compile(r"\b(urgent|asap|blocker|blocking|incident|outage|security|p0|sev1|critical|"
                    r"rollback|revert|breach|escalat\w*|churn)\b", re.I)
DEPEND = re.compile(r"\b(blocks|blocked by|depends on|dependency|handoff|hand off|waiting on|cross-team)\b", re.I)
RULE = re.compile(r"\b(no|never|must|always|only|prohibit\w*|forbid\w*|requires?|not allowed)\b", re.I)

# Per persona: the vocabulary of their area and the source kinds where their work lives.
PERSONA = {
    "engineer": r"deploy\w*|release|cron|schedul\w*|ci|pipeline|api|infra\w*|database|migration|schema|incident|"
                r"on-call|oncall|rollback|revert\w*|logs?|logging|parser|webhooks?|retr\w+|ingestion|service|backups?|"
                r"security|latency|workers?|batch\w*|config\w*|production|pr|code",
    "pm": r"pric\w+|launch\w*|general availability|roadmap|customers?|contracts?|renewal|sla|preview|pilot|marketing|"
          r"sales|landing|promis\w+|subscriptions?|order forms?|proposals?|deadline|brochure|packaging|headline|"
          r"route lens|scope|beta|ga",
    "new_hire": r"policy|process|handbook|onboarding|on-call|oncall|release\w*|deploy\w*|production|window|approval|"
                r"access|incident|security|review|standard|convention|wiki|faq",
}
HOME = {"engineer": ("pr", "commit"), "pm": ("email",), "new_hire": ("wiki", "doc")}
WHERE = {"pr": "a PR", "commit": "a commit", "email": "a customer email", "wiki": "the wiki", "doc": "a doc"}
BASE = {"decision": 30, "contradiction": 45, "agent_violation": 44, "pr_deviation": 44,
        "stale_doc": 38, "premise_changed": 32}
MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}
DATE_ISO = re.compile(r"\b(20\d\d)-(\d\d)-(\d\d)\b")
DATE_MD = re.compile(r"\b(?:by|before|until|due|on|deadline)\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})\b", re.I)


def deadline_days(text: str, ref: datetime, today: datetime) -> int | None:
    """Days from today to the nearest future deadline mentioned in text, else None."""
    found = []
    for y, m, d in DATE_ISO.findall(text):
        try:
            found.append(datetime(int(y), int(m), int(d), tzinfo=today.tzinfo))
        except ValueError:
            pass
    for mon, d in DATE_MD.findall(text):
        try:
            found.append(datetime(ref.year, MONTHS[mon[:3].lower()], int(d), tzinfo=today.tzinfo))
        except ValueError:
            pass
    days = [(f - today).days for f in found if (f - today).days >= -1]
    return min(days) if days else None


def score(text: str, persona: str, kind: str, ts: datetime, today: datetime, *, source_kind: str | None = None,
          teams: set[str] = frozenset(), links: int = 0, changed: bool = False) -> tuple[int, list[str]]:
    """Next-best-action score with the human-readable reasons behind it. Deterministic.

    kind is "decision" or an alert kind. Points, then clamped to 30..98:
      base by kind (a contradiction outranks a stale doc outranks a plain decision)  30-45
      persona vocabulary hits (distinct terms): 1 / 2 / 3+ -> +10 / +18 / +24; none -> -12
      evidence lives where the persona works (engineer pr/commit, pm email, new hire wiki)  +12
      new hire: a standing rule ("no", "must", "only")  +10
      the decision changed an earlier one  +6
      other open alerts point at the same decision: +6 each, max +12
      deadline in 2 / 7 / 30 days  +15 / +10 / +5;  urgent words  +8;  cross-team dependency  +6
      age: last 7 days +8, last 30 days +4, over a year -6
    """
    pts, reasons = BASE.get(kind, 30), []
    if kind != "decision":
        reasons.append(f"open {kind.replace('_', ' ')} alert")
    hits = len({m.lower() for m in re.findall(rf"\b(?:{PERSONA[persona]})\b", text, re.I)})
    who = persona.replace("_", " ")
    if hits:
        pts += (0, 10, 18)[hits] if hits < 3 else 24
        reasons.append(f"relevant to {who}")
    else:
        pts -= 12
    if source_kind in HOME[persona]:
        pts += 12
        reasons.append(f"evidence in {WHERE[source_kind]}")
    if persona == "new_hire" and RULE.search(text):
        pts += 10
        reasons.append("a standing rule")
    if changed:
        pts += 6
        reasons.append("changed an earlier decision")
    if links:
        pts += min(12, 6 * links)
        reasons.append(f"{links} other open alert(s) on this decision")
    dd = deadline_days(text, ts, today)
    if dd is not None and dd <= 30:
        pts += 15 if dd <= 2 else 10 if dd <= 7 else 5
        reasons.append(f"deadline in {max(dd, 0)} days" if dd > 0 else "deadline today")
    if m := URGENT.search(text):
        pts += 8
        reasons.append(f"urgent: \"{m.group(0).lower()}\"")
    mentioned = {t for t in teams if re.search(rf"\b{re.escape(t)}\b", text, re.I)}
    if DEPEND.search(text) or len(mentioned) >= 2:
        pts += 6
        reasons.append("cross-team dependency" + (f" ({', '.join(sorted(mentioned))})" if mentioned else ""))
    age = (today - utc(ts)).days
    if age <= 7:
        pts += 8
        reasons.append("from the last 7 days")
    elif age <= 30:
        pts += 4
        reasons.append("from the last 30 days")
    elif age > 365:
        pts -= 6
    return max(30, min(98, pts)), reasons


def rank(decs: list[dict], alerts: list[dict], kinds: dict[str, str], persona: str, since: datetime,
         today: datetime, teams: set[str]) -> list[tuple[int, list[str], str, dict]]:
    """Candidates (score, reasons, "decision"|"alert", doc), best first. Ties break on recency, then id."""
    dmap = {d["id"]: d for d in decs}
    links: dict[str, int] = {}
    for a in alerts:
        for i in {a.get("decision_id"), a.get("related_decision_id")} - {None}:
            links[i] = links.get(i, 0) + 1
    cands = []
    for d in decs:
        if utc(d["ts"]) >= since and d["status"] == "active":
            src = kinds.get(d["quotes"][0]["source_id"]) if d["quotes"] else None
            s, r = score(f"{d['topic']} {d['statement']} {d['rationale']}", persona, "decision", d["ts"], today,
                         source_kind=src, teams=teams, links=links.get(d["id"], 0), changed=bool(d.get("supersedes")))
            cands.append((s, r, "decision", d))
    for a in alerts:  # open alerts are actionable whatever their age
        d = dmap.get(a.get("decision_id") or "")
        rel = dmap.get(a.get("related_decision_id") or "")
        text = " ".join(x for x in (a["explanation"], d and d["statement"], rel and rel["statement"],
                                    d and d["topic"]) if x)
        others = max(0, links.get(a.get("related_decision_id") or a.get("decision_id") or "", 0) - 1)
        s, r = score(text, persona, a["kind"], (d or a)["ts"] if d else a["created_at"], today,
                     source_kind=kinds.get(a.get("source_id") or ""), teams=teams, links=others)
        cands.append((s, r, "alert", a))
    cands.sort(key=lambda c: (c[0], utc(c[3].get("ts") or c[3]["created_at"]), c[3]["id"]), reverse=True)
    return cands


class Prose(BaseModel):
    summary: str
    highlights: list[str]
    titles: list[str]
    whys: list[str]


async def briefing(req: BriefingRequest, workspaces: list[str]) -> Briefing:
    t0 = time.perf_counter()
    st = get_store()
    since, today = utc(req.since), now()
    decs, alerts, people, resolved = await asyncio.gather(
        st.query("decisions", workspaces), st.query("alerts", workspaces, status="open"),
        st.query("people", workspaces), st.query("resolutions", workspaces))
    done = {r["alert_id"] for r in resolved}
    alerts = [a for a in alerts if a["id"] not in done]
    await scrub_alerts(alerts)
    teams = {p["team"].lower() for p in people if p.get("team")}
    active_people = {p["name"].lower() for p in people if p["status"] == "active"}
    kinds = {i: x["kind"] for i, x in (await st.get_many(
        "sources", [d["quotes"][0]["source_id"] for d in decs if d["quotes"] and utc(d["ts"]) >= since]
        + [a["source_id"] for a in alerts if a.get("source_id")])).items()}
    cands = rank(decs, alerts, kinds, req.persona, since, today, teams)
    top = cands[:8]

    who = sorted((Person(**p) for p in people if p["status"] == "active"),
                 key=lambda p: -sum(1 for d in decs if p.name.split()[0].lower() in d["owner"].lower()))[:4] \
        if req.persona == "new_hire" else []

    if not top:
        return Briefing(persona=req.persona, since=req.since, summary=f"Nothing new in the record since {since.date()}.",
                        highlights=[], actions=[], who_to_ask=who, latency_ms=int((time.perf_counter() - t0) * 1000))

    lines = []
    for i, (s, r, kind, o) in enumerate(top):
        body = o["statement"] if kind == "decision" else f"{o['kind']} alert: {o['explanation']}"
        lines.append(f"{i + 1}. [{kind}, score {s}] {body} (factors: {'; '.join(r)})")
    recent = sorted((d for d in decs if utc(d["ts"]) >= since), key=lambda d: d["ts"], reverse=True)[:15]
    prompt = (f"Write a catch-up briefing for a {req.persona.replace('_', ' ')} covering {since.date()} to {today.date()}.\n"
              "DECISIONS in the period:\n" + "\n".join(f"- {utc(d['ts']).date()} [{d['status']}] {d['statement']}" for d in recent) +
              "\n\nRANKED ACTIONS (keep this order):\n" + "\n".join(lines) +
              "\n\nsummary: exactly two short, specific sentences, at most 35 words together, about the top-ranked "
              "actions for this reader. Name the concrete things: what changed, what it now blocks or makes stale, with "
              "the PR number, page title, customer or date when the facts give one. Example of the shape: \"Two things "
              "matter this week: the Friday deploy ban now blocks PR #412, and the Release process wiki is stale. "
              "Pricing for new Route Lens customers moved to USD 149.\" Never describe the briefing itself (no "
              "\"This briefing covers\") and no generic filler."
              f" highlights: 3 to 5 short bullets. titles and whys: exactly {len(top)} "
              "each, one per action in order; title is an imperative under 10 words, why is one sentence from the facts.")
    pr = await llm.generate_json(prompt, Prose, system="You are Canon. Use only the facts given.")

    pairs = [(q["source_id"], q["quote"], o["id"] if kind == "decision" else o.get("decision_id"))
             for _, _, kind, o in top for q in o["quotes"][:1]]
    cmap: dict[str | None, list] = {}
    for c in await citations(pairs):
        cmap.setdefault(c.decision_id, []).append(c)
    actions = []
    for i, (s, r, kind, o) in enumerate(top):
        did = o["id"] if kind == "decision" else o.get("decision_id")
        if kind == "alert":
            chip = "resolve_alert"
        elif o["owner"].lower() in active_people:
            chip = "ask_person"
        else:
            chip = "view_decision"
        title = pr["titles"][i] if i < len(pr["titles"]) else (o.get("statement") or o["explanation"])[:80]
        why = pr["whys"][i] if i < len(pr["whys"]) else "; ".join(r)
        actions.append(Action(priority=s, title=title, why=why, reasons=r, citations=cmap.get(did, [])[:2], chip=chip))
    res = Briefing(persona=req.persona, since=req.since, summary=pr["summary"], highlights=pr["highlights"],
                   actions=actions, who_to_ask=who, latency_ms=int((time.perf_counter() - t0) * 1000))
    from canon.core import log_activity
    await log_activity(workspaces[-1], req.actor, "briefing", f"Briefing for {req.persona} since {since.date()}",
                       [o["id"] for _, _, _, o in top])
    return res
