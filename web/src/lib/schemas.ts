// Zod mirrors of backend/canon/models.py: the API boundary. Datetimes arrive as ISO strings.
import { z } from 'zod'

const ts = z.string()
const nul = <T extends z.ZodType>(t: T) => t.nullable().default(null)

export const SourceKind = z.enum(['slack', 'meeting', 'wiki', 'pr', 'commit', 'email', 'doc', 'paste', 'agent'])
export const Persona = z.enum(['engineer', 'pm', 'new_hire'])
export const Verdict = z.enum(['allow', 'warn', 'block'])
export const AlertKind = z.enum(['contradiction', 'stale_doc', 'premise_changed', 'agent_violation', 'pr_deviation'])
export const Reconciliation = z.enum(['new', 'same', 'update', 'contradiction'])
export const ResolveAction = z.enum(['accept_update', 'dismiss', 'retire_decision'])

export const Quote = z.object({ source_id: z.string(), quote: z.string() })

export const Source = z.object({
  id: nul(z.string()),
  workspace: z.string().default('acme'),
  kind: SourceKind,
  title: z.string(),
  author: z.string(),
  ts,
  url: nul(z.string()),
  text: z.string(),
  synthetic: z.boolean().default(true),
  image_b64: nul(z.string()),
})

export const Decision = z.object({
  id: z.string(),
  workspace: z.string(),
  statement: z.string(),
  rationale: z.string(),
  assumptions: z.array(z.string()).default([]),
  owner: z.string(),
  ts,
  topic: z.string(),
  status: z.enum(['active', 'superseded', 'retired']).default('active'),
  version: z.number().int().default(1),
  supersedes: z.array(z.string()).default([]),
  superseded_by: nul(z.string()),
  quotes: z.array(Quote),
  created_by: z.string().default('human'),
})

export const Alert = z.object({
  id: z.string(),
  workspace: z.string(),
  kind: AlertKind,
  severity: z.enum(['high', 'medium', 'low']),
  decision_id: nul(z.string()),
  related_decision_id: nul(z.string()),
  source_id: nul(z.string()),
  explanation: z.string(),
  quotes: z.array(Quote).default([]),
  status: z.enum(['open', 'resolved']).default('open'),
  resolution: nul(z.string()),
  created_by: z.string().default('canon'),
  created_at: ts,
})

export const Activity = z.object({
  id: z.string(),
  workspace: z.string(),
  actor: z.string(),
  action: z.enum(['ingest', 'ask', 'check', 'record', 'briefing', 'resolve', 'expert', 'search', 'flag']),
  summary: z.string(),
  ref_ids: z.array(z.string()).default([]),
  ref_titles: z.array(z.string()).default([]),
  verdict: nul(Verdict),
  explanation: nul(z.string()),
  created_at: ts,
})

export const Person = z.object({
  id: z.string(),
  name: z.string(),
  role: z.string(),
  team: z.string(),
  status: z.enum(['active', 'left']).default('active'),
  left_at: nul(ts),
})

export const Citation = z.object({
  source_id: z.string(),
  decision_id: nul(z.string()),
  quote: z.string(),
  title: z.string(),
  kind: SourceKind,
  ts,
  url: nul(z.string()),
})

export const TimelineEntry = z.object({
  ts,
  decision_id: z.string(),
  statement: z.string(),
  status: z.string(),
  relation: nul(Reconciliation),
})

export const ReconciledDecision = z.object({
  decision: Decision,
  relation: Reconciliation,
  related_decision_id: nul(z.string()),
  explanation: z.string().default(''),
})

export const IngestResult = z.object({
  source: Source,
  decisions: z.array(ReconciledDecision),
  alerts: z.array(Alert),
  rejected_quotes: z.number().int().default(0),
  latency_ms: z.number(),
})

export const AskResult = z.object({
  answer: z.string(),
  citations: z.array(Citation),
  timeline: z.array(TimelineEntry).default([]),
  refused: z.boolean().default(false),
  latency_ms: z.number(),
})

export const Action = z.object({
  priority: z.number().min(0).max(100),
  title: z.string(),
  why: z.string(),
  deadline: nul(ts),
  reasons: z.array(z.string()),
  citations: z.array(Citation),
  chip: z.enum(['open_source', 'view_decision', 'resolve_alert', 'ask_person', 'draft_reply']),
})

export const Briefing = z.object({
  persona: Persona,
  since: ts,
  summary: z.string(),
  highlights: z.array(z.string()),
  actions: z.array(Action),
  who_to_ask: z.array(Person).default([]),
  latency_ms: z.number(),
})

export const CheckResult = z.object({
  verdict: Verdict,
  explanation: z.string(),
  decisions: z.array(Decision),
  citations: z.array(Citation),
  latency_ms: z.number(),
})

export const DecisionDetail = z.object({
  decision: Decision,
  timeline: z.array(TimelineEntry),
  sources: z.array(Source),
  alerts: z.array(Alert),
})

export const EvalReport = z.object({
  run_at: ts,
  model: z.string(),
  decisions_planted: z.number(),
  decisions_found: z.number(),
  contradictions_planted: z.number(),
  contradictions_found: z.number(),
  false_positives: z.number(),
  check_cases: z.number(),
  check_correct: z.number(),
  unanswerable: z.number(),
  refused_correctly: z.number(),
  p50_ms: z.number(),
  p95_ms: z.number(),
  notes: z.array(z.string()).default([]),
})

export const Health = z.object({ ok: z.boolean(), model: z.string().default('') })
export const Ok = z.object({ ok: z.boolean() })

export type SourceKind = z.infer<typeof SourceKind>
export type Persona = z.infer<typeof Persona>
export type Verdict = z.infer<typeof Verdict>
export type AlertKind = z.infer<typeof AlertKind>
export type Reconciliation = z.infer<typeof Reconciliation>
export type ResolveAction = z.infer<typeof ResolveAction>
export type Quote = z.infer<typeof Quote>
export type Source = z.infer<typeof Source>
export type SourceInput = z.input<typeof Source>
export type Decision = z.infer<typeof Decision>
export type Alert = z.infer<typeof Alert>
export type Activity = z.infer<typeof Activity>
export type Person = z.infer<typeof Person>
export type Citation = z.infer<typeof Citation>
export type TimelineEntry = z.infer<typeof TimelineEntry>
export type ReconciledDecision = z.infer<typeof ReconciledDecision>
export type IngestResult = z.infer<typeof IngestResult>
export type AskResult = z.infer<typeof AskResult>
export type Action = z.infer<typeof Action>
export type Briefing = z.infer<typeof Briefing>
export type CheckResult = z.infer<typeof CheckResult>
export type DecisionDetail = z.infer<typeof DecisionDetail>
export type EvalReport = z.infer<typeof EvalReport>
