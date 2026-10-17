import { useSuspenseQuery } from '@tanstack/react-query'
import { Section } from '@/components/error-boundary'
import { PageHeader } from '@/components/page-header'
import { SectionHead } from '@/components/section-head'
import { RowsSkeleton } from '@/components/states'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { fmtDate, fmtTime } from '@/lib/format'
import { q } from '@/lib/query'

export const pct = (a: number, b: number) => (b ? Math.round((a / b) * 100) : 0)

export default function BenchmarkPage() {
  return (
    <main className="mx-auto max-w-[1440px] px-4 pt-8 pb-12 md:px-8">
      <Section fallback={<ReportSkeleton />}>
        <Report />
      </Section>
    </main>
  )
}

function Report() {
  const { data: e } = useSuspenseQuery(q.evalReport())
  const rows: [string, number, number][] = [
    ['Decisions extracted', e.decisions_planted, e.decisions_found],
    ['Contradictions and updates', e.contradictions_planted, e.contradictions_found],
    ['check_intent verdicts (allow, warn, block)', e.check_cases, e.check_correct],
    ['Unanswerable questions, refused', e.unanswerable, e.refused_correctly],
  ]
  return (
    <>
      <PageHeader
        eyebrow={`Benchmark / labelled gold set / run ${fmtDate(e.run_at)} ${fmtTime(e.run_at)} / ${e.model}`}
        title="We planted the problems."
        quiet="Here is what Canon found."
      />
      <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Kpi label="Contradictions found" value={e.contradictions_found} of={e.contradictions_planted} note="Planted across Slack, wiki and PRs" />
        <Kpi
          label="False positives"
          value={e.false_positives}
          meter={Math.min(100, e.false_positives * 4)}
          hot
          note="Alerts with no planted conflict behind them"
        />
        <Kpi label="Refused correctly" value={e.refused_correctly} of={e.unanswerable} note='Unanswerable questions answered "I do not know"' />
        <Card size="sm">
          <CardContent className="flex flex-col gap-2">
            <span className="label text-foreground">Latency p50 / p95</span>
            <span className="font-heading text-5xl leading-none tnum">
              {(e.p50_ms / 1000).toFixed(1)}
              <span className="text-2xl text-muted-foreground"> / {(e.p95_ms / 1000).toFixed(1)} s</span>
            </span>
            <Progress value={Math.min(100, pct(e.p50_ms, 5000))} aria-label="p50 latency against a 5 second budget" className="h-1.5" />
            <span className="text-sm text-muted-foreground">End to end, per call</span>
          </CardContent>
        </Card>
      </div>

      <div className="mt-10 grid gap-10 lg:grid-cols-2">
        <section aria-labelledby="task-h">
          <SectionHead id="task-h" title="By task" note="data/gold/gold.json" />
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="label">Task</TableHead>
                <TableHead className="label text-right">Planted</TableHead>
                <TableHead className="label text-right">Found</TableHead>
                <TableHead className="label text-right">Score</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map(([t, p, f]) => (
                <TableRow key={t}>
                  <TableCell className="whitespace-normal">{t}</TableCell>
                  <TableCell className="text-right tnum">{p}</TableCell>
                  <TableCell className="text-right tnum">{f}</TableCell>
                  <TableCell className="text-right font-medium tnum">{pct(f, p)}%</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </section>
        <Card className="self-start">
          <CardContent>
            <p className="label mb-3 text-foreground">Notes and misses, in the open</p>
            {e.notes.length === 0 ? (
              <p className="text-muted-foreground">No notes for this run.</p>
            ) : (
              <ul className="list-disc space-y-2 pl-5 text-[15px]">
                {e.notes.map((n, i) => (
                  <li key={i}>{n}</li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  )
}

function Kpi({ label, value, of, meter, note, hot }: { label: string; value: number; of?: number; meter?: number; note: string; hot?: boolean }) {
  return (
    <Card size="sm">
      <CardContent className="flex flex-col gap-2">
        <span className="label text-foreground">{label}</span>
        <span className="font-heading text-5xl leading-none tnum">
          {value}
          {of !== undefined && <span className="text-2xl text-muted-foreground"> / {of}</span>}
        </span>
        <Progress
          value={meter ?? pct(value, of ?? 0)}
          aria-label={of !== undefined ? `${value} of ${of}` : label}
          className={hot ? 'h-1.5 [&>[data-slot=progress-indicator]]:bg-signal' : 'h-1.5'}
        />
        <span className="text-sm text-muted-foreground">{note}</span>
      </CardContent>
    </Card>
  )
}

function ReportSkeleton() {
  return (
    <div className="flex flex-col gap-8" role="status" aria-label="Loading the last benchmark run">
      <Skeleton className="h-4 w-96" />
      <Skeleton className="h-12 w-2/3" />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[0, 1, 2, 3].map(i => (
          <Skeleton key={i} className="h-36" />
        ))}
      </div>
      <RowsSkeleton rows={4} />
    </div>
  )
}
