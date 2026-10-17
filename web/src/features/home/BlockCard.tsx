import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { newestFirst } from '@/components/activity-feed'
import { VerdictBadge } from '@/components/badges'
import { SourceChip } from '@/components/citation'
import { ago, fmtDate, isDecisionId } from '@/lib/format'
import { q } from '@/lib/query'
import type { Activity } from '@/lib/schemas'

/** The most recent agent block: the moment Canon stopped an agent breaking a decision. Shown first on Home. */
export function BlockCard() {
  const feed = useQuery(q.activity())
  const block = feed.data && newestFirst(feed.data).find(a => a.verdict === 'block' && a.actor.startsWith('agent:'))
  return block ? <Card key={block.id} a={block} /> : null
}

function Card({ a }: { a: Activity }) {
  const id = a.ref_ids[0]
  const detail = useQuery({ ...q.decision(id ?? ''), enabled: isDecisionId(id) })
  const d = detail.data?.decision
  const src = d && detail.data?.sources.find(s => s.id === d.quotes[0]?.source_id)
  return (
    <section
      aria-label="Latest agent block"
      className="overflow-hidden rounded-lg border-2 border-signal bg-card motion-safe:animate-in motion-safe:fade-in-0 motion-safe:slide-in-from-top-1 motion-safe:duration-200"
    >
      <div className="flex flex-wrap items-center gap-3 bg-signal px-5 py-2.5 text-white">
        <VerdictBadge verdict="block" className="bg-white text-signal-ink dark:text-[#a82710]" />
        <span className="font-mono text-xs tracking-[0.08em] uppercase">
          Agent blocked / {a.actor.slice(6)} / {ago(a.created_at)}
        </span>
      </div>
      <div className="flex flex-col gap-4 p-5">
        <h2 className="text-[22px] leading-snug font-medium">{a.summary}</h2>
        {a.explanation && <p className="text-muted-foreground">{a.explanation}</p>}
        {id && (
          <div>
            <p className="label mb-2">Deciding decision</p>
            <div className="border-l-2 border-signal pl-4">
              {isDecisionId(id) ? (
                <Link to={`/decisions/${id}`} className="font-heading text-lg underline underline-offset-4 hover:text-signal-ink">
                  {d?.statement ?? a.ref_titles[0] ?? id}
                </Link>
              ) : (
                <span className="font-heading text-lg">{a.ref_titles[0] ?? id}</span>
              )}
              {d && (
                <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                  <span>
                    {d.owner} / {fmtDate(d.ts)}
                  </span>
                  {src && <SourceChip kind={src.kind} title={src.title} />}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
