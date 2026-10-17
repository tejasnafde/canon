import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { Explanation, usePeople } from '@/components/people'
import { Avatar, Bar, ErrorState, ListSkeleton } from '@/components/states'
import { addressedTo, AUTHORITY_WORD, ownedBy } from '@/lib/org'
import { q } from '@/lib/query'
import { fmtDate, fmtLong } from '@/lib/record'
import type { Alert, Decision, Level, Person } from '@/lib/schemas'
import { useTitle } from '@/lib/title'

const LEVEL: Record<Level, string> = { exec: 'Runs the company', head: 'Heads a team', lead: 'Leads an area', ic: '' }

export default function PersonPage() {
  const { id = '' } = useParams()
  const people = usePeople()
  const p = people.data?.find(x => x.id === id)
  useTitle(p?.name ?? 'person')

  return (
    <main className="wrap">
      <Link to="/org" className="back">
        &larr; All people
      </Link>
      {people.isError ? (
        <ErrorState error={people.error} retry={() => void people.refetch()} />
      ) : people.isPending ? (
        <div role="status" aria-label="Loading the person" aria-busy="true" style={{ marginTop: 20 }}>
          <Bar w={320} h={44} />
          <Bar w="40%" h={18} style={{ marginTop: 14 }} />
        </div>
      ) : !p ? (
        <div className="flag plain" role="alert" style={{ marginTop: 24 }}>
          <h3>Nobody on record has this address.</h3>
          <p className="muted" style={{ marginTop: 6 }}>
            <Link to="/org">See everyone at Northwind Labs</Link>.
          </p>
        </div>
      ) : (
        <Profile p={p} people={people.data} />
      )}
    </main>
  )
}

function Profile({ p, people }: { p: Person; people: Person[] }) {
  const decisions = useQuery(q.decisions())
  const alerts = useQuery(q.allAlerts())
  const mine = decisions.data ? ownedBy(decisions.data, p.name) : null
  const asked = alerts.data ? addressedTo(alerts.data, p.name) : []
  const open = asked.filter(a => a.status === 'open')
  const settled = asked.filter(a => a.status !== 'open')
  const manager = p.reports_to ? people.find(x => x.id === p.reports_to) : undefined
  const reports = people.filter(x => x.reports_to === p.id)
  const successor = p.successor ? people.find(x => x.id === p.successor) : undefined
  const gone = p.status === 'left'
  const level = LEVEL[p.level]

  return (
    <>
      <div className={gone ? 'person-head left' : 'person-head'}>
        <Avatar name={p.name} />
        <div>
          <h1 style={{ margin: 0 }}>{p.name}</h1>
          <p className="muted" style={{ marginTop: 6 }}>
            {p.role}, {p.team}
            {level ? `. ${level}` : ''}.
          </p>
        </div>
      </div>
      {gone && (
        <p className="status" style={{ marginTop: 24 }}>
          Left on {p.left_at ? fmtLong(p.left_at) : 'an unknown date'}
          {successor ? (
            <>
              . <Link to={`/org/${successor.id}`}>{successor.name}</Link> took over
            </>
          ) : null}
          .{mine ? ` Canon kept ${mine.all.length} decision${mine.all.length === 1 ? '' : 's'} from them.` : ''}
        </p>
      )}

      <div className="split section">
        <div>
          <h2>Decided</h2>
          <Decisions list={mine?.official} pending={decisions.isPending} error={decisions.error} empty="No official decisions on record." />

          <h2 style={{ marginTop: 56 }}>Proposed or claimed</h2>
          <Decisions list={mine?.proposed} pending={decisions.isPending} error={null} empty="Nothing waiting for agreement." />

          <h2 style={{ marginTop: 56 }}>Waiting on {gone ? 'them' : p.name.split(' ')[0]}</h2>
          <Alerts list={open} pending={alerts.isPending} empty="Nobody is waiting on them to confirm a claim." />

          {settled.length > 0 && (
            <>
              <h2 style={{ marginTop: 56 }}>Confirmed or dismissed</h2>
              <Alerts list={settled} pending={false} empty="" />
            </>
          )}
        </div>

        <aside>
          <h2>Reports to</h2>
          <div style={{ marginTop: 16 }}>{manager ? <PersonRow p={manager} /> : <p className="muted">Nobody. {p.name} runs the company.</p>}</div>
          {reports.length > 0 && (
            <>
              <h2 style={{ marginTop: 48 }}>Their team</h2>
              <ul className="tl" style={{ marginTop: 16 }}>
                {reports.map(r => (
                  <li key={r.id} style={{ display: 'block' }}>
                    <PersonRow p={r} />
                  </li>
                ))}
              </ul>
            </>
          )}
        </aside>
      </div>
    </>
  )
}

function PersonRow({ p }: { p: Person }) {
  return (
    <span className="person" style={p.status === 'left' ? { color: 'var(--ink-3)' } : undefined}>
      <Avatar name={p.name} small />
      <span>
        <Link to={`/org/${p.id}`}>{p.name}</Link>, {p.role.toLowerCase()}
        {p.status === 'left' ? ' (left)' : ''}
      </span>
    </span>
  )
}

function Decisions({ list, pending, error, empty }: { list: Decision[] | undefined; pending: boolean; error: unknown; empty: string }) {
  if (error) return <ErrorState error={error} />
  if (pending || !list) return <ListSkeleton rows={3} label="Loading decisions" />
  if (list.length === 0)
    return (
      <p className="muted" style={{ marginTop: 14 }}>
        {empty}
      </p>
    )
  const sorted = [...list].sort((a, b) => (a.status === 'active' ? 0 : 1) - (b.status === 'active' ? 0 : 1) || b.ts.localeCompare(a.ts))
  return (
    <ul className="tl" style={{ marginTop: 16 }}>
      {sorted.map(d => (
        <li key={d.id} className={d.status === 'active' ? undefined : 'old'}>
          <span className="when">{fmtDate(d.effective_at ?? d.ts)}</span>
          <span>
            <Link to={`/decisions/${d.id}`}>{d.statement}</Link>
            <span className="auth">
              {AUTHORITY_WORD[d.authority]}
              {d.status === 'superseded' ? ', replaced' : d.status === 'retired' ? ', retired' : ''}
            </span>
          </span>
        </li>
      ))}
    </ul>
  )
}

function Alerts({ list, pending, empty }: { list: Alert[]; pending: boolean; empty: string }) {
  if (pending) return <ListSkeleton rows={2} label="Loading open items" />
  if (list.length === 0)
    return (
      <p className="muted" style={{ marginTop: 14 }}>
        {empty}
      </p>
    )
  return (
    <ul className="list" style={{ marginTop: 20 }}>
      {list.map(a => (
        <li key={a.id}>
          <p style={{ marginTop: 0, color: 'var(--ink)' }}>
            <Explanation a={a} />
          </p>
          {a.decision_id && (
            <p className="src">
              <Link to={`/decisions/${a.related_decision_id ?? a.decision_id}`}>See the decision</Link>
              {a.resolution ? `. ${a.resolution}` : ''}
            </p>
          )}
        </li>
      ))}
    </ul>
  )
}
