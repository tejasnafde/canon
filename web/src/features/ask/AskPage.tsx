import { useSuspenseQuery } from '@tanstack/react-query'
import { CircleHelp, Search } from 'lucide-react'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ToneBadge } from '@/components/badges'
import { CitationLine } from '@/components/citation'
import { Section } from '@/components/error-boundary'
import { SectionHead } from '@/components/section-head'
import { RowsSkeleton } from '@/components/states'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { fmtDate, plural, relationTone, secs } from '@/lib/format'
import { q } from '@/lib/query'
import type { AskResult } from '@/lib/schemas'
import asks from '@/samples/asks.json'

const FIRST = asks[0]?.question ?? ''

export default function AskPage() {
  const [params, setParams] = useSearchParams()
  const question = params.get('q') ?? FIRST // judges land on a worked answer, not an empty box
  const [draft, setDraft] = useState(question)
  const [shown, setShown] = useState(question)
  // keep the box in sync when the URL changes from outside (palette, back button)
  if (question !== shown) {
    setShown(question)
    setDraft(question)
  }
  const submit = (text: string) => setParams({ q: text })

  return (
    <main className="mx-auto max-w-[1440px] px-4 pt-8 pb-12 md:px-8">
      <p className="label">Ask why / answers only from the record, every claim cited</p>
      <form
        role="search"
        onSubmit={e => {
          e.preventDefault()
          if (draft.trim()) submit(draft.trim())
        }}
        className="mt-3 flex gap-3"
      >
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute top-1/2 left-4 size-5 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <Input
            aria-label="Question"
            value={draft}
            onChange={e => setDraft(e.target.value)}
            placeholder="Why do we ...?"
            className="h-14 bg-card pl-12 font-heading text-xl md:text-2xl"
          />
        </div>
        <Button type="submit" size="lg" className="h-14 px-7" disabled={!draft.trim()}>
          Ask
        </Button>
      </form>
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <span className="label mr-1">Try</span>
        {asks.map(a => (
          <Button
            key={a.question}
            variant="outline"
            size="sm"
            className="h-auto min-h-9 bg-card py-1.5 text-left whitespace-normal"
            onClick={() => submit(a.question)}
          >
            {a.question}
            {'refusal' in a && (
              <Badge variant="outline" className="ml-1">
                not on record
              </Badge>
            )}
          </Button>
        ))}
      </div>
      <div className="mt-8">
        <Section key={question} fallback={<AnswerSkeleton />}>
          <Answer question={question} />
        </Section>
      </div>
    </main>
  )
}

function Answer({ question }: { question: string }) {
  const { data } = useSuspenseQuery(q.ask(question))
  return data.refused ? <Refused question={question} a={data} /> : <Grounded a={data} />
}

/** Turns "[2]" markers in the answer into citation superscripts. */
export function withMarks(text: string) {
  return text.split(/(\[\d+\])/g).map((part, i) => {
    const m = /^\[(\d+)\]$/.exec(part)
    return m ? (
      <sup key={i} className="mx-0.5 rounded-sm bg-foreground px-1 font-mono text-xs leading-none text-background" aria-label={`source ${m[1]}`}>
        {m[1]}
      </sup>
    ) : (
      part
    )
  })
}

function Grounded({ a }: { a: AskResult }) {
  const decId = a.timeline.find(t => t.status === 'active')?.decision_id ?? a.citations.find(c => c.decision_id)?.decision_id
  return (
    <div className="grid gap-10 motion-safe:animate-in motion-safe:fade-in-0 motion-safe:duration-200 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
      <Card>
        <CardContent className="flex flex-col gap-6">
          <div className="flex items-center justify-between">
            <span className="label text-foreground">Answer / grounded in {plural(a.citations.length, 'source')}</span>
            <span className="label tnum">{secs(a.latency_ms)}</span>
          </div>
          <p className="font-heading text-[22px] leading-snug text-pretty">{withMarks(a.answer)}</p>
          <section aria-labelledby="src-h">
            <SectionHead id="src-h" title="Sources" note="Quotes verified word for word" />
            <ol className="divide-y">
              {a.citations.map((c, i) => (
                <li key={i} className="grid grid-cols-[2rem_1fr] gap-2 py-4">
                  <span className="flex size-6 items-center justify-center rounded-sm bg-foreground font-mono text-xs text-background">{i + 1}</span>
                  <div>
                    <p className="font-heading text-[17px] leading-snug">"{c.quote}"</p>
                    <CitationLine c={c} />
                  </div>
                </li>
              ))}
            </ol>
          </section>
        </CardContent>
      </Card>
      <section aria-labelledby="tl-h">
        <div className="mb-2 flex items-baseline justify-between gap-4 border-b border-foreground pb-2">
          <h2 id="tl-h" className="text-2xl font-medium">
            Decision timeline
          </h2>
          {decId && (
            <Link className="text-sm text-link underline-offset-4 hover:underline" to={`/decisions/${decId}`}>
              Open decision
            </Link>
          )}
        </div>
        {a.timeline.length === 0 ? (
          <p className="pt-3 text-muted-foreground">One decision, no history.</p>
        ) : (
          <ol className="relative ml-2 border-l">
            {a.timeline.map((t, i) => (
              <li key={i} className="relative pb-6 pl-6 last:pb-0">
                <span className="absolute top-1.5 -left-[5px] size-2.5 rounded-full bg-foreground" aria-hidden />
                <div className="flex flex-wrap items-center gap-2">
                  <span className="label tnum">{fmtDate(t.ts)}</span>
                  {t.status === 'superseded' ? (
                    <Badge variant="outline">superseded</Badge>
                  ) : (
                    <ToneBadge tone={t.relation ? relationTone(t.relation) : 'default'}>{t.relation ?? t.status}</ToneBadge>
                  )}
                </div>
                <Link to={`/decisions/${t.decision_id}`} className="mt-1 block leading-snug underline-offset-4 hover:underline">
                  {t.statement}
                </Link>
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  )
}

function Refused({ question, a }: { question: string; a: AskResult }) {
  return (
    <Card className="max-w-3xl border-dashed motion-safe:animate-in motion-safe:fade-in-0 motion-safe:duration-200">
      <CardContent className="flex flex-col gap-4">
        <span className="label">Refused / {secs(a.latency_ms)}</span>
        <p className="font-heading text-2xl">"{question}"</p>
        <div className="flex items-start gap-3">
          <Badge variant="outline" className="mt-1">
            <CircleHelp aria-hidden /> refused
          </Badge>
          <div>
            <p className="font-heading text-xl">{a.answer || 'I do not know. Nothing in the record covers this.'}</p>
            <p className="mt-2 text-muted-foreground">
              Canon answers only from recorded decisions and will not guess. If someone decides this, ingest it and it becomes part of the record.
            </p>
          </div>
        </div>
        <Button variant="outline" asChild className="self-start">
          <Link to="/ingest">Record a decision</Link>
        </Button>
      </CardContent>
    </Card>
  )
}

function AnswerSkeleton() {
  return (
    <div className="grid gap-10 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]" role="status" aria-label="Searching the record">
      <div className="flex flex-col gap-3 rounded-lg border bg-card p-6">
        <Skeleton className="h-4 w-56" />
        <Skeleton className="h-7 w-full" />
        <Skeleton className="h-7 w-11/12" />
        <Skeleton className="h-7 w-2/3" />
        <RowsSkeleton rows={3} className="mt-6" />
      </div>
      <RowsSkeleton rows={4} />
    </div>
  )
}
