// Plain-language views of the record: labels, source lines, and what breaks which decision.
import type { Alert, Decision, Persona, SourceKind } from './schemas'

/** The demo history ends here; "away for" counts back from it. */
export const DEMO_END = '2026-10-17T00:00:00Z'
export const PUBLIC_URL = 'https://canon.tn07.dev'
export const DISCORD_INVITE = 'https://discord.gg/HwSgjmcgF5'

export const PERSONA_LABEL: Record<Persona, string> = {
  engineer: 'Engineering',
  pm: 'Product',
  design: 'Design',
  data: 'Data',
  security: 'Security',
  sales: 'Sales',
  support: 'Support',
  marketing: 'Marketing',
  finance: 'Finance',
  operations: 'Operations',
  people: 'People (HR)',
  legal: 'Legal',
  leadership: 'Leadership',
  new_hire: 'New hire',
}

export const FEATURED: { id: Persona; label: string }[] = [
  { id: 'engineer', label: 'Engineer' },
  { id: 'pm', label: 'Product' },
  { id: 'sales', label: 'Sales' },
]

export const PERSONA_GROUPS: { label: string; ids: Persona[] }[] = [
  { label: 'Build', ids: ['engineer', 'pm', 'design', 'data', 'security'] },
  { label: 'Customers', ids: ['sales', 'support', 'marketing'] },
  { label: 'Company', ids: ['finance', 'operations', 'people', 'legal', 'leadership'] },
  { label: 'Just joined', ids: ['new_hire'] },
]

export const AWAY = [
  { key: '1w', label: '1 week', months: 0, days: 7 },
  { key: '1m', label: '1 month', months: 1, days: 0 },
  { key: '3m', label: '3 months', months: 3, days: 0 },
] as const
export type Away = (typeof AWAY)[number]['key']

export function sinceFor(key: Away, end = DEMO_END): string {
  const span = AWAY.find(a => a.key === key) ?? AWAY[2]
  const d = new Date(end)
  d.setUTCMonth(d.getUTCMonth() - span.months)
  d.setUTCDate(d.getUTCDate() - span.days)
  return d.toISOString()
}

const KIND: Record<SourceKind, string> = {
  slack: 'Slack',
  meeting: 'Meeting',
  wiki: 'Wiki',
  pr: 'PR',
  commit: 'Commit',
  email: 'Email',
  doc: 'Document',
  paste: 'Pasted',
  agent: 'Agent',
}

export const fmtDate = (iso: string) =>
  new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })
export const fmtLong = (iso: string) => new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' })

/** "Meeting, INC-042 review, 9 Mar 2026". PR titles already start with "PR 684". */
export function srcLine(s: { kind: SourceKind; title: string; ts: string }): string {
  const title = s.title.replace(/:\s+/, ', ')
  const lead = s.kind === 'pr' && /^PR\b/i.test(title) ? title : `${KIND[s.kind]}, ${title}`
  return `${lead}, ${fmtDate(s.ts)}`
}

export const secs = (ms: number) => `${(ms / 1000).toFixed(1)} seconds`

export const avatar = (name: string) => `https://api.dicebear.com/9.x/notionists/svg?seed=${encodeURIComponent(name)}&backgroundColor=f6f1e7`

/** Discord actors look like `human:discord/<name>`; agents `agent:<name>`. */
export function actorName(actor: string): string {
  const m = /^human:discord\/(.+)$/.exec(actor)
  if (m?.[1]) return `${m[1]} on Discord`
  if (actor === 'human:web') return 'A visitor'
  if (actor === 'canon') return 'Canon'
  return actor.replace(/^agent:/, '').replace(/^human:/, '')
}

/**
 * The decision an alert says is being broken. A contradiction points `decision_id` at the new,
 * conflicting decision and `related_decision_id` at the standing rule; the other kinds point
 * `decision_id` at the rule itself.
 */
export function ruleOf(a: Alert): string | null {
  return a.kind === 'contradiction' ? (a.related_decision_id ?? a.decision_id) : a.decision_id
}

/** Open alerts grouped by the decision they break. One source counts once per decision and kind. */
export function breaksByDecision(alerts: Alert[]): Map<string, Alert[]> {
  const m = new Map<string, Alert[]>()
  const seen = new Set<string>()
  for (const a of alerts) {
    const id = ruleOf(a)
    const key = `${id ?? ''}|${a.kind}|${a.source_id ?? a.id}`
    if (a.status !== 'open' || !id || seen.has(key)) continue
    seen.add(key)
    m.set(id, [...(m.get(id) ?? []), a])
  }
  return m
}

/** Documents that still describe an old decision: distinct sources behind open stale_doc alerts. */
export const staleDocIds = (alerts: Alert[]) => [
  ...new Set(alerts.filter(a => a.kind === 'stale_doc' && a.status === 'open').flatMap(a => (a.source_id ? [a.source_id] : []))),
]

/** Distinct sources the record quotes. Stands in for "items read" until the API exposes a count. */
export const quotedSourceCount = (decisions: Decision[]) => new Set(decisions.flatMap(d => d.quotes.map(q => q.source_id))).size

/** Broken first (most breaks first), then newest first. */
export function rankDecisions(decisions: Decision[], breaks: Map<string, Alert[]>): Decision[] {
  const n = (d: Decision) => (d.status === 'active' ? (breaks.get(d.id)?.length ?? 0) : 0)
  return [...decisions].sort((a, b) => n(b) - n(a) || b.ts.localeCompare(a.ts))
}

/** The quote an alert holds from one source, if any. */
export const quoteFrom = (a: Alert, sourceId: string | null | undefined) => a.quotes.find(q => q.source_id === sourceId)?.quote

/** Eval notes carry extra figures as text, e.g. "stale docs found 8/8", "184 stored quotes". */
export function noteFigures(notes: string[]) {
  const all = notes.join('\n')
  const frac = (re: RegExp) => {
    const m = re.exec(all)
    return m ? { found: Number(m[1]), of: Number(m[2]) } : null
  }
  const quotes = /(\d+) stored quotes/.exec(all)
  return {
    stale: frac(/stale docs found (\d+)\/(\d+)/),
    premise: frac(/premise changes found (\d+)\/(\d+)/),
    quotes: quotes ? Number(quotes[1]) : null,
  }
}
