import { CircleAlert, Inbox, RotateCw } from 'lucide-react'
import type { ReactNode } from 'react'
import { ApiError, ContractError } from '@/lib/api'
import { cn } from '@/lib/utils'
import { Alert, AlertDescription, AlertTitle } from './ui/alert'
import { Button } from './ui/button'
import { Skeleton } from './ui/skeleton'

/** Plain words for what went wrong. */
export function friendly(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 404) return 'Not on record. It may have been removed, or the link is wrong.'
    if (error.status === 429) return 'Too many requests. Wait a few seconds and try again.'
    if (error.status >= 500) return 'Canon had a problem on its side. Try again in a moment.'
    return error.message
  }
  if (error instanceof ContractError) return 'Canon sent an answer this page does not understand. The error was reported.'
  if (error instanceof TypeError) return 'Canon is out of reach. Check your connection and try again.'
  return error instanceof Error ? error.message : 'Unknown error.'
}

export function ErrorState({ error, retry, title = 'Canon did not answer' }: { error: unknown; retry?: () => void; title?: string }) {
  return (
    <Alert variant="destructive" className="border-signal/40 bg-signal-soft/40">
      <CircleAlert aria-hidden />
      <AlertTitle className="text-foreground">{title}</AlertTitle>
      <AlertDescription className="text-muted-foreground">
        <p>{friendly(error)}</p>
        {retry && (
          <Button variant="outline" size="sm" className="mt-3" onClick={retry}>
            <RotateCw aria-hidden /> Try again
          </Button>
        )}
      </AlertDescription>
    </Alert>
  )
}

export function EmptyState({ title, children, action }: { title: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-start gap-2 rounded-lg border border-dashed bg-card/60 p-6">
      <Inbox className="size-5 text-muted-foreground" aria-hidden />
      <p className="font-medium">{title}</p>
      {children && <div className="text-[15px] text-muted-foreground">{children}</div>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}

/** Rows of grey bars shaped like the content that is coming. */
export function RowsSkeleton({ rows = 4, className }: { rows?: number; className?: string }) {
  return (
    <div className={cn('flex flex-col gap-4', className)} role="status" aria-label="Loading">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="flex flex-col gap-2">
          <Skeleton className="h-5 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      ))}
    </div>
  )
}
