"""F3 reconciliation, F4 stale docs, F13 premise watch. Gemini judges, code decides what to write."""
import asyncio
import re
from typing import Literal

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


class Judgement(BaseModel):
    relation: Literal["new", "same", "update", "contradiction"]
    related: str  # label like "D2", or "" for new
    explanation: str


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


SYSTEM = "You are Canon, a strict auditor of a company's decision record. Judge only from the text given. Be conservative."


def _dline(label: str, d: dict) -> str:
    return f"[{label}] ({utc(d['ts']).date()}, owner {d['owner']}, status {d['status']}) {d['statement']}"


async def candidates(emb: list[float], scope: list[str], k: int = 5, min_score: float = RELATED_MIN,
                     active_only: bool = True) -> list[tuple[dict, float]]:
    hits = await get_store().nearest("decisions", scope, emb, k * 2)
    return [(d, s) for d, s in hits if s >= min_score and (not active_only or d["status"] == "active")][:k]


async def judge(dec: dict, cands: list[tuple[dict, float]], src: dict) -> tuple[str, dict | None, str]:
    """Returns (relation, related decision dict or None, explanation)."""
    if not cands:
        return "new", None, "No related decision in the record."
    labels = {f"D{i + 1}": d for i, (d, _) in enumerate(cands)}
    prompt = (
        f"NEW decision ({utc(dec['ts']).date()}, from {src['kind']} \"{src['title']}\" by {src['author']}): "
        f"{dec['statement']}\nRationale: {dec['rationale']}\n\n"
        "EXISTING decisions:\n" + "\n".join(_dline(l, d) for l, d in labels.items()) +
        "\n\nClassify the NEW decision against the closest EXISTING one:\n"
        "- same: restates it, no change in substance\n"
        "- update: an intentional change to it by people with the authority to change it (a review, meeting, "
        "approval or announcement that revises, replaces, narrows or extends it); newer intent wins\n"
        "- contradiction: conflicts with it but is NOT an authorised change: an implementation, promise, email, "
        "doc or plan that ignores or breaks the existing decision\n"
        "- new: a different subject; none of them is about the same thing\n"
        "Set related to the label (e.g. D1), or \"\" for new. One sentence of explanation."
    )
    r = await llm.generate_json(prompt, Judgement, system=SYSTEM)
    rel = pick(labels, r["related"])
    if r["relation"] != "new" and rel is None:
        return "new", None, r["explanation"]
    return r["relation"], (rel if r["relation"] != "new" else None), r["explanation"]


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
        "differently)? List those. Do not list a decision just because it is on the same topic. "
        "evidence_quote must be copied word for word from the SOURCE below. Return an empty list if none.\n\n"
        f"SOURCE:\n{source_text[:6000]}"
    )
    r = await llm.generate_json(prompt, PremiseCheck, system=SYSTEM)
    out = []
    for b in r["broken"]:
        d = pick(labels, b["decision"])
        if d and verified(b["evidence_quote"], source_text):
            out.append((d, Broken(**b)))
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
            out.append((c, StaleHit(**h)))
    return out
