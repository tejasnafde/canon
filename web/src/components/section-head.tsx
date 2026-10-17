import { Badge } from './ui/badge'

/** Serif section title over an ink rule, with a quiet note on the right. */
export function SectionHead({ id, title, note, count }: { id: string; title: string; note?: string; count?: number }) {
  return (
    <div className="mb-2 flex items-baseline justify-between gap-4 border-b border-foreground pb-2">
      <h2 id={id} className="text-2xl font-medium">
        {title}
        {count !== undefined && count > 0 && (
          <Badge variant="signal" className="ml-3 align-middle">
            {count}
          </Badge>
        )}
      </h2>
      {note && <span className="label text-right">{note}</span>}
    </div>
  )
}
