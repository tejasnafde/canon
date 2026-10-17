// Mirrors backend/canon/models.py. Datetimes arrive as ISO strings.
export type SourceKind = 'slack' | 'meeting' | 'wiki' | 'pr' | 'commit' | 'email' | 'doc' | 'paste' | 'agent'
export type Persona = 'engineer' | 'pm' | 'new_hire'
export type Verdict = 'allow' | 'warn' | 'block'
export type AlertKind = 'contradiction' | 'stale_doc' | 'premise_changed' | 'agent_violation' | 'pr_deviation'
export type Reconciliation = 'new' | 'same' | 'update' | 'contradiction'

export interface Quote { source_id: string; quote: string }

export interface Source {
  id?: string | null; workspace?: string; kind: SourceKind; title: string; author: string
  ts: string; url?: string | null; text: string; synthetic?: boolean; image_b64?: string | null
}

export interface Decision {
  id: string; workspace: string; statement: string; rationale: string; assumptions: string[]
  owner: string; ts: string; topic: string; status: 'active' | 'superseded' | 'retired'
  version: number; supersedes: string[]; superseded_by: string | null; quotes: Quote[]; created_by: string
}

export interface Alert {
  id: string; workspace: string; kind: AlertKind; severity: 'high' | 'medium' | 'low'
  decision_id: string | null; related_decision_id?: string | null; source_id: string | null; explanation: string; quotes: Quote[]
  status: 'open' | 'resolved'; resolution: string | null; created_by: string; created_at: string
}

export interface Activity {
  id: string; workspace: string; actor: string
  action: 'ingest' | 'ask' | 'check' | 'record' | 'briefing' | 'resolve' | 'expert' | 'search' | 'flag'
  summary: string; ref_ids: string[]; ref_titles: string[]; verdict: Verdict | null
  explanation?: string | null; created_at: string
}

export interface Person { id: string; name: string; role: string; team: string; status: 'active' | 'left'; left_at: string | null }

export interface Citation {
  source_id: string; decision_id: string | null; quote: string; title: string; kind: SourceKind; ts: string; url: string | null
}

export interface TimelineEntry { ts: string; decision_id: string; statement: string; status: string; relation: Reconciliation | null }

export interface ReconciledDecision { decision: Decision; relation: Reconciliation; related_decision_id: string | null; explanation: string }
export interface IngestResult { source: Source; decisions: ReconciledDecision[]; alerts: Alert[]; rejected_quotes: number; latency_ms: number }
export interface AskResult { answer: string; citations: Citation[]; timeline: TimelineEntry[]; refused: boolean; latency_ms: number }

export interface Action {
  priority: number; title: string; why: string; deadline: string | null; reasons: string[]; citations: Citation[]
  chip: 'open_source' | 'view_decision' | 'resolve_alert' | 'ask_person' | 'draft_reply'
}
export interface Briefing {
  persona: Persona; since: string; summary: string; highlights: string[]; actions: Action[]; who_to_ask: Person[]; latency_ms: number
}
export interface CheckResult { verdict: Verdict; explanation: string; decisions: Decision[]; citations: Citation[]; latency_ms: number }
export interface DecisionDetail { decision: Decision; timeline: TimelineEntry[]; sources: Source[]; alerts: Alert[] }
export interface EvalReport {
  run_at: string; model: string; decisions_planted: number; decisions_found: number
  contradictions_planted: number; contradictions_found: number; false_positives: number
  check_cases: number; check_correct: number; unanswerable: number; refused_correctly: number
  p50_ms: number; p95_ms: number; notes: string[]
}
export type ResolveAction = 'accept_update' | 'dismiss' | 'retire_decision'
