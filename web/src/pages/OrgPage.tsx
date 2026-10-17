import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { usePeople } from '@/components/people'
import { Avatar, ErrorState, ListSkeleton } from '@/components/states'
import { orgTree, ownedBy, type OrgNode } from '@/lib/org'
import { q } from '@/lib/query'
import { fmtDate } from '@/lib/record'
import type { Decision, Person } from '@/lib/schemas'
import { useTitle } from '@/lib/title'

export default function OrgPage() {
  useTitle('people')
  const people = usePeople()
  const decisions = useQuery(q.decisions())
  const tree = people.data ? orgTree(people.data) : []
  const left = people.data?.filter(p => p.status === 'left').length ?? 0

  return (
    <main className="wrap">
      <h1>People.</h1>
      <p className="lede">
        Who decides what at Northwind Labs. A decision counts as official when the person who owns the area makes it. When someone leaves, their
        decisions stay on record{left ? `: ${left === 1 ? 'one person has' : `${left} people have`} left so far` : ''}.
      </p>
      {people.isError ? (
        <ErrorState error={people.error} retry={() => void people.refetch()} />
      ) : people.isPending ? (
        <div style={{ marginTop: 28 }}>
          <ListSkeleton rows={8} label="Loading the people" />
        </div>
      ) : (
        <ul className="org" aria-busy={decisions.isPending}>
          {tree.map(n => (
            <Node key={n.person.id} n={n} people={people.data} decisions={decisions.data} />
          ))}
        </ul>
      )}
    </main>
  )
}

function Node({ n, people, decisions }: { n: OrgNode; people: Person[]; decisions: Decision[] | undefined }) {
  const p = n.person
  const mine = decisions ? ownedBy(decisions, p.name) : null
  const gone = p.status === 'left'
  const successor = gone && p.successor ? people.find(x => x.id === p.successor) : undefined
  return (
    <li className={`lvl-${p.level}${gone ? ' left' : ''}`}>
      <div className="who">
        <Avatar name={p.name} />
        <Link to={`/org/${p.id}`}>
          <h3>{p.name}</h3>
          <span className="role">
            {p.role}
            {gone && (
              <>
                . Left {p.left_at ? fmtDate(p.left_at) : ''}
                {successor ? `, ${successor.name} took over` : ''}
              </>
            )}
          </span>
        </Link>
        <span className="n">
          {mine === null
            ? ''
            : gone
              ? `Canon kept ${count(mine.all.length)} from them`
              : mine.all.length === 0
                ? 'No decisions yet'
                : `${mine.official.length} official decision${mine.official.length === 1 ? '' : 's'}${mine.proposed.length ? `, ${mine.proposed.length} proposed` : ''}`}
        </span>
      </div>
      {n.reports.length > 0 && (
        <ul>
          {n.reports.map(c => (
            <Node key={c.person.id} n={c} people={people} decisions={decisions} />
          ))}
        </ul>
      )}
    </li>
  )
}

const count = (n: number) => (n === 1 ? '1 decision' : `${n} decisions`)
