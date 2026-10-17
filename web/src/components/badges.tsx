import { ShieldAlert, ShieldCheck, ShieldX } from 'lucide-react'
import { humanize, priorityTone, type Tone } from '@/lib/format'
import type { Verdict } from '@/lib/schemas'
import { cn } from '@/lib/utils'
import { Badge } from './ui/badge'

const VERDICT = {
  block: { tone: 'signal', Icon: ShieldX },
  warn: { tone: 'warn', Icon: ShieldAlert },
  allow: { tone: 'ok', Icon: ShieldCheck },
} as const satisfies Record<Verdict, { tone: Tone; Icon: typeof ShieldX }>

export function VerdictBadge({ verdict, className }: { verdict: Verdict; className?: string }) {
  const { tone, Icon } = VERDICT[verdict]
  return (
    <Badge variant={tone} className={className}>
      <Icon aria-hidden />
      {verdict}
    </Badge>
  )
}

export function ToneBadge({ tone, children, className }: { tone: Tone; children: string; className?: string }) {
  return (
    <Badge variant={tone} className={className}>
      {humanize(children)}
    </Badge>
  )
}

/** Score 0-100 with a meter. The word says the same as the colour, for people who cannot see it. */
export function PriorityScore({ priority, top }: { priority: number; top?: boolean }) {
  const { tone, label } = priorityTone(priority)
  return (
    <div className="flex w-16 flex-col gap-1.5" aria-label={`Priority ${priority} of 100, ${label}`}>
      <span className={cn('font-heading text-3xl leading-none tnum', top && 'text-signal-ink')}>{priority}</span>
      <span className="h-1 w-full overflow-hidden rounded-full bg-muted" aria-hidden>
        <span
          className={cn('block h-full', tone === 'signal' ? 'bg-signal' : tone === 'warn' ? 'bg-warn-ink' : 'bg-muted-foreground')}
          style={{ width: `${priority}%` }}
        />
      </span>
      <span className="label">{label}</span>
    </div>
  )
}
