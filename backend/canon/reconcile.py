"""F3 reconciliation, F4 stale docs, F13 premise watch. Gemini judges, code decides what to write."""
import asyncio
import re

from pydantic import BaseModel

from canon import llm
from canon.store import get_store, utc

RELATED_MIN = 0.72   # decision-to-decision cosine below this is "new" without asking Gemini
DOC_MIN = 0.70       # decision-to-wiki-chunk cosine for the stale scan
PREMISE_MIN = 0.68   # new-info-to-decision cosine for the premise scan


def norm(s: str) -> str:
    return " ".join(s.split())


def verified(quote: str, text: str) -> bool:
    q = norm(quote)
    return bool(q) and q in norm(text)


NO_LABELS = ("Never write internal labels such as D1, C2 or W1 in prose; name a decision by what it says "
             "and its owner, and a document by its title.")
_LABEL = re.compile(r"(?i:\bthe\s+)?(?i:\b(?:existing|active|earlier|older|new|newer|current)\s+)?"
                    r"(?i:\bdecision\s+)?\[?\b([DCW]\d{1,2})\b\]?")


def _short(s: str, n: int = 80) -> str:
    s = norm(s).rstrip(".")
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "..."


def unlabel(text: str, labels: dict[str, dict] | None = None, fallback: dict | None = None) -> str:
    """Replace prompt labels (D1, [C2]) the model leaked into prose with what they point at.

    A decision becomes `the decision "<statement>" (<owner>, <date>)`, a chunk its quoted title. An unknown
    D-label falls back to `fallback` (the decision an alert is about) or "an earlier decision".
    """
    labels = labels or {}

    def sub(m: re.Match) -> str:
        x = labels.get(m.group(1).upper())
        if x is None and m.group(1)[0] in "Dd":
            x = fallback
            if x is None:
                return "an earlier decision"
        if x is None:
            return m.group(0)
        if "statement" in x:
            return f"the decision \"{_short(x['statement'])}\" ({x.get('owner', '')}, {utc(x['ts']).date()})"
        return f"\"{x.get('title') or 'a document'}\""

    return _LABEL.sub(sub, text or "")


def pick(labels: dict[str, dict], ref: str) -> dict | None:
    """Resolve a model's reference: "D1", "[D1]", "D1: ...", or the referenced statement echoed back."""
    m = re.match(r"\W*([A-Z]\d+)\b", ref or "")
    if m and m.group(1) in labels:
        return labels[m.group(1)]
    r = norm(ref).lower()
    for x in labels.values():
        t = norm(x.get("statement") or x.get("text") or "").lower()
        if r and t and (t.startswith(r[:60]) or r.startswith(t[:60])):
            return x
    return None


class Assessment(BaseModel):
    decision: str            # label like "D2"
    restates: bool           # says the same thing, no change in substance
    conflicts: bool          # NEW and this decision cannot both hold, or acting on NEW breaks it
    explicit_supersede: bool  # NEW deliberately revises or replaces THIS decision, not just acts differently
    why: str


class Judgement(BaseModel):
    assessments: list[Assessment]
    authority_evidence: str  # word-for-word quote showing approval or a decision outcome, or ""


class Broken(BaseModel):
    decision: str  # label
    assumption: str
    evidence_quote: str
    explanation: str


class PremiseCheck(BaseModel):
    broken: list[Broken]


class StaleHit(BaseModel):
    excerpt: str  # label like "W1"
    quote: str
    explanation: str


class StaleCheck(BaseModel):
    stale: list[StaleHit]


SYSTEM = ("You are Canon, a strict auditor of a company's decision record. Judge only from the text given. "
          "Be conservative. " + NO_LABELS)


def _dline(label: str, d: dict) -> str:
    return f"[{label}] ({utc(d['ts']).date()}, owner {d['owner']}, status {d['status']}) {d['statement']}"


async def candidates(emb: list[float], scope: list[str], k: int = 5, min_score: float = RELATED_MIN,
                     active_only: bool = True) -> list[tuple[dict, float]]:
    hits = await get_store().nearest("decisions", scope, emb, k * 2)
    return [(d, s) for d, s in hits if s >= min_score and (not active_only or d["status"] == "active")][:k]


def decide(assessments: list[dict], labels: dict[str, dict], authorised,
           violators: set[str] = frozenset()) -> tuple[str, dict | None, dict | None]:
    """Relation from the structured judgement, in code. Returns (relation, related decision, its assessment).

    A conflict outranks a restatement: a paste that repeats an earlier violation still breaks the rule.
    A conflict is an update only when the text deliberately revises the decision AND carries authority
    (a verified approval quote, or the old decision's own owner); anything else that conflicts is a contradiction.
    Only a standing rule can be contradicted: two one-off actions that disagree (who covers a pager, where lunch
    is) are coordination, not drift. A decision already flagged as contradicting the record (`violators`) is not
    a conflict target either: that breach is already reported, and disagreeing with it restates the rule.
    """
    seen = [(a, pick(labels, a["decision"])) for a in assessments]
    seen = [(a, d) for a, d in seen if d is not None]
    for a, d in seen:
        if a["conflicts"] and d.get("kind", "rule") == "rule" and d["id"] not in violators:
            return ("update" if a["explicit_supersede"] and authorised(d) else "contradiction"), d, a
    for a, d in seen:
        if a["restates"]:
            return "same", d, a
    for a, d in seen:
        if a["explicit_supersede"] and authorised(d):
            return "update", d, a  # narrows or extends it without a conflict
    return "new", None, None


JUDGE = """NEW decision ({date}, from {kind} "{title}" by {author}): {statement}
Rationale: {rationale}

SOURCE it came from:
{text}

EXISTING decisions:
{existing}

Assess the NEW decision against EVERY existing decision, one entry each, with these independent flags:
- restates: it says the same thing as the existing one, no change in substance.
- conflicts: the NEW decision and the existing one cannot both be followed, or doing what the NEW one says
  breaks the existing rule. An operational action, schedule, job, PR, promise or plan that violates an active
  rule conflicts with it, even if it is phrased as routine work and never mentions the rule.
  Both must be about the same thing (the same system, policy, product, event or resource); two different
  meetings, rooms, lunches or tickets do not conflict just because they look alike. A rule about HOW a process
  runs does not conflict with a rule that pauses or limits WHETHER it runs, and a rule for one path, team or
  customer group does not conflict with a different rule for another (the SOURCE may say they are separate).
- explicit_supersede: the SOURCE deliberately changes THIS existing decision: it says to replace, revise, lift,
  move or narrow it, or it is the outcome of a review, meeting or approval that sets new terms on its subject.
  Simply doing something different, or following an older document, is NOT explicit_supersede.
- why: one sentence on this pair.
An existing decision can be restated and conflicted by the same text only if it is internally inconsistent;
judge each pair on its own.
authority_evidence: a short span COPIED WORD FOR WORD from the SOURCE that shows an approval or a decision
outcome (e.g. "I approve this change", "Decision from the review"), or "" if there is none."""


async def judge(dec: dict, cands: list[tuple[dict, float]], src: dict,
                violators: set[str] = frozenset()) -> tuple[str, dict | None, str]:
    """Returns (relation, related decision dict or None, explanation)."""
    if not cands:
        return "new", None, "No related decision in the record."
    labels = {f"D{i + 1}": d for i, (d, _) in enumerate(cands)}
    prompt = JUDGE.format(date=utc(dec["ts"]).date(), kind=src["kind"], title=src["title"], author=src["author"],
                          statement=dec["statement"], rationale=dec["rationale"],
                          text=llm.source_block(src["text"][:4000]),
                          existing="\n".join(_dline(l, d) for l, d in labels.items()))
    r = await llm.generate_json(prompt, Judgement, system=SYSTEM)
    approved = verified(r["authority_evidence"], src["text"]) and len(r["authority_evidence"].split()) >= 2
    people = {norm(src["author"]).lower(), norm(dec["owner"]).lower()}
    # A meeting record is a decision forum: the group setting new terms there is the authority.
    authorised = lambda d: approved or src["kind"] == "meeting" or norm(d["owner"]).lower() in people  # noqa: E731
    rel, old, a = decide(r["assessments"], labels, authorised, violators)
    if a is None:
        return "new", None, "No existing decision covers the same subject."
    return rel, old, unlabel(a["why"], labels, old)


async def premise_check(source_text: str, items: list[dict], emb_list: list[list[float]],
                        scope: list[str]) -> list[tuple[dict, Broken]]:
    """F13: does new info break an assumption behind an active decision?"""
    found = await asyncio.gather(*(candidates(e, scope, 6, PREMISE_MIN) for e in emb_list))
    pool: dict[str, dict] = {}
    for hits in found:
        for d, _ in hits:
            pool[d["id"]] = d
    if not pool:
        return []
    labels = {f"D{i + 1}": d for i, d in enumerate(list(pool.values())[:10])}
    prompt = (
        "NEW information:\n" + "\n".join(f"- {i['statement']}" for i in items) +
        "\n\nACTIVE decisions:\n" +
        "\n".join(f"[{l}] {d['statement']} Why: {d['rationale']}\n  stated assumptions: "
                  + ("; ".join(d.get("assumptions") or []) or "none") for l, d in labels.items()) +
        "\n\nA decision rests on premises: conditions in its own wording (\"while X stays below N\"), stated "
        "assumptions, and implicit facts that made it sensible (e.g. a 24 hour retry assumes requests stay "
        "valid for 24 hours; a price assumes a cost). For each decision ask: does the NEW information make one "
        "of its premises false (a number crossed a stated limit, a cost or duration changed, a vendor behaves "
        "differently)? List those. Do not list a decision just because it is on the same topic. An action, PR, "
        "plan or copy that disobeys a decision does not break its premise (that is a violation, reported "
        "elsewhere); only facts about the world do. "
        "evidence_quote must be copied word for word from the SOURCE below. Return an empty list if none.\n\n"
        f"SOURCE:\n{source_text[:6000]}"
    )
    r = await llm.generate_json(prompt, PremiseCheck, system=SYSTEM)
    # Text the decision's own sources already contain (its rationale, repeated in a later thread) is not new
    # information, so it cannot break a premise.
    own = await get_store().get_many("sources", [q["source_id"] for d in labels.values() for q in d["quotes"]])
    out = []
    for b in r["broken"]:
        d = pick(labels, b["decision"])
        if (d and d["id"] not in {x["id"] for x, _ in out} and len(b["assumption"].split()) >= 3
                and verified(b["evidence_quote"], source_text)
                and not any(verified(b["evidence_quote"], own[q["source_id"]]["text"])
                            for q in d["quotes"] if q["source_id"] in own)):
            out.append((d, Broken(**{**b, "explanation": unlabel(b["explanation"], labels, d)})))
    return out


async def stale_check(dec: dict, emb: list[float], scope: list[str], source_id: str) -> list[tuple[dict, StaleHit]]:
    """F4: wiki/doc chunks, older than the decision, that the decision makes outdated."""
    hits = await get_store().nearest("chunks", scope, emb, 10)
    chunks = [c for c, s in hits if s >= DOC_MIN and c.get("kind") in ("wiki", "doc")
              and c["source_id"] != source_id and utc(c["ts"]) <= utc(dec["ts"])][:4]
    if not chunks:
        return []
    labels = {f"W{i + 1}": c for i, c in enumerate(chunks)}
    prompt = (
        f"DECISION ({utc(dec['ts']).date()}): {dec['statement']}\n\n"
        "Older documentation excerpts:\n" +
        "\n\n".join(f"[{l}] {c.get('title', '')}\n{c['text']}" for l, c in labels.items()) +
        "\n\nWhich excerpts state something this decision makes wrong or outdated? For each, copy the outdated "
        "sentence word for word as quote. Return an empty list if none are outdated."
    )
    r = await llm.generate_json(prompt, StaleCheck, system=SYSTEM)
    out = []
    for h in r["stale"]:
        c = pick(labels, h["excerpt"])
        if c and verified(h["quote"], c["text"]):
            out.append((c, StaleHit(**{**h, "explanation": unlabel(h["explanation"], labels)})))
    return out
