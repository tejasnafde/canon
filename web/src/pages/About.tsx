import { Link } from 'react-router-dom'

export default function About() {
  return (
    <main className="page" style={{ maxWidth: 860 }}>
      <div className="label">About</div>
      <h1 className="h1" style={{ marginTop: 8 }}>One record of decisions, for people and agents.</h1>
      <p className="lede" style={{ marginTop: 18 }}>
        Canon is the shared memory of a company. It reads Slack threads, meeting notes, wiki pages, PRs and email,
        pulls out each decision with a quote checked word for word, and flags anything that drifts from the record.
        AI agents call the same record over MCP and get blocked when they are about to break a decision.
      </p>

      <div className="state" style={{ marginTop: 24, borderStyle: 'solid', borderColor: 'var(--warn)', background: 'var(--warn-bg)' }}>
        <div className="label ink">All data is synthetic</div>
        <p className="small" style={{ marginTop: 6 }}>Northwind Labs, its people and its decisions are invented for this demo. No real company or customer data is used. What you ingest goes to a private workspace for your browser only.</p>
      </div>

      <section style={{ marginTop: 28 }}>
        <div className="sec"><h2 className="h3">The stack</h2></div>
        <table>
          <tbody>
            <tr><td><b>Gemini on Vertex AI</b></td><td>Extraction, reconciliation, answers and agent checks, with structured output. Embeddings for retrieval.</td></tr>
            <tr><td><b>ADK</b></td><td>The Canon agent, also reachable over A2A.</td></tr>
            <tr><td><b>Firestore vector search</b></td><td>Decisions, sources, alerts and activity, with vector indexes on decisions and chunks.</td></tr>
            <tr><td><b>Cloud Run</b></td><td>One service: the HTTP API, the MCP server at /mcp and the A2A endpoint.</td></tr>
            <tr><td><b>Firebase Hosting</b></td><td>Serves this web app and forwards API and MCP calls to Cloud Run.</td></tr>
          </tbody>
        </table>
      </section>

      <section style={{ marginTop: 28 }}>
        <div className="sec"><h2 className="h3">Where to start</h2></div>
        <ul className="small" style={{ paddingLeft: 18, lineHeight: 1.9, marginTop: 8 }}>
          <li><Link className="lnk" to="/ask">Ask why</Link> the team stopped deploying on Fridays.</li>
          <li><Link className="lnk" to="/ingest">Ingest</Link> a sample that contradicts the record and watch the alert appear on Home.</li>
          <li><Link className="lnk" to="/agents">Call check_intent</Link> over MCP and see the agent get blocked.</li>
        </ul>
      </section>
    </main>
  )
}
