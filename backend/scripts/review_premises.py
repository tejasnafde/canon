"""Re-judge open premise_changed alerts with the W20 rule (reconcile.PREMISE_RULE + premise_holds) and dismiss the
ones that fail it through core.resolve_alert, which also writes activity. One Gemini call per alert.

  GOOGLE_APPLICATION_CREDENTIALS=... uv run python scripts/review_premises.py --workspace acme4 --dry-run
  GOOGLE_APPLICATION_CREDENTIALS=... uv run python scripts/review_premises.py --workspace acme4 --apply
"""
import argparse
import asyncio
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import BaseModel  # noqa: E402

from canon import core, llm  # noqa: E402
from canon.models import ResolveRequest  # noqa: E402
from canon.reconcile import PREMISE_RULE, SYSTEM, premise_holds  # noqa: E402
from canon.store import get_store  # noqa: E402


class Rejudge(BaseModel):
    assumption_quote: str
    contradicts: bool
    trivial: bool
    why: str


async def rejudge(a: dict, d: dict, src_text: str) -> tuple[bool, dict]:
    evidence = next((q["quote"] for q in a["quotes"] if q["source_id"] == a["source_id"]), "")
    prompt = (f"DECISION: {d['statement']}\nWhy: {d.get('rationale') or ''}\nStated assumptions: "
              f"{'; '.join(d.get('assumptions') or []) or 'none'}\n\nALERT raised earlier: {a['explanation']}\n"
              f"NEW information (evidence): \"{evidence}\"\n\nSOURCE of the new information:\n"
              f"{llm.source_block(src_text[:4000])}\n\n{PREMISE_RULE}\nJudge whether this alert is a real premise "
              "change. why: one sentence.")
    r = await llm.generate_json(prompt, Rejudge, system=SYSTEM)
    return premise_holds({**r, "evidence_quote": evidence}, d), r


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    ap.add_argument("--batch", type=int, default=5)
    a = ap.parse_args()
    st, ws = get_store(), [a.workspace]
    alerts = await st.query("alerts", ws, kind="premise_changed", status="open")
    decs = await st.get_many("decisions", [x["decision_id"] for x in alerts if x.get("decision_id")])
    srcs = await st.get_many("sources", [x["source_id"] for x in alerts if x.get("source_id")])
    note = f"auto-dismissed: not a premise change (re-judged {date.today().isoformat()})"
    keep = drop = 0
    for i in range(0, len(alerts), a.batch):
        batch = [x for x in alerts[i:i + a.batch] if x.get("decision_id") in decs]
        judged = await asyncio.gather(*(rejudge(x, decs[x["decision_id"]], srcs.get(x["source_id"], {}).get("text", ""))
                                        for x in batch))
        for x, (ok, r) in zip(batch, judged):
            keep, drop = keep + ok, drop + (not ok)
            print(f"{'KEEP   ' if ok else 'DISMISS'} {x['id']} {x['explanation'][:110]}\n        -> {r['why'][:160]}")
            if a.apply and not ok:
                await core.resolve_alert(x["id"], ResolveRequest(action="dismiss", note=note,
                                                                 actor="agent:canon-premise-review"), ws)
    print(f"{len(alerts)} open premise alerts: keep {keep}, dismiss {drop}" + ("" if a.apply else " (dry run)"))


if __name__ == "__main__":
    asyncio.run(main())
