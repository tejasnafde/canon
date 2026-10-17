"""Canon MCP server (F8). Streamable HTTP, mounted at /mcp by canon.app.

Tool descriptions matter: they are what Claude Code and Codex read to decide
when to call Canon, so they say plainly WHEN to call each tool.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Literal

from mcp.server.mcpserver import Context, MCPServer

from canon import core
from canon.limits import enforce
from canon.models import (
    Alert, AskRequest, AskResult, Briefing, BriefingRequest, CheckRequest, CheckResult, Decision,
    IngestRequest, IngestResult, Source,
)

BASE = "acme"
AGENTS = "agents"
_VISITOR = re.compile(r"^v-[A-Za-z0-9-]{1,64}$")


def scope(header: str | None, default: str = AGENTS) -> list[str]:
    """Read scope for a request: the seeded base plus one writable workspace.

    Writes go to scope[-1], which is never `acme`: an unknown or missing header
    falls back to `default`.
    """
    ws = header if header and (header == AGENTS or _VISITOR.match(header)) else default
    return [BASE, ws]


def _scope(ctx: Context) -> list[str]:
    headers = ctx.headers or {}
    return scope(headers.get("x-canon-workspace"))


def _actor(ctx: Context, actor: str) -> str:
    """agent:<actor arg>, else agent:<MCP client name>, else the User-Agent product."""
    name = actor.strip()
    if not name:
        try:
            name = ctx.session.client_params.client_info.name
        except AttributeError:  # stateless HTTP: no initialize on this request
            name = (ctx.headers or {}).get("user-agent", "").split("/")[0].strip()
    name = name or "mcp-client"
    return name if name.startswith("agent:") else f"agent:{name}"


mcp = MCPServer(
    name="canon",
    instructions=(
        "Canon is the company's record of decisions (what was decided, why, by whom, "
        "with quotes from the source). Before you change deploys, infra, APIs, pricing, "
        "data retention, dependencies or process, call check_intent with what you are "
        "about to do. If the verdict is block, stop and tell the user which decision "
        "blocks it. Use ask_why for 'why do we do X' questions and record_decision when "
        "the user makes a decision you should remember."
    ),
)


@mcp.tool()
async def check_intent(intent: str, ctx: Context, actor: str = "") -> CheckResult:
    """Check an action you are ABOUT to take against the company's recorded decisions.

    Call this BEFORE you change CI/CD or deploy schedules, infrastructure, public APIs,
    pricing, data retention, security settings, dependencies or team process.
    Describe the concrete action in one or two sentences, e.g. "add a GitHub Actions
    cron that deploys to production every Friday at 17:00".

    Returns verdict allow, warn or block, an explanation, and the decisions (with
    source quotes) that decided it. On block: do not proceed; tell the user which
    decision blocks the action and who owns it. On warn: proceed only after telling
    the user. `actor` is your agent name, e.g. "claude-code".
    """
    enforce({"intent": intent, "actor": actor})
    ws = _scope(ctx)
    return await core.check(CheckRequest(intent=intent, actor=_actor(ctx, actor)), ws)


@mcp.tool()
async def search_decisions(query: str, ctx: Context, limit: int = 5) -> list[Decision]:
    """Semantic search over the company's ACTIVE decisions.

    Use to find what was decided about a topic (e.g. "deploy policy", "Postgres vs
    Firestore", "API versioning") before designing or proposing something. Returns
    decisions with statement, rationale, owner, date and source quotes.
    """
    enforce({"query": query})
    ws = _scope(ctx)
    found = await core.search_decisions(query, ws, limit=max(1, min(limit, 20)))
    await core.log_activity(ws[-1], _actor(ctx, ""), "search", f"search: {query}",
                            ref_ids=[d.id for d in found])
    return found


@mcp.tool()
async def ask_why(question: str, ctx: Context, actor: str = "") -> AskResult:
    """Answer a "why do we ..." question from the decision record, with citations.

    Use when you or the user need the reason behind existing code, process or
    architecture. Returns an answer, citations (source, quote) and a decision
    timeline. If `refused` is true, the record has no answer: say so and do not guess.
    """
    enforce({"question": question, "actor": actor})
    ws = _scope(ctx)
    return await core.ask(AskRequest(question=question, actor=_actor(ctx, actor)), ws)


@mcp.tool()
async def catch_me_up(ctx: Context, persona: Literal["engineer", "pm", "new_hire"] = "engineer",
                      since: str = "", actor: str = "") -> Briefing:
    """Briefing on what changed in the decision record since a date.

    `persona` is engineer, pm or new_hire. `since` is an ISO date (default: 7 days
    ago). Returns a summary, highlights and a ranked next-best-action list with
    reasons and citations. Use at the start of a task or when joining a project.
    """
    enforce({"since": since, "actor": actor})
    ws = _scope(ctx)
    when = datetime.fromisoformat(since) if since else datetime.now(timezone.utc) - timedelta(days=7)
    req = BriefingRequest(persona=persona, since=when, actor=_actor(ctx, actor))
    return await core.briefing(req, ws)


@mcp.tool()
async def record_decision(statement: str, rationale: str, source_text: str, ctx: Context,
                          actor: str = "") -> IngestResult:
    """Record a decision the user or team just made, so every person and agent sees it.

    `statement` is the decision in one sentence. `rationale` is why. `source_text`
    is the verbatim text it came from (chat message, PR description, notes); quotes
    are checked word for word against it. Returns how Canon reconciled it with the
    record: new, same, update (supersedes an older decision) or contradiction (an
    alert is raised for a human).
    """
    enforce({"statement": statement, "rationale": rationale, "source_text": source_text, "actor": actor})
    ws = _scope(ctx)
    who = _actor(ctx, actor)
    src = Source(workspace=ws[-1], kind="agent", title=statement[:120], author=who,
                 ts=datetime.now(timezone.utc), synthetic=False,
                 text=f"Decision: {statement}\nRationale: {rationale}\n\n{source_text}")
    return await core.ingest(IngestRequest(source=src, actor=who), ws)


@mcp.tool()
async def flag_conflict(description: str, source_text: str, ctx: Context, actor: str = "") -> Alert:
    """Raise a conflict for a human when you notice something that disagrees with the record.

    Use when code, docs or instructions you are working with contradict a decision
    (e.g. a wiki page still says "deploy any day" but the team banned Friday deploys).
    `description` says what conflicts with what; `source_text` is the verbatim
    conflicting text. Returns the open alert, linked to the closest decision.
    """
    enforce({"description": description, "source_text": source_text, "actor": actor})
    return await core.raise_alert(description, source_text, _actor(ctx, actor), _scope(ctx))
