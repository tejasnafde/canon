import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { Avatar, Bar, ErrorState, TextSkeleton } from '@/components/states'
import { q } from '@/lib/query'
import { actorName, fmtDate, fmtLong, quoteFrom, ruleOf, srcLine } from '@/lib/record'
import type { Alert, DecisionDetail } from '@/lib/schemas'
import { useTitle } from '@/lib/title'

const VERDICT = { allow: 'Allow', warn: 'Warn', block: 'Block' } as const

export default function DecisionPage() {
  const { id = '' } = useParams()
  const detail = useQuery(q.decision(id))
  useTitle(detail.data?.decision.statement ?? 'decision')

  return (
    <main className="wrap">
      <Link to="/decisions" className="back">
        &larr; All decisions
      </Link>
      {detail.isError ? (
        <ErrorState error={detail.error} retry={() => void detail.refetch()} title="This decision did not load." />
      ) : detail.isPending ? (
        <div role="status" aria-label="Loading the decision" aria-busy="true" style={{ marginTop: 20 }}>
          <Bar w={220} h={16} />
          <Bar w="80%" h={44} style={{ marginTop: 16 }} />
          <Bar w="55%" h={44} style={{ marginTop: 10 }} />
          <div style={{ marginTop: 40 }}>
            <TextSkeleton lines={4} />
          </div>
        </div>
      ) : (
        <Detail d={detail.data} />
      )}
    </main>
  )
}

function Detail({ d }: { d: DecisionDetail }) {
  const dec = d.decision
  const people = useQuery(q.people())
  const activity = useQuery(q.activity())
  const role = people.data?.find(p => p.name === dec.owner)?.role.toLowerCase()
  const where = d.sources.find(s => s.id === dec.quotes[0]?.source_id)
  const breaking = d.alerts.filter(a => a.status === 'open' && ruleOf(a) === dec.id)
  const replaces = d.timeline.filter(t => dec.supersedes.includes(t.decision_id))
  const replacedBy = dec.superseded_by ? d.timeline.find(t => t.decision_id === dec.superseded_by) : undefined
  const checks = (activity.data ?? []).filter(a => a.ref_ids.includes(dec.id)).slice(0, 6)

  const status =
    dec.status !== 'active' ? (
      <>{dec.status === 'superseded' ? 'Replaced by a newer decision' : 'Retired'}</>
    ) : breaking.length ? (
      <span className="breaks">
        <span className="dot" aria-hidden />
        Active, but {breaking.length === 1 ? 'one thing breaks' : `${breaking.length} things break`} it
      </span>
    ) : (
      <>Active. Nothing on record goes against it.</>
    )

  return (
    <>
      <p className="status">{status}</p>
      <h1 className="statement">{dec.statement}</h1>
      <div className="facts">
        <div>
          <span className="label">Owner</span>
          <span className="person">
            <Avatar name={dec.owner} small />
            {dec.owner}
            {role ? `, ${role}` : ''}
          </span>
        </div>
        <div>
          <span className="label">Decided</span>
          {fmtLong(dec.ts)}
        </div>
        {where && (
          <div>
            <span className="label">Where</span>
            {where.title}
          </div>
        )}
        {replaces.length > 0 && (
          <div>
            <span className="label">Replaces</span>
            {replaces.map(t => (
              <Link key={t.decision_id} to={`/decisions/${t.decision_id}`} style={{ display: 'block', maxWidth: '32ch' }}>
                {t.statement}
              </Link>
            ))}
          </div>
        )}
        {replacedBy && (
          <div>
            <span className="label">Replaced by</span>
            <Link to={`/decisions/${replacedBy.decision_id}`} style={{ display: 'block', maxWidth: '32ch' }}>
              {replacedBy.statement}
            </Link>
          </div>
        )}
      </div>

      <div className="split section">
        <div>
          <div className="why">
            <h2>Why</h2>
            <p style={{ marginTop: 14 }}>{dec.rationale || 'The record gives no reason.'}</p>
            {dec.quotes.map((qt, i) => (
              <div key={i}>
                <blockquote className="q" style={{ marginTop: 18 }}>
                  "{qt.quote}"
                </blockquote>
                {d.sources.find(s => s.id === qt.source_id) && (
                  <p className="src" style={{ paddingLeft: 17 }}>
                    {srcLine(d.sources.find(s => s.id === qt.source_id) ?? { kind: 'doc', title: '', ts: dec.ts })},{' '}
                    {d.sources.find(s => s.id === qt.source_id)?.author}
                  </p>
                )}
              </div>
            ))}
            {dec.assumptions.length > 0 && (
              <p className="muted" style={{ marginTop: 18, fontSize: 16 }}>
                It holds while: {dec.assumptions.join(' ')}
              </p>
            )}
          </div>

          <h2 style={{ marginTop: 56 }}>What breaks it now</h2>
          {breaking.length === 0 ? (
            <p className="muted" style={{ marginTop: 14 }}>
              Nothing open. Canon checks every new message, document and agent action against this decision.
            </p>
          ) : (
            <ul className="list breaks-list" style={{ marginTop: 20 }}>
              {breaking.map(a => (
                <Breaker key={a.id} a={a} />
              ))}
            </ul>
          )}
        </div>

        <aside>
          <h2>Timeline</h2>
          <ul className="tl" style={{ marginTop: 16 }}>
            {d.timeline.map((t, i) => (
              <li key={`${t.decision_id}-${i}`} className={t.decision_id === dec.id ? 'key' : t.status !== 'active' ? 'old' : undefined}>
                <span className="when">{fmtDate(t.ts)}</span>
                <span>{t.decision_id === dec.id ? t.statement : <Link to={`/decisions/${t.decision_id}`}>{t.statement}</Link>}</span>
              </li>
            ))}
            {breaking.map(a => (
              <li key={a.id} className="bad">
                <span className="when">{fmtDate(a.created_at)}</span>
                <span>
                  {a.kind === 'stale_doc'
                    ? 'A document still says the old rule.'
                    : a.kind === 'premise_changed'
                      ? 'A reason behind it may no longer hold.'
                      : 'Something goes against it.'}
                </span>
              </li>
            ))}
          </ul>

          {checks.length > 0 ? (
            <>
              <h2 style={{ marginTop: 48 }}>Recent checks</h2>
              <ul className="tl" style={{ marginTop: 16 }}>
                {checks.map(c => (
                  <li key={c.id}>
                    <span className="when">{fmtDate(c.created_at)}</span>
                    <span>
                      {actorName(c.actor)}:{' '}
                      <span className={c.verdict === 'block' ? 'breaks' : undefined}>{c.verdict ? VERDICT[c.verdict] : c.action}</span>.{' '}
                      <span className="muted">{c.summary.replace(/^Checked:\s*/, '')}</span>
                    </span>
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className="small muted" style={{ marginTop: 24 }}>
              When an AI agent or a Discord member checks an action against this decision, the check appears here.{' '}
              <Link to="/agent">See how agents use Canon</Link>.
            </p>
          )}
        </aside>
      </div>
    </>
  )
}

function Breaker({ a }: { a: Alert }) {
  const src = useQuery({ ...q.source(a.source_id ?? ''), enabled: !!a.source_id })
  const quote = quoteFrom(a, a.source_id)
  const doc = a.kind === 'stale_doc'
  const title = src.data?.title
  return (
    <li className={doc ? 'doc' : undefined}>
      <h3>
        <span className={doc ? 'dot hollow' : 'dot'} aria-hidden />
        {src.isPending && a.source_id ? (
          <Bar w="50%" h={20} style={{ display: 'inline-block' }} />
        ) : doc ? (
          `${title ?? 'A document'} still gives the old rule.`
        ) : a.kind === 'premise_changed' ? (
          `${title ?? 'New information'} may change the reason behind it.`
        ) : (
          `${title ?? 'A new message'} goes against it.`
        )}
      </h3>
      {quote && <blockquote className="q">"{quote}"</blockquote>}
      <p>{a.explanation}</p>
      {src.data && (
        <p className="src">
          {srcLine(src.data)}, {src.data.author}
          {doc ? '. Out of date.' : ''}
        </p>
      )}
    </li>
  )
}
