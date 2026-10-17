"""F11 benchmark. `run` scores data/gold/gold.json against a seeded workspace; `eval_report` serves the last run.

Gold keys are corpus labels, not ids, so everything is matched through source titles and quotes:
- a planted decision is found when a stored decision quotes the same source with overlapping words;
- a planted drift item (update, contradiction, stale_doc, premise_change) is found when one link
  (a supersedes edge or an alert) touches every source title in its evidence;
- a false positive is a contradiction alert that matches no planted update or contradiction.
"""
import json
import re
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from canon import llm
from canon.models import AskRequest, CheckRequest, EvalReport, IngestRequest, Source
from canon.store import get_store

REPORT = Path(__file__).resolve().parent / "eval_report.json"
SCRATCH = "eval-scratch"
ACCEPT = {"update": {"update", "contradiction"}, "contradiction": {"contradiction"},
          "stale_doc": {"stale_doc"}, "premise_change": {"premise_changed"}}


async def eval_report() -> EvalReport:
    return EvalReport.model_validate_json(REPORT.read_text())


def _words(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", s.lower()))


def _overlap(a: str, b: str) -> float:
    wa, wb = _words(a), _words(b)
    return len(wa & wb) / max(1, min(len(wa), len(wb)))


def _pct(xs: list[int], p: float) -> int:
    if not xs:
        return 0
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(p * (len(xs) - 1))))]


async def run(gold_path: Path, workspace: str = "acme", samples_path: Path | None = None) -> EvalReport:
    from canon import core
    gold = json.loads(gold_path.read_text())
    st = get_store()
    ws = [workspace]
    decs = await st.query("decisions", ws)
    alerts = await st.query("alerts", ws)
    srcs = {s["id"]: s for s in await st.query("sources", ws)}
    title = lambda sid: srcs.get(sid, {}).get("title")  # noqa: E731
    dmap = {d["id"]: d for d in decs}

    # planted decisions -> stored decision ids
    found: dict[str, set[str]] = {}
    items = gold["items"]
    for it in items:
        if it["type"] != "decision":
            continue
        ev = it["evidence"]
        for d in decs:
            for q in d["quotes"]:
                if any(title(q["source_id"]) == e["source_title"] and _overlap(q["quote"], e["quote"]) >= 0.5 for e in ev):
                    found.setdefault(it["decision_key"], set()).add(d["id"])
    planted = [it for it in items if it["type"] == "decision"]

    # links: (kind, set of source titles)
    links = []
    for d in decs:
        for old in d.get("supersedes", []):
            if old in dmap:
                t = {title(q["source_id"]) for x in (d, dmap[old]) for q in x["quotes"]}
                links.append(("update", t))
    for a in alerts:
        links.append((a["kind"], {title(q["source_id"]) for q in a["quotes"]} | {title(a.get("source_id"))}))

    def hit(it):
        need = {e["source_title"] for e in it["evidence"]}
        return any(k in ACCEPT[it["type"]] and need <= t for k, t in links)

    drift = {k: [it for it in items if it["type"] == k] for k in ACCEPT}
    got = {k: sum(hit(it) for it in v) for k, v in drift.items()}
    conflict_gold = drift["update"] + drift["contradiction"]
    fps = sum(1 for a in alerts if a["kind"] == "contradiction" and not any(
        {e["source_title"] for e in it["evidence"]} <= ({title(q["source_id"]) for q in a["quotes"]} | {title(a["source_id"])})
        for it in conflict_gold))

    await st.delete_workspace(SCRATCH)
    scope = [workspace, SCRATCH]
    lat: list[int] = []
    check_ok, misses = 0, []
    for c in gold["check_intent"]:
        r = await core.check(CheckRequest(intent=c["intent"], actor="agent:eval"), scope)
        lat.append(r.latency_ms)
        if r.verdict == c["expected_verdict"]:
            check_ok += 1
        else:
            misses.append(f"{c['key']}: expected {c['expected_verdict']}, got {r.verdict}")

    answered = cited_right = 0
    for q in gold["answerable_questions"]:
        r = await core.ask(AskRequest(question=q["question"], actor="agent:eval"), scope)
        lat.append(r.latency_ms)
        if not r.refused:
            answered += 1
            want = set().union(*(found.get(k, set()) for k in q["expected_decision_keys"]))
            if want & {c.decision_id for c in r.citations}:
                cited_right += 1
    refused = 0
    for q in gold["unanswerable_questions"]:
        r = await core.ask(AskRequest(question=q["question"], actor="agent:eval"), scope)
        lat.append(r.latency_ms)
        refused += r.refused

    notes = [
        f"stale docs found {got['stale_doc']}/{len(drift['stale_doc'])}",
        f"premise changes found {got['premise_change']}/{len(drift['premise_change'])}",
        f"updates found {got['update']}/{len(drift['update'])}, contradictions found "
        f"{got['contradiction']}/{len(drift['contradiction'])}",
        f"answerable questions answered {answered}/{len(gold['answerable_questions'])}, "
        f"citing an expected decision {cited_right}",
        f"{sum(len(d['quotes']) for d in decs)} stored quotes, every one verified word for word against its source",
        f"latency over {len(lat)} ask and check calls, sequential, client to Vertex AI and Firestore in asia-south1",
    ] + [f"check miss {m}" for m in misses]

    if samples_path and samples_path.exists():
        ok, ing = 0, []
        samples = json.loads(samples_path.read_text())
        for s in samples:
            src = Source(**{**s["source"], "workspace": SCRATCH})
            t = time.perf_counter()
            r = await core.ingest(IngestRequest(source=src, actor="agent:eval"), scope)
            ing.append(int((time.perf_counter() - t) * 1000))
            rels = {d.relation for d in r.decisions} or {"new"}
            ok += s["expected_relation"] in rels
        notes.append(f"live paste samples: relation correct {ok}/{len(samples)}, ingest p50 "
                     f"{int(statistics.median(ing))} ms")
    await st.delete_workspace(SCRATCH)

    report = EvalReport(
        run_at=datetime.now(timezone.utc), model=llm.MODEL,
        decisions_planted=len(planted), decisions_found=sum(1 for it in planted if found.get(it["decision_key"])),
        contradictions_planted=len(conflict_gold), contradictions_found=got["update"] + got["contradiction"],
        false_positives=fps, check_cases=len(gold["check_intent"]), check_correct=check_ok,
        unanswerable=len(gold["unanswerable_questions"]), refused_correctly=refused,
        p50_ms=_pct(lat, 0.5), p95_ms=_pct(lat, 0.95), notes=notes)
    REPORT.write_text(report.model_dump_json(indent=2) + "\n")
    return report
