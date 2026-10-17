import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { confirmer, personByName, plainUnverified, withOrg } from '@/lib/org'
import { q } from '@/lib/query'
import type { Alert } from '@/lib/schemas'

/** The org-filled people list (see withOrg). */
export function usePeople() {
  return useQuery({ ...q.people(), select: withOrg })
}

/** An alert's explanation. For "Unverified" alerts the person who should confirm links to their page. */
export function Explanation({ a }: { a: Alert }) {
  const people = usePeople()
  const who = confirmer(a)
  const text = plainUnverified(a.explanation)
  const p = who ? personByName(people.data ?? []).get(who) : undefined
  const at = who ? text.lastIndexOf(who) : -1
  if (!who || !p || at < 0) return <>{text}</>
  return (
    <>
      {text.slice(0, at)}
      <Link to={`/org/${p.id}`}>{who}</Link>
      {text.slice(at + who.length)}
    </>
  )
}
