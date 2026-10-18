import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Bar, ErrorState, TextSkeleton, friendly } from '@/components/states'
import { callTool } from '@/lib/mcp'
import { q } from '@/lib/query'
import { fmtLong, PUBLIC_URL, srcLine } from '@/lib/record'
import { CheckResult, type Verdict } from '@/lib/schemas'
import { useTitle } from '@/lib/title'

const REQUEST = 'Add a job that deploys the dispatch service to production every Friday at 15:00.'
const INTENT = 'Deploy the production dispatch service every Friday at 15:00 SGT using a cron job.'

const SAMPLES = [
  { label: 'Release a config change on Friday', intent: 'Release a configuration-only change to production this Friday afternoon.' },
  { label: 'Quote a new customer USD 99', intent: 'Send a new Route Lens customer a quote at USD 99 per workspace per month.' },
  { label: 'Deploy on Tuesday morning', intent: 'Deploy the dispatch service to production on Tuesday at 10:00 SGT.' },
]
const FIRST = 'Keep the five-minute fleet dashboard cache now that traffic is 3,400 events a second.'

const VERDICT_WORD: Record<Verdict, string> = { allow: 'Allow', warn: 'Check with a person first', block: 'Block' }

export default function AgentPage() {
  useTitle('watch an AI agent get stopped')
  const check = useQuery(q.check(INTENT))
  const people = useQuery(q.people())
  const rule = check.data?.decisions[0]
  const cite = check.data?.citations.find(c => c.decision_id === rule?.id) ?? check.data?.citations[0]
  const role = people.data?.find(p => p.name === rule?.owner)?.role.toLowerCase()
  const verdict = check.data?.verdict

  return (
    <main className="wrap">
      <h1>Watch an AI agent get stopped.</h1>
      <p className="lede">
        Coding agents write and ship code on their own. They do not know what your team decided last spring. Canon gives them that memory, and they
        ask it before they act.
      </p>

      <div className="story">
        <ol className="steps">
          <li>
            <span>
              A developer asks Claude Code: <q>{REQUEST}</q>
            </span>
          </li>
          <li>
            <span>Before it writes anything, the agent asks Canon whether this is allowed. A real tool call, not a script.</span>
          </li>
          <li className="now">
            <span>Canon finds the rule, who made it, when, and the outage behind it. It says no.</span>
          </li>
          <li>
            <span>The agent does not add the job. It explains why and offers Tuesday or Thursday morning instead.</span>
          </li>
        </ol>
        {check.isError ? (
          <ErrorState error={check.error} retry={() => void check.refetch()} />
        ) : check.isPending ? (
          <div className="verdict block" role="status" aria-label="Asking Canon" aria-busy="true">
            <Bar w={180} h={56} />
            <div style={{ marginTop: 20 }}>
              <TextSkeleton lines={4} />
            </div>
          </div>
        ) : (
          <div className={verdict === 'block' ? 'verdict block' : 'verdict'}>
            <div className="word">{VERDICT_WORD[check.data.verdict]}</div>
            <p className="rule">{rule?.statement ?? check.data.explanation}</p>
            {rule && (
              <dl>
                <dt>Owner</dt>
                <dd>
                  {rule.owner}
                  {role ? `, ${role}` : ''}
                </dd>
                <dt>Decided</dt>
                <dd>
                  {fmtLong(rule.ts)}
                  {cite ? `, in ${cite.title}` : ''}
                </dd>
                <dt>Why</dt>
                <dd>{rule.rationale}</dd>
              </dl>
            )}
            <p className="next">
              Every check is written to the record, so people can see what their agents asked.{' '}
              {rule && <Link to={`/decisions/${rule.id}`}>See this decision</Link>}
            </p>
          </div>
        )}
      </div>

      <div className="section">
        <h2>The same exchange, as the agent saw it</h2>
        <div className="term">
          <div className="step">
            <div className="who">developer</div>
            {REQUEST}
          </div>
          <div className="step">
            <div className="who">claude code</div>
            <span className="dim">Before I write this, I will check it against the company's decisions.</span>
            <div className="call">
              canon.check_intent
              <br />
              <span className="dim">action:</span> "{INTENT}"
            </div>
          </div>
          <div className="step">
            <div className="who">canon</div>
            {check.data ? (
              <>
                <span className={verdict === 'block' ? 'red' : verdict === 'allow' ? 'green' : undefined}>{check.data.verdict.toUpperCase()}</span>{' '}
                {check.data.explanation}
                {rule && (
                  <>
                    <br />
                    <span className="dim">
                      owner: {rule.owner} &nbsp; decided: {rule.ts.slice(0, 10)}
                      {cite && <> &nbsp; source: {cite.title}</>}
                      <br />
                      answered in {check.data.latency_ms} ms
                    </span>
                  </>
                )}
              </>
            ) : (
              <span className="dim">{check.isError ? 'Canon did not answer.' : 'checking...'}</span>
            )}
          </div>
          <div className="step">
            <div className="who">claude code</div>I did not add this job. Northwind banned production deploys on Fridays after an outage in March, and
            the ban covers scheduled jobs. <span className="green">I can schedule it for Tuesday or Thursday morning instead. Which one?</span>
          </div>
        </div>
        <p className="small muted" style={{ marginTop: 12 }}>
          Canon's lines are the live answer to this check. The developer and agent lines show the conversation around it.
        </p>
      </div>

      <div className="section grid2">
        <TryIt />
        <div>
          <h2>Connect your own agent</h2>
          <p className="muted" style={{ marginTop: 8 }}>
            Canon speaks MCP, the standard plug that lets AI assistants use outside tools. One line connects it.
          </p>
          <p className="label" style={{ marginTop: 28 }}>
            Claude Code
          </p>
          <code className="line">claude mcp add --transport http canon {PUBLIC_URL}/mcp</code>
          <p className="label" style={{ marginTop: 20 }}>
            Codex
          </p>
          <code className="line">codex mcp add canon --url {PUBLIC_URL}/mcp</code>
          <p className="small muted" style={{ marginTop: 20 }}>
            Your agent gets six tools: search decisions, ask why, catch me up, check an action, record a decision, and flag a conflict.
          </p>
        </div>
      </div>
    </main>
  )
}

function TryIt() {
  const [params] = useSearchParams()
  // /agent?intent=... pre-fills the box (the judge path on Home links here), capped like the API.
  const [intent, setIntent] = useState(params.get('intent')?.slice(0, 2000) || FIRST)
  const run = useMutation({
    mutationFn: async (i: string) => CheckResult.parse(await callTool('check_intent', { intent: i, actor: 'playground' })),
  })
  const r = run.data
  const cite = r?.citations[0]
  return (
    <div id="try">
      <h2>Try it yourself</h2>
      <p className="muted" style={{ margin: '8px 0 24px' }}>
        Describe something an agent wants to do. Canon tells you if it is allowed.
      </p>
      <form
        onSubmit={e => {
          e.preventDefault()
          if (intent.trim()) run.mutate(intent.trim())
        }}
      >
        <textarea className="input" aria-label="An action an agent wants to take" value={intent} onChange={e => setIntent(e.target.value)} />
        <div className="choices small" style={{ marginTop: 14 }}>
          {SAMPLES.map(s => (
            <button
              key={s.label}
              type="button"
              aria-pressed={intent === s.intent}
              onClick={() => {
                setIntent(s.intent)
                run.mutate(s.intent)
              }}
            >
              {s.label}
            </button>
          ))}
        </div>
        <div style={{ marginTop: 20 }}>
          <button type="submit" className="btn" disabled={run.isPending || !intent.trim()}>
            {run.isPending ? 'Checking...' : 'Check it'}
          </button>
        </div>
      </form>
      <div aria-live="polite">
        {run.isError && (
          <div className="result">
            <p>
              <b>The check did not run.</b> {friendly(run.error)}
            </p>
          </div>
        )}
        {r && (
          <div className="result">
            <p>
              <b className={r.verdict === 'block' ? 'breaks' : undefined}>{VERDICT_WORD[r.verdict]}.</b> {r.explanation}
            </p>
            {cite && <p className="src">{srcLine(cite)}.</p>}
            <p className="src">Called check_intent over MCP in {r.latency_ms} ms.</p>
          </div>
        )}
      </div>
      <div className="legend">
        <span>
          <b>Allow</b>, no rule against it
        </span>
        <span>
          <b>Warn</b>, check with a person first
        </span>
        <span>
          <b className="breaks">Block</b>, it breaks a decision
        </span>
      </div>
    </div>
  )
}
