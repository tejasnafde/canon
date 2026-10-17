import { describe, expect, it } from 'vitest'
import { EvalReport } from '@/lib/schemas'
import { rows } from './BenchmarkPage'

const report = EvalReport.parse({
  run_at: '2026-10-17T13:40:14Z',
  model: 'gemini-3.5-flash-lite',
  decisions_planted: 40,
  decisions_found: 37,
  contradictions_planted: 17,
  contradictions_found: 16,
  false_positives: 1,
  check_cases: 15,
  check_correct: 15,
  unanswerable: 5,
  refused_correctly: 5,
  p50_ms: 1127,
  p95_ms: 1442,
  notes: ['stale docs found 7/8', '190 stored quotes, every one verified'],
})

describe('benchmark rows', () => {
  it('binds every figure to its report key, so a new run updates the page', () => {
    const r = rows(report)
    expect(r.map(x => x.key)).toEqual([
      'decisions_found',
      'contradictions_found',
      'stale_found',
      'check_correct',
      'refused_correctly',
      'p50_ms',
      'quotes',
    ])
    expect(r[0]?.title).toBe('Found 37 of 40 decisions')
    expect(r[1]?.body).toContain('1 false alarm.')
    expect(r[2]?.title).toBe('Found 7 of 8 out-of-date documents')
    expect(r[5]?.title).toBe('A typical answer in 1.1 seconds')
    expect(r[6]?.title).toContain('190 quotes')
  })
})
