import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { api, MOCK } from './api'
import type { Activity, AlertKind, Citation, Verdict } from './types'

// ---------- data ----------

export interface Load<T> { data?: T; error?: string; loading: boolean; reload: () => void }

/** Runs `fn` on mount and when `deps` change; `pollMs` re-runs it quietly in the background. */
export function useApi<T>(fn: () => Promise<T>, deps: unknown[], pollMs?: number): Load<T> {
  const [state, setState] = useState<{ data?: T; error?: string; loading: boolean }>({ loading: true })
  const [tick, setTick] = useState(0)
  const fnRef = useRef(fn)
  fnRef.current = fn
  useEffect(() => {
    let alive = true
    setState(s => ({ data: s.data, loading: true }))
    const run = () => fnRef.current().then(
      data => alive && setState({ data, loading: false }),
      e => alive && setState(s => ({ data: s.data, error: String(e.message ?? e), loading: false })),
    )
    run()
    const id = pollMs ? setInterval(run, pollMs) : undefined
    return () => { alive = false; clearInterval(id) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick, pollMs])
  const reload = useCallback(() => setTick(t => t + 1), [])
  return { ...state, reload }
}

// ---------- states ----------

/** Loading copy that admits a cold start after a moment instead of showing a blank. */
export function Waking({ what = 'Loading' }: { what?: string }) {
  const [slow, setSlow] = useState(false)
  useEffect(() => { const id = setTimeout(() => setSlow(true), 1500); return () => clearTimeout(id) }, [])
  return (
    <div className="state" role="status" aria-live="polite">
      <div className="label ink">{slow ? 'Waking up Canon' : what}</div>
      {slow && <p className="small muted" style={{ marginTop: 6 }}>Canon scales to zero when idle. The first request takes a few seconds.</p>}
    </div>
  )
}

export function Failed({ error, retry }: { error: string; retry?: () => void }) {
  return (
    <div className="state err" role="alert">
      <div className="label ink">Canon did not answer</div>
      <p className="small muted" style={{ margin: '6px 0 10px' }}>{error}</p>
      {retry && <button className="btn sm ghost" onClick={retry}>Try again</button>}
    </div>
  )
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="state"><p className="small muted">{children}</p></div>
}

/** Render a Load: loading, error, empty or data. */
export function Show<T>({ load, empty, what, children }: {
  load: Load<T>; empty?: (d: T) => ReactNode | false; what?: string; children: (d: T) => ReactNode
}) {
  if (load.data === undefined) {
    if (load.error) return <Failed error={load.error} retry={load.reload} />
    return <Waking what={what} />
  }
  const e = empty?.(load.data)
  return <>{e ? <Empty>{e}</Empty> : children(load.data)}</>
}

// ---------- formatting ----------

export const fmtDate = (iso: string) =>
  new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })

export const fmtTime = (iso: string) =>
  new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })

export function ago(iso: string) {
  const m = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60_000))
  if (m < 1) return 'just now'
  if (m < 60) return `${m} min ago`
  if (m < 1440) return `${Math.round(m / 60)} h ago`
  return `${Math.round(m / 1440)} d ago`
}

export const secs = (ms: number) => `${(ms / 1000).toFixed(1)} s`

export const alertTag = (k: AlertKind) =>
  ({ contradiction: 'red', agent_violation: 'red', pr_deviation: 'red', stale_doc: 'redsoft', premise_changed: 'amber' })[k]

export const V = ({ v }: { v: Verdict }) => <span className={`v ${v}`}>{v}</span>

export function Cite({ c }: { c: Citation }) {
  return (
    <div className="src">
      <span className="ok-mark">verified</span>
      <span className="chip"><span className="k">{c.kind}</span> {c.title} / {fmtDate(c.ts)}</span>
      {c.decision_id && <Link className="lnk small" to={`/decisions/${c.decision_id}`}>decision</Link>}
    </div>
  )
}

// ---------- shell ----------

const links: [string, string][] = [
  ['/', 'Home'], ['/decisions', 'Decisions'], ['/ask', 'Ask why'], ['/ingest', 'Ingest'],
  ['/agents', 'Agents'], ['/benchmark', 'Benchmark'], ['/about', 'About'],
]

export function Bar() {
  const health = useApi(api.health, [])
  const status = health.data ? 'online' : health.error ? 'offline' : 'waking up'
  return (
    <header className="bar">
      <Link className="mark" to="/"><i></i>Canon</Link>
      <nav className="nav" aria-label="Main">
        {links.map(([to, t]) => <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => isActive ? 'on' : ''}>{t}</NavLink>)}
      </nav>
      <div className="right">
        <span className="ws">Workspace <b>Northwind Labs</b> / synthetic data{MOCK && ' / mock'}</span>
        <span className="live" style={health.data ? undefined : { color: 'var(--ink-3)' }}>{status}</span>
      </div>
    </header>
  )
}

// ---------- activity feed (home rail and agents page) ----------

export const useActivity = () => useApi(api.activity, [], 2000)

/** One feed for the home rail and the agents page; the caller owns the 2 s poll (useActivity). */
export function ActivityFeed({ feed, limit = 8 }: { feed: Load<Activity[]>; limit?: number }) {
  return (
    <section className="sheet pad">
      <div className="row" style={{ justifyContent: 'space-between', borderBottom: '1px solid var(--ink)', paddingBottom: 8 }}>
        <h2 className="h3" style={{ fontSize: 18 }}>Agent activity</h2><span className="live">live</span>
      </div>
      <Show load={feed} what="Loading activity" empty={a => a.length === 0 && 'No activity yet. Call a tool in the playground, or connect an agent.'}>
        {a => (
          <div className="rows" aria-live="polite">
            {sortNewest(a).slice(0, limit).map(x => <FeedItem key={x.id} a={x} />)}
          </div>
        )}
      </Show>
    </section>
  )
}

export const sortNewest = (a: Activity[]) => [...a].sort((x, y) => y.created_at.localeCompare(x.created_at))

function FeedItem({ a }: { a: Activity }) {
  const agent = a.actor.startsWith('agent:')
  return (
    <div className="feed-item">
      <span className="t">{fmtTime(a.created_at)}</span>
      <div>
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <span className={`actor ${agent ? 'agent' : ''}`}>{agent ? a.actor.slice(6) : a.actor}</span>
          {a.verdict && <V v={a.verdict} />}
        </div>
        <div className="small" style={{ marginTop: 3 }}>{a.summary}</div>
        {/* ref_titles[i] names ref_ids[i]; only a decision (d-) has a page, and the deciding one comes first */}
        {a.ref_titles.length > 0 && (
          <div className="label" style={{ marginTop: 4 }}>
            {a.verdict ? 'deciding: ' : 'refs: '}
            {a.ref_titles.slice(0, 2).map((t, i) => (
              <span key={i}>
                {i > 0 && ' / '}
                {/^d(-|ec_)/.test(a.ref_ids[i] ?? '') ? <Link className="lnk" to={`/decisions/${a.ref_ids[i]}`}>{short(t, 60)}</Link> : short(t, 60)}
              </span>
            ))}
            {a.ref_titles.length > 2 && ` +${a.ref_titles.length - 2}`}
          </div>
        )}
      </div>
    </div>
  )
}

export const short = (s: string, n = 70) => (s.length > n ? s.slice(0, n - 1).trimEnd() + '...' : s)
