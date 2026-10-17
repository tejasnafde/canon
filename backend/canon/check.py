"""F7 agent guard: an intended action against the record -> allow / warn / block."""
import asyncio
import os
import time

from pydantic import BaseModel

from canon import llm
from canon.ask import citations, context, retrieve
from canon.models import CheckRequest, CheckResult, Decision
from canon.reconcile import NO_LABELS, pick, unlabel
from canon.store import get_store, new_id, now

CHECK_THINK = int(os.environ.get("CANON_CHECK_THINK", "0"))  # thinking budget for the verdict
CHECK_MIN = 0.64  # below this no decision covers the intent: allow without asking Gemini
CHECK_SPREAD = 0.12  # judge only decisions within this cosine of the best match


class Judgement(BaseModel):
    decision: str  # the bracketed label only, e.g. D1
    applies: bool  # the decision governs this kind of action
    violates: bool  # the action does what the decision forbids, or skips what it requires
    exception_met: bool  # the action satisfies an exception the record documents
    note: str  # one sentence naming the decision and owner, true for the facts above


class Guard(BaseModel):
    judgements: list[Judgement]


def verdict_of(judged: list[tuple[dict, dict]], broken: set[str]) -> tuple[str, list[tuple[dict, dict]]]:
    """Decide in code from the model's per-decision judgements; (verdict, deciding (decision, judgement) pairs).

    block: an active decision is violated with no documented exception, and its premise still holds.
    warn: the only violated decisions have a changed premise, or the action relies on one that does.
    allow: everything else (no relevant decision, or a documented exception is met, here or in its own decision).
    """
    hit = [(d, j) for d, j in judged if j["applies"]]
    # An exception recorded as its own decision (e.g. the emergency rule) that the action satisfies excuses the rest.
    excused = any(j["exception_met"] and not j["violates"] for _, j in hit)
    bad = [(d, j) for d, j in hit if j["violates"] and not j["exception_met"] and not excused]
    if hard := [(d, j) for d, j in bad if d["id"] not in broken]:
        return "block", hard
    if shaky := bad or [(d, j) for d, j in hit if d["id"] in broken and not j["exception_met"]]:
        return "warn", shaky
    return "allow", hit


async def check(req: CheckRequest, workspaces: list[str]) -> CheckResult:
    t = time.perf_counter()
    (decs, _), open_alerts = await asyncio.gather(retrieve(req.intent, workspaces, k_dec=10, k_chunk=0),
                                                  get_store().query("alerts", workspaces, status="open"))
    # A decision flagged as contradicting the record (e.g. a rogue PR) is not authority for an action.
    rogue = {a["decision_id"] for a in open_alerts if a["kind"] == "contradiction"}
    live = [(d, s) for d, s in decs if d["status"] == "active" and s >= CHECK_MIN and d["id"] not in rogue]
    # Only decisions near the best match go to Gemini: the tail is off-topic, costs latency and invites stray flags.
    active = [d for d, s in live if s >= live[0][1] - CHECK_SPREAD][:5] if live else []
    verdict, why, deciding = "allow", "No decision in the record covers this action.", []
    if active:
        ctx, labels = context(active, [])
        ids = {d["id"]: l for l, d in labels.items()}
        broken = {a["decision_id"] for a in open_alerts if a["kind"] == "premise_changed"}
        flags = [f"[{ids[a['decision_id']]}] {a['kind']}: {a['explanation'][:200]}" for a in open_alerts
                 if a.get("decision_id") in ids and a["kind"] == "premise_changed"]
        prompt = (f"INTENDED ACTION by {req.actor}: {req.intent}\n\nACTIVE decisions:\n{ctx}\n\n"
                  + (("OPEN ALERTS on these decisions:\n" + "\n".join(flags) + "\n\n") if flags else "") +
                  "Judge every decision above, one judgement each, in the order given (decision = its label, e.g. D1). Read its conditions and exceptions "
                  "closely; an exception may be recorded as a separate decision.\n"
                  "- applies: true if the decision governs this kind of action (same system, time, customer or process)\n"
                  "- violates: true if the action does what the decision forbids or skips what it requires\n"
                  "- exception_met: true only if the action itself states the conditions of a documented exception to this "
                  "decision, whether written in it or recorded as another decision above (for example an emergency rule)\n"
                  "- note: one short sentence (at most 20 words) on how the action relates to the decision, naming its owner")
        r = await llm.generate_json(prompt, Guard, think=CHECK_THINK, temperature=0.0,
                                    system="You are Canon, a guard that checks actions against the company's decisions. " + NO_LABELS)
        js = r["judgements"]
        # The model often echoes a paraphrased statement instead of the label, so map by position when it judged
        # every decision in order; fall back to the label otherwise.
        judged = list(zip(active, js)) if len(js) == len(active) else \
            [(d, j) for d, j in ((pick(labels, j["decision"]), j) for j in js) if d]
        judged = list({d["id"]: (d, j) for d, j in judged}.values())  # one judgement per decision
        verdict, top = verdict_of(judged, broken)
        deciding = [d for d, _ in top]
        if top:
            why = " ".join(unlabel(j["note"], labels, d) for d, j in top[:2])
        if verdict == "warn" and any(d["id"] in broken for d in deciding):
            why = f"{why} The premise behind this decision has changed, so it needs review."
    from canon.core import log_activity
    ws = workspaces[-1]
    cites, _ = await asyncio.gather(
        citations([(q["source_id"], q["quote"], d["id"]) for d in deciding for q in d["quotes"][:1]]),
        log_activity(ws, req.actor, "check", f"Checked: {req.intent[:120]}", [d["id"] for d in deciding], verdict,
                     explanation=why))
    if verdict == "block" and req.actor.startswith("agent:"):
        await get_store().put("alerts", {
            "id": new_id("a"), "workspace": ws, "kind": "agent_violation", "severity": "medium",
            "decision_id": deciding[0]["id"], "source_id": None,
            "explanation": f"{req.actor} intended: {req.intent[:200]}. Blocked: {why}",
            "quotes": [{"source_id": c.source_id, "quote": c.quote} for c in cites[:1]],
            "status": "open", "resolution": None, "created_by": req.actor, "created_at": now()})
    return CheckResult(verdict=verdict, explanation=why, decisions=[Decision(**d) for d in deciding],
                       citations=cites, latency_ms=int((time.perf_counter() - t) * 1000))
