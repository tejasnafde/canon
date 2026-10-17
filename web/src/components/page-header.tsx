import type { ReactNode } from 'react'

/** Mono eyebrow, serif title with an optional quiet second half, actions on the right. */
export function PageHeader({ eyebrow, title, quiet, children }: { eyebrow: ReactNode; title: string; quiet?: string; children?: ReactNode }) {
  return (
    <header className="flex flex-col gap-5 border-b border-foreground pb-6 md:flex-row md:items-end md:justify-between">
      <div className="min-w-0 flex-1">
        <p className="label">{eyebrow}</p>
        <h1 className="mt-2 text-[34px] leading-[1.08] font-medium text-balance md:text-[40px]">
          {title} {quiet && <span className="text-muted-foreground">{quiet}</span>}
        </h1>
      </div>
      {children && <div className="flex flex-wrap items-end gap-4 md:shrink-0">{children}</div>}
    </header>
  )
}
