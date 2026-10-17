import { useMutation, useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bar, ErrorState } from '@/components/states'
import { api } from '@/lib/api'
import { invalidateRecord, q } from '@/lib/query'
import { fmtLong, quoteFrom, secs, srcLine } from '@/lib/record'
import type { Alert, Decision, IngestResult, Reconciliation } from '@/lib/schemas'
import { useTitle } from '@/lib/title'
import samples from '@/samples/live_paste.json'

const SAMPLE_LABEL: Record<string, string> = {
  'friday-contradiction': 'Friday deploy job',
  'timeout-update': 'New timeout setting',
  'new-label-policy': 'New label supplier',
}

const RELATION: Record<Reconciliation, string> = {
  new: 'Something new. Nothing on record covers it yet.',
  same: 'Already on record. Canon added this as more evidence.',
  update: 'Replaces an older decision.',
  contradiction: 'Goes against a decision that is still active.',
}

export default function PastePage() {
  useTitle('paste a message and see what it breaks')
  const decisions = useQuery(q.decisions())
  const [pick, setPick] = useState(samples[0]?.key ?? '')
  const [text, setText] = useState(samples[0]?.source.text ?? '')
  const sample = samples.find(s => s.key === pick)
  const run = useMutation({
    mutationFn: () => {
      const base = sample?.source
      return api.ingest({
        kind: 'paste',
        title: base && base.text === text ? base.title : 'Pasted message',
        author: base && base.text === text ? base.author : 'Visitor',
        ts: new Date().toISOString(),
        text,
        synthetic: true,
      })
    },
    onSuccess: () => void invalidateRecord(),
  })
  const n = decisions.data?.length

  return (
    <main className="wrap">
      <Link to="/" className="back">
        &larr; Stories
      </Link>
      <h1 style={{ marginTop: 16 }}>Paste a new message and see what it breaks.</h1>
      <p className="lede">
        A Slack message, meeting notes, an email. Canon reads it, compares it with every decision Northwind has made, and tells you what it goes
        against.
      </p>

      <div className="samples">
        <span className="label">Try a sample</span>
        <div className="choices">
          {samples.map(s => (
            <button
              key={s.key}
              type="button"
              aria-pressed={pick === s.key}
              onClick={() => {
                setPick(s.key)
                setText(s.source.text)
                run.reset()
              }}
            >
              {SAMPLE_LABEL[s.key] ?? s.source.title}
            </button>
          ))}
        </div>
      </div>
      <form
        onSubmit={e => {
          e.preventDefault()
          if (text.trim()) run.mutate()
        }}
      >
        <textarea
          className="input"
          style={{ marginTop: 20 }}
          aria-label="Message to check"
          value={text}
          onChange={e => {
            setText(e.target.value)
            setPick('')
          }}
        />
        <div style={{ marginTop: 20, display: 'flex', gap: 20, alignItems: 'center', flexWrap: 'wrap' }}>
          <button type="submit" className="btn" disabled={run.isPending || !text.trim()}>
            {run.isPending ? 'Checking...' : 'Check this message'}
          </button>
          <span className="small muted">Your paste stays in your own space. Other visitors do not see it.</span>
        </div>
      </form>
      <p className="progress" aria-live="polite">
        {run.isPending ? (
          <Stages n={n} />
        ) : run.data ? (
          `Read the message. Checked ${n ?? 'all'} decisions. Done in ${secs(run.data.latency_ms)}.`
        ) : (
          ''
        )}
      </p>

      {run.isError && <ErrorState error={run.error} retry={() => run.mutate()} title="Canon could not check this message." />}
      {run.isPending && (
        <div className="section split" role="status" aria-label="Checking the message" aria-busy="true">
          <div className="flag">
            <Bar w="70%" h={24} />
            <div className="vs">
              <Bar h={80} />
              <Bar h={80} />
            </div>
          </div>
          <div>
            <Bar w="60%" h={26} />
            <Bar h={120} style={{ marginTop: 20 }} />
          </div>
        </div>
      )}
      {run.data && <Result r={run.data} decisions={decisions.data ?? []} />}
    </main>
  )
}

/** Honest staged progress: the steps the ingest runs, advanced on a timer while the one request is in flight. */
function Stages({ n }: { n: number | undefined }) {
  const [t, setT] = useState(0)
  useEffect(() => {
    const i = setInterval(() => setT(x => x + 1), 1000)
    return () => clearInterval(i)
  }, [])
  const steps = ['Reading the message.', 'Pulling out decisions and checking every quote word for word.', `Comparing with ${n ?? 'all'} decisions.`]
  return <>{steps.slice(0, Math.min(steps.length, 1 + Math.floor(t / 1.2))).join(' ')}</>
}

function Result({ r, decisions }: { r: IngestResult; decisions: Decision[] }) {
  const byId = new Map(decisions.map(d => [d.id, d]))
  const conflicts = r.alerts.filter(a => a.kind === 'contradiction' || a.kind === 'agent_violation')
  const stale = r.alerts.filter(a => a.kind === 'stale_doc')
  const premise = r.alerts.filter(a => a.kind === 'premise_changed')
  const updates = r.decisions.filter(x => x.relation === 'update' && x.related_decision_id)

  return (
    <div className="section split">
      <div>
        {conflicts.map(a => (
          <Conflict key={a.id} a={a} r={r} rule={byId.get(a.related_decision_id ?? '')} />
        ))}
        {updates.map(u => {
          const old = byId.get(u.related_decision_id ?? '')
          return (
            <div key={u.decision.id} className="flag plain" style={{ marginTop: 48 }}>
              <h3>Replaces {old ? <q>{old.statement}</q> : 'an older decision'}.</h3>
              <p style={{ marginTop: 8, color: 'var(--ink-2)' }}>{u.explanation}</p>
              {old && (
                <p className="src">
                  Decided by {old.owner} on {fmtLong(old.ts)}.
                </p>
              )}
            </div>
          )
        })}
        {stale.map(a => (
          <Stale key={a.id} a={a} />
        ))}
        {premise.map(a => (
          <div key={a.id} className="flag plain" style={{ marginTop: 48 }}>
            <h3>
              It may change the reason behind {byId.get(a.decision_id ?? '') ? <q>{byId.get(a.decision_id ?? '')?.statement}</q> : 'a decision'}.
            </h3>
            <p style={{ marginTop: 8, color: 'var(--ink-2)' }}>{a.explanation}</p>
          </div>
        ))}
        {conflicts.length + updates.length + stale.length + premise.length === 0 && (
          <div className="flag plain">
            <h3>Nothing on record goes against this message.</h3>
            <p style={{ marginTop: 8, color: 'var(--ink-2)' }}>Canon saved what it found, so later messages are checked against it too.</p>
          </div>
        )}
      </div>
      <aside className="understood">
        <h2>What Canon understood</h2>
        {r.decisions.length === 0 && (
          <p className="muted" style={{ marginTop: 20 }}>
            No decision in this message. Canon kept it as context.
          </p>
        )}
        {r.decisions.map(x => (
          <dl key={x.decision.id}>
            <dt>What</dt>
            <dd>{x.decision.statement}</dd>
            <dt>Who</dt>
            <dd>{x.decision.owner}</dd>
            {x.decision.rationale && (
              <>
                <dt>Why</dt>
                <dd>{x.decision.rationale}</dd>
              </>
            )}
            {x.decision.assumptions.length > 0 && (
              <>
                <dt>Assumes</dt>
                <dd>{x.decision.assumptions.join(' ')}</dd>
              </>
            )}
            <dt>Result</dt>
            <dd className={x.relation === 'contradiction' ? 'breaks' : undefined}>{RELATION[x.relation]}</dd>
          </dl>
        ))}
        <p className="small muted" style={{ marginTop: 20 }}>
          Canon saved this as a new item{r.alerts.length ? ` and raised ${r.alerts.length === 1 ? 'one alert' : `${r.alerts.length} alerts`}` : ''}.
          {r.alerts.length ? ' A person can accept or dismiss them.' : ''}
          {r.rejected_quotes > 0
            ? ` It dropped ${r.rejected_quotes} quote${r.rejected_quotes === 1 ? '' : 's'} it could not find word for word.`
            : ''}
        </p>
      </aside>
    </div>
  )
}

function Conflict({ a, r, rule }: { a: Alert; r: IngestResult; rule: Decision | undefined }) {
  const mine = r.decisions.find(x => x.decision.id === a.decision_id)?.decision
  const newQuote = mine?.quotes[0]?.quote ?? quoteFrom(a, r.source.id)
  const old = a.quotes.find(x => x.source_id !== r.source.id)
  const oldSrc = useQuery({ ...q.source(old?.source_id ?? ''), enabled: !!old })
  return (
    <div className="flag" style={{ marginBottom: 48 }}>
      <h3>Goes against {rule ? <q>{rule.statement}</q> : 'an active decision.'}</h3>
      <div className="vs">
        <div>
          <span className="label">The new message, today</span>
          {newQuote && <blockquote>"{newQuote}"</blockquote>}
          <p className="by">{r.source.author}, pasted</p>
        </div>
        <div>
          <span className="label">The decision{rule ? `, ${fmtLong(rule.ts)}` : ''}</span>
          {old && <blockquote>"{old.quote}"</blockquote>}
          <p className="by">
            {rule?.owner}
            {oldSrc.data ? `, ${oldSrc.data.title}` : ''}
          </p>
        </div>
      </div>
      <p className="small muted" style={{ marginTop: 18 }}>
        {a.explanation} Both quotes are checked word for word against their source.
      </p>
      {rule && (
        <p className="small" style={{ marginTop: 8 }}>
          <Link to={`/decisions/${rule.id}`}>See the decision</Link>
        </p>
      )}
    </div>
  )
}

function Stale({ a }: { a: Alert }) {
  const doc = useQuery({ ...q.source(a.source_id ?? ''), enabled: !!a.source_id })
  const said = quoteFrom(a, a.source_id)
  return (
    <div className="flag plain" style={{ marginTop: 48 }}>
      <h3>
        <span className="dot hollow" aria-hidden />
        It also shows {doc.data ? `the ${doc.data.title} page` : 'a document'} is out of date.
      </h3>
      {said && (
        <>
          <p style={{ marginTop: 8, color: 'var(--ink-2)' }}>That page still says:</p>
          <blockquote>"{said}"</blockquote>
        </>
      )}
      {doc.data && (
        <p className="src">
          {srcLine(doc.data)}. Ask {doc.data.author}, who wrote it, to update it.
        </p>
      )}
    </div>
  )
}
