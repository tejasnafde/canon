import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ToneBadge } from '@/components/badges'
import { SectionHead } from '@/components/section-head'
import { EmptyState, ErrorState, RowsSkeleton } from '@/components/states'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ago, alertTone, fmtDate } from '@/lib/format'
import { q } from '@/lib/query'
import type { Alert } from '@/lib/schemas'
import { cn } from '@/lib/utils'

export function AlertsList() {
  const alerts = useQuery(q.alerts())
  const [all, setAll] = useState(false)
  const list = alerts.data && [...alerts.data].sort((x, y) => y.created_at.localeCompare(x.created_at))
  return (
    <section aria-labelledby="alerts-h">
      <SectionHead id="alerts-h" title="Open drift alerts" note="Docs and work that disagree with the record" count={list?.length} />
      {alerts.isPending ? (
        <RowsSkeleton rows={3} />
      ) : !list ? (
        <ErrorState error={alerts.error} retry={() => void alerts.refetch()} />
      ) : list.length === 0 ? (
        <EmptyState
          title="No open alerts"
          action={
            <Button size="sm" variant="outline" asChild>
              <Link to="/ingest">Test the drift check in Ingest</Link>
            </Button>
          }
        >
          Nothing on record disagrees right now.
        </EmptyState>
      ) : (
        <>
          <ul className="divide-y">
            {(all ? list : list.slice(0, CAP)).map(a => (
              <AlertRow key={a.id} a={a} />
            ))}
          </ul>
          {list.length > CAP && (
            <Button size="sm" variant="outline" className="mt-2" onClick={() => setAll(v => !v)} aria-expanded={all}>
              {all ? 'Show fewer' : `Show all ${list.length}`}
            </Button>
          )}
        </>
      )}
    </section>
  )
}

const CAP = 5
const HOUR = 3_600_000

/** Relative only inside the last hour; older alerts get a date so equal stamps do not look like a bug. */
const stamp = (iso: string) => (Date.now() - new Date(iso).getTime() < HOUR ? ago(iso) : fmtDate(iso))

const BAR = { high: 'bg-signal', medium: 'bg-signal/50', low: 'bg-warn-ink/60' } as const

function AlertRow({ a }: { a: Alert }) {
  return (
    <li className="grid grid-cols-[4px_1fr] gap-4 py-4 motion-safe:animate-in motion-safe:fade-in-0 motion-safe:duration-200">
      <span className={cn('rounded-full', BAR[a.severity])} aria-hidden />
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <ToneBadge tone={alertTone(a.kind)}>{a.kind}</ToneBadge>
          <Badge variant="outline">{a.severity}</Badge>
          <span className="label ml-auto">{stamp(a.created_at)}</span>
        </div>
        <p className="mt-2">{a.explanation}</p>
        <div className="mt-1 flex flex-wrap gap-x-5 gap-y-1 text-sm">
          {a.decision_id && (
            <Link className="text-link underline-offset-4 hover:underline" to={`/decisions/${a.decision_id}`}>
              Open the decision
            </Link>
          )}
          {a.related_decision_id && (
            <Link className="text-link underline-offset-4 hover:underline" to={`/decisions/${a.related_decision_id}`}>
              Open the decision it conflicts with
            </Link>
          )}
        </div>
      </div>
    </li>
  )
}
