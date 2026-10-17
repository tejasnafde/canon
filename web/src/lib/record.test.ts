import { describe, expect, it } from 'vitest'
import { shouldRetry } from './query'
import { ApiError } from './api'
import { actorName, breaksByDecision, noteFigures, quotedSourceCount, rankDecisions, sinceFor, srcLine, staleDocIds } from './record'
import { Alert, Decision, Persona } from './schemas'
import { PERSONA_GROUPS, PERSONA_LABEL } from './record'

const alert = (p: Partial<Alert>) =>
  Alert.parse({ id: 'a', workspace: 'acme', kind: 'contradiction', severity: 'high', explanation: '', created_at: '2026-10-01T00:00:00Z', ...p })
const dec = (id: string, ts: string, status = 'active') =>
  Decision.parse({
    id,
    workspace: 'acme',
    statement: id,
    rationale: '',
    owner: 'Mei Tan',
    ts,
    topic: 't',
    status,
    quotes: [{ source_id: `s-${id}`, quote: 'q' }],
  })

describe('away for', () => {
  it('counts back from the end of the demo history', () => {
    expect(sinceFor('1w')).toBe('2026-10-10T00:00:00.000Z')
    expect(sinceFor('1m')).toBe('2026-09-17T00:00:00.000Z')
    expect(sinceFor('3m')).toBe('2026-07-17T00:00:00.000Z')
  })
})

describe('what breaks which decision', () => {
  const alerts = [
    // a contradiction points decision_id at the new message and related_decision_id at the rule
    alert({ id: 'c', kind: 'contradiction', decision_id: 'new', related_decision_id: 'rule', source_id: 's1' }),
    alert({ id: 's', kind: 'stale_doc', decision_id: 'rule', related_decision_id: 'old', source_id: 'wiki' }),
    alert({ id: 's2', kind: 'stale_doc', decision_id: 'other', source_id: 'wiki' }),
    alert({ id: 'p', kind: 'premise_changed', decision_id: 'cache' }),
    alert({ id: 'r', kind: 'contradiction', decision_id: 'x', related_decision_id: 'rule', status: 'resolved' }),
  ]
  it('counts open alerts against the rule they break', () => {
    const b = breaksByDecision(alerts)
    expect(b.get('rule')?.map(a => a.id)).toEqual(['c', 's'])
    expect(b.get('new')).toBeUndefined()
    expect(b.get('cache')?.length).toBe(1)
  })
  it('counts each out-of-date document once', () => {
    expect(staleDocIds(alerts)).toEqual(['wiki'])
  })
  it('puts broken decisions first, then newest first', () => {
    const ds = [dec('a', '2026-01-01T00:00:00Z'), dec('rule', '2025-01-01T00:00:00Z'), dec('b', '2026-05-01T00:00:00Z')]
    expect(rankDecisions(ds, breaksByDecision(alerts)).map(d => d.id)).toEqual(['rule', 'b', 'a'])
    expect(quotedSourceCount(ds)).toBe(3)
  })
})

describe('labels', () => {
  it('writes one plain source line', () => {
    expect(srcLine({ kind: 'meeting', title: 'INC-042 review: the Friday release', ts: '2026-03-09T04:30:00Z' })).toBe(
      'Meeting, INC-042 review, the Friday release, 9 Mar 2026',
    )
    expect(srcLine({ kind: 'pr', title: 'PR 684: unattended dispatch refresh', ts: '2026-08-14T04:30:00Z' })).toBe(
      'PR 684, unattended dispatch refresh, 14 Aug 2026',
    )
  })
  it('names Discord members and agents', () => {
    expect(actorName('human:discord/mei')).toBe('mei on Discord')
    expect(actorName('agent:claude-code')).toBe('claude-code')
  })
  it('labels and groups all 14 personas exactly once', () => {
    const grouped = PERSONA_GROUPS.flatMap(g => g.ids).sort()
    expect(grouped).toEqual([...Persona.options].sort())
    expect(Object.keys(PERSONA_LABEL).sort()).toEqual([...Persona.options].sort())
  })
  it('reads extra figures from the eval notes', () => {
    expect(noteFigures(['stale docs found 8/8', '184 stored quotes, every one verified'])).toEqual({
      stale: { found: 8, of: 8 },
      premise: null,
      quotes: 184,
    })
  })
  it('retries cold starts but not client errors', () => {
    expect(shouldRetry(0, new ApiError(503, 'x'))).toBe(true)
    expect(shouldRetry(0, new ApiError(404, 'x'))).toBe(false)
  })
})
