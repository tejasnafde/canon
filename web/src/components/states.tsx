import type { CSSProperties, ReactNode } from 'react'
import { ApiError, ContractError } from '@/lib/api'
import { avatar } from '@/lib/record'

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

export function ErrorState({ error, retry, title = 'Canon did not answer.' }: { error: unknown; retry?: () => void; title?: string }) {
  return (
    <div className="flag plain" role="alert" style={{ marginTop: 24 }}>
      <h3>{title}</h3>
      <p className="muted" style={{ marginTop: 6 }}>
        {friendly(error)}
      </p>
      {retry && (
        <button type="button" className="btn ghost" style={{ marginTop: 14 }} onClick={retry}>
          Try again
        </button>
      )}
    </div>
  )
}

export function Empty({ children }: { children: ReactNode }) {
  return (
    <p className="muted" style={{ marginTop: 16 }}>
      {children}
    </p>
  )
}

/** A grey bar the size of a line of text. */
export function Bar({ w = '100%', h = 18, style }: { w?: string | number; h?: number; style?: CSSProperties }) {
  return <span className="sk" style={{ width: w, height: h, ...style }} />
}

/** Hairline list rows shaped like the content that is coming. */
export function ListSkeleton({ rows = 4, label = 'Loading' }: { rows?: number; label?: string }) {
  return (
    <ul className="list" role="status" aria-label={label} aria-busy="true">
      {Array.from({ length: rows }, (_, i) => (
        <li key={i}>
          <Bar w={`${70 - (i % 3) * 12}%`} h={22} />
          <Bar w="52%" h={15} style={{ marginTop: 12 }} />
        </li>
      ))}
    </ul>
  )
}

export function TextSkeleton({ lines = 3, h = 18, label = 'Loading' }: { lines?: number; h?: number; label?: string }) {
  return (
    <div role="status" aria-label={label} aria-busy="true" style={{ display: 'grid', gap: 12 }}>
      {Array.from({ length: lines }, (_, i) => (
        <Bar key={i} w={i === lines - 1 ? '60%' : '100%'} h={h} />
      ))}
    </div>
  )
}

export function Avatar({ name, small }: { name: string; small?: boolean }) {
  return <img className={small ? 'avatar sm' : 'avatar'} src={avatar(name)} alt="" loading="lazy" width={small ? 22 : 28} height={small ? 22 : 28} />
}
