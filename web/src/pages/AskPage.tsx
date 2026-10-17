import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ErrorState, TextSkeleton } from '@/components/states'
import { q } from '@/lib/query'
import { fmtDate, secs, srcLine } from '@/lib/record'
import type { AskResult } from '@/lib/schemas'
import { useTitle } from '@/lib/title'
import asks from '@/samples/asks.json'

const FIRST = asks[0]?.question ?? 'Why can we no longer deploy production on Fridays?'
const EXAMPLES = [
  'What should we quote a new Route Lens customer?',
  'When did the Route Lens launch move, and why?',
  'Can Sakura backups live outside Japan?',
]
const UNKNOWABLE = asks.find(a => a.refusal)?.question ?? 'What is Northwind Labs annual recurring revenue for 2026?'

export default function AskPage() {
  useTitle('ask why')
  const [params, setParams] = useSearchParams()
  const question = params.get('q')?.trim() || FIRST
  const ask = (text: string) => setParams({ q: text }, { replace: true })
  const answer = useQuery(q.ask(question))
  const refusal = useQuery(q.ask(UNKNOWABLE))

  return (
    <main className="wrap">
      <h1>Ask why.</h1>
      <p className="lede">Ask why something is the way it is. Canon answers only from what Northwind actually said and wrote, and shows you where.</p>
      <AskForm key={question} initial={question} onAsk={ask} />
      <div className="choices small" style={{ marginTop: 16 }}>
        <span className="muted">Or try</span>
        {[FIRST, ...EXAMPLES]
          .filter(x => x !== question)
          .slice(0, 3)
          .map(x => (
            <button key={x} type="button" className="wrapok" onClick={() => ask(x)}>
              {x}
            </button>
          ))}
      </div>

      <div className="section split">
        <div className="answer" aria-live="polite">
          {answer.isError ? (
            <ErrorState error={answer.error} retry={() => void answer.refetch()} />
          ) : answer.isPending ? (
            <TextSkeleton lines={5} label="Finding the answer" />
          ) : (
            <Answer r={answer.data} />
          )}
        </div>
        <aside>
          {answer.data && answer.data.timeline.length > 0 && <Timeline r={answer.data} />}
          <div className={answer.data?.timeline.length ? 'dk' : undefined}>
            <h2>When Canon does not know</h2>
            <p className="question">"{UNKNOWABLE}"</p>
            <div className="ans">
              {refusal.isPending ? (
                <TextSkeleton lines={2} h={16} />
              ) : refusal.isError ? (
                <span className="muted">Canon did not answer this example.</span>
              ) : refusal.data.refused ? (
                <>
                  <b style={{ fontWeight: 500 }}>I do not know.</b> {stripIdk(refusal.data.answer)}
                </>
              ) : (
                refusal.data.answer
              )}
            </div>
            <p className="small muted" style={{ marginTop: 12 }}>
              Canon will not guess. When nothing it has read answers the question, it says so. <Link to="/benchmark">See the test results</Link>.
            </p>
          </div>
        </aside>
      </div>
    </main>
  )
}

const stripIdk = (s: string) => s.replace(/^\s*I do not know\.?\s*/i, '')

function AskForm({ initial, onAsk }: { initial: string; onAsk: (q: string) => void }) {
  const [draft, setDraft] = useState(initial)
  return (
    <form
      className="askrow"
      onSubmit={e => {
        e.preventDefault()
        if (draft.trim()) onAsk(draft.trim())
      }}
    >
      <input className="input" aria-label="Your question" value={draft} onChange={e => setDraft(e.target.value)} />
      <button type="submit" className="btn" disabled={!draft.trim()}>
        Ask
      </button>
    </form>
  )
}

function Answer({ r }: { r: AskResult }) {
  if (r.refused)
    return (
      <>
        <p className="label" style={{ marginBottom: 14 }}>
          Answered in {secs(r.latency_ms)}
        </p>
        <p>
          <b style={{ fontWeight: 500 }}>I do not know.</b> {stripIdk(r.answer)}
        </p>
      </>
    )
  const paras = r.answer.split(/\n{2,}/).filter(Boolean)
  return (
    <>
      <p className="label" style={{ marginBottom: 14 }}>
        Answered in {secs(r.latency_ms)}, from {r.citations.length} quote{r.citations.length === 1 ? '' : 's'}
      </p>
      {paras.map((p, i) => (
        <p key={i}>{p}</p>
      ))}
      {r.citations.length > 0 && (
        <ol className="cites">
          {r.citations.map((c, i) => (
            <li key={`${c.source_id}-${i}`}>
              <span className="n">{i + 1}</span>
              <div>
                <span className="s">{c.decision_id ? <Link to={`/decisions/${c.decision_id}`}>{srcLine(c)}</Link> : srcLine(c)}</span>
                <q>{c.quote}</q>
              </div>
            </li>
          ))}
        </ol>
      )}
    </>
  )
}

function Timeline({ r }: { r: AskResult }) {
  const current = [...r.timeline].reverse().find(t => t.status === 'active')
  return (
    <>
      <h2>How this decision changed</h2>
      <ul className="tl" style={{ marginTop: 16 }}>
        {r.timeline.map((t, i) => (
          <li key={`${t.decision_id}-${i}`} className={t.status === 'active' ? 'key' : 'old'}>
            <span className="when">{fmtDate(t.ts)}</span>
            <span>
              <Link to={`/decisions/${t.decision_id}`} style={{ textDecoration: 'none' }}>
                {t.statement}
              </Link>
              {t.status !== 'active' && (
                <span className="muted" style={{ fontWeight: 400 }}>
                  {' '}
                  Replaced.
                </span>
              )}
            </span>
          </li>
        ))}
      </ul>
      {current && (
        <p className="small" style={{ marginTop: 14 }}>
          <Link to={`/decisions/${current.decision_id}`}>See the full decision</Link>
        </p>
      )}
    </>
  )
}
