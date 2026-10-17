import { describe, expect, it } from 'vitest'
import { alertTone, isDecisionId, priorityTone } from './format'
import { shouldRetry } from './query'
import { ApiError } from './api'

describe('priorityTone', () => {
  it.each([
    [100, 'signal', 'urgent'],
    [80, 'signal', 'urgent'],
    [79, 'warn', 'soon'],
    [50, 'warn', 'soon'],
    [49, 'outline', 'later'],
    [0, 'outline', 'later'],
  ])('%i is %s / %s', (p, tone, label) => {
    expect(priorityTone(p)).toEqual({ tone, label })
  })
})

describe('mappings', () => {
  it('shows conflicts in the signal colour and premise changes in amber', () => {
    expect(alertTone('contradiction')).toBe('signal')
    expect(alertTone('premise_changed')).toBe('warn')
  })
  it('links only decision ids', () => {
    expect(isDecisionId('d-12')).toBe(true)
    expect(isDecisionId('dec_nofri')).toBe(true)
    expect(isDecisionId('src_1')).toBe(false)
    expect(isDecisionId(undefined)).toBe(false)
  })
  it('retries cold starts but not client errors', () => {
    expect(shouldRetry(0, new ApiError(503, 'x'))).toBe(true)
    expect(shouldRetry(0, new TypeError('Failed to fetch'))).toBe(true)
    expect(shouldRetry(0, new ApiError(404, 'x'))).toBe(false)
    expect(shouldRetry(3, new ApiError(503, 'x'))).toBe(false)
  })
})
