"""F6 catch me up and F12 onboarding. Scores are computed in code; Gemini only writes the prose."""
import asyncio
import re
import time
from datetime import datetime

from pydantic import BaseModel

from canon import llm
from canon.ask import citations
from canon.models import Action, Briefing, BriefingRequest, Person
from canon.store import get_store, now, utc

URGENT = re.compile(r"\b(urgent|asap|blocker|blocking|incident|outage|security|p0|sev1|critical|"
                    r"rollback|revert|breach|escalat\w*|churn)\b", re.I)
DEPEND = re.compile(r"\b(blocks|blocked by|depends on|dependency|handoff|hand off|waiting on|cross-team)\b", re.I)
PERSONA = {
    "engineer": r"deploy|release|api|code|infra|database|db|migration|pr\b|ci\b|test|incident|on-call|oncall|"
                r"service|latency|schema|kubernetes|backend|frontend|security",
    "pm": r"roadmap|pricing|price|customer|launch|scope|deadline|priority|feature|contract|sla|revenue|"
          r"beta|ga\b|marketing|sales|q[1-4]",
    "new_hire": r"policy|process|always|never|rule|convention|onboarding|how we|standard|default|must|"
                r"handbook|on-call|oncall|review",
}
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


def score(text: str, persona: str, ts: datetime, today: datetime, teams: set[str],
          alert_severity: str | None, open_alerts: int) -> tuple[int, list[str]]:
    """Next-best-action score 0-100 with the human-readable reasons behind it."""
    pts, reasons = 10, []
    dd = deadline_days(text, ts, today)
    if dd is not None and dd <= 30:
        p = 30 if dd <= 2 else 20 if dd <= 7 else 10
        pts += p
        reasons.append(f"deadline in {max(dd, 0)} days" if dd > 0 else "deadline today")
    if m := URGENT.search(text):
        pts += 15
        reasons.append(f"urgent: \"{m.group(0).lower()}\"")
    mentioned = {t for t in teams if re.search(rf"\b{re.escape(t)}\b", text, re.I)}
    if DEPEND.search(text) or len(mentioned) >= 2:
        pts += 15
        reasons.append("cross-team dependency" + (f" ({', '.join(sorted(mentioned))})" if mentioned else ""))
    hits = len(set(m.lower() for m in re.findall(PERSONA[persona], text, re.I)))
    if hits:
        pts += min(20, 8 * hits)
        reasons.append(f"relevant to {persona.replace('_', ' ')}")
    if alert_severity:
        pts += {"high": 25, "medium": 15, "low": 5}[alert_severity]
        reasons.append(f"open {alert_severity} alert")
    elif open_alerts:
        pts += 15
        reasons.append(f"{open_alerts} open alert(s) on this decision")
    age = (today - utc(ts)).days
    if age <= 7:
        pts += 10
        reasons.append("from the last 7 days")
    return max(0, min(100, pts)), reasons


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
    teams = {p["team"] for p in people if p.get("team")}
    active_people = {p["name"].lower() for p in people if p["status"] == "active"}
    by_dec: dict[str, list[dict]] = {}
    for a in alerts:
        by_dec.setdefault(a.get("decision_id") or "", []).append(a)
    dmap = {d["id"]: d for d in decs}

    cands = []  # (score, reasons, kind, obj)
    for d in decs:
        if utc(d["ts"]) >= since and d["status"] == "active":
            s, r = score(f"{d['topic']} {d['statement']} {d['rationale']}", req.persona, d["ts"], today, teams,
                         None, len(by_dec.get(d["id"], [])))
            cands.append((s, r, "decision", d))
    for a in alerts:  # open alerts are actionable whatever their age
        d = dmap.get(a.get("decision_id") or "")
        text = f"{a['kind']} {a['explanation']} {d['statement'] if d else ''}"
        s, r = score(text, req.persona, d["ts"] if d else a["created_at"], today, teams, a["severity"], 0)
        cands.append((s, r, "alert", a))
    cands.sort(key=lambda c: c[0], reverse=True)
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
              f"\n\nsummary: 2 or 3 sentences. highlights: 3 to 5 short bullets. titles and whys: exactly {len(top)} "
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
