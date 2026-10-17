import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Avatar, Bar, ErrorState, ListSkeleton, TextSkeleton } from '@/components/states'
import { q } from '@/lib/query'
import { breaksByDecision, fmtDate, fmtLong, quoteFrom, rankDecisions, srcLine } from '@/lib/record'
import type { Alert, Decision, Person } from '@/lib/schemas'
import { useTitle } from '@/lib/title'

const DAY_ONE = '2025-01-01T00:00:00Z'

/** The topics a person owns decisions on, most first. */
function topicsOf(name: string, decisions: Decision[], n = 3) {
  const count = new Map<string, number>()
  for (const d of decisions) if (d.owner === name && d.status === 'active') count.set(d.topic, (count.get(d.topic) ?? 0) + 1)
  return [...count.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, n)
    .map(([t]) => t)
}

export default function NewHirePage() {
  useTitle('I am new here')
  const decisions = useQuery(q.decisions())
  const alerts = useQuery(q.alerts())
  const people = useQuery(q.people())
  const briefing = useQuery(q.briefing('new_hire', DAY_ONE))

  const breaks = alerts.data ? breaksByDecision(alerts.data) : new Map<string, Alert[]>()
  const ranked = decisions.data
    ? rankDecisions(
        decisions.data.filter(d => d.status === 'active'),
        breaks,
      )
    : []
  const seen = new Set<string>()
  const must = ranked.filter(d => !seen.has(d.topic) && seen.add(d.topic)).slice(0, 5)
  const stale = alerts.data
    ?.filter(a => a.kind === 'stale_doc' && a.source_id)
    .sort((a, b) => (breaks.get(b.decision_id ?? '')?.length ?? 0) - (breaks.get(a.decision_id ?? '')?.length ?? 0))[0]
  const left = people.data?.filter(p => p.status === 'left') ?? []

  return (
    <main className="wrap">
      <Link to="/" className="back">
        &larr; Stories
      </Link>
      <h1 style={{ marginTop: 16 }}>Welcome to Northwind Labs.</h1>
      <p className="lede">
        Canon read two years of company history so you do not have to. These are the things that will get you in trouble if you do not know them, and
        a document you should not trust.
      </p>

      <div style={{ marginTop: 40 }}>
        {alerts.isError ? (
          <ErrorState error={alerts.error} retry={() => void alerts.refetch()} />
        ) : stale ? (
          <StaleFlag alert={stale} rule={decisions.data?.find(d => d.id === stale.decision_id)} />
        ) : alerts.isPending ? (
          <div className="flag">
            <TextSkeleton lines={3} label="Loading the out-of-date document" />
          </div>
        ) : null}
      </div>

      <div className="split section">
        <div>
          <h2>{must.length || 5} things you must know</h2>
          {decisions.isError ? (
            <ErrorState error={decisions.error} retry={() => void decisions.refetch()} />
          ) : decisions.isPending || alerts.isPending ? (
            <ListSkeleton rows={5} />
          ) : (
            <ol className="list must">
              {must.map((d, i) => (
                <li key={d.id}>
                  <span className="n">{i + 1}</span>
                  <div>
                    <h3>
                      <Link to={`/decisions/${d.id}`} style={{ textDecoration: 'none' }}>
                        {d.statement}
                      </Link>
                    </h3>
                    {d.rationale && <p>{d.rationale}</p>}
                    <SourceLine id={d.quotes[0]?.source_id} />
                  </div>
                </li>
              ))}
            </ol>
          )}
          <p className="small muted" style={{ marginTop: 16 }}>
            Ranked by how often something at Northwind still goes against the rule.
          </p>
        </div>

        <aside>
          <h2>People to ask</h2>
          {briefing.isError ? (
            <ErrorState error={briefing.error} retry={() => void briefing.refetch()} />
          ) : briefing.isPending ? (
            <ListSkeleton rows={4} label="Finding people to ask" />
          ) : (
            <ul className="people">
              {briefing.data.who_to_ask.map(p => (
                <PersonRow key={p.id} person={p}>
                  {decisions.data && topicsOf(p.name, decisions.data).join(', ')}
                </PersonRow>
              ))}
            </ul>
          )}
          {left.length > 0 && (
            <>
              <h2 style={{ marginTop: 48 }}>People who left</h2>
              <ul className="people">
                {left.map(p => {
                  const owned = decisions.data?.filter(d => d.owner === p.name).length ?? 0
                  const topic = decisions.data ? topicsOf(p.name, decisions.data, 1)[0] : undefined
                  return (
                    <PersonRow key={p.id} person={p} note={p.left_at ? `left ${fmtLong(p.left_at).replace(/^\d+ /, '')}` : 'left'}>
                      {owned > 0 ? (
                        <>
                          Canon kept {owned} of {p.name.split(' ')[0]}'s decisions in their own words.{' '}
                          {topic && <Link to={`/ask?q=${encodeURIComponent(`What did ${p.name} decide about ${topic}, and why?`)}`}>Ask why</Link>}
                        </>
                      ) : (
                        'No decisions on record.'
                      )}
                    </PersonRow>
                  )
                })}
              </ul>
            </>
          )}
        </aside>
      </div>
    </main>
  )
}

function PersonRow({ person, note, children }: { person: Person; note?: string; children?: React.ReactNode }) {
  return (
    <li>
      <Avatar name={person.name} />
      <div>
        <b>{person.name}</b>,{' '}
        <span className="role">
          {person.role.toLowerCase()}
          {note ? `, ${note}` : ''}
        </span>
        {children && <p>{children}</p>}
      </div>
    </li>
  )
}

function SourceLine({ id, prefix = '' }: { id: string | undefined; prefix?: string }) {
  const src = useQuery({ ...q.source(id ?? ''), enabled: !!id })
  if (!id || src.isError) return null
  return <p className="src">{src.data ? prefix + srcLine(src.data) : <Bar w="40%" h={14} />}</p>
}

function StaleFlag({ alert, rule }: { alert: Alert; rule: Decision | undefined }) {
  const doc = useQuery(q.source(alert.source_id ?? ''))
  const said = quoteFrom(alert, alert.source_id)
  if (doc.isPending) return <TextSkeleton lines={3} label="Loading the out-of-date document" />
  const title = doc.data?.title ?? 'This document'
  return (
    <div className="flag">
      <h3>The {title} page is out of date. Do not follow it.</h3>
      {said && (
        <p style={{ marginTop: 8 }}>
          The page still says <q>{said}</q>
        </p>
      )}
      {rule && (
        <p style={{ marginTop: 8 }}>
          The team decided otherwise on {fmtLong(rule.ts)}: <q>{rule.quotes[0]?.quote ?? rule.statement}</q>
        </p>
      )}
      <p className="src">
        {doc.data ? srcLine(doc.data) : ''}
        {rule ? `. Overruled on ${fmtDate(rule.ts)}, owner ${rule.owner}.` : ''}
      </p>
    </div>
  )
}
