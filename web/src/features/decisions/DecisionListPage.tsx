import { useQuery, useSuspenseQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { useDeferredValue, useState } from 'react'
import { Link } from 'react-router-dom'
import { Section } from '@/components/error-boundary'
import { PageHeader } from '@/components/page-header'
import { EmptyState, RowsSkeleton } from '@/components/states'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { fmtDate, plural } from '@/lib/format'
import { q } from '@/lib/query'
import type { Decision } from '@/lib/schemas'

type Filter = 'active' | 'all'

export default function DecisionListPage() {
  const [filter, setFilter] = useState<Filter>('active')
  const [text, setText] = useState('')
  return (
    <main className="mx-auto max-w-[1100px] px-4 pt-8 pb-12 md:px-8">
      <PageHeader eyebrow="Decisions / open alerts first, then newest" title="What the company decided.">
        <Tabs value={filter} onValueChange={v => setFilter(v as Filter)}>
          <TabsList aria-label="Filter by status">
            <TabsTrigger value="active" className="px-3 text-[15px]">
              Active
            </TabsTrigger>
            <TabsTrigger value="all" className="px-3 text-[15px]">
              All
            </TabsTrigger>
          </TabsList>
        </Tabs>
        <div className="relative">
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
          <Input
            value={text}
            onChange={e => setText(e.target.value)}
            placeholder="Filter by text, owner, topic"
            aria-label="Filter decisions"
            className="w-72 bg-card pl-9"
          />
        </div>
      </PageHeader>
      <div className="mt-4">
        <Section fallback={<RowsSkeleton rows={6} className="pt-4" />}>
          <List filter={filter} text={useDeferredValue(text)} />
        </Section>
      </div>
    </main>
  )
}

const matches = (d: Decision, t: string) => `${d.statement} ${d.owner} ${d.topic}`.toLowerCase().includes(t.toLowerCase())

function List({ filter, text }: { filter: Filter; text: string }) {
  const { data } = useSuspenseQuery(q.decisions())
  const alerts = useQuery(q.alerts()).data ?? []
  const open = new Map<string, number>()
  for (const a of alerts)
    if (a.status === 'open') for (const id of new Set([a.decision_id, a.related_decision_id])) if (id) open.set(id, (open.get(id) ?? 0) + 1)
  // Decisions with open alerts first (most alerts first), then newest.
  const ds = data
    .filter(d => (filter === 'all' || d.status === 'active') && matches(d, text.trim()))
    .sort((a, b) => (open.get(b.id) ?? 0) - (open.get(a.id) ?? 0) || b.ts.localeCompare(a.ts))
  if (data.length === 0)
    return (
      <EmptyState
        title="The record is empty"
        action={
          <Button size="sm" asChild>
            <Link to="/ingest">Ingest a source</Link>
          </Button>
        }
      >
        Decisions appear here once Canon reads a source.
      </EmptyState>
    )
  if (ds.length === 0) return <EmptyState title="No decisions match">Try fewer words, or switch to All.</EmptyState>
  return (
    <ul className="divide-y">
      {ds.map(d => (
        <li key={d.id}>
          <Link
            to={`/decisions/${d.id}`}
            className="grid grid-cols-1 gap-x-6 gap-y-1 rounded-md px-2 py-4 transition-colors duration-150 hover:bg-card sm:grid-cols-[8rem_1fr_auto] sm:items-baseline"
          >
            <span className="label tnum">{fmtDate(d.ts)}</span>
            <span className="min-w-0">
              <span className="block font-heading text-xl leading-snug">{d.statement}</span>
              <span className="text-sm text-muted-foreground">
                {d.owner} / {d.topic}
                {d.version > 1 && ` / v${d.version}`}
              </span>
            </span>
            <span className="flex flex-wrap gap-2 justify-self-start">
              {open.has(d.id) && <Badge variant="signal-soft">{plural(open.get(d.id) ?? 0, 'open alert')}</Badge>}
              <Badge variant={d.status === 'active' ? 'ok' : 'outline'}>{d.status}</Badge>
            </span>
          </Link>
        </li>
      ))}
    </ul>
  )
}
