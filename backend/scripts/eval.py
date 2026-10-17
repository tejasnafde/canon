"""Run the gold-set benchmark against a seeded workspace and write canon/eval_report.json.

  uv run python scripts/eval.py --data ../data [--workspace acme]
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from canon.eval import run  # noqa: E402


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(Path(__file__).resolve().parents[2] / "data"))
    ap.add_argument("--workspace", default="acme")
    a = ap.parse_args()
    data = Path(a.data)
    r = await run(data / "gold" / "gold.json", a.workspace, data / "samples" / "live_paste.json")
    print(r.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
