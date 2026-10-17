"""F5 ask why: cited answer + decision timeline, refuses when the record has no answer.
Also the retrieval and citation helpers that check/expert/briefing share.
"""
import asyncio
import time

from pydantic import BaseModel

from canon import llm
from canon.models import AskRequest, AskResult, Citation, Decision, TimelineEntry
from canon.reconcile import norm, verified
from canon.store import get_store, utc

ASK_MIN = 0.66  # query-to-record cosine below this means "I do not know" without calling Gemini
REFUSAL = "I do not know. The record has no decision or document that answers this."


async def retrieve(text: str, scope: list[str], k_dec: int = 8, k_chunk: int = 6):
    [q] = await llm.embed([text], "RETRIEVAL_QUERY")
    st = get_store()
    decs, chunks = await asyncio.gather(st.nearest("decisions", scope, q, k_dec),
                                        st.nearest("chunks", scope, q, k_chunk) if k_chunk else asyncio.sleep(0, []))
    return decs, chunks


async def citations(pairs: list[tuple[str, str, str | None]]) -> list[Citation]:
    """pairs: (source_id, quote, decision_id). Looks up source metadata, keeps order, dedupes."""
    srcs = await get_store().get_many("sources", [p[0] for p in pairs])
    out, seen = [], set()
    for sid, quote, did in pairs:
        s = srcs.get(sid)
        if not s or (sid, quote) in seen:
            continue
        seen.add((sid, quote))
        out.append(Citation(source_id=sid, decision_id=did, quote=quote, title=s["title"], kind=s["kind"],
                            ts=s["ts"], url=s.get("url")))
    return out


async def timeline(decs: list[dict], scope: list[str]) -> list[TimelineEntry]:
    """Walk supersedes / superseded_by chains from the given decisions, oldest first."""
    st = get_store()
    seen = {d["id"]: d for d in decs}
    frontier = {i for d in decs for i in d.get("supersedes", []) + [d.get("superseded_by")] if i} - seen.keys()
    for _ in range(5):
        if not frontier:
            break
        got = {k: v for k, v in (await st.get_many("decisions", list(frontier))).items() if v["workspace"] in scope}
        seen.update(got)
        frontier = {i for d in got.values() for i in d.get("supersedes", []) + [d.get("superseded_by")] if i} - seen.keys()
    out = [TimelineEntry(ts=d["ts"], decision_id=d["id"], statement=d["statement"], status=d["status"],
                         relation="update" if d.get("supersedes") else "new") for d in seen.values()]
    return sorted(out, key=lambda e: utc(e.ts))


class Cited(BaseModel):
    ref: str  # D1 / C1
    quote: str


class Answer(BaseModel):
    answerable: bool
    answer: str
    cited: list[Cited]


def context(decs: list[dict], chunks: list[dict]) -> tuple[str, dict[str, dict]]:
    labels: dict[str, dict] = {}
    lines = []
    for i, d in enumerate(decs):
        labels[f"D{i + 1}"] = d
        q = " | ".join(x["quote"] for x in d["quotes"][:2])
        lines.append(f"[D{i + 1}] {utc(d['ts']).date()} {d['status']} owner={d['owner']}: {d['statement']} "
                     f"Why: {d['rationale']} Quote: \"{q}\"")
    for i, c in enumerate(chunks):
        labels[f"C{i + 1}"] = c
        lines.append(f"[C{i + 1}] {c.get('kind', '')} \"{c.get('title', '')}\" {utc(c['ts']).date()}: {c['text'][:900]}")
    return "\n".join(lines), labels


async def map_citations(cited: list[dict], labels: dict[str, dict]) -> list[Citation]:
    pairs = []
    for c in cited:
        x = labels.get(c["ref"].strip("[] "))
        if not x:
            continue
        if "statement" in x:  # decision: cite the verified quote that best matches
            q = next((q for q in x["quotes"] if norm(c["quote"]) in q["quote"]), x["quotes"][0])
            pairs.append((q["source_id"], q["quote"], x["id"]))
        else:
            q = norm(c["quote"]) if verified(c["quote"], x["text"]) else norm(x["text"][:200])
            pairs.append((x["source_id"], q, None))
    return await citations(pairs)


async def ask(req: AskRequest, workspaces: list[str]) -> AskResult:
    t = time.perf_counter()
    decs, chunks = await retrieve(req.question, workspaces)
    top = max([s for _, s in decs + chunks], default=0.0)
    res = AskResult(answer=REFUSAL, citations=[], refused=True, latency_ms=0)
    if top >= ASK_MIN:
        ctx, labels = context([d for d, s in decs if s >= ASK_MIN - 0.06],
                              [c for c, s in chunks if s >= ASK_MIN - 0.06])
        prompt = (f"QUESTION: {req.question}\n\nRECORD:\n{ctx}\n\n"
                  "Answer the question in 2 to 4 sentences using ONLY the record. Prefer active decisions; when a "
                  "decision was superseded, say what changed and when. Cite every claim with refs (D1, C2) and a "
                  "short quote copied from that ref. If the record does not answer the question, set answerable "
                  "false and answer \"\".")
        r = await llm.generate_json(prompt, Answer, system="You are Canon, the company's decision record. Never guess.")
        cites = await map_citations(r["cited"], labels) if r["answerable"] else []
        if r["answerable"] and cites:
            cited_decs = [labels[c["ref"].strip("[] ")] for c in r["cited"]
                          if c["ref"].strip("[] ") in labels and "statement" in labels[c["ref"].strip("[] ")]]
            res = AskResult(answer=r["answer"], citations=cites, timeline=await timeline(cited_decs, workspaces),
                            refused=False, latency_ms=0)
    res.latency_ms = int((time.perf_counter() - t) * 1000)
    from canon.core import log_activity
    await log_activity(workspaces[-1], req.actor, "ask", f"Asked: {req.question[:120]}" + (" (refused)" if res.refused else ""),
                       [c.decision_id or c.source_id for c in res.citations])
    return res


async def search_decisions(query: str, workspaces: list[str], limit: int = 5) -> list[Decision]:
    decs, _ = await retrieve(query, workspaces, k_dec=limit * 3, k_chunk=0)
    return [Decision(**d) for d, s in decs if d["status"] == "active" and s >= ASK_MIN - 0.08][:limit]
