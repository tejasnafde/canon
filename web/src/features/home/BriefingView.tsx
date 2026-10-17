import { useSuspenseQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { PriorityScore, ToneBadge } from '@/components/badges'
import { CitationLine, QuoteBlock } from '@/components/citation'
import { SectionHead } from '@/components/section-head'
import { EmptyState } from '@/components/states'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { fmtDate, reasonTone, secs } from '@/lib/format'
import { q } from '@/lib/query'
import type { Action, Persona, Person } from '@/lib/schemas'
import { cn } from '@/lib/utils'
import { SINCE, sinceIso, type Since } from './since'

export function BriefingView({ persona, since, stale }: { persona: Persona; since: Since; stale: boolean }) {
  const { data: br } = useSuspenseQuery(q.briefing(persona, sinceIso(since)))
  const actions = [...br.actions].sort((x, y) => y.priority - x.priority)
  return (
    <div className={cn('flex flex-col gap-10 transition-opacity duration-200', stale && 'opacity-60')} aria-busy={stale}>
      <Card className="py-0">
        <CardContent className="grid gap-0 px-0 md:grid-cols-[1.3fr_1fr]">
          <div className="p-6 md:border-r">
            <div className="mb-3 flex items-center justify-between">
              <span className="label text-foreground">Briefing / {SINCE[since]}</span>
              <span className="label tnum">{stale ? 'updating' : secs(br.latency_ms)}</span>
            </div>
            <p className="font-heading text-[22px] leading-snug text-pretty">{br.summary}</p>
          </div>
          <div className="p-6">
            <p className="label mb-2">Highlights</p>
            {br.highlights.length === 0 ? (
              <p className="text-muted-foreground">Nothing new in this window.</p>
            ) : (
              <ol className="divide-y">
                {br.highlights.map((h, i) => (
                  <li key={i} className="grid grid-cols-[2rem_1fr] py-2.5 text-[15px]">
                    <span className="font-mono text-xs text-muted-foreground tnum">{String(i + 1).padStart(2, '0')}</span>
                    {h}
                  </li>
                ))}
              </ol>
            )}
          </div>
        </CardContent>
      </Card>

      {persona === 'new_hire' && br.who_to_ask.length > 0 && <PeopleToAsk people={br.who_to_ask} />}

      <section aria-labelledby="actions-h">
        <SectionHead id="actions-h" title="Next best actions" note="Ranked 0 to 100" />
        {actions.length === 0 ? (
          <EmptyState title="No actions">The record and your work agree. Nothing needs you now.</EmptyState>
        ) : (
          <ol className="divide-y">
            {actions.map((a, i) => (
              <ActionRow key={`${a.title}-${i}`} a={a} top={i === 0} />
            ))}
          </ol>
        )}
      </section>
    </div>
  )
}

function PeopleToAsk({ people }: { people: Person[] }) {
  return (
    <section aria-labelledby="people-h">
      <SectionHead id="people-h" title="People to ask" note="From who decided what" />
      <ul className="grid gap-3 sm:grid-cols-2">
        {people.map(p => (
          <li key={p.id} className="flex items-center justify-between gap-3 rounded-lg border bg-card px-4 py-3">
            <div className="min-w-0">
              <p className="font-medium">{p.name}</p>
              <p className="truncate text-sm text-muted-foreground">
                {p.role} / {p.team}
              </p>
            </div>
            {p.status === 'left' ? <Badge variant="warn">left {p.left_at ? fmtDate(p.left_at) : ''}</Badge> : <Badge variant="ok">active</Badge>}
          </li>
        ))}
      </ul>
    </section>
  )
}

const CHIP: Record<Action['chip'], string> = {
  open_source: 'Open source',
  view_decision: 'View decision',
  resolve_alert: 'Resolve alert',
  ask_person: 'Ask why',
  draft_reply: 'Draft reply',
}

function ActionRow({ a, top }: { a: Action; top: boolean }) {
  const dec = a.citations.find(c => c.decision_id)?.decision_id
  const to = dec && a.chip !== 'ask_person' ? `/decisions/${dec}` : `/ask?q=${encodeURIComponent(a.title)}`
  const cite = a.citations[0]
  return (
    <li
      className={cn(
        'grid grid-cols-[4rem_1fr] gap-x-5 gap-y-3 py-5 sm:grid-cols-[4rem_1fr_auto]',
        top && 'rounded-lg bg-card px-4 ring-1 ring-signal/30',
      )}
    >
      <PriorityScore priority={a.priority} top={top} />
      <div className="min-w-0">
        <h3 className="text-xl font-medium">{a.title}</h3>
        <p className="mt-1 text-muted-foreground">{a.why}</p>
        {/* design review: two reasons max */}
        {a.reasons.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2">
            {a.reasons.slice(0, 2).map(r => (
              <ToneBadge key={r} tone={reasonTone(r)}>
                {r}
              </ToneBadge>
            ))}
          </div>
        )}
        {cite && (
          <QuoteBlock quote={cite.quote} className="mt-3 text-base">
            <CitationLine c={cite} />
          </QuoteBlock>
        )}
      </div>
      <Button variant={top ? 'default' : 'outline'} size="sm" asChild className="col-start-2 justify-self-start sm:col-start-3 sm:justify-self-end">
        <Link to={to}>{CHIP[a.chip]}</Link>
      </Button>
    </li>
  )
}
