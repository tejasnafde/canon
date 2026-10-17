"""The seam between the HTTP/MCP/agent layer (W3) and the core (W2).

W2 implements these. W3 only calls these. Signatures are the contract.
`workspaces` is the read scope (e.g. ["acme", "v-123"]); writes go to workspaces[-1].
"""
from canon.models import (
    Activity, Alert, AskRequest, AskResult, Briefing, BriefingRequest, CheckRequest,
    CheckResult, Decision, DecisionDetail, EvalReport, ExpertRequest, IngestRequest,
    IngestResult, Person, ResolveRequest, Source,
)

from canon.ask import ask, search_decisions  # noqa: E402
from canon.briefing import briefing  # noqa: E402
from canon.check import check  # noqa: E402
from canon.eval import eval_report  # noqa: E402
from canon.expert import expert  # noqa: E402
from canon.ingest import ingest  # noqa: E402
from canon.store import (  # noqa: E402
    get_decision, get_source, list_activity, list_alerts, list_decisions, list_people, log_activity,
    reset_workspace, resolve_alert,
)

__all__ = [
    "ingest", "ask", "briefing", "check", "expert", "search_decisions", "list_decisions", "get_decision",
    "list_alerts", "resolve_alert", "get_source", "list_activity", "log_activity", "list_people", "eval_report",
    "reset_workspace",
]
