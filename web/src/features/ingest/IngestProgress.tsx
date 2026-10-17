import { Check } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

export const STEP_MS = 1300

export const ingestSteps = (records?: number) => [
  'Reading the source',
  'Pulling out decisions with Gemini',
  'Checking every quote word for word',
  `Reading ${records ?? 'the'} decisions on record to reconcile`,
  'Checking docs for drift',
]

// ponytail: timed stages, the API has no progress stream; the last stage holds until the answer lands.
export function IngestProgress({ records }: { records?: number }) {
  const steps = ingestSteps(records)
  const [at, setAt] = useState(0)
  useEffect(() => {
    const id = setInterval(() => setAt(a => Math.min(a + 1, steps.length - 1)), STEP_MS)
    return () => clearInterval(id)
  }, [steps.length])
  return (
    <div className="rounded-lg border bg-card p-6" role="status">
      <p className="label mb-3 text-foreground">Working</p>
      <Progress value={((at + 1) / steps.length) * 90} aria-label="Ingest progress" className="mb-5 h-1.5" />
      <ol className="flex flex-col gap-3">
        {steps.map((s, i) => (
          <li key={s} className={cn('flex items-center gap-3 transition-colors duration-200', i > at && 'text-muted-foreground')}>
            <span
              className={cn(
                'flex size-6 shrink-0 items-center justify-center rounded-full border',
                i < at && 'border-ok-ink bg-ok-soft text-ok-ink',
                i === at && 'border-foreground motion-safe:animate-pulse',
              )}
              aria-hidden
            >
              {i < at ? <Check className="size-3.5" /> : <span className="font-mono text-xs">{i + 1}</span>}
            </span>
            <span>
              {s}
              {i === at && '...'}
            </span>
            <span className="sr-only">{i < at ? 'done' : i === at ? 'in progress' : 'waiting'}</span>
          </li>
        ))}
      </ol>
    </div>
  )
}
