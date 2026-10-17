"""Load data/corpus + people.json into a workspace through ingest.

Extraction runs concurrently (semaphore); commits run strictly in (ts, title) order because
supersession and stale-doc detection depend on chronology. Resumable: source ids are
deterministic, already-committed sources are skipped.

  uv run python scripts/seed.py --data ../data            # workspace acme
  uv run python scripts/seed.py --workspace test-w2 --only "Release" --reset
"""
import argparse
import asyncio
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from canon.ingest import commit, prepare  # noqa: E402
from canon.models import Source  # noqa: E402
from canon.store import get_store  # noqa: E402


def load(data: Path) -> list[dict]:
    rows = [json.loads(line) for f in sorted((data / "corpus").glob("*.jsonl")) for line in f.open() if line.strip()]
    return sorted(rows, key=lambda r: (r["ts"], r["title"]))


def source_id(ws: str, r: dict) -> str:
    return "s-" + hashlib.sha1(f"{ws}|{r['ts']}|{r['title']}".encode()).hexdigest()[:12]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(Path(__file__).resolve().parents[2] / "data"))
    ap.add_argument("--workspace", default="acme")
    ap.add_argument("--only", nargs="*", help="title substrings to include")
    ap.add_argument("--reset", action="store_true", help="delete the workspace first")
    ap.add_argument("--concurrency", type=int, default=8)
    a = ap.parse_args()
    data, ws, st = Path(a.data), a.workspace, get_store()
    if a.reset:
        await st.delete_workspace(ws)

    people = json.loads((data / "people.json").read_text())
    # Doc ids are global, so a bare person id would move that person out of another workspace (acme2 took
    # acme's people this way). Ids are workspace-scoped except in acme; acme2 keeps its legacy bare ids.
    pid = (lambda i: i) if ws in ("acme", "acme2") else (lambda i: f"{ws}-{i}")
    await asyncio.gather(*(st.put("people", {**p, "id": pid(p["id"]), "workspace": ws}) for p in people))

    rows = load(data)
    if a.only:
        rows = [r for r in rows if any(o.lower() in r["title"].lower() for o in a.only)]
    have = await st.get_many("sources", [source_id(ws, r) for r in rows])
    todo = [r for r in rows if source_id(ws, r) not in have]
    print(f"{len(people)} people, {len(rows)} sources, {len(rows) - len(todo)} already in {ws}", flush=True)

    sem = asyncio.Semaphore(a.concurrency)

    async def prep(r):
        async with sem:
            return await prepare(Source(**{**r, "id": source_id(ws, r), "workspace": ws}), ws, "human:seed")

    t0 = time.perf_counter()
    tasks = [asyncio.create_task(prep(r)) for r in todo]
    stats = {"decisions": 0, "alerts": 0, "rejected": 0}
    for i, task in enumerate(tasks):
        res = await commit(await task, [ws], "human:seed", log=False)
        stats["decisions"] += sum(d.relation != "same" for d in res.decisions)
        stats["alerts"] += len(res.alerts)
        stats["rejected"] += res.rejected_quotes
        rels = ",".join(d.relation for d in res.decisions)
        print(f"[{i + 1}/{len(todo)}] {res.source.kind:7} {res.source.title[:50]:50} {rels} "
              f"{' '.join(x.kind for x in res.alerts)}", flush=True)
    print(f"done in {time.perf_counter() - t0:.0f}s: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
