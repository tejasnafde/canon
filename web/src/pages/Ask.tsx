import { useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import asks from '../samples/asks.json'
import type { AskResult } from '../types'
import { Cite, fmtDate, Show, useApi } from '../ui'

const relTag = { new: 'ink', same: 'line', update: 'amber', contradiction: 'redsoft' } as const

export default function Ask() {
  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? asks[0].question // judges land on a worked answer, not an empty box
  const [draft, setDraft] = useState(q)
  const submit = (question: string) => { setDraft(question); setParams({ q: question }) }
  const onSubmit = (e: FormEvent) => { e.preventDefault(); if (draft.trim()) submit(draft.trim()) }

  return (
    <main className="page">
      <div className="label">Ask why / answers only from the record, every claim cited</div>
      <form className="askbox" style={{ marginTop: 12 }} onSubmit={onSubmit} role="search">
        <input aria-label="Question" value={draft} onChange={e => setDraft(e.target.value)} placeholder="Why do we ...?" />
        <button className="btn" type="submit">Ask</button>
      </form>
      <div className="sugg">
        <span className="label">Try</span>
        {asks.map(a => <button key={a.question} onClick={() => submit(a.question)}>{a.question}{'refusal' in a && <span className="label" style={{ marginLeft: 6 }}>(not on record)</span>}</button>)}
      </div>
      <div style={{ marginTop: 28 }}>
        <Answer key={q} q={q} />
      </div>
    </main>
  )
}

function Answer({ q }: { q: string }) {
  const r = useApi(() => api.ask(q), [q])
  return <Show load={r} what="Searching the record">{a => a.refused ? <Refused q={q} a={a} /> : <Grounded a={a} />}</Show>
}

/** Turns "[2]" markers in the answer into citation badges. */
function withMarks(text: string) {
  return text.split(/(\[\d+\])/g).map((part, i) => {
    const m = part.match(/^\[(\d+)\]$/)
    return m ? <sup key={i} className="c">{m[1]}</sup> : part
  })
}

function Grounded({ a }: { a: AskResult }) {
  const decId = a.timeline.find(t => t.status === 'active')?.decision_id ?? a.citations.find(c => c.decision_id)?.decision_id
  return (
    <div className="grid two">
      <section className="sheet pad">
        <div className="row" style={{ justifyContent: 'space-between', marginBottom: 12 }}>
          <span className="label ink">Answer / grounded in {a.citations.length} source{a.citations.length === 1 ? '' : 's'}</span>
          <span className="label tnum">{(a.latency_ms / 1000).toFixed(1)} s</span>
        </div>
        <p className="ans">{withMarks(a.answer)}</p>
        <div className="sec" style={{ marginTop: 22 }}><h2 className="h3">Sources</h2><span className="label">quotes verified word for word</span></div>
        <div className="rows">
          {a.citations.map((c, i) => (
            <div key={i} className="cite"><span className="n">{i + 1}</span>
              <div><div className="q" style={{ fontSize: 15, border: 0, padding: 0 }}>"{c.quote}"<Cite c={c} /></div></div>
            </div>
          ))}
        </div>
      </section>
      <section>
        <div className="sec"><h2 className="h3">Decision timeline</h2>{decId && <Link className="label lnk" to={`/decisions/${decId}`}>open decision</Link>}</div>
        {a.timeline.length === 0 ? <p className="small muted" style={{ paddingTop: 10 }}>One decision, no history.</p> : (
          <div className="tl2">
            {a.timeline.map((t, i) => (
              <div key={i}>
                <span className="label tnum">{fmtDate(t.ts)}</span>
                <span className={`tag ${t.status === 'superseded' ? 'line' : t.relation ? relTag[t.relation] : 'ink'}`}>{t.status === 'superseded' ? 'superseded' : t.relation ?? t.status}</span>
                <Link to={`/decisions/${t.decision_id}`}>{t.statement}</Link>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

function Refused({ q, a }: { q: string; a: AskResult }) {
  return (
    <section className="refuse pad" style={{ maxWidth: 820 }}>
      <div className="label" style={{ marginBottom: 10 }}>Refused / {(a.latency_ms / 1000).toFixed(1)} s</div>
      <div className="h2" style={{ fontSize: 24 }}>"{q}"</div>
      <div className="row" style={{ marginTop: 16, gap: 14, alignItems: 'flex-start' }}>
        <span className="tag line" style={{ flex: 'none' }}>refused</span>
        <div>
          <p className="ans" style={{ fontSize: 19 }}>{a.answer || 'I do not know. Nothing in the record covers this.'}</p>
          <p className="small muted" style={{ marginTop: 6 }}>Canon answers only from recorded decisions and will not guess. If someone decides this, paste it into Ingest and it becomes part of the record.</p>
        </div>
      </div>
      <div className="row" style={{ marginTop: 14 }}><Link className="btn sm ghost" to="/ingest">Record a decision</Link></div>
    </section>
  )
}
