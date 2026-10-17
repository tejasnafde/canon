import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError, ContractError } from './api'

const reply = (body: unknown, status = 200) =>
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } }))

afterEach(() => vi.restoreAllMocks())

describe('api client', () => {
  it('parses a valid response and fills pydantic defaults', async () => {
    reply([{ id: 'a1', workspace: 'acme', actor: 'agent:bot', action: 'check', summary: 's', created_at: '2026-10-17T10:00:00Z' }])
    const [a] = await api.activity()
    expect(a).toMatchObject({ ref_ids: [], ref_titles: [], verdict: null, explanation: null })
  })

  it('sends the workspace header', async () => {
    const f = reply({ ok: true, model: 'm' })
    await api.health()
    const headers = f.mock.calls[0]?.[1]?.headers as Record<string, string>
    expect(headers['X-Canon-Workspace']).toMatch(/^v-/)
  })

  it('rejects a response that breaks the contract', async () => {
    reply({ verdict: 'maybe', explanation: '', decisions: [], citations: [], latency_ms: 1 })
    await expect(api.check('x')).rejects.toBeInstanceOf(ContractError)
  })

  it('turns FastAPI errors into ApiError with the detail', async () => {
    reply({ error: 'not_found', detail: 'd-1' }, 404)
    const err = await api.decision('d-1').catch((e: unknown) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect((err as ApiError).status).toBe(404)
    expect((err as ApiError).message).toBe('404 not_found: d-1')
  })
})
