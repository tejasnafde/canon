import type { AlertKind, Reconciliation } from './schemas'

export const fmtDate = (iso: string) => new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })

export const fmtTime = (iso: string) => new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })

export function ago(iso: string, now = Date.now()) {
  const m = Math.max(0, Math.round((now - new Date(iso).getTime()) / 60_000))
  if (m < 1) return 'just now'
  if (m < 60) return `${m} min ago`
  if (m < 1440) return `${Math.round(m / 60)} h ago`
  return `${Math.round(m / 1440)} d ago`
}

export const secs = (ms: number) => `${(ms / 1000).toFixed(1)} s`

export const short = (s: string, n = 70) => (s.length > n ? s.slice(0, n - 1).trimEnd() + '...' : s)

export const plural = (n: number, word: string) => `${n} ${word}${n === 1 ? '' : 's'}`

export const humanize = (s: string) => s.replaceAll('_', ' ')

export type Tone = 'signal' | 'signal-soft' | 'warn' | 'ok' | 'outline' | 'default'

/** Next-best-action priority (0-100) to a badge tone and a word. */
export function priorityTone(p: number): { tone: Tone; label: 'urgent' | 'soon' | 'later' } {
  if (p >= 80) return { tone: 'signal', label: 'urgent' }
  if (p >= 50) return { tone: 'warn', label: 'soon' }
  return { tone: 'outline', label: 'later' }
}

export const alertTone = (k: AlertKind): Tone =>
  (
    ({
      contradiction: 'signal',
      agent_violation: 'signal',
      pr_deviation: 'signal',
      stale_doc: 'signal-soft',
      premise_changed: 'warn',
    }) satisfies Record<AlertKind, Tone>
  )[k]

export const relationTone = (r: Reconciliation): Tone =>
  (({ new: 'default', same: 'outline', update: 'warn', contradiction: 'signal' }) satisfies Record<Reconciliation, Tone>)[r]

/** A scoring reason that points at a conflict reads red, the rest amber. */
export const reasonTone = (r: string): Tone => (/contradict|block|violat/i.test(r) ? 'signal-soft' : 'warn')

/** Only decisions have a page; ids look like `d-...` or `dec_...`. */
export const isDecisionId = (id: string | undefined) => !!id && /^d(-|ec_)/.test(id)

export type JsonTok = { t: 'key' | 'str' | 'num' | 'lit' | 'punct'; s: string }

/** Tiny tokenizer for pretty-printed JSON, enough to colour it. Unknown text passes through as punct. */
export function jsonTokens(src: string): JsonTok[] {
  const out: JsonTok[] = []
  const re = /("(?:\\.|[^"\\])*")(\s*:)?|(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)|\b(true|false|null)\b|([^"\d\-tfn]+|.)/g
  for (const m of src.matchAll(re)) {
    if (m[1]) {
      out.push({ t: m[2] ? 'key' : 'str', s: m[1] })
      if (m[2]) out.push({ t: 'punct', s: m[2] })
    } else if (m[3]) out.push({ t: 'num', s: m[3] })
    else if (m[4]) out.push({ t: 'lit', s: m[4] })
    else out.push({ t: 'punct', s: m[0] })
  }
  return out
}
