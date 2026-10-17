import { api } from '../api'
import type { EvalReport } from '../types'
import { fmtDate, fmtTime, Show, useApi } from '../ui'

const pct = (a: number, b: number) => (b ? Math.round((a / b) * 100) : 0)

export default function Benchmark() {
  const r = useApi(api.evalReport, [])
  return (
    <main className="page">
      <Show load={r} what="Loading the last benchmark run">{e => <Report e={e} />}</Show>
    </main>
  )
}

function Report({ e }: { e: EvalReport }) {
  const rows: [string, number, number][] = [
    ['Decisions extracted', e.decisions_planted, e.decisions_found],
    ['Contradictions and updates', e.contradictions_planted, e.contradictions_found],
    ['check_intent verdicts (allow / warn / block)', e.check_cases, e.check_correct],
    ['Unanswerable questions, refused', e.unanswerable, e.refused_correctly],
  ]
  return (
    <>
      <div className="label">Benchmark / labelled gold set / run {fmtDate(e.run_at)} {fmtTime(e.run_at)} / {e.model}</div>
      <h1 className="h1" style={{ marginTop: 8 }}>We planted the problems. <span style={{ color: 'var(--ink-3)' }}>Here is what Canon found.</span></h1>

      <div className="kpis" style={{ marginTop: 24 }}>
        <Kpi label="Contradictions found" big={e.contradictions_found} of={e.contradictions_planted} note="planted across Slack, wiki, PRs" />
        <div>
          <span className="label ink">False positives</span>
          <div className="big tnum">{e.false_positives}</div>
          <div className="meter"><b style={{ width: `${Math.min(100, e.false_positives * 4)}%`, background: 'var(--signal)' }}></b></div>
          <div className="small muted" style={{ marginTop: 8 }}>alerts with no planted conflict behind them</div>
        </div>
        <Kpi label="Refused correctly" big={e.refused_correctly} of={e.unanswerable} note='unanswerable questions, said "I do not know"' />
        <div>
          <span className="label ink">Latency p50 / p95</span>
          <div className="big tnum">{(e.p50_ms / 1000).toFixed(1)}<small> / {(e.p95_ms / 1000).toFixed(1)} s</small></div>
          <div className="meter"><b style={{ width: `${Math.min(100, pct(e.p50_ms, 5000))}%` }}></b></div>
          <div className="small muted" style={{ marginTop: 8 }}>end to end, per call</div>
        </div>
      </div>

      <div className="grid two" style={{ gap: 40, marginTop: 30 }}>
        <section>
          <div className="sec"><h2 className="h3">By task</h2><span className="label">data/gold/gold.json</span></div>
          <table>
            <thead><tr><th>Task</th><th className="n">Planted</th><th className="n">Found</th><th className="n">Score</th></tr></thead>
            <tbody>{rows.map(([t, p, f]) => <tr key={t}><td>{t}</td><td className="n">{p}</td><td className="n">{f}</td><td className="n">{pct(f, p)}%</td></tr>)}</tbody>
          </table>
        </section>
        <section className="sheet pad" style={{ alignSelf: 'start' }}>
          <div className="label ink" style={{ marginBottom: 6 }}>Notes and misses, in the open</div>
          {e.notes.length === 0 ? <p className="small muted">No notes for this run.</p> : (
            <ul className="small" style={{ paddingLeft: 18, lineHeight: 1.7 }}>{e.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>
          )}
        </section>
      </div>
    </>
  )
}

function Kpi({ label, big, of, note }: { label: string; big: number; of: number; note: string }) {
  return (
    <div>
      <span className="label ink">{label}</span>
      <div className="big tnum">{big}<small> / {of}</small></div>
      <div className="meter"><b style={{ width: `${pct(big, of)}%` }}></b></div>
      <div className="small muted" style={{ marginTop: 8 }}>{note}</div>
    </div>
  )
}
