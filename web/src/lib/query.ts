import { QueryClient, queryOptions } from '@tanstack/react-query'
import { api, ApiError } from './api'
import type { Persona } from './schemas'

/** 4xx means the request is wrong; retrying will not help. Network errors and 5xx (cold start) get retried. */
export const shouldRetry = (count: number, err: unknown) => count < 3 && !(err instanceof ApiError && err.status >= 400 && err.status < 500)

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: shouldRetry,
      retryDelay: n => Math.min(1000 * 2 ** n, 8000),
      refetchOnWindowFocus: false,
    },
    mutations: { retry: 0 },
  },
})

// Gemini-backed reads are slow and cost money: cache them for the session and retry once.
const llm = { staleTime: 5 * 60_000, gcTime: 30 * 60_000, retry: (n: number, e: unknown) => n < 1 && shouldRetry(n, e) }

export const q = {
  health: () => queryOptions({ queryKey: ['health'], queryFn: api.health, staleTime: 60_000, retry: 6 }),
  activity: () => queryOptions({ queryKey: ['activity'], queryFn: api.activity, refetchInterval: 2000, staleTime: 0 }),
  alerts: () => queryOptions({ queryKey: ['alerts'], queryFn: api.alerts, refetchInterval: 10_000 }),
  decisions: () => queryOptions({ queryKey: ['decisions'], queryFn: api.decisions }),
  decision: (id: string) => queryOptions({ queryKey: ['decision', id], queryFn: () => api.decision(id) }),
  briefing: (persona: Persona, since: string) =>
    queryOptions({ queryKey: ['briefing', persona, since], queryFn: () => api.briefing(persona, since), ...llm }),
  ask: (question: string) => queryOptions({ queryKey: ['ask', question], queryFn: () => api.ask(question), ...llm }),
  source: (id: string) => queryOptions({ queryKey: ['source', id], queryFn: () => api.source(id), staleTime: 30 * 60_000 }),
  people: () => queryOptions({ queryKey: ['people'], queryFn: api.people, staleTime: 10 * 60_000 }),
  check: (intent: string) => queryOptions({ queryKey: ['check', intent], queryFn: () => api.check(intent), ...llm }),
  evalReport: () => queryOptions({ queryKey: ['eval'], queryFn: api.evalReport, staleTime: 10 * 60_000 }),
}

/** After anything that writes to the record. */
export const invalidateRecord = () =>
  Promise.all([['alerts'], ['decisions'], ['decision'], ['activity'], ['briefing']].map(queryKey => queryClient.invalidateQueries({ queryKey })))
