"""API contract. Lead-owned: change only together with SPEC.md."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SourceKind = Literal["slack", "meeting", "wiki", "pr", "commit", "email", "doc", "paste", "agent"]
Persona = Literal["engineer", "pm", "new_hire"]
Verdict = Literal["allow", "warn", "block"]
AlertKind = Literal["contradiction", "stale_doc", "premise_changed", "agent_violation", "pr_deviation"]
Reconciliation = Literal["new", "same", "update", "contradiction"]


class Quote(BaseModel):
    source_id: str
    quote: str


class Source(BaseModel):
    id: str | None = None
    workspace: str = "acme"
    kind: SourceKind
    title: str
    author: str
    ts: datetime
    url: str | None = None
    text: str
    synthetic: bool = True
    image_b64: str | None = None  # F17: optional image/PDF page, ingest only


class Decision(BaseModel):
    id: str
    workspace: str
    statement: str
    rationale: str
    assumptions: list[str] = []
    owner: str
    ts: datetime
    topic: str
    status: Literal["active", "superseded", "retired"] = "active"
    version: int = 1  # 1 + length of the supersedes chain
    supersedes: list[str] = []
    superseded_by: str | None = None
    quotes: list[Quote]
    created_by: str = "human"


class Alert(BaseModel):
    id: str
    workspace: str
    kind: AlertKind
    severity: Literal["high", "medium", "low"]
    decision_id: str | None = None
    source_id: str | None = None
    explanation: str
    quotes: list[Quote] = []
    status: Literal["open", "resolved"] = "open"
    resolution: str | None = None
    created_by: str = "canon"
    created_at: datetime


class Activity(BaseModel):
    id: str
    workspace: str
    actor: str  # human:web | agent:<name>
    action: Literal["ingest", "ask", "check", "record", "briefing", "resolve", "expert", "search", "flag"]
    summary: str
    ref_ids: list[str] = []
    ref_titles: list[str] = []  # display text for ref_ids, so the feed needs no second lookup
    verdict: Verdict | None = None
    created_at: datetime


class Person(BaseModel):
    id: str
    name: str
    role: str
    team: str
    status: Literal["active", "left"] = "active"
    left_at: datetime | None = None


class Citation(BaseModel):
    source_id: str
    decision_id: str | None = None
    quote: str
    title: str
    kind: SourceKind
    ts: datetime
    url: str | None = None


class TimelineEntry(BaseModel):
    ts: datetime
    decision_id: str
    statement: str
    status: str
    relation: Reconciliation | None = None


# ---- requests / results ----

class IngestRequest(BaseModel):
    source: Source
    actor: str = "human:web"


class ReconciledDecision(BaseModel):
    decision: Decision
    relation: Reconciliation
    related_decision_id: str | None = None
    explanation: str = ""


class IngestResult(BaseModel):
    source: Source
    decisions: list[ReconciledDecision]
    alerts: list[Alert]
    rejected_quotes: int = 0  # extractions dropped because the quote was not in the source
    latency_ms: int


class AskRequest(BaseModel):
    question: str
    actor: str = "human:web"


class AskResult(BaseModel):
    answer: str
    citations: list[Citation]
    timeline: list[TimelineEntry] = []
    refused: bool = False
    latency_ms: int


class BriefingRequest(BaseModel):
    persona: Persona
    since: datetime
    actor: str = "human:web"


class Action(BaseModel):
    priority: int = Field(ge=0, le=100)
    title: str
    why: str
    deadline: datetime | None = None
    reasons: list[str]  # scoring factors, e.g. "deadline in 2 days", "blocks marketing"
    citations: list[Citation]
    chip: Literal["open_source", "view_decision", "resolve_alert", "ask_person", "draft_reply"]


class Briefing(BaseModel):
    persona: Persona
    since: datetime
    summary: str
    highlights: list[str]
    actions: list[Action]
    who_to_ask: list[Person] = []  # F12 onboarding
    latency_ms: int


class CheckRequest(BaseModel):
    intent: str
    actor: str = "human:web"


class CheckResult(BaseModel):
    verdict: Verdict
    explanation: str
    decisions: list[Decision]
    citations: list[Citation]
    latency_ms: int


class ExpertRequest(BaseModel):
    person_id: str
    question: str
    actor: str = "human:web"


class ResolveRequest(BaseModel):
    action: Literal["accept_update", "dismiss", "retire_decision"]
    note: str = ""
    actor: str = "human:web"


class DecisionDetail(BaseModel):
    decision: Decision
    timeline: list[TimelineEntry]
    sources: list[Source]
    alerts: list[Alert]


class EvalReport(BaseModel):
    run_at: datetime
    model: str
    decisions_planted: int
    decisions_found: int
    contradictions_planted: int
    contradictions_found: int
    false_positives: int
    check_cases: int
    check_correct: int
    unanswerable: int
    refused_correctly: int
    p50_ms: int
    p95_ms: int
    notes: list[str] = []
