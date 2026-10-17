import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import type { Alert, DecisionDetail, ResolveAction, Source } from '../types'
import { alertTag, fmtDate, Show, useApi } from '../ui'

export function DecisionList() {
  const list = useApi(api.decisions, [])
  return (
    <main className="page">
      <div className="label">Decisions / the record, newest first</div>
      <h1 className="h1" style={{ fontSize: 36, margin: '8px 0 20px' }}>What the company decided.</h1>
      <Show load={list} what="Loading decisions" empty={d => d.length === 0 && 'The record is empty. Ingest a source to add decisions.'}>
        {ds => (
          <div className="rows dlist">
            {[...ds].sort((a, b) => b.ts.localeCompare(a.ts)).map(d => (
              <Link key={d.id} to={`/decisions/${d.id}`}>
                <span className="label tnum">{fmtDate(d.ts)}</span>
                <span><span className="h3">{d.statement}</span><br /><span className="small muted">{d.owner} / {d.topic}</span></span>
                <span className={`tag ${d.status === 'active' ? 'green' : 'line'}`}>{d.status}</span>
              </Link>
            ))}
          </div>
        )}
      </Show>
    </main>
  )
}

export default function Decision() {
  const { id = '' } = useParams()
  const detail = useApi(() => api.decision(id), [id])
  return (
    <main className="page">
      <div className="label"><Link className="lnk" to="/decisions">Decisions</Link> / {detail.data?.decision.topic ?? '...'} / {id}</div>
      <div style={{ marginTop: 14 }}>
        <Show load={detail} what="Loading the decision">{d => <Body d={d} reload={detail.reload} />}</Show>
      </div>
    </main>
  )
}

function Body({ d, reload }: { d: DecisionDetail; reload: () => void }) {
  const dec = d.decision
  const src = (sid: string | null) => d.sources.find(s => s.id === sid)
  const premise = d.alerts.some(a => a.kind === 'premise_changed' && a.status === 'open')
  const open = d.alerts.filter(a => a.status === 'open')
  return (
    <div className="grid dec-grid">
      <div>
        <div className="row" style={{ gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
          <span className={`tag ${dec.status === 'active' ? 'green' : 'line'}`}>{dec.status}</span>
          {dec.version > 1 && <span className="tag line">v{dec.version} / supersedes {dec.supersedes.length}</span>}
          <span className="tag line">recorded by {dec.created_by}</span>
        </div>
        <h1 className="stmt">{dec.statement}</h1>
        {dec.superseded_by && <p className="small" style={{ marginTop: 10 }}>Superseded by <Link className="lnk" to={`/decisions/${dec.superseded_by}`}>a newer decision</Link>.</p>}
        <div className="meta">
          <div><span className="label">Owner</span><b>{dec.owner}</b></div>
          <div><span className="label">Decided</span><b className="tnum">{fmtDate(dec.ts)}</b></div>
          <div><span className="label">Topic</span><b>{dec.topic}</b></div>
          <div><span className="label">Open alerts</span><b className="tnum">{open.length}</b></div>
        </div>

        {d.timeline.length > 0 && (
          <section style={{ marginTop: 22 }}>
            <div className="label ink" style={{ marginBottom: 14 }}>How it evolved</div>
            <div className="htl">
              {d.timeline.map((t, i) => (
                <Link key={i} to={`/decisions/${t.decision_id}`} className={t.relation === 'contradiction' ? 'bad' : t.decision_id === dec.id && t.status === 'active' ? 'cur' : ''}>
                  <span className="label">{fmtDate(t.ts)}{t.relation && ` / ${t.relation}`}</span>
                  <p>{t.statement}</p>
                </Link>
              ))}
            </div>
          </section>
        )}

        <div className="grid two" style={{ gap: 28, marginTop: 26 }}>
          <section>
            <div className="sec"><h2 className="h3">Why</h2></div>
            <p style={{ marginTop: 10 }}>{dec.rationale || 'No rationale was recorded.'}</p>
          </section>
          <section>
            <div className="sec"><h2 className="h3">Assumptions</h2><span className="label">Canon watches these</span></div>
            {dec.assumptions.length === 0 ? <p className="small muted" style={{ marginTop: 10 }}>None recorded.</p> : (
              <ul className="assume">{dec.assumptions.map(a => <li key={a}>{a}</li>)}</ul>
            )}
            {premise && <p className="small" style={{ marginTop: 6 }}><span className="tag amber">premise changed</span> See the alert on the right.</p>}
          </section>
        </div>

        <section style={{ marginTop: 26 }}>
          <div className="sec"><h2 className="h3">Verified quotes</h2><span className="label">Each one matched word for word in its source</span></div>
          <div className="grid" style={{ gap: 18, marginTop: 14 }}>
            {dec.quotes.length === 0 && <p className="small muted">No quotes stored.</p>}
            {dec.quotes.map((q, i) => <QuoteBlock key={i} quote={q.quote} s={src(q.source_id)} />)}
          </div>
        </section>
      </div>

      <aside className="grid" style={{ gap: 22 }}>
        {d.alerts.length === 0 && <div className="state"><div className="label ink">No conflicts</div><p className="small muted" style={{ marginTop: 6 }}>Nothing on record disagrees with this decision.</p></div>}
        {d.alerts.map(a => <Conflict key={a.id} a={a} src={src} dec={dec.quotes[0]?.quote} reload={reload} />)}
      </aside>
    </div>
  )
}

function QuoteBlock({ quote, s }: { quote: string; s?: Source }) {
  return (
    <div className="q">"{quote}"
      {s && <div className="src"><span className="ok-mark">verified</span><span className="chip"><span className="k">{s.kind}</span> {s.title} / {fmtDate(s.ts)}</span><span className="muted">{s.author}</span></div>}
    </div>
  )
}

function Conflict({ a, src, dec, reload }: { a: Alert; src: (id: string | null) => Source | undefined; dec?: string; reload: () => void }) {
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const s = src(a.source_id)
  const theirs = a.quotes.find(q => q.source_id === a.source_id) ?? a.quotes[0]
  const resolve = async (action: ResolveAction) => {
    setBusy(true); setErr('')
    try { await api.resolve(a.id, action); reload() } catch (e) { setErr(String((e as Error).message)) } finally { setBusy(false) }
  }
  return (
    <section className="conflict" style={a.status === 'resolved' ? { opacity: 0.6 } : undefined}>
      <div className="hd"><span className="label">{a.status === 'resolved' ? `Resolved / ${a.resolution}` : 'Contradicted by'} / {a.kind.replace('_', ' ')}</span><span className="label">{a.severity}</span></div>
      <div style={{ padding: '14px 16px 4px' }}>
        <span className={`tag ${alertTag(a.kind)}`}>{a.kind.replace('_', ' ')}</span>
        {s && <div className="h3" style={{ marginTop: 8 }}>{s.title}</div>}
        <p className="small muted" style={{ marginTop: 4 }}>{a.explanation}</p>
      </div>
      {theirs && (
        <div className="vs">
          <div><div className="label" style={{ marginBottom: 6 }}>The source says</div><div className="q red" style={{ fontSize: 15 }}>"{theirs.quote}"</div></div>
          <div><div className="label" style={{ marginBottom: 6 }}>The record says</div><div className="q" style={{ fontSize: 15 }}>"{dec ?? '...'}"</div></div>
        </div>
      )}
      {a.status === 'open' && (
        <div className="row" style={{ padding: '4px 16px 14px', gap: 8, flexWrap: 'wrap' }}>
          <button className="btn sm" disabled={busy} onClick={() => resolve('accept_update')}>Accept update</button>
          <button className="btn sm ghost" disabled={busy} onClick={() => resolve('dismiss')}>Dismiss</button>
          <button className="btn sm ghost" disabled={busy} onClick={() => resolve('retire_decision')}>Retire decision</button>
          {err && <span className="no-mark" role="alert">{err}</span>}
        </div>
      )}
    </section>
  )
}
