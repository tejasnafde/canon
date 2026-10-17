export const SINCE = { '7': 'Last 7 days', '30': 'Last 30 days', all: 'Since day one' } as const
export type Since = keyof typeof SINCE
export const DAY_ONE = '2025-01-01T00:00:00Z' // first day of the Northwind Labs corpus

/** Day-rounded, so the briefing query key stays stable within a day and hits the cache. */
export function sinceIso(s: Since, now = Date.now()) {
  if (s === 'all') return DAY_ONE
  const d = new Date(now - Number(s) * 86_400_000)
  d.setUTCHours(0, 0, 0, 0)
  return d.toISOString()
}
