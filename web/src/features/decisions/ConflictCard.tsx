import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { ToneBadge } from '@/components/badges'
import { QuoteBlock } from '@/components/citation'
import { friendly } from '@/components/states'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card'
import { api } from '@/lib/api'
import { alertTone, humanize } from '@/lib/format'
import { invalidateRecord, q } from '@/lib/query'
import type { Alert, DecisionDetail, ResolveAction, Source } from '@/lib/schemas'
import { cn } from '@/lib/utils'

const DONE: Record<ResolveAction, string> = {
  accept_update: 'Update accepted.',
  dismiss: 'Alert dismissed.',
  retire_decision: 'Decision retired.',
}

interface Props {
  a: Alert
  decisionId: string
  src: (id: string | null) => Source | undefined
  recordQuote?: string
}

export function ConflictCard({ a, decisionId, src, recordQuote }: Props) {
  const qc = useQueryClient()
  const key = q.decision(decisionId).queryKey
  // optimistic: the card greys out at once, and rolls back if the server says no
  const resolve = useMutation({
    mutationFn: (action: ResolveAction) => api.resolve(a.id, action),
    onMutate: async action => {
      await qc.cancelQueries({ queryKey: key })
      const prev = qc.getQueryData<DecisionDetail>(key)
      qc.setQueryData<DecisionDetail>(
        key,
        d => d && { ...d, alerts: d.alerts.map(x => (x.id === a.id ? { ...x, status: 'resolved', resolution: action } : x)) },
      )
      return { prev }
    },
    onError: (err, _action, ctx) => {
      qc.setQueryData(key, ctx?.prev)
      toast.error('Could not resolve the alert', { description: friendly(err) })
    },
    onSuccess: (_alert, action) => toast.success(DONE[action]),
    onSettled: () => invalidateRecord(),
  })

  const s = src(a.source_id)
  const theirs = a.quotes.find(x => x.source_id === a.source_id) ?? a.quotes[0]
  // the record side: the alert's other quote, else this decision's quote when it differs
  const record = a.quotes.find(x => x !== theirs)?.quote ?? (recordQuote !== theirs?.quote ? recordQuote : undefined)
  const resolved = a.status === 'resolved'

  return (
    <Card className={cn('gap-0 py-0 transition-opacity duration-200', resolved ? 'opacity-60' : 'border-signal/50')}>
      <CardHeader className={cn('flex items-center justify-between border-b py-2.5', resolved ? 'bg-muted' : 'bg-signal text-white')}>
        <span className="font-mono text-xs tracking-[0.08em] uppercase">
          {resolved ? `Resolved / ${humanize(a.resolution ?? '')}` : 'Contradicted by'}
        </span>
        <span className="font-mono text-xs tracking-[0.08em] uppercase">{a.severity}</span>
      </CardHeader>
      <CardContent className="flex flex-col gap-3 py-5">
        <ToneBadge tone={alertTone(a.kind)}>{a.kind}</ToneBadge>
        {s && <h3 className="text-xl font-medium">{s.title}</h3>}
        <p className="text-[15px] text-muted-foreground">{a.explanation}</p>
        {theirs && (
          <div className={cn('mt-1 grid gap-4', record && 'sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2')}>
            <div>
              <p className="label mb-1.5">The source says</p>
              <QuoteBlock quote={theirs.quote} tone="signal" className="text-base" />
            </div>
            {record && (
              <div>
                <p className="label mb-1.5">The record says</p>
                <QuoteBlock quote={record} className="text-base" />
              </div>
            )}
          </div>
        )}
      </CardContent>
      {!resolved && (
        <CardFooter className="flex flex-wrap gap-2 bg-transparent">
          <Button size="sm" disabled={resolve.isPending} onClick={() => resolve.mutate('accept_update')}>
            Accept update
          </Button>
          <Button size="sm" variant="outline" disabled={resolve.isPending} onClick={() => resolve.mutate('dismiss')}>
            Dismiss
          </Button>
          <Button size="sm" variant="outline" disabled={resolve.isPending} onClick={() => resolve.mutate('retire_decision')}>
            Retire decision
          </Button>
        </CardFooter>
      )}
    </Card>
  )
}
