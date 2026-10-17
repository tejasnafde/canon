import {
  BadgeCheck,
  BookOpen,
  Bot,
  ClipboardPaste,
  FileText,
  GitCommitHorizontal,
  GitPullRequest,
  Hash,
  Mail,
  Users,
  type LucideIcon,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { fmtDate } from '@/lib/format'
import type { Citation, SourceKind } from '@/lib/schemas'
import { cn } from '@/lib/utils'

export function Verified() {
  return (
    <span className="inline-flex items-center gap-1 font-mono text-xs tracking-wide text-ok-ink uppercase">
      <BadgeCheck className="size-3.5" aria-hidden /> verified
    </span>
  )
}

const KIND_ICON: Record<SourceKind, LucideIcon> = {
  slack: Hash,
  meeting: Users,
  wiki: BookOpen,
  pr: GitPullRequest,
  commit: GitCommitHorizontal,
  email: Mail,
  doc: FileText,
  paste: ClipboardPaste,
  agent: Bot,
}

export function SourceChip({ kind, title, date }: { kind: SourceKind; title: string; date?: string }) {
  const Icon = KIND_ICON[kind]
  return (
    <span className="inline-flex max-w-full items-center gap-2 rounded-sm border bg-background/60 px-2 py-0.5 text-xs">
      <Icon className="size-3.5 shrink-0" aria-hidden />
      <span className="font-mono font-medium tracking-wide uppercase">{kind}</span>
      <span className="truncate text-muted-foreground">
        {title}
        {date && ` / ${fmtDate(date)}`}
      </span>
    </span>
  )
}

export function CitationLine({ c }: { c: Citation }) {
  return (
    <div className="mt-2 flex flex-wrap items-center gap-2">
      <Verified />
      <SourceChip kind={c.kind} title={c.title} date={c.ts} />
      {c.decision_id && (
        <Link className="text-sm text-link underline-offset-4 hover:underline" to={`/decisions/${c.decision_id}`}>
          Open decision
        </Link>
      )}
    </div>
  )
}

export function QuoteBlock({ quote, tone, className, children }: { quote: string; tone?: 'signal'; className?: string; children?: React.ReactNode }) {
  return (
    <blockquote className={cn('quote', tone === 'signal' && 'border-signal', className)}>
      <p>"{quote}"</p>
      {children}
    </blockquote>
  )
}
