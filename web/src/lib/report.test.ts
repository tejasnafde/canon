import { afterEach, describe, expect, it, vi } from 'vitest'
import { reportError, toClientError } from './report'

afterEach(() => vi.restoreAllMocks())

describe('reportError', () => {
  it('drops the query string, which can hold what the user typed', () => {
    history.pushState({}, '', '/ask?q=secret')
    expect(toClientError(new Error('boom'), 'onerror').path).toBe('/ask')
  })

  it('samples, then dedupes the same message', () => {
    const f = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response())
    expect(reportError(new Error('a'), 'boundary', () => 0.99)).toBe(false) // sampled out
    expect(reportError(new Error('a'), 'boundary', () => 0)).toBe(true)
    expect(reportError(new Error('a'), 'boundary', () => 0)).toBe(false) // already sent
    expect(f).toHaveBeenCalledTimes(1)
    expect(f.mock.calls[0]?.[0]).toBe('/api/client-error')
  })
})
