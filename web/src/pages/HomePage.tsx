import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Bar } from '@/components/states'
import { q } from '@/lib/query'
import { DISCORD_INVITE, quotedSourceCount, staleDocIds } from '@/lib/record'
import { useTitle } from '@/lib/title'

const REFUSAL = 'What is Northwind Labs annual recurring revenue for 2026?'
const ask = (question: string) => `/ask?q=${encodeURIComponent(question)}`

export default function HomePage() {
  useTitle()
  const stats = useQuery(q.stats())
  // until /api/stats is deployed (404), count from the lists as before
  const fallback = stats.isError
  const decisions = useQuery(q.decisions())
  const alerts = useQuery({ ...q.alerts(), enabled: fallback })
  const n = stats.data?.decisions ?? decisions.data?.length
  const sources = stats.data?.sources ?? (fallback && decisions.data ? quotedSourceCount(decisions.data) : undefined)
  const official = stats.data?.decisions_official ?? (fallback ? decisions.data?.filter(d => d.authority === 'official').length : undefined)
  const stale = stats.data?.stale_docs ?? (fallback && alerts.data ? staleDocIds(alerts.data).length : undefined)
  const failed = fallback && (decisions.isError || alerts.isError)

  const fig = (value: number | undefined, label: string, failed: boolean) => (
    <div>
      {value === undefined ? (
        failed ? (
          <span className="faint">-</span>
        ) : (
          <Bar w={56} h={30} style={{ display: 'inline-block', verticalAlign: -4 }} />
        )
      ) : (
        value
      )}
      <small>{label}</small>
    </div>
  )

  return (
    <main className="wrap">
      <div className="hero">
        <div>
          <h1>The shared memory of a company, for its people and its AI agents.</h1>
          <p className="lede">
            Teams decide things in Slack threads, meetings and pull requests, then forget. Canon keeps every decision and the reason behind it, and
            warns you when a person, a document or an AI agent is about to break one.
          </p>
        </div>
        <div>
          <div className="figures" aria-busy={sources === undefined || official === undefined || stale === undefined}>
            {fig(sources, stats.data ? 'items read' : 'sources quoted', failed)}
            {fig(official, 'official decisions', failed)}
            {fig(stale, 'documents now out of date', failed)}
          </div>
          {n !== undefined && official !== undefined && n > official && (
            <p className="small muted" style={{ marginTop: 14 }}>
              {n} decisions on record in all. The other {n - official} are proposals or claims nobody has confirmed yet.
            </p>
          )}
          <p className="demo">
            Northwind Labs is a made-up 60-person logistics software company. Canon read two years of its Slack, meetings, wiki pages and pull
            requests, January 2025 to October 2026.
          </p>
        </div>
      </div>

      <div className="section judges">
        <h2>For judges: try this in two minutes</h2>
        <ol className="tryit">
          <li>
            <Link to="/new-hire">New hire</Link>
            <span>Open it. The Release process wiki is flagged as out of date, with the newer decision beside it.</span>
          </li>
          <li>
            <Link to="/agent">For agents</Link>
            <span>
              Under Try it yourself, type <q>Add a cron job that deploys the dispatch service to production every Friday at 15:00</q>. The verdict is
              Block.
            </span>
          </li>
          <li>
            <Link to="/paste">Paste</Link>
            <span>Click the sample Friday deploy job, then Check this message. You see the conflict and the stale wiki.</span>
          </li>
          <li>
            <Link to={ask("What's our tech stack?")}>Ask why</Link>
            <span>
              Ask <Link to={ask("What's our tech stack?")}>What's our tech stack?</Link> or{' '}
              <Link to={ask('Why did we choose Postgres?')}>Why did we choose Postgres?</Link> Then <Link to={ask(REFUSAL)}>{REFUSAL}</Link> Canon
              says it does not know.
            </span>
          </li>
          <li>
            <a href={DISCORD_INVITE} target="_blank" rel="noreferrer">
              Discord
            </a>
            <span>Join the server and post in #engineering. Canon replies under your message within about a minute.</span>
          </li>
        </ol>
        <p className="proof small">
          <a href="https://github.com/tejasnafde/canon">GitHub repo</a>
          <a href="https://canon-tn07.web.app">Firebase Hosting</a>
          <a href="https://canon-ezvux7gqxa-el.a.run.app/health">Cloud Run</a>
          <a href="https://canon.tn07.dev/mcp">MCP endpoint</a>
          <Link to="/benchmark">How well does it work</Link>
        </p>
      </div>

      <div className="section">
        <h2>Pick a story</h2>
        <ul className="stories">
          <Story to="/new-hire" title="I am new here" go="Two minutes">
            The things every new person at Northwind must know, which document is wrong, and who to ask.
          </Story>
          <Story to="/catch-up" title="What changed while I was away?" go="One minute">
            Pick your role. Get a short summary and a to-do list, most urgent first.
          </Story>
          <Story to="/agent" title="Watch an AI agent get stopped" go="Live">
            A coding agent is asked to deploy on a Friday. It checks with Canon first, and Canon says no.
          </Story>
          <Story to="/paste" title="Paste a new message and see what it breaks" go="Try it" minor>
            Canon reads it, checks it against {n ? `all ${n}` : 'every one of the'} decisions, and shows any conflict in a few seconds.
          </Story>
          <li className="minor">
            <a href={DISCORD_INVITE} target="_blank" rel="noreferrer">
              <h3>Talk to Canon in Discord</h3>
              <span className="go">Join the server</span>
              <p>Post a message in the Northwind Labs server. Canon learns it within two minutes.</p>
            </a>
          </li>
        </ul>
      </div>
    </main>
  )
}

function Story({ to, title, go, minor, children }: { to: string; title: string; go: string; minor?: boolean; children: React.ReactNode }) {
  return (
    <li className={minor ? 'minor' : undefined}>
      <Link to={to}>
        <h3>{title}</h3>
        <span className="go">{go}</span>
        <p>{children}</p>
      </Link>
    </li>
  )
}
