import { useSuspenseQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { ToneBadge } from '@/components/badges'
import { QuoteBlock, SourceChip, Verified } from '@/components/citation'
import { Section } from '@/components/error-boundary'
import { SectionHead } from '@/components/section-head'
import { EmptyState, RowsSkeleton } from '@/components/states'
import { Badge } from '@/components/ui/badge'
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb'
import { Skeleton } from '@/components/ui/skeleton'
import { fmtDate } from '@/lib/format'
import { q } from '@/lib/query'
import type { DecisionDetail } from '@/lib/schemas'
import { cn } from '@/lib/utils'
import { ConflictCard } from './ConflictCard'

export default function DecisionPage() {
  const { id = '' } = useParams()
  return (
    <main className="mx-auto max-w-[1440px] px-4 pt-6 pb-12 md:px-8">
      <Section key={id} fallback={<DetailSkeleton />}>
        <Detail id={id} />
      </Section>
    </main>
  )
}

function Detail({ id }: { id: string }) {
  const { data } = useSuspenseQuery(q.decision(id))
  return (
    <>
      <Breadcrumb>
        <BreadcrumbList className="text-[15px]">
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link to="/decisions">Decisions</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>{data.decision.topic}</BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage className="font-mono text-sm">{id}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      <Body d={data} />
    </>
  )
}

function Body({ d }: { d: DecisionDetail }) {
  const dec = d.decision
  const src = (sid: string | null) => d.sources.find(s => s.id === sid)
  const open = d.alerts.filter(a => a.status === 'open')
  const premise = open.some(a => a.kind === 'premise_changed')
  return (
    <div className="mt-5 grid gap-10 lg:grid-cols-[minmax(0,1fr)_420px]">
      <article className="min-w-0">
        <div className="mb-4 flex flex-wrap gap-2">
          <Badge variant={dec.status === 'active' ? 'ok' : 'outline'}>{dec.status}</Badge>
          {dec.version > 1 && (
            <Badge variant="outline">
              v{dec.version} / supersedes {dec.supersedes.length}
            </Badge>
          )}
          <Badge variant="outline">recorded by {dec.created_by}</Badge>
        </div>
        <h1 className="text-[34px] leading-[1.12] font-medium text-balance md:text-[40px]">{dec.statement}</h1>
        {dec.superseded_by && (
          <p className="mt-3">
            Superseded by{' '}
            <Link className="text-link underline underline-offset-4" to={`/decisions/${dec.superseded_by}`}>
              a newer decision
            </Link>
            .
          </p>
        )}
        <dl className="mt-6 grid grid-cols-2 border-y sm:grid-cols-4">
          {(
            [
              ['Owner', dec.owner],
              ['Decided', fmtDate(dec.ts)],
              ['Topic', dec.topic],
              ['Open alerts', String(open.length)],
            ] as const
          ).map(([k, v]) => (
            <div key={k} className="border-r px-4 py-3 last:border-r-0 first:pl-0">
              <dt className="label">{k}</dt>
              <dd className="mt-1 font-medium tnum">{v}</dd>
            </div>
          ))}
        </dl>

        {d.timeline.length > 0 && (
          <section className="mt-8" aria-labelledby="tl-h">
            <h2 id="tl-h" className="label mb-3 font-sans text-foreground">
              How it evolved
            </h2>
            <ol className="grid gap-3 sm:grid-cols-[repeat(auto-fit,minmax(200px,1fr))]">
              {d.timeline.map((t, i) => {
                const current = t.decision_id === dec.id && t.status === 'active'
                return (
                  <li key={i}>
                    <Link
                      to={`/decisions/${t.decision_id}`}
                      aria-current={current ? 'page' : undefined}
                      className={cn(
                        'block h-full rounded-md border-t-4 bg-card p-3 transition-colors duration-150 hover:bg-accent',
                        t.relation === 'contradiction' ? 'border-signal' : current ? 'border-foreground' : 'border-border',
                      )}
                    >
                      <span className="label">
                        {fmtDate(t.ts)}
                        {t.relation && ` / ${t.relation}`}
                      </span>
                      <p
                        className={cn(
                          'mt-1 text-[15px] leading-snug',
                          t.status === 'superseded' && 'text-muted-foreground line-through decoration-1',
                        )}
                      >
                        {t.statement}
                      </p>
                    </Link>
                  </li>
                )
              })}
            </ol>
          </section>
        )}

        <div className="mt-10 grid gap-10 md:grid-cols-2">
          <section aria-labelledby="why-h">
            <SectionHead id="why-h" title="Why" />
            <p className="mt-3">{dec.rationale || 'No rationale was recorded.'}</p>
          </section>
          <section aria-labelledby="as-h">
            <SectionHead id="as-h" title="Assumptions" note="Canon watches these" />
            {dec.assumptions.length === 0 ? (
              <p className="mt-3 text-muted-foreground">None recorded.</p>
            ) : (
              <ul className="mt-2 divide-y">
                {dec.assumptions.map(a => (
                  <li key={a} className="py-2">
                    {a}
                  </li>
                ))}
              </ul>
            )}
            {premise && (
              <p className="mt-3 flex items-center gap-2 text-[15px]">
                <ToneBadge tone="warn">premise changed</ToneBadge> See the alert beside this.
              </p>
            )}
          </section>
        </div>

        <section className="mt-10" aria-labelledby="q-h">
          <SectionHead id="q-h" title="Verified quotes" note="Each one matched word for word in its source" />
          <div className="mt-4 flex flex-col gap-6">
            {dec.quotes.length === 0 && <p className="text-muted-foreground">No quotes stored.</p>}
            {dec.quotes.map((qt, i) => {
              const s = src(qt.source_id)
              return (
                <QuoteBlock key={i} quote={qt.quote}>
                  {s && (
                    <div className="mt-2 flex flex-wrap items-center gap-2 font-sans text-sm">
                      <Verified />
                      <SourceChip kind={s.kind} title={s.title} date={s.ts} />
                      <span className="text-muted-foreground">{s.author}</span>
                    </div>
                  )}
                </QuoteBlock>
              )
            })}
          </div>
        </section>
      </article>

      <aside className="flex flex-col gap-5" aria-label="Conflicts">
        {d.alerts.length === 0 ? (
          <EmptyState title="No conflicts">Nothing on record disagrees with this decision.</EmptyState>
        ) : (
          d.alerts.map(a => <ConflictCard key={a.id} a={a} decisionId={dec.id} src={src} recordQuote={dec.quotes[0]?.quote} />)
        )}
      </aside>
    </div>
  )
}

function DetailSkeleton() {
  return (
    <div className="mt-8 grid gap-10 lg:grid-cols-[minmax(0,1fr)_420px]" role="status" aria-label="Loading the decision">
      <div className="flex flex-col gap-4">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-4/5" />
        <RowsSkeleton rows={4} className="mt-6" />
      </div>
      <Skeleton className="h-72 w-full" />
    </div>
  )
}
