import { useQuery } from '@tanstack/react-query'
import { Bot, User } from 'lucide-react'
import { Link } from 'react-router-dom'
import { fmtTime, isDecisionId, short } from '@/lib/format'
import { q } from '@/lib/query'
import type { Activity } from '@/lib/schemas'
import { VerdictBadge } from './badges'
import { EmptyState, ErrorState, RowsSkeleton } from './states'
import { Button } from './ui/button'
import { Card, CardAction, CardContent, CardHeader, CardTitle } from './ui/card'
import { ScrollArea } from './ui/scroll-area'

export const newestFirst = (a: Activity[]) => [...a].sort((x, y) => y.created_at.localeCompare(x.created_at))

export function LiveDot({ label = 'live' }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 font-mono text-xs tracking-wide text-ok-ink uppercase">
      <span className="size-2 rounded-full bg-ok-ink motion-safe:animate-pulse" aria-hidden />
      {label}
    </span>
  )
}

/** Every agent read, write and check, polled every 2 s. Shared by Home and Agents. */
export function ActivityFeed({ limit = 8, className }: { limit?: number; className?: string }) {
  const feed = useQuery(q.activity())
  return (
    <Card className={className} size="sm">
      <CardHeader className="border-b">
        <CardTitle>
          <h2>Agent activity</h2>
        </CardTitle>
        <CardAction>
          <LiveDot />
        </CardAction>
      </CardHeader>
      <CardContent>
        {feed.isPending ? (
          <RowsSkeleton rows={5} />
        ) : feed.isError && !feed.data ? (
          <ErrorState error={feed.error} retry={() => void feed.refetch()} />
        ) : feed.data.length === 0 ? (
          <EmptyState
            title="No activity yet"
            action={
              <Button size="sm" variant="outline" asChild>
                <Link to="/agents">Call a tool in the playground</Link>
              </Button>
            }
          >
            Connect an agent, or call a tool from the playground. Each call shows here.
          </EmptyState>
        ) : (
          <ScrollArea className="max-h-[640px]">
            <ol className="divide-y" aria-live="polite" aria-label="Recent activity">
              {newestFirst(feed.data)
                .slice(0, limit)
                .map(a => (
                  <FeedItem key={a.id} a={a} />
                ))}
            </ol>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  )
}

function FeedItem({ a }: { a: Activity }) {
  const agent = a.actor.startsWith('agent:')
  const name = agent ? a.actor.slice(6) : a.actor
  const Icon = agent ? Bot : User
  return (
    <li className="grid grid-cols-[3.25rem_1fr] gap-2 py-3 motion-safe:animate-in motion-safe:fade-in-0 motion-safe:duration-200">
      <time className="pt-0.5 font-mono text-xs text-muted-foreground tnum" dateTime={a.created_at}>
        {fmtTime(a.created_at)}
      </time>
      <div className="min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span className="inline-flex min-w-0 items-center gap-1.5 font-mono text-sm font-medium">
            <Icon className={agent ? 'size-4 text-signal-ink' : 'size-4 text-muted-foreground'} aria-label={agent ? 'agent' : 'person'} />
            <span className="truncate">{name}</span>
          </span>
          {a.verdict && <VerdictBadge verdict={a.verdict} />}
        </div>
        <p className="mt-1 text-[15px] leading-snug">{a.summary}</p>
        {a.ref_titles.length > 0 && <Refs a={a} />}
      </div>
    </li>
  )
}

/** ref_titles[i] names ref_ids[i]; the deciding decision comes first. */
function Refs({ a }: { a: Activity }) {
  return (
    <p className="mt-1.5 text-xs text-muted-foreground">
      <span className="font-mono tracking-wide uppercase">{a.verdict ? 'Deciding: ' : 'Refs: '}</span>
      {a.ref_titles.slice(0, 2).map((t, i) => {
        const id = a.ref_ids[i]
        return (
          <span key={i}>
            {i > 0 && ' / '}
            {isDecisionId(id) ? (
              <Link className="text-link underline-offset-4 hover:underline" to={`/decisions/${id}`}>
                {short(t, 60)}
              </Link>
            ) : (
              short(t, 60)
            )}
          </span>
        )
      })}
      {a.ref_titles.length > 2 && ` +${a.ref_titles.length - 2}`}
    </p>
  )
}
