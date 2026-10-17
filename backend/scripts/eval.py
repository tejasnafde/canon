"""Run the gold-set benchmark against a seeded workspace and write canon/eval_report.json.

  uv run python scripts/eval.py --data ../data [--workspace acme]
  uv run python scripts/eval.py --health [--write]   # W20 memory-health replay only (about 35 Gemini calls)

--health replays data/gold/authority_cases.json into a throwaway workspace; run it with CANON_MEMORY_STORE=1 so
nothing touches Firestore. --write merges its fields into the committed eval_report.json.
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from canon import llm  # noqa: E402
from canon.eval import REPORT, health, run  # noqa: E402
from canon.models import EvalReport  # noqa: E402


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(Path(__file__).resolve().parents[2] / "data"))
    ap.add_argument("--workspace", default="acme")
    ap.add_argument("--health", action="store_true")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    data = Path(a.data)
    if a.health:
        h = await health(data / "gold" / "authority_cases.json")
        print(json.dumps(h, indent=2), f"\ngenerate calls: {sum(llm._spent.values())}")
        if a.write:
            r = EvalReport.model_validate_json(REPORT.read_text())
            notes = [n for n in r.notes if not n.startswith(("authority case", "checkpoint", "chain", "memory health"))]
            r = r.model_copy(update={**{k: v for k, v in h.items() if k != "notes"}, "notes": notes + [
                "memory health: data/gold/authority_cases.json replayed in time order, live Gemini, in-memory store"]
                + h["notes"]})
            REPORT.write_text(r.model_dump_json(indent=2) + "\n")
        return
    r = await run(data / "gold" / "gold.json", a.workspace, data / "samples" / "live_paste.json")
    print(r.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
