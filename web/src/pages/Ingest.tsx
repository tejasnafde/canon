import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import samples from '../samples/live_paste.json'
import type { IngestResult, Source, SourceKind } from '../types'
import { alertTag, Failed, secs, useApi } from '../ui'

const KINDS: SourceKind[] = ['paste', 'slack', 'meeting', 'wiki', 'pr', 'commit', 'email', 'doc']

const fromSample = (i: number): Source => ({ ...(samples[i].source as Source), ts: new Date().toISOString() })

export default function Ingest() {
  const [pick, setPick] = useState<number | null>(0)
  const [src, setSrc] = useState<Source>(() => fromSample(0))
  const [result, setResult] = useState<IngestResult>()
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [resetMsg, setResetMsg] = useState('')
  const record = useApi(api.decisions, [])
  const n = record.data?.length

  const choose = (i: number) => { setPick(i); setSrc(fromSample(i)); setResult(undefined); setError('') }
  const edit = (patch: Partial<Source>) => { setPick(null); setSrc(s => ({ ...s, ...patch })) }

  const run = async () => {
    setBusy(true); setError(''); setResult(undefined)
    try { setResult(await api.ingest({ ...src, ts: new Date(src.ts).toISOString() })) }
    catch (e) { setError(String((e as Error).message)) }
    finally { setBusy(false) }
  }
  const reset = async () => {
    setResetMsg('')
    try { await api.reset(); setResetMsg('Your workspace is empty again.'); setResult(undefined) }
    catch (e) { setResetMsg(String((e as Error).message)) }
  }

  return (
    <main className="page">
      <div className="grid ingest-grid">
        <section>
          <div className="label">Ingest / paste anything: Slack, transcript, wiki, PR, email</div>
          <h1 className="h1" style={{ fontSize: 36, marginTop: 8 }}>Feed the record.</h1>
          <div className="label" style={{ margin: '18px 0 8px' }}>Samples</div>
          <div className="samples">
            {samples.map((s, i) => (
              <button key={s.key} className={`sample ${pick === i ? 'on' : ''}`} onClick={() => choose(i)} aria-pressed={pick === i}>
                <span className={`tag ${pick === i ? 'ink' : 'line'}`} style={{ textAlign: 'center' }}>{s.expected_relation}</span>{s.source.title}
              </button>
            ))}
          </div>
          <div className="form2">
            <label><span className="label">Kind</span>
              <select className="input" style={{ width: '100%' }} value={src.kind} onChange={e => edit({ kind: e.target.value as SourceKind })}>{KINDS.map(k => <option key={k}>{k}</option>)}</select></label>
            <label><span className="label">Author</span><input className="input" value={src.author} onChange={e => edit({ author: e.target.value })} /></label>
            <label style={{ gridColumn: '1 / -1' }}><span className="label">Title</span><input className="input" value={src.title} onChange={e => edit({ title: e.target.value })} /></label>
          </div>
          <label><span className="label">Text</span>
            <textarea className="input" rows={12} value={src.text} onChange={e => edit({ text: e.target.value })} /></label>
          <div className="row" style={{ marginTop: 12, justifyContent: 'space-between' }}>
            <span className="label">Writes to your private workspace only</span>
            <button className="btn" onClick={run} disabled={busy || !src.text.trim() || !src.title.trim()}>{busy ? 'Working' : 'Ingest and reconcile'}</button>
          </div>
          <div className="row small" style={{ marginTop: 18, gap: 10 }}>
            <button className="btn sm ghost" onClick={reset}>Reset my workspace</button>
            <span className="muted" role="status">{resetMsg}</span>
          </div>
        </section>

        <section aria-live="polite">
          {busy && <Working n={n} />}
          {error && <Failed error={error} retry={run} />}
          {result && <Result r={result} n={n} />}
          {!busy && !error && !result && (
            <div className="state">
              <div className="label ink">Nothing ingested yet</div>
              <p className="small muted" style={{ marginTop: 6 }}>Pick a sample and press Ingest. Canon extracts each decision, checks every quote word for word, and reconciles it with {n ?? 'the'} decisions on record.</p>
            </div>
          )}
        </section>
      </div>
    </main>
  )
}

function Working({ n }: { n?: number }) {
  const steps = [
    'Reading the source',
    'Extracting decisions with Gemini',
    'Checking every quote word for word',
    `Reading ${n ?? 'the'} decisions on record to reconcile`,
    'Checking docs for drift',
  ]
  const [at, setAt] = useState(0)
  // ponytail: timed stages, the API has no progress stream; the last stage holds until the answer lands.
  useEffect(() => { const id = setInterval(() => setAt(a => Math.min(a + 1, steps.length - 1)), 1300); return () => clearInterval(id) }, [steps.length])
  return (
    <div className="state" role="status">
      <div className="label ink" style={{ marginBottom: 8 }}>Working</div>
      <ul className="steps">{steps.map((s, i) => <li key={s} className={i < at ? 'done' : i === at ? 'now' : ''}>{s}{i === at && '...'}</li>)}</ul>
    </div>
  )
}

function Result({ r, n }: { r: IngestResult; n?: number }) {
  const quotes = r.decisions.reduce((k, d) => k + d.decision.quotes.length, 0)
  return (
    <>
      <div className="row" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
        <span className="label ink">Result / {r.source.title}</span><span className="label">gemini-3.5-flash-lite / structured output</span>
      </div>
      <div className="stats">
        <div><span className="label">Decisions</span><b className="tnum">{r.decisions.length}</b></div>
        <div><span className="label">Quotes verified</span><b className="tnum">{quotes}<span style={{ fontSize: 20, color: 'var(--ink-3)' }}> / {quotes + r.rejected_quotes}</span></b></div>
        <div><span className="label">Alerts raised</span><b className="tnum" style={{ color: r.alerts.length ? 'var(--signal)' : undefined }}>{r.alerts.length}</b></div>
        <div><span className="label">Latency</span><b className="tnum">{secs(r.latency_ms)}</b></div>
      </div>

      <div className="sec" style={{ marginTop: 22 }}><h2 className="h3">Extracted and reconciled</h2>{n !== undefined && <span className="label">against {n} decisions on record</span>}</div>
      {r.decisions.length === 0 && <p className="small muted" style={{ padding: '12px 0' }}>No decisions in this text. Canon stores nothing it cannot quote.</p>}
      <div className="rows">
        {r.decisions.map(d => (
          <div key={d.decision.id} className="dec">
            <div className={`rel ${d.relation}`}>{d.relation}</div>
            <div>
              <Link to={`/decisions/${d.decision.id}`} className="h3">{d.decision.statement}</Link>
              {d.explanation && <div className="small muted" style={{ marginTop: 2 }}>{d.explanation}</div>}
              {d.related_decision_id && <Link className="lnk small" to={`/decisions/${d.related_decision_id}`}>{d.relation === 'update' ? 'Supersedes' : d.relation === 'same' ? 'Same as' : 'Conflicts with'} the decision on record</Link>}
              {d.decision.quotes.map((q, i) => <div key={i} className={`q ${d.relation === 'contradiction' ? 'red' : ''}`} style={{ fontSize: 15, marginTop: 8 }}>"{q.quote}" <span className="ok-mark" style={{ marginLeft: 6 }}>verified</span></div>)}
            </div>
          </div>
        ))}
        {r.rejected_quotes > 0 && (
          <div className="dec">
            <div className="rel" style={{ color: 'var(--signal)', border: '1px dashed var(--signal)' }}>rejected</div>
            <div className="small muted">{r.rejected_quotes} extracted claim{r.rejected_quotes === 1 ? '' : 's'} dropped: the quote was not in the source text. Canon never stores a quote it cannot match word for word.</div>
          </div>
        )}
      </div>

      <div className="sec" style={{ marginTop: 18 }}><h2 className="h3">Alerts raised</h2>{r.alerts.length > 0 && <Link className="label lnk" to="/">see them on Home</Link>}</div>
      {r.alerts.length === 0 ? <p className="small muted" style={{ padding: '10px 0' }}>No conflicts with the record.</p> : (
        <div className="rows">
          {r.alerts.map(a => (
            <div key={a.id} className="row" style={{ padding: '10px 0', gap: 10, alignItems: 'baseline' }}>
              <span className={`tag ${alertTag(a.kind)}`}>{a.kind.replace('_', ' ')}</span>
              {a.decision_id ? <Link className="lnk" to={`/decisions/${a.decision_id}`}>{a.explanation}</Link> : <span>{a.explanation}</span>}
              <span className="tag line" style={{ marginLeft: 'auto' }}>{a.severity}</span>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
