import { useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { ErrorState, ListSkeleton } from '@/components/states'
import { q } from '@/lib/query'
import { fmtLong, noteFigures } from '@/lib/record'
import type { EvalReport } from '@/lib/schemas'
import { useTitle } from '@/lib/title'

const s = (ms: number) => (ms / 1000).toFixed(1)
const MODEL: Record<string, string> = { 'gemini-3.5-flash-lite': 'Gemini 3.5 Flash Lite' }

/** One result row per figure. Every number is read from the report by key, so a new run updates the page. */
export function rows(r: EvalReport): { key: string; fig: ReactNode; title: string; body: ReactNode }[] {
  const n = noteFigures(r.notes)
  const miss = r.notes.find(x => x.startsWith('check miss'))
  const out = [
    {
      key: 'decisions_found',
      fig: <Frac a={r.decisions_found} b={r.decisions_planted} />,
      title: `Found ${r.decisions_found} of ${r.decisions_planted} decisions`,
      body: 'From messy chats and transcripts, Canon pulled out the real decisions, with who made them and when.',
    },
    {
      key: 'contradictions_found',
      fig: <Frac a={r.contradictions_found} b={r.contradictions_planted} />,
      title: `Caught ${r.contradictions_found} of ${r.contradictions_planted} changes and contradictions`,
      body: `When a new message changed or went against an old decision, Canon noticed. It raised ${r.false_positives} false alarm${r.false_positives === 1 ? '' : 's'}.`,
    },
  ]
  if (n.stale)
    out.push({
      key: 'stale_found',
      fig: <Frac a={n.stale.found} b={n.stale.of} />,
      title:
        n.stale.found === n.stale.of
          ? `Found all ${n.stale.of} out-of-date documents`
          : `Found ${n.stale.found} of ${n.stale.of} out-of-date documents`,
      body: 'Wiki pages that still describe an old decision were flagged.',
    })
  out.push(
    {
      key: 'check_correct',
      fig: <Frac a={r.check_correct} b={r.check_cases} />,
      title: `Gave agents the right answer ${r.check_correct} of ${r.check_cases} times`,
      body: `Allow, warn or block.${miss ? ` The miss: ${miss.replace(/^check miss [\w-]+:\s*/, '')}.` : ''}`,
    },
    {
      key: 'refused_correctly',
      fig: <Frac a={r.refused_correctly} b={r.unanswerable} />,
      title: `Said "I do not know" to ${r.refused_correctly === r.unanswerable ? 'all ' : ''}${r.refused_correctly} of ${r.unanswerable} questions it could not answer`,
      body: 'It did not make anything up when the record had no answer.',
    },
    {
      key: 'p50_ms',
      fig: (
        <>
          {s(r.p50_ms)} <small>s</small>
        </>
      ),
      title: `A typical answer in ${s(r.p50_ms)} seconds`,
      body: `Half of all questions and checks came back faster than this. 95 in 100 came back within ${s(r.p95_ms)} seconds.`,
    },
  )
  if (n.quotes !== null)
    out.push({
      key: 'quotes',
      fig: <>{n.quotes}</>,
      title: `Every one of ${n.quotes} quotes checked word for word`,
      body: 'Canon keeps a quote only if it appears exactly in the source. No invented quotes.',
    })
  return out
}

/** Memory health: the labelled replay of data/gold/authority_cases.json. Rows appear only for fields the report carries. */
export function healthRows(r: EvalReport): { key: string; fig: ReactNode; title: string; body: ReactNode }[] {
  const out = []
  const stored = r.health_decisions_stored
  if (stored != null && r.health_untraceable != null) {
    const good = stored - r.health_untraceable
    out.push({
      key: 'health_untraceable',
      fig: <Frac a={good} b={stored} />,
      title: r.health_untraceable === 0 ? `All ${stored} stored decisions are real` : `${good} of ${stored} stored decisions are real`,
      body: `Each stored decision was traced back to one the test set planted. ${r.health_untraceable === 0 ? 'Nothing was invented' : `${r.health_untraceable} matched nothing`}.`,
    })
  }
  if (r.health_duplicates != null)
    out.push({
      key: 'health_duplicates',
      fig: <>{r.health_duplicates}</>,
      title:
        r.health_duplicates === 0
          ? 'No decision stored twice'
          : `${r.health_duplicates} decision${r.health_duplicates === 1 ? '' : 's'} stored twice`,
      body: 'When the same rule came in from several places, Canon kept one decision and added the new quote to it.',
    })
  if (r.health_checkpoints != null && r.health_checkpoints_correct != null)
    out.push({
      key: 'health_checkpoints_correct',
      fig: <Frac a={r.health_checkpoints_correct} b={r.health_checkpoints} />,
      title: `Right set of rules at ${r.health_checkpoints_correct} of ${r.health_checkpoints} points in time`,
      body: 'We stopped the replay at the end of each quarter and compared the decisions in force with the answer key.',
    })
  if (r.health_chains != null && r.health_chains_correct != null)
    out.push({
      key: 'health_chains_correct',
      fig: <Frac a={r.health_chains_correct} b={r.health_chains} />,
      title: `Kept the history of ${r.health_chains_correct} of ${r.health_chains} rules that changed over time`,
      body: 'Each new version points back at the one it replaced, in the right order.',
    })
  if (r.authority_cases != null && r.authority_correct != null)
    out.push({
      key: 'authority_correct',
      fig: <Frac a={r.authority_correct} b={r.authority_cases} />,
      title: `Told official decisions from proposals and claims in ${r.authority_correct} of ${r.authority_cases} cases`,
      body: 'A guest or someone outside the area cannot overrule an official decision. Canon flags it as unverified and names who should confirm it. An old copy of a document does not undo a newer rule.',
    })
  return out
}

function Results({ list }: { list: ReturnType<typeof rows> }) {
  return (
    <ol className="results">
      {list.map(x => (
        <li key={x.key} data-key={x.key}>
          <div className="fig">{x.fig}</div>
          <div>
            <h3>{x.title}</h3>
            <p>{x.body}</p>
          </div>
        </li>
      ))}
    </ol>
  )
}

function Frac({ a, b }: { a: number; b: number }) {
  return (
    <>
      {a} <small>of {b}</small>
    </>
  )
}

export default function BenchmarkPage() {
  useTitle('how well does it work?')
  const report = useQuery(q.evalReport())
  const r = report.data
  return (
    <main className="wrap">
      <h1>How well does it work?</h1>
      <p className="lede">
        We hid known decisions, changes and conflicts in Northwind's history, then checked how many Canon found on its own.
        {r ? ` These are the results of the last run, on ${fmtLong(r.run_at)}.` : ''}
      </p>
      {report.isError ? (
        <ErrorState error={report.error} retry={() => void report.refetch()} />
      ) : !r ? (
        <div style={{ marginTop: 28 }}>
          <ListSkeleton rows={6} label="Loading the results" />
        </div>
      ) : (
        <>
          <Results list={rows(r)} />
          {healthRows(r).length > 0 && (
            <div className="section">
              <h2>Memory health</h2>
              <p className="lede" style={{ marginTop: 12 }}>
                A memory is only useful if it stays clean. We replayed a small labelled history in date order, with real Gemini calls, and checked
                what Canon kept.
              </p>
              <Results list={healthRows(r)} />
            </div>
          )}
          <p className="small muted" style={{ marginTop: 24 }}>
            Model: {MODEL[r.model] ?? r.model} on Vertex AI, in Mumbai (asia-south1). The test set and the scoring script are in the GitHub repo.
          </p>
        </>
      )}
    </main>
  )
}
