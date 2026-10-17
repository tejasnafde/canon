import { TriangleAlert } from 'lucide-react'
import { Link } from 'react-router-dom'
import { PageHeader } from '@/components/page-header'
import { SectionHead } from '@/components/section-head'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Table, TableBody, TableCell, TableRow } from '@/components/ui/table'

const STACK: [string, string][] = [
  ['Gemini on Vertex AI', 'Extraction, reconciliation, answers and agent checks, with structured output. Embeddings for retrieval.'],
  ['ADK', 'The Canon agent, also reachable over A2A.'],
  ['Firestore vector search', 'Decisions, sources, alerts and activity, with vector indexes on decisions and chunks.'],
  ['Cloud Run', 'One service: the HTTP API, the MCP server at /mcp and the A2A endpoint.'],
  ['Firebase Hosting', 'Serves this web app and forwards API and MCP calls to Cloud Run.'],
]

const link = 'text-link underline underline-offset-4'

export default function AboutPage() {
  return (
    <main className="mx-auto max-w-[860px] px-4 pt-8 pb-12 md:px-8">
      <PageHeader eyebrow="About" title="One record of decisions, for people and agents." />
      <p className="mt-6 font-heading text-[22px] leading-snug text-pretty">
        Canon is the shared memory of a company. It reads Slack threads, meeting notes, wiki pages, PRs and email, pulls out each decision with a
        quote checked word for word, and flags anything that drifts from the record. AI agents call the same record over MCP and get blocked when they
        are about to break a decision.
      </p>

      <Alert className="mt-8 border-warn-ink/40 bg-warn-soft">
        <TriangleAlert aria-hidden className="text-warn-ink" />
        <AlertTitle>All data is synthetic</AlertTitle>
        <AlertDescription className="text-foreground">
          Northwind Labs, its people and its decisions are invented for this demo. No real company or customer data is used. What you ingest goes to a
          private workspace for your browser only.
        </AlertDescription>
      </Alert>

      <section className="mt-10" aria-labelledby="stack-h">
        <SectionHead id="stack-h" title="The stack" />
        <Table>
          <TableBody>
            {STACK.map(([k, v]) => (
              <TableRow key={k}>
                <TableCell className="w-56 align-top font-medium whitespace-normal">{k}</TableCell>
                <TableCell className="whitespace-normal">{v}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </section>

      <section className="mt-10" aria-labelledby="start-h">
        <SectionHead id="start-h" title="Where to start" />
        <ul className="mt-3 list-disc space-y-2 pl-5">
          <li>
            <Link className={link} to="/ask">
              Ask why
            </Link>{' '}
            the team stopped deploying on Fridays.
          </li>
          <li>
            <Link className={link} to="/ingest">
              Ingest
            </Link>{' '}
            a sample that contradicts the record and watch the alert appear on Home.
          </li>
          <li>
            <Link className={link} to="/agents">
              Call check_intent
            </Link>{' '}
            over MCP and see the agent get blocked.
          </li>
          <li>
            Press <kbd className="rounded-sm border bg-muted px-1.5 font-mono text-sm">Ctrl K</kbd> anywhere to jump to a decision or ask a question.
          </li>
        </ul>
      </section>
    </main>
  )
}
