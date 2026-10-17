"""F7 agent guard: an intended action against the record -> allow / warn / block."""
import asyncio
import os
import time
from typing import Literal

from pydantic import BaseModel

from canon import llm
from canon.ask import citations, context, retrieve
from canon.models import CheckRequest, CheckResult, Decision
from canon.reconcile import NO_LABELS, pick, unlabel
from canon.store import get_store, new_id, now

CHECK_THINK = int(os.environ.get("CANON_CHECK_THINK", "0"))  # thinking budget for the verdict
CHECK_MIN = 0.64  # below this no decision covers the intent: allow without asking Gemini


class Guard(BaseModel):
    verdict: Literal["allow", "warn", "block"]
    explanation: str
    deciding: list[str]  # labels


async def check(req: CheckRequest, workspaces: list[str]) -> CheckResult:
    t = time.perf_counter()
    (decs, _), open_alerts = await asyncio.gather(retrieve(req.intent, workspaces, k_dec=10, k_chunk=0),
                                                  get_store().query("alerts", workspaces, status="open"))
    # A decision flagged as contradicting the record (e.g. a rogue PR) is not authority for an action.
    rogue = {a["decision_id"] for a in open_alerts if a["kind"] == "contradiction"}
    active = [d for d, s in decs if d["status"] == "active" and s >= CHECK_MIN and d["id"] not in rogue][:6]
    verdict, why, deciding = "allow", "No decision in the record covers this action.", []
    if active:
        ctx, labels = context(active, [])
        ids = {d["id"]: l for l, d in labels.items()}
        flags = [f"[{ids[a['decision_id']]}] {a['kind']}: {a['explanation'][:200]}" for a in open_alerts
                 if a.get("decision_id") in ids and a["kind"] == "premise_changed"]
        prompt = (f"INTENDED ACTION by {req.actor}: {req.intent}\n\nACTIVE decisions:\n{ctx}\n\n"
                  + (("OPEN ALERTS on these decisions:\n" + "\n".join(flags) + "\n\n") if flags else "") +
                  "Read each decision's conditions and exceptions closely; an exception may be recorded as a "
                  "separate decision. Verdict:\n"
                  "- block: the action violates an active decision and meets none of its documented exceptions\n"
                  "- warn: the action does not violate any decision, but it keeps relying on a decision whose "
                  "premise has changed (see OPEN ALERTS), so a human must review it first\n"
                  "- allow: consistent with the record, including when it satisfies a documented exception, "
                  "or no decision is relevant\n"
                  "deciding = labels of the decisions behind the verdict ([] for allow when none is relevant). "
                  "explanation: 1 or 2 sentences naming the decision and owner.")
        r = await llm.generate_json(prompt, Guard, think=CHECK_THINK,
                                    system="You are Canon, a guard that checks actions against the company's decisions. " + NO_LABELS)
        deciding = [d for d in (pick(labels, x) for x in r["deciding"]) if d]
        verdict, why = r["verdict"], unlabel(r["explanation"], labels, deciding[0] if deciding else None)
        if verdict != "allow" and not deciding:
            deciding = active[:1]
        broken = {a["decision_id"] for a in open_alerts if a["kind"] == "premise_changed"}
        if verdict == "block" and all(d["id"] in broken for d in deciding):
            # A decision whose premise no longer holds cannot hard-block; a human reviews it first.
            verdict, why = "warn", f"{why} The premise behind this decision has changed, so it needs review."
    cites = await citations([(q["source_id"], q["quote"], d["id"]) for d in deciding for q in d["quotes"][:1]])
    ws = workspaces[-1]
    if verdict == "block" and req.actor.startswith("agent:"):
        await get_store().put("alerts", {
            "id": new_id("a"), "workspace": ws, "kind": "agent_violation", "severity": "medium",
            "decision_id": deciding[0]["id"], "source_id": None,
            "explanation": f"{req.actor} intended: {req.intent[:200]}. Blocked: {why}",
            "quotes": [{"source_id": c.source_id, "quote": c.quote} for c in cites[:1]],
            "status": "open", "resolution": None, "created_by": req.actor, "created_at": now()})
    from canon.core import log_activity
    await log_activity(ws, req.actor, "check", f"Checked: {req.intent[:120]}", [d["id"] for d in deciding], verdict,
                       explanation=why)
    return CheckResult(verdict=verdict, explanation=why, decisions=[Decision(**d) for d in deciding],
                       citations=cites, latency_ms=int((time.perf_counter() - t) * 1000))
