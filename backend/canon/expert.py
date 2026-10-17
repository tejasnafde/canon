"""F15 ask the departed expert: answer in their voice, only from their recorded decisions and quotes."""
import time

from canon import llm
from canon.ask import ASK_MIN, Answer, context, map_citations, retrieve
from canon.models import AskResult, ExpertRequest
from canon.store import get_store


async def expert(req: ExpertRequest, workspaces: list[str]) -> AskResult:
    t = time.perf_counter()
    person = await get_store().get("people", req.person_id)
    if not person or person["workspace"] not in workspaces:
        raise KeyError(req.person_id)
    name = person["name"]
    decs, chunks = await retrieve(f"{name}: {req.question}", workspaces, k_dec=30, k_chunk=20)
    first = name.split()[0].lower()
    mine = [d for d, s in decs if first in d["owner"].lower() and s >= ASK_MIN - 0.06][:6]
    srcs = await get_store().get_many("sources", [c["source_id"] for c, _ in chunks])
    said = [c for c, s in chunks if s >= ASK_MIN - 0.06
            and first in srcs.get(c["source_id"], {}).get("author", "").lower()][:4]
    res = AskResult(answer=f"I do not know. {name} left no recorded decision or message about this.",
                    citations=[], refused=True, latency_ms=0)
    if mine or said:
        ctx, labels = context(mine, said)
        prompt = (f"You are answering as {name} ({person['role']}, {person['team']}), who has left the company. "
                  f"QUESTION: {req.question}\n\nTHEIR RECORD:\n{ctx}\n\n"
                  f"Answer in the first person as {name}, in 2 to 4 sentences, using ONLY their record. Cite refs (D1, "
                  "C1) with a short quote copied from each. If their record does not answer it, set answerable false.")
        r = await llm.generate_json(prompt, Answer, system="Speak only from the given record. Never invent opinions.")
        cites = await map_citations(r["cited"], labels) if r["answerable"] else []
        if r["answerable"] and cites:
            res = AskResult(answer=r["answer"], citations=cites, refused=False, latency_ms=0)
    res.latency_ms = int((time.perf_counter() - t) * 1000)
    from canon.core import log_activity
    await log_activity(workspaces[-1], req.actor, "expert", f"Asked {name}: {req.question[:100]}",
                       [c.decision_id or c.source_id for c in res.citations])
    return res
