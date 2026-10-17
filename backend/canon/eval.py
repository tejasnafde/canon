"""F11 benchmark. `run` scores the gold set against the seeded workspace; `eval_report` serves the last run."""
import json
from pathlib import Path

from canon.models import EvalReport

REPORT = Path(__file__).resolve().parent / "eval_report.json"


async def eval_report() -> EvalReport:
    return EvalReport.model_validate_json(REPORT.read_text())
