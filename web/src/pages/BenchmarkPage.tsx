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
          <ol className="results">
            {rows(r).map(x => (
              <li key={x.key} data-key={x.key}>
                <div className="fig">{x.fig}</div>
                <div>
                  <h3>{x.title}</h3>
                  <p>{x.body}</p>
                </div>
              </li>
            ))}
          </ol>
          <p className="small muted" style={{ marginTop: 24 }}>
            Model: {MODEL[r.model] ?? r.model} on Vertex AI, in Mumbai (asia-south1). The test set and the scoring script are in the GitHub repo.
          </p>
        </>
      )}
    </main>
  )
}
