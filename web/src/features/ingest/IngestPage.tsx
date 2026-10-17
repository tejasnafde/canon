import { useMutation, useQuery } from '@tanstack/react-query'
import { RotateCcw } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { PageHeader } from '@/components/page-header'
import { EmptyState, ErrorState, friendly } from '@/components/states'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { api } from '@/lib/api'
import { plural } from '@/lib/format'
import { invalidateRecord, q } from '@/lib/query'
import { SourceKind, type SourceInput } from '@/lib/schemas'
import { cn } from '@/lib/utils'
import samples from '@/samples/live_paste.json'
import { IngestProgress } from './IngestProgress'
import { IngestResultView } from './IngestResultView'

const KINDS = SourceKind.options.filter(k => k !== 'agent')

interface Draft {
  kind: SourceInput['kind']
  title: string
  author: string
  text: string
}

const fromSample = (i: number): Draft => {
  const s = samples[i]?.source
  return { kind: SourceKind.catch('paste').parse(s?.kind), title: s?.title ?? '', author: s?.author ?? '', text: s?.text ?? '' }
}

export default function IngestPage() {
  const [pick, setPick] = useState<number | null>(0)
  const [draft, setDraft] = useState<Draft>(() => fromSample(0))
  const record = useQuery(q.decisions())
  const n = record.data?.length

  const ingest = useMutation({
    mutationFn: (d: Draft) => api.ingest({ ...d, ts: new Date().toISOString(), synthetic: true }),
    onSuccess: r => {
      void invalidateRecord()
      toast.success(`Ingested "${r.source.title}"`, {
        description: `${plural(r.decisions.length, 'decision')}, ${plural(r.alerts.length, 'alert')} raised.`,
      })
    },
  })

  const reset = useMutation({
    mutationFn: api.reset,
    onSuccess: () => {
      ingest.reset()
      void invalidateRecord()
      toast.success('Your workspace is empty again.')
    },
    onError: e => toast.error('Could not reset the workspace', { description: friendly(e) }),
  })

  const choose = (i: number) => {
    setPick(i)
    setDraft(fromSample(i))
    ingest.reset()
  }
  const edit = (patch: Partial<Draft>) => {
    setPick(null)
    setDraft(d => ({ ...d, ...patch }))
  }
  const ready = draft.text.trim() && draft.title.trim()

  return (
    <main className="mx-auto max-w-[1440px] px-4 pt-8 pb-12 md:px-8">
      <PageHeader eyebrow="Ingest / paste anything: Slack, transcript, wiki, PR, email" title="Feed the record." />
      <div className="mt-8 grid gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
        <form
          className="flex flex-col gap-5"
          onSubmit={e => {
            e.preventDefault()
            if (ready) ingest.mutate(draft)
          }}
        >
          <fieldset>
            <legend className="label mb-2">Samples</legend>
            <div className="flex flex-col gap-2">
              {samples.map((s, i) => (
                <button
                  key={s.key}
                  type="button"
                  aria-pressed={pick === i}
                  onClick={() => choose(i)}
                  className={cn(
                    'grid grid-cols-[8.5rem_1fr] items-center gap-3 rounded-md border px-3 py-2.5 text-left text-[15px] transition-colors duration-150',
                    pick === i ? 'border-foreground bg-card' : 'bg-transparent hover:bg-card',
                  )}
                >
                  <Badge variant={pick === i ? 'default' : 'outline'} className="w-full">
                    {s.expected_relation}
                  </Badge>
                  {s.source.title}
                </button>
              ))}
            </div>
          </fieldset>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-2">
              <Label htmlFor="kind" className="label">
                Kind
              </Label>
              <Select value={draft.kind} onValueChange={v => edit({ kind: SourceKind.parse(v) })}>
                <SelectTrigger id="kind" className="w-full bg-card">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {KINDS.map(k => (
                    <SelectItem key={k} value={k}>
                      {k}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="author" className="label">
                Author
              </Label>
              <Input id="author" className="bg-card" value={draft.author} onChange={e => edit({ author: e.target.value })} />
            </div>
            <div className="flex flex-col gap-2 sm:col-span-2">
              <Label htmlFor="title" className="label">
                Title
              </Label>
              <Input id="title" className="bg-card" required value={draft.title} onChange={e => edit({ title: e.target.value })} />
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="text" className="label">
              Text
            </Label>
            <Textarea id="text" required rows={10} className="min-h-56 bg-card" value={draft.text} onChange={e => edit({ text: e.target.value })} />
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span className="text-sm text-muted-foreground">Writes to your private workspace only.</span>
            <Button type="submit" disabled={ingest.isPending || !ready}>
              {ingest.isPending ? 'Working' : 'Ingest and reconcile'}
            </Button>
          </div>
          <ResetDialog onConfirm={() => reset.mutate()} pending={reset.isPending} />
        </form>

        <section aria-live="polite" aria-label="Result">
          {ingest.isPending ? (
            <IngestProgress records={n} />
          ) : ingest.isError ? (
            <ErrorState error={ingest.error} retry={() => ingest.mutate(draft)} title="Ingest failed" />
          ) : ingest.data ? (
            <IngestResultView r={ingest.data} records={n} />
          ) : (
            <EmptyState title="Nothing ingested yet">
              Pick a sample and press Ingest. Canon pulls out each decision, checks every quote word for word, and reconciles it with{' '}
              {n === undefined ? 'the' : n} decisions on record.
            </EmptyState>
          )}
        </section>
      </div>
    </main>
  )
}

function ResetDialog({ onConfirm, pending }: { onConfirm: () => void; pending: boolean }) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button type="button" variant="ghost" size="sm" className="self-start text-muted-foreground">
          <RotateCcw aria-hidden /> Reset my workspace
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="font-heading text-xl">Reset your workspace?</DialogTitle>
          <DialogDescription className="text-[15px]">
            This deletes everything you ingested from this browser. The shared Northwind Labs record stays as it is.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <DialogClose asChild>
            <Button onClick={onConfirm} disabled={pending} className="bg-signal text-white hover:bg-signal/90">
              Reset
            </Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
