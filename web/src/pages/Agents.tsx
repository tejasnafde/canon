import { useState } from 'react'
import { Link } from 'react-router-dom'
import examples from '../samples/agent_playground.json'
import { callTool, MCP_URL } from '../mcp'
import type { CheckResult } from '../types'
import { ActivityFeed, useActivity } from '../ui'

type Field = { name: string; long?: boolean; kind?: 'persona' | 'number' }
const TOOLS: { name: string; blurb: string; fields: Field[] }[] = [
  { name: 'check_intent', blurb: 'allow / warn / block', fields: [{ name: 'intent', long: true }, { name: 'actor' }] },
  { name: 'search_decisions', blurb: 'semantic search', fields: [{ name: 'query' }, { name: 'limit', kind: 'number' }] },
  { name: 'ask_why', blurb: 'cited answer', fields: [{ name: 'question', long: true }, { name: 'actor' }] },
  { name: 'catch_me_up', blurb: 'briefing by persona', fields: [{ name: 'persona', kind: 'persona' }, { name: 'since' }, { name: 'actor' }] },
  { name: 'record_decision', blurb: 'write + reconcile', fields: [{ name: 'statement' }, { name: 'rationale' }, { name: 'source_text', long: true }, { name: 'actor' }] },
  { name: 'flag_conflict', blurb: 'raise an alert', fields: [{ name: 'description' }, { name: 'source_text', long: true }, { name: 'actor' }] },
]

// The playground always calls as actor "playground", so its rows are easy to spot in the feed.
function exampleArgs(tool: string): Record<string, string> {
  const ex = examples.find(e => e.tool === tool)
  const args: Record<string, string> = {}
  for (const [k, v] of Object.entries(ex?.args ?? {})) args[k] = k === 'since' ? String(v).slice(0, 10) : String(v)
  if (TOOLS.find(t => t.name === tool)!.fields.some(f => f.name === 'actor')) args.actor = 'playground'
  return args
}

export default function Agents() {
  const feed = useActivity()
  const [tool, setTool] = useState(TOOLS[0].name)
  const [args, setArgs] = useState(() => exampleArgs(TOOLS[0].name))
  const [out, setOut] = useState<{ tool: string; ms: number; data?: unknown; error?: string }>()
  const [busy, setBusy] = useState(false)
  const spec = TOOLS.find(t => t.name === tool)!

  const pick = (name: string) => { setTool(name); setArgs(exampleArgs(name)); setOut(undefined) }
  const run = async () => {
    setBusy(true)
    const t0 = performance.now()
    const typed: Record<string, unknown> = { ...args }
    if ('limit' in typed) typed.limit = Number(typed.limit) || 5
    try { const data = await callTool(tool, typed); setOut({ tool, ms: Math.round(performance.now() - t0), data }) }
    catch (e) { setOut({ tool, ms: Math.round(performance.now() - t0), error: String((e as Error).message) }) }
    finally { setBusy(false) }
  }
  const check = out?.tool === 'check_intent' && out.data ? out.data as CheckResult : undefined

  return (
    <main className="page">
      <div style={{ marginBottom: 22 }}>
        <div className="label">Agents / the same MCP tools Claude Code and Codex call</div>
        <h1 className="h1" style={{ fontSize: 36, marginTop: 8 }}>Agents read the record before they act.</h1>
      </div>

      <section className="connect pad" style={{ marginBottom: 24 }}>
        <div className="row" style={{ justifyContent: 'space-between', flexWrap: 'wrap' }}>
          <h2 className="h3">Connect your agent</h2>
          <span className="small muted">Streamable HTTP, no key needed for the demo.</span>
        </div>
        <div className="grid two" style={{ gap: 16, marginTop: 4 }}>
          <div><div className="label" style={{ marginTop: 8 }}>MCP URL</div><div className="cmd">{MCP_URL}</div></div>
          <div><div className="label" style={{ marginTop: 8 }}>Claude Code</div><div className="cmd">claude mcp add --transport http canon {MCP_URL}</div></div>
        </div>
      </section>

      <div className="grid agents-grid">
        <nav className="tools" aria-label="MCP tools">
          <div className="label" style={{ marginBottom: 6 }}>MCP tools</div>
          {TOOLS.map(t => <button key={t.name} className={tool === t.name ? 'on' : ''} aria-pressed={tool === t.name} onClick={() => pick(t.name)}>{t.name}<small>{t.blurb}</small></button>)}
        </nav>

        <section>
          <form className="sheet pad" onSubmit={e => { e.preventDefault(); run() }}>
            <div className="row" style={{ justifyContent: 'space-between' }}><h2 className="h3">{tool}</h2><span className="label">example loaded</span></div>
            {spec.fields.map(f => (
              <label key={f.name} className="field" style={{ display: 'block' }}>
                <span className="label">{f.name}</span>
                {f.kind === 'persona'
                  ? <select className="input" value={args[f.name] ?? 'engineer'} onChange={e => setArgs({ ...args, [f.name]: e.target.value })}>{['engineer', 'pm', 'new_hire'].map(p => <option key={p}>{p}</option>)}</select>
                  : f.long
                    ? <textarea className="input" rows={3} value={args[f.name] ?? ''} onChange={e => setArgs({ ...args, [f.name]: e.target.value })} style={{ fontFamily: 'var(--sans)', fontSize: 16 }} />
                    : <input className="input" type={f.kind === 'number' ? 'number' : 'text'} value={args[f.name] ?? ''} onChange={e => setArgs({ ...args, [f.name]: e.target.value })} />}
              </label>
            ))}
            <div className="row" style={{ marginTop: 14, justifyContent: 'space-between' }}>
              <span className="label">POST /mcp / tools/call</span>
              <button className="btn" type="submit" disabled={busy}>{busy ? 'Calling' : 'Call tool'}</button>
            </div>
          </form>

          {busy && <div className="state" role="status" style={{ marginTop: 16 }}><div className="label ink">Calling {tool} over MCP...</div></div>}
          {out?.error && (
            <div className="state err" role="alert" style={{ marginTop: 16 }}>
              <div className="label ink">The tool call failed</div><p className="small muted" style={{ marginTop: 6 }}>{out.error}</p>
            </div>
          )}
          {check && (
            <div className={`verdict-big ${check.verdict}`} style={{ marginTop: 16 }}>
              <span className="label" style={{ color: '#fff' }}>Verdict</span><b>{check.verdict}</b>
              <span style={{ fontSize: 15 }}>
                {check.decisions[0]
                  ? <>Deciding: <Link to={`/decisions/${check.decisions[0].id}`} style={{ textDecoration: 'underline' }}>{check.decisions[0].statement}</Link> ({check.decisions[0].owner})</>
                  : check.explanation}
              </span>
              <span className="label" style={{ color: '#fff', marginLeft: 'auto', whiteSpace: 'nowrap' }}>{out!.ms} ms</span>
            </div>
          )}
          {out?.data !== undefined && (
            <>
              {!check && <div className="label" style={{ margin: '16px 0 6px' }}>Response / {out.ms} ms round trip</div>}
              <pre className="resp" tabIndex={0} aria-label="Raw tool response">{JSON.stringify(out.data, null, 2)}</pre>
            </>
          )}
        </section>

        <aside><ActivityFeed feed={feed} limit={10} /></aside>
      </div>
    </main>
  )
}
