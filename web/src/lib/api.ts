import { z } from 'zod'
import * as S from './schemas'

export const MOCK = import.meta.env.VITE_MOCK === '1'

const WS_KEY = 'canon-ws'

/** This browser's private workspace, `v-<uuid>`, kept in localStorage. */
export function workspace(): string {
  let ws = localStorage.getItem(WS_KEY)
  if (!ws || !/^v-[A-Za-z0-9-]{1,64}$/.test(ws)) {
    ws = 'v-' + crypto.randomUUID()
    localStorage.setItem(WS_KEY, ws)
  }
  return ws
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/** The response did not match the contract in models.py. */
export class ContractError extends Error {
  constructor(path: string, issues: z.core.$ZodIssue[]) {
    const first = issues[0]
    super(`Unexpected response from ${path}: ${first ? `${first.path.join('.')} ${first.message}` : 'invalid'}`)
    this.name = 'ContractError'
  }
}

type Method = 'GET' | 'POST'

/** FastAPI errors look like {error, detail} or {detail}. */
async function errorText(res: Response): Promise<string> {
  try {
    const j: unknown = await res.json()
    if (j && typeof j === 'object') {
      const { error, detail } = j as { error?: unknown; detail?: unknown }
      const d = detail === undefined ? '' : typeof detail === 'string' ? detail : JSON.stringify(detail)
      return [error, d].filter(Boolean).join(': ') || res.statusText
    }
  } catch {
    // not JSON
  }
  return res.statusText
}

async function raw(method: Method, path: string, body?: unknown): Promise<unknown> {
  if (MOCK) return (await import('./mock')).mockApi(method, path, body)
  const res = await fetch(path, {
    method,
    headers: { 'X-Canon-Workspace': workspace(), ...(body ? { 'Content-Type': 'application/json' } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new ApiError(res.status, `${res.status} ${await errorText(res)}`)
  return res.json()
}

export async function call<T extends z.ZodType>(schema: T, method: Method, path: string, body?: unknown): Promise<z.infer<T>> {
  const parsed = schema.safeParse(await raw(method, path, body))
  if (!parsed.success) throw new ContractError(path, parsed.error.issues)
  return parsed.data
}

const id = encodeURIComponent

export const api = {
  health: () => call(S.Health, 'GET', '/health'),
  ingest: (source: S.SourceInput) => call(S.IngestResult, 'POST', '/api/ingest', { source }),
  ask: (question: string) => call(S.AskResult, 'POST', '/api/ask', { question }),
  briefing: (persona: S.Persona, since: string) => call(S.Briefing, 'POST', '/api/briefing', { persona, since }),
  check: (intent: string) => call(S.CheckResult, 'POST', '/api/check', { intent }),
  decisions: () => call(z.array(S.Decision), 'GET', '/api/decisions'),
  decision: (d: string) => call(S.DecisionDetail, 'GET', `/api/decisions/${id(d)}`),
  alerts: () => call(z.array(S.Alert), 'GET', '/api/alerts?status=open'),
  resolve: (a: string, action: S.ResolveAction) => call(S.Alert, 'POST', `/api/alerts/${id(a)}/resolve`, { action }),
  source: (s: string) => call(S.Source, 'GET', `/api/sources/${id(s)}`),
  activity: () => call(z.array(S.Activity), 'GET', '/api/activity'),
  people: () => call(z.array(S.Person), 'GET', '/api/people'),
  evalReport: () => call(S.EvalReport, 'GET', '/api/eval'),
  reset: () => call(S.Ok, 'POST', '/api/workspace/reset'),
}
