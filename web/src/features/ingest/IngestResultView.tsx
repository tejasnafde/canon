import { Link } from 'react-router-dom'
import { ToneBadge } from '@/components/badges'
import { QuoteBlock, Verified } from '@/components/citation'
import { SectionHead } from '@/components/section-head'
import { Badge } from '@/components/ui/badge'
import { alertTone, plural, relationTone, secs } from '@/lib/format'
import type { IngestResult, ReconciledDecision } from '@/lib/schemas'
import { cn } from '@/lib/utils'

export function IngestResultView({ r, records }: { r: IngestResult; records?: number }) {
  const quotes = r.decisions.reduce((k, d) => k + d.decision.quotes.length, 0)
  return (
    <div className="flex flex-col gap-8 motion-safe:animate-in motion-safe:fade-in-0 motion-safe:slide-in-from-bottom-1 motion-safe:duration-200">
      <div>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <span className="label text-foreground">Result / {r.source.title}</span>
          <span className="label">Gemini structured output</span>
        </div>
        <dl className="grid grid-cols-2 overflow-hidden rounded-lg border bg-card sm:grid-cols-4">
          <Stat label="Decisions" value={String(r.decisions.length)} />
          <Stat label="Quotes verified" value={String(quotes)} of={quotes + r.rejected_quotes} />
          <Stat label="Alerts raised" value={String(r.alerts.length)} hot={r.alerts.length > 0} />
          <Stat label="Latency" value={secs(r.latency_ms)} />
        </dl>
      </div>

      <section aria-labelledby="ex-h">
        <SectionHead id="ex-h" title="Extracted and reconciled" note={records === undefined ? undefined : `Against ${records} decisions on record`} />
        {r.decisions.length === 0 && <p className="py-3 text-muted-foreground">No decisions in this text. Canon stores nothing it cannot quote.</p>}
        <ul className="divide-y">
          {r.decisions.map(d => (
            <DecisionRow key={d.decision.id} d={d} />
          ))}
          {r.rejected_quotes > 0 && (
            <li className="grid grid-cols-[7.5rem_1fr] gap-4 py-4">
              <Badge variant="outline" className="w-full border-dashed border-signal text-signal-ink">
                rejected
              </Badge>
              <p className="text-[15px] text-muted-foreground">
                {plural(r.rejected_quotes, 'extracted claim')} dropped: the quote was not in the source text. Canon never stores a quote it cannot
                match word for word.
              </p>
            </li>
          )}
        </ul>
      </section>

      <section aria-labelledby="al-h">
        <SectionHead id="al-h" title="Alerts raised" />
        {r.alerts.length === 0 ? (
          <p className="py-3 text-muted-foreground">No conflicts with the record.</p>
        ) : (
          <>
            <ul className="divide-y">
              {r.alerts.map(a => (
                <li key={a.id} className="flex flex-wrap items-baseline gap-3 py-3">
                  <ToneBadge tone={alertTone(a.kind)}>{a.kind}</ToneBadge>
                  {a.decision_id ? (
                    <Link className="flex-1 underline-offset-4 hover:underline" to={`/decisions/${a.decision_id}`}>
                      {a.explanation}
                    </Link>
                  ) : (
                    <span className="flex-1">{a.explanation}</span>
                  )}
                  <Badge variant="outline">{a.severity}</Badge>
                </li>
              ))}
            </ul>
            <Link className="mt-2 inline-block text-sm text-link underline-offset-4 hover:underline" to="/">
              See them on Home
            </Link>
          </>
        )}
      </section>
    </div>
  )
}

function Stat({ label, value, of, hot }: { label: string; value: string; of?: number; hot?: boolean }) {
  return (
    <div className="border-r border-b p-4 last:border-r-0 sm:border-b-0">
      <dt className="label">{label}</dt>
      <dd className={cn('mt-1 font-heading text-3xl tnum', hot && 'text-signal-ink')}>
        {value}
        {of !== undefined && <span className="text-xl text-muted-foreground"> / {of}</span>}
      </dd>
    </div>
  )
}

const RELATED: Record<string, string> = { update: 'Supersedes', same: 'Same as', contradiction: 'Conflicts with', new: 'Related to' }

function DecisionRow({ d }: { d: ReconciledDecision }) {
  return (
    <li className="grid grid-cols-[7.5rem_1fr] gap-4 py-4">
      <ToneBadge tone={relationTone(d.relation)} className="w-full">
        {d.relation}
      </ToneBadge>
      <div className="min-w-0">
        <Link to={`/decisions/${d.decision.id}`} className="font-heading text-xl leading-snug underline-offset-4 hover:underline">
          {d.decision.statement}
        </Link>
        {d.explanation && <p className="mt-1 text-[15px] text-muted-foreground">{d.explanation}</p>}
        {d.related_decision_id && (
          <Link className="mt-1 inline-block text-sm text-link underline-offset-4 hover:underline" to={`/decisions/${d.related_decision_id}`}>
            {RELATED[d.relation]} the decision on record
          </Link>
        )}
        {d.decision.quotes.map((qt, i) => (
          <QuoteBlock key={i} quote={qt.quote} tone={d.relation === 'contradiction' ? 'signal' : undefined} className="mt-3 text-base">
            <div className="mt-1.5">
              <Verified />
            </div>
          </QuoteBlock>
        ))}
      </div>
    </li>
  )
}
