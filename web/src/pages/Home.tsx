import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import type { Action, Activity, Persona } from '../types'
import { ActivityFeed, ago, alertTag, Cite, fmtDate, type Load, secs, Show, sortNewest, useActivity, useApi, V } from '../ui'

const SINCE = { '7': 'Last 7 days', '30': 'Last 30 days', all: 'Since day one' } as const
type Since = keyof typeof SINCE
const DAY_ONE = '2025-01-01T00:00:00Z' // first day of the Northwind Labs corpus

const sinceIso = (s: Since) => s === 'all' ? DAY_ONE : new Date(Date.now() - Number(s) * 86_400_000).toISOString()

const PERSONAS: [Persona, string][] = [['engineer', 'Engineer'], ['pm', 'PM'], ['new_hire', 'New hire']]

export default function Home() {
  const [persona, setPersona] = useState<Persona>('engineer')
  const [since, setSince] = useState<Since>('7')
  const choose = (p: Persona) => { setPersona(p); if (p === 'new_hire') setSince('all') }
  const feed = useActivity()

  return (
    <>
    <div className="strap"><p>Canon is the shared memory of a company. People and AI agents read it, write it, and get blocked when they break a decision.</p></div>
    <main className="page">
      <div className="hero">
        <div>
          <div className="label">Catch me up / {new Date().toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'short', year: 'numeric' })}</div>
          <h1 className="h1" style={{ marginTop: 8, fontSize: 38 }}>Here is what changed. <span style={{ color: 'var(--ink-3)' }}>And what to do about it.</span></h1>
        </div>
        <div className="row" style={{ gap: 14 }}>
          <div>
            <div className="label" style={{ marginBottom: 6 }} id="persona-l">I am a</div>
            <div className="seg" role="group" aria-labelledby="persona-l">
              {PERSONAS.map(([p, t]) => <button key={p} className={persona === p ? 'on' : ''} aria-pressed={persona === p} onClick={() => choose(p)}>{t}</button>)}
            </div>
          </div>
          <div>
            <label className="label" style={{ marginBottom: 6, display: 'block' }} htmlFor="since">Since</label>
            <select id="since" className="input" value={since} onChange={e => setSince(e.target.value as Since)}>
              {Object.entries(SINCE).map(([k, t]) => <option key={k} value={k}>{t}</option>)}
            </select>
          </div>
        </div>
      </div>

      <div className="grid home-grid" style={{ marginTop: 28 }}>
        <div className="grid" style={{ gap: 32 }}>
          <LatestBlock feed={feed} />
          <BriefingView persona={persona} since={since} />
          <Alerts />
        </div>
        <aside className="grid" style={{ gap: 12 }}>
          <ActivityFeed feed={feed} />
          <Link to="/agents" className="btn ghost sm" style={{ justifyContent: 'center' }}>Open agent playground</Link>
        </aside>
      </div>
    </main>
    </>
  )
}

/** The most recent agent block: the moment Canon stopped an agent breaking a decision. */
function LatestBlock({ feed }: { feed: Load<Activity[]> }) {
  const block = feed.data && sortNewest(feed.data).find(a => a.verdict === 'block' && a.actor.startsWith('agent:'))
  if (!block) return null
  return <BlockCard key={block.id} a={block} />
}

function BlockCard({ a }: { a: Activity }) {
  const id = a.ref_ids[0]
  const detail = useApi(() => (id ? api.decision(id) : Promise.resolve(undefined)), [id])
  const d = detail.data?.decision
  const src = d && detail.data?.sources.find(s => s.id === d.quotes[0]?.source_id)
  return (
    <section className="blockcard" aria-label="Latest agent block">
      <div className="hd">
        <V v="block" />
        <span className="label">Agent blocked / {a.actor.slice(6)} / {ago(a.created_at)}</span>
      </div>
      <div className="bd">
        <div className="h3" style={{ fontSize: 22 }}>{a.summary}</div>
        {id && (
          <div>
            <div className="label" style={{ marginBottom: 6 }}>Deciding decision</div>
            <div className="q red">
              <Link to={`/decisions/${id}`} className="lnk" style={{ color: 'var(--ink)' }}>{d?.statement ?? a.ref_titles[0] ?? id}</Link>
              {d && (
                <div className="src">
                  <span className="muted">{d.owner} / {fmtDate(d.ts)}</span>
                  {src && <span className="chip"><span className="k">{src.kind}</span> {src.title}</span>}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  )
}

function BriefingView({ persona, since }: { persona: Persona; since: Since }) {
  const b = useApi(() => api.briefing(persona, sinceIso(since)), [persona, since])
  return (
    <>
      <Show load={b} what="Reading the record for your briefing">
        {br => (
          <>
            <section className="sheet brief" style={{ opacity: b.loading ? 0.6 : 1 }} aria-busy={b.loading}>
              <div>
                <div className="row" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
                  <span className="label ink">Briefing / {SINCE[since]}</span>
                  <span className="label tnum">{b.loading ? 'updating' : secs(br.latency_ms)}</span>
                </div>
                <p className="lede">{br.summary}</p>
              </div>
              <div>
                <div className="label" style={{ marginBottom: 4 }}>Highlights</div>
                {br.highlights.length === 0 ? <p className="small muted">Nothing new in this window.</p> : (
                  <ul className="hl">{br.highlights.map((h, i) => <li key={i}><span>{String(i + 1).padStart(2, '0')}</span>{h}</li>)}</ul>
                )}
              </div>
            </section>
            {persona === 'new_hire' && br.who_to_ask.length > 0 && (
              <section>
                <div className="sec"><h2 className="h3">People to ask</h2><span className="label">from who decided what</span></div>
                <ul className="people">
                  {br.who_to_ask.map(p => (
                    <li key={p.id}>
                      <div><b>{p.name}</b> <span className="muted small">{p.role} / {p.team}</span></div>
                      {p.status === 'left'
                        ? <span className="tag amber">left {p.left_at ? fmtDate(p.left_at) : ''}</span>
                        : <span className="tag green">active</span>}
                    </li>
                  ))}
                </ul>
              </section>
            )}
            <section>
              <div className="sec"><h2 className="h3">Next best actions</h2><span className="label">Ranked 0-100</span></div>
              {br.actions.length === 0 ? <p className="small muted" style={{ padding: '12px 0' }}>No actions. The record and your work agree.</p> : (
                <div className="rows">{[...br.actions].sort((x, y) => y.priority - x.priority).map((a, i) => <ActionRow key={i} a={a} top={i === 0} />)}</div>
              )}
            </section>
          </>
        )}
      </Show>
    </>
  )
}

const CHIP: Record<Action['chip'], string> = {
  open_source: 'Open source', view_decision: 'View decision', resolve_alert: 'Resolve alert', ask_person: 'Ask why', draft_reply: 'Draft reply',
}

function ActionRow({ a, top }: { a: Action; top: boolean }) {
  const dec = a.citations.find(c => c.decision_id)?.decision_id
  const to = dec && a.chip !== 'ask_person' ? `/decisions/${dec}` : `/ask?q=${encodeURIComponent(a.title)}`
  return (
    <div className={`act ${top ? 'top' : ''}`}>
      <div className="score tnum" aria-label={`priority ${a.priority}`}>{a.priority}<small><b style={{ width: `${a.priority}%` }}></b></small></div>
      <div>
        <div className="h3">{a.title}</div>
        <div className="muted small" style={{ marginTop: 4 }}>{a.why}</div>
        <div className="reasons">
          {/* design review: two reasons max, no ghost tags */}
          {a.reasons.slice(0, 2).map(r => <span key={r} className={`tag ${/contradict|block|violat/i.test(r) ? 'redsoft' : 'amber'}`}>{r}</span>)}
        </div>
        {a.citations[0] && <div className="q" style={{ marginTop: 10, fontSize: 15 }}>"{a.citations[0].quote}"<Cite c={a.citations[0]} /></div>}
      </div>
      <Link className={`btn sm ${top ? '' : 'ghost'}`} to={to}>{CHIP[a.chip]}</Link>
    </div>
  )
}

function Alerts() {
  // polled, so an ingest elsewhere shows up here without a reload
  const al = useApi(api.alerts, [], 5000)
  return (
    <section>
      <div className="sec">
        <h2 className="h3">Open drift alerts {al.data && <span className="tag red" style={{ marginLeft: 8, verticalAlign: 4 }}>{al.data.length}</span>}</h2>
        <span className="label">Docs and work that disagree with the record</span>
      </div>
      <Show load={al} what="Loading alerts" empty={a => a.length === 0 && 'No open alerts. Paste something into Ingest to test the drift check.'}>
        {list => (
          <div className="rows">
            {[...list].sort((x, y) => y.created_at.localeCompare(x.created_at)).map(a => (
              <div key={a.id} className={`alert ${a.severity}`}>
                <div className="bar4"></div>
                <div>
                  <div className="row" style={{ gap: 10, alignItems: 'baseline' }}>
                    <span className={`tag ${alertTag(a.kind)}`}>{a.kind.replace('_', ' ')}</span>
                    <span className="label" style={{ marginLeft: 'auto' }}>{a.severity} / {ago(a.created_at)}</span>
                  </div>
                  <div style={{ marginTop: 6 }}>{a.explanation}</div>
                  {a.decision_id && <Link className="lnk small" to={`/decisions/${a.decision_id}`}>Open the decision</Link>}
                </div>
              </div>
            ))}
          </div>
        )}
      </Show>
    </section>
  )
}
