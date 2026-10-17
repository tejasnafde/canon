// Browser error reporting: fire and forget to /api/client-error. Sampled, deduped, capped, no PII.
import { MOCK } from './api'

const SAMPLE = 0.5
const MAX_PER_SESSION = 10
const seen = new Set<string>()

export interface ClientError {
  message: string
  stack: string
  source: 'onerror' | 'unhandledrejection' | 'boundary' | 'route'
  path: string
}

export function toClientError(err: unknown, source: ClientError['source']): ClientError {
  const e = err instanceof Error ? err : new Error(typeof err === 'string' ? err : 'Unknown error')
  return {
    message: e.message.slice(0, 500),
    stack: (e.stack ?? '').slice(0, 2000),
    source,
    // pathname only: query strings can hold what the user typed
    path: location.pathname,
  }
}

export function reportError(err: unknown, source: ClientError['source'], rand = Math.random): boolean {
  const body = toClientError(err, source)
  if (MOCK || seen.size >= MAX_PER_SESSION || seen.has(body.message) || rand() >= SAMPLE) return false
  seen.add(body.message)
  fetch('/api/client-error', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    keepalive: true,
  }).catch(() => {})
  return true
}

export function installGlobalHandlers() {
  window.addEventListener('error', e => reportError(e.error ?? e.message, 'onerror'))
  window.addEventListener('unhandledrejection', e => reportError(e.reason, 'unhandledrejection'))
}
