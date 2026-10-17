import type {
  Activity, Alert, AskResult, Briefing, CheckResult, Decision, DecisionDetail, EvalReport,
  IngestResult, Person, Persona, ResolveAction, Source,
} from './types'

export const MOCK = import.meta.env.VITE_MOCK === '1'

export function workspace(): string {
  let ws = localStorage.getItem('canon-ws')
  if (!ws || !/^v-[A-Za-z0-9-]{1,64}$/.test(ws)) {
    ws = 'v-' + crypto.randomUUID()
    localStorage.setItem('canon-ws', ws)
  }
  return ws
}

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message) }
}

async function call<T>(method: 'GET' | 'POST', path: string, body?: unknown): Promise<T> {
  if (MOCK) return (await import('./mock')).mockApi(method, path, body) as Promise<T>
  const res = await fetch(path, {
    method,
    headers: { 'X-Canon-Workspace': workspace(), ...(body ? { 'Content-Type': 'application/json' } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    let detail = res.statusText
    try { const j = await res.json(); detail = j.detail ? `${j.error}: ${typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail)}` : j.error ?? detail } catch { /* not JSON */ }
    throw new ApiError(res.status, `${res.status} ${detail}`)
  }
  return res.json()
}

export const api = {
  health: () => call<{ ok: boolean; model: string }>('GET', '/healthz'),
  ingest: (source: Source) => call<IngestResult>('POST', '/api/ingest', { source }),
  ask: (question: string) => call<AskResult>('POST', '/api/ask', { question }),
  briefing: (persona: Persona, since: string) => call<Briefing>('POST', '/api/briefing', { persona, since }),
  check: (intent: string) => call<CheckResult>('POST', '/api/check', { intent }),
  decisions: () => call<Decision[]>('GET', '/api/decisions'),
  decision: (id: string) => call<DecisionDetail>('GET', `/api/decisions/${encodeURIComponent(id)}`),
  alerts: () => call<Alert[]>('GET', '/api/alerts?status=open'),
  resolve: (id: string, action: ResolveAction) => call<Alert>('POST', `/api/alerts/${encodeURIComponent(id)}/resolve`, { action }),
  activity: () => call<Activity[]>('GET', '/api/activity'),
  people: () => call<Person[]>('GET', '/api/people'),
  evalReport: () => call<EvalReport>('GET', '/api/eval'),
  reset: () => call<{ ok: boolean }>('POST', '/api/workspace/reset'),
}
