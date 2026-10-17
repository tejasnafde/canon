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

# One row per persona, the only place relevance is tuned:
#   label  how the prose addresses the reader ("For Sales, ...")
#   focus  what they care about, told to Gemini
#   teams  team names (matched against a person's team or role) that this persona belongs to or works with
#   words  vocabulary of their area (regex alternation, whole words, case-insensitive)
#   home   source kinds where their work lives
#   rule / high / cross  extra points for a standing rule, a high-severity alert, a cross-team dependency
PERSONAS: dict[str, dict] = {
    "engineer": dict(
        label="Engineering", focus="deploys, code, infrastructure, incidents and reliability",
        teams=("platform", "integrations", "quality", "engineering", "infrastructure", "sre"),
        words=r"deploy\w*|release|cron|schedul\w*|ci|pipeline|api|infra\w*|database|migration|schema|incident|"
              r"on-call|oncall|rollback|revert\w*|logs?|logging|parser|webhooks?|retr\w+|ingestion|service|backups?|"
              r"security|latency|workers?|batch\w*|config\w*|production|pr|code",
        home=("pr", "commit")),
    "pm": dict(
        label="Product", focus="roadmap, launches, scope, pricing and customer promises",
        teams=("product",),
        words=r"pric\w+|launch\w*|general availability|roadmap|customers?|contracts?|renewal|sla|preview|pilot|"
              r"marketing|sales|landing|promis\w+|subscriptions?|order forms?|proposals?|deadline|brochure|packaging|"
              r"headline|route lens|scope|beta|ga",
        home=("email",)),
    "design": dict(
        label="Design", focus="UX, UI, user research, accessibility and brand",
        teams=("design", "ux", "product"),
        words=r"design\w*|ux|ui|figma|mockups?|wireframes?|prototyp\w+|usability|accessib\w+|a11y|brand\w*|"
              r"layout|user research|research|labels?|icons?|colou?rs?|copy|screens?|flows?|dashboard|onboarding",
        home=("doc", "meeting")),
    "data": dict(
        label="Data", focus="metrics, pipelines, dashboards, data quality and retention",
        teams=("data", "analytics"),
        words=r"data|analytics|dashboards?|metrics?|warehouse|bigquery|pipelines?|etl|retention|schema|reports?|"
              r"forecast\w*|models?|experiments?|a/b|kpis?|events?|tracking|eta|accuracy",
        home=("pr", "doc")),
    "security": dict(
        label="Security", focus="access, secrets, vulnerabilities, audits and incidents",
        teams=("security",),
        words=r"security|access|sso|mfa|2fa|encrypt\w*|keys?|secrets?|tokens?|vulnerab\w+|cve|pentest|audit\w*|"
              r"soc ?2|iso|breach|incident|permissions?|least privilege|compliance|pii|gdpr|credentials?|phishing",
        home=("pr", "wiki"), high=6),
    "sales": dict(
        label="Sales", focus="pricing, discounts, deals, decks and what customers were promised",
        teams=("sales", "revenue", "account"),
        words=r"pric\w+|discount\w*|deals?|quotes?|prospects?|customers?|renewals?|contracts?|decks?|demos?|"
              r"order forms?|proposals?|quota|commission\w*|upsell|trials?|pilots?|rfp|promis\w+|route lens|usd",
        home=("email", "meeting")),
    "support": dict(
        label="Support", focus="tickets, SLAs, escalations, outages and customer-facing answers",
        teams=("customer", "support", "success"),
        words=r"support|tickets?|customers?|sla|escalat\w*|incident|outage|refund\w*|faq|help ?desk|status page|"
              r"response time|onboarding|churn|bugs?|macros?|tier|downtime|complain\w*",
        home=("email", "slack")),
    "marketing": dict(
        label="Marketing", focus="launches, campaigns, messaging, website and public claims",
        teams=("marketing", "brand", "growth"),
        words=r"launch\w*|campaigns?|brand\w*|messaging|landing|website|blog|webinars?|press|announce\w*|headlines?|"
              r"brochures?|seo|social|positioning|case stud\w+|newsletter|claims?|general availability|pric\w+",
        home=("doc", "email")),
    "finance": dict(
        label="Finance", focus="budget, spend, billing, revenue and pricing changes",
        teams=("finance", "accounting"),
        words=r"budget\w*|costs?|spend\w*|invoic\w+|billing|revenue|pric\w+|discount\w*|forecast\w*|payroll|"
              r"expens\w+|procurement|vendors?|arr|margin|payments?|refund\w*|tax|usd|cloud bill|savings",
        home=("email", "doc")),
    "operations": dict(
        label="Operations", focus="processes, vendors, dispatch, schedules and on-call",
        teams=("operations", "ops"),
        words=r"operations?|process\w*|vendors?|procurement|logistics|warehouse|dispatch\w*|carriers?|fleet|"
              r"shipping|schedul\w*|capacity|sla|on-call|oncall|tooling|runbooks?|maintenance|window|escalat\w*",
        home=("wiki", "meeting")),
    "people": dict(
        label="People (HR)", focus="hiring, the handbook, leave, review cycles and policies for staff",
        teams=("people", "hr", "talent", "recruiting"),
        words=r"hiring|hires?|recruit\w*|interview\w*|handbook|leave|pto|vacation|holidays?|review cycles?|"
              r"performance|promotions?|compensation|salar\w+|benefits|offboard\w*|onboard\w*|headcount|remote|"
              r"training|employees?|staff|policy",
        home=("wiki", "doc"), rule=6),
    "legal": dict(
        label="Legal", focus="contracts, DPAs, data residency, retention and compliance",
        teams=("legal", "compliance"),
        words=r"contracts?|dpa|data residency|residency|retention|gdpr|privacy|terms|liabilit\w+|indemn\w+|msa|"
              r"nda|compliance|licens\w+|subprocessors?|regulat\w+|consent|pii|deletion|clauses?|eu|region",
        home=("email", "doc"), rule=6),
    "leadership": dict(
        label="Leadership", focus="high-severity risks, cross-team dependencies, OKRs, budget and strategy",
        teams=("leadership", "executive", "exec", "ceo", "cto", "coo", "founder"),
        words=r"okrs?|budget\w*|strategy|roadmap|headcount|board|revenue|arr|hiring|launch\w*|pric\w+|churn|"
              r"risks?|targets?|quarter\w*|q[1-4]|investors?|customers?|contracts?|incident",
        home=("meeting",), high=10, cross=6),
    "new_hire": dict(
        label="a new hire", focus="the standing rules, processes and who decided what",
        teams=(),
        words=r"policy|process|handbook|onboarding|on-call|oncall|release\w*|deploy\w*|production|window|approval|"
              r"access|incident|security|review|standard|convention|wiki|faq",
        home=("wiki", "doc"), rule=10),
}
WHERE = {"pr": "a PR", "commit": "a commit", "email": "an email", "wiki": "the wiki", "doc": "a doc",
         "meeting": "a meeting", "slack": "Slack"}
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


def on_team(persona: str, person: dict | None) -> str | None:
    """The person's team when it is one this persona belongs to or works with (team or role text), else None."""
    if not person:
        return None
    hay = f"{person.get('team', '')} {person.get('role', '')}".lower()
    return person.get("team") if any(re.search(rf"\b{t}\b", hay) for t in PERSONAS[persona]["teams"]) else None


def owner_of(owner: str, people: list[dict]) -> dict | None:
    """Match a decision owner string to a person: full name first, then first name."""
    o = (owner or "").lower()
    return next((p for p in people if p["name"].lower() in o), None) or \
        next((p for p in people if p["name"].split()[0].lower() in o.split()), None)


def score(text: str, persona: str, kind: str, ts: datetime, today: datetime, *, source_kind: str | None = None,
          teams: set[str] = frozenset(), links: int = 0, changed: bool = False, severity: str | None = None,
          owner_team: str | None = None) -> tuple[int, list[str]]:
    """Next-best-action score with the human-readable reasons behind it. Deterministic.

    kind is "decision" or an alert kind. P = PERSONAS[persona]. Points, then clamped to 30..98:
      base by kind (a contradiction outranks a stale doc outranks a plain decision)  30-45
      persona vocabulary hits (distinct terms of P.words): 1 / 2 / 3+ -> +10 / +18 / +24; none -> -12
      evidence lives where the persona works (source kind in P.home)  +12
      the decision owner sits on one of P.teams  +12
      a standing rule ("no", "must", "only")  +P.rule (new hire 10, legal and people 6)
      a high-severity alert  +P.high (leadership 10, security 6)
      the decision changed an earlier one  +6
      other open alerts point at the same decision: +6 each, max +12
      deadline in 2 / 7 / 30 days  +15 / +10 / +5;  urgent words  +8
      cross-team dependency  +6, plus P.cross (leadership 6)
      age: last 7 days +8, last 30 days +4, over a year -6
    """
    P = PERSONAS[persona]
    pts, reasons = BASE.get(kind, 30), []
    if kind != "decision":
        reasons.append(f"open {kind.replace('_', ' ')} alert")
    hits = len({m.lower() for m in re.findall(rf"\b(?:{P['words']})\b", text, re.I)})
    if hits:
        pts += (0, 10, 18)[hits] if hits < 3 else 24
        reasons.append(f"relevant to {P['label']}")
    else:
        pts -= 12
    if source_kind in P["home"]:
        pts += 12
        reasons.append(f"evidence in {WHERE.get(source_kind, source_kind)}")
    if owner_team:
        pts += 12
        reasons.append(f"decided by {owner_team}")
    if P.get("rule") and RULE.search(text):
        pts += P["rule"]
        reasons.append("a standing rule")
    if P.get("high") and severity == "high":
        pts += P["high"]
        reasons.append("high severity")
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
        pts += 6 + P.get("cross", 0)
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
         today: datetime, teams: set[str], people: list[dict] = ()) -> list[tuple[int, list[str], str, dict]]:
    """Candidates (score, reasons, "decision"|"alert", doc), best first. Ties break on recency, then id."""
    dmap = {d["id"]: d for d in decs}
    team_of = {d["id"]: on_team(persona, owner_of(d["owner"], people)) for d in decs} if people else {}
    links: dict[str, int] = {}
    for a in alerts:
        for i in {a.get("decision_id"), a.get("related_decision_id")} - {None}:
            links[i] = links.get(i, 0) + 1
    cands = []
    for d in decs:
        if utc(d["ts"]) >= since and d["status"] == "active":
            src = kinds.get(d["quotes"][0]["source_id"]) if d["quotes"] else None
            s, r = score(f"{d['topic']} {d['statement']} {d['rationale']}", persona, "decision", d["ts"], today,
                         source_kind=src, teams=teams, links=links.get(d["id"], 0), changed=bool(d.get("supersedes")),
                         owner_team=team_of.get(d["id"]))
            cands.append((s, r, "decision", d))
    for a in alerts:  # open alerts are actionable whatever their age
        d = dmap.get(a.get("decision_id") or "")
        rel = dmap.get(a.get("related_decision_id") or "")
        text = " ".join(x for x in (a["explanation"], d and d["statement"], rel and rel["statement"],
                                    d and d["topic"]) if x)
        others = max(0, links.get(a.get("related_decision_id") or a.get("decision_id") or "", 0) - 1)
        s, r = score(text, persona, a["kind"], (d or a)["ts"] if d else a["created_at"], today,
                     source_kind=kinds.get(a.get("source_id") or ""), teams=teams, links=others,
                     severity=a.get("severity"), owner_team=team_of.get(d["id"]) if d else None,
                     changed=bool(rel and rel.get("supersedes")))  # breaks a rule that was itself a revision
        cands.append((s, r, "alert", a))
    cands.sort(key=lambda c: (c[0], utc(c[3].get("ts") or c[3]["created_at"]), c[3]["id"]), reverse=True)
    return cands


def who_to_ask(persona: str, people: list[dict], decs: list[dict]) -> list[Person]:
    """Up to 4 active people: team in the persona's teams, then a team or role match, then by decisions owned."""
    owned = lambda p: sum(1 for d in decs if p["name"].split()[0].lower() in d["owner"].lower())  # noqa: E731
    fit = lambda p: 0 if p.get("team", "").lower() in PERSONAS[persona]["teams"] else 1 if on_team(persona, p) else 2  # noqa: E731
    act = [p for p in people if p["status"] == "active"]
    return [Person(**p) for p in sorted(act, key=lambda p: (fit(p), -owned(p), p["name"]))[:4]]


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
    cands = rank(decs, alerts, kinds, req.persona, since, today, teams, people)
    top = cands[:8]
    who = who_to_ask(req.persona, people, decs)
    P = PERSONAS[req.persona]

    if not top:
        return Briefing(persona=req.persona, since=req.since, summary=f"Nothing new in the record since {since.date()}.",
                        highlights=[], actions=[], who_to_ask=who, latency_ms=int((time.perf_counter() - t0) * 1000))

    lines = []
    for i, (s, r, kind, o) in enumerate(top):
        body = o["statement"] if kind == "decision" else f"{o['kind']} alert: {o['explanation']}"
        lines.append(f"{i + 1}. [{kind}, score {s}] {body} (factors: {'; '.join(r)})")
    recent = sorted((d for d in decs if utc(d["ts"]) >= since), key=lambda d: d["ts"], reverse=True)[:15]
    prompt = (f"Write a catch-up briefing for {P['label']} covering {since.date()} to {today.date()}. "
              f"This reader cares about {P['focus']}; frame every line for them, not for engineers in general.\n"
              "DECISIONS in the period:\n" + "\n".join(f"- {utc(d['ts']).date()} [{d['status']}] {d['statement']}" for d in recent) +
              "\n\nRANKED ACTIONS (keep this order):\n" + "\n".join(lines) +
              "\n\nsummary: exactly two short, specific sentences, at most 35 words together, about the top-ranked "
              f"actions for this reader, and it starts with \"For {P['label']}, \". Name the concrete things: what changed, "
              "what it now blocks or makes stale, with the PR number, page title, customer or date when the facts give "
              "one. Example of the shape (for Engineering): \"For Engineering, two things matter: the Friday deploy ban "
              "now blocks PR #412, and the Release process wiki is stale.\" Never describe the briefing itself (no "
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
