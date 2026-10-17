import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { usePeople } from '@/components/people'
import { Avatar, ErrorState, ListSkeleton } from '@/components/states'
import { AUTHORITY_WORD } from '@/lib/org'
import { q } from '@/lib/query'
import { breaksByDecision, fmtDate, rankDecisions } from '@/lib/record'
import type { Alert, Decision } from '@/lib/schemas'
import { useTitle } from '@/lib/title'

type Status = 'all' | 'broken' | 'active' | 'replaced'
const PAGE = 40

export default function DecisionListPage() {
  useTitle('decisions')
  const decisions = useQuery(q.decisions())
  const alerts = useQuery(q.alerts())
  const people = usePeople()
  const [team, setTeam] = useState('all')
  const [status, setStatus] = useState<Status>('all')
  const [all, setAll] = useState(false)

  const breaks = alerts.data ? breaksByDecision(alerts.data) : new Map<string, Alert[]>()
  const person = new Map((people.data ?? []).map(p => [p.name, p]))
  const teamOf = (d: Decision) => person.get(d.owner)?.team ?? 'Other'
  const broken = (d: Decision) => d.status === 'active' && (breaks.get(d.id)?.length ?? 0) > 0
  const ranked = decisions.data ? rankDecisions(decisions.data, breaks) : []
  const teams = [...new Set(ranked.map(teamOf))].sort()
  const shown = ranked
    .filter(d => team === 'all' || teamOf(d) === team)
    .filter(d =>
      status === 'all' ? true : status === 'broken' ? broken(d) : status === 'active' ? d.status === 'active' && !broken(d) : d.status !== 'active',
    )
  const visible = all ? shown : shown.slice(0, PAGE)

  return (
    <main className="wrap">
      <h1>Decisions.</h1>
      <p className="lede">
        Every decision Canon found in Northwind's Slack, meetings, wiki pages and pull requests. The ones something now breaks come first, then the
        rest, newest first. Each links back to the words people actually used.
      </p>

      <div className="filters">
        <div className="row">
          <span className="label" id="team-label">
            Team
          </span>
          <div className="choices" role="group" aria-labelledby="team-label">
            {['all', ...teams].map(t => (
              <button key={t} type="button" aria-pressed={team === t} onClick={() => setTeam(t)}>
                {t === 'all' ? 'All' : t}
              </button>
            ))}
          </div>
        </div>
        <div className="row">
          <span className="label" id="status-label">
            Status
          </span>
          <div className="choices" role="group" aria-labelledby="status-label">
            {(
              [
                ['all', `All ${ranked.length || ''}`.trim()],
                ['broken', 'Broken'],
                ['active', 'Active'],
                ['replaced', 'Replaced'],
              ] as const
            ).map(([k, label]) => (
              <button key={k} type="button" aria-pressed={status === k} onClick={() => setStatus(k)}>
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div style={{ marginTop: 28 }}>
        {decisions.isError ? (
          <ErrorState error={decisions.error} retry={() => void decisions.refetch()} />
        ) : decisions.isPending || alerts.isPending ? (
          <ListSkeleton rows={8} label="Loading decisions" />
        ) : shown.length === 0 ? (
          <p className="muted">No decisions match these filters.</p>
        ) : (
          <table className="rows">
            <thead>
              <tr>
                <th>Decision</th>
                <th>Owner</th>
                <th>Decided</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {visible.map(d => {
                const n = d.status === 'active' ? (breaks.get(d.id)?.length ?? 0) : 0
                const who = person.get(d.owner)
                const gone = who?.status === 'left'
                return (
                  <tr key={d.id}>
                    <td className={d.status === 'active' ? 'd' : 'd muted'}>
                      <Link to={`/decisions/${d.id}`}>{d.statement}</Link>
                    </td>
                    <td className="owner">
                      <span className="person">
                        <Avatar name={d.owner} small />
                        <span>
                          {who ? (
                            <Link to={`/org/${who.id}`} className="plain">
                              {d.owner}
                            </Link>
                          ) : (
                            d.owner
                          )}
                          {gone && <span className="gone"> (left)</span>}
                        </span>
                      </span>
                      <span className="team">{teamOf(d)}</span>
                    </td>
                    <td className="s tnum">{fmtDate(d.ts)}</td>
                    {n > 0 ? (
                      <td className="s breaks">
                        <span className="dot" aria-hidden />
                        Broken by {n}
                        <span className="auth">{AUTHORITY_WORD[d.authority]}</span>
                      </td>
                    ) : (
                      <td className={d.status === 'active' ? 's' : 's muted'}>
                        {d.status === 'active' ? 'Active' : d.status === 'superseded' ? 'Replaced' : 'Retired'}
                        <span className="auth">{AUTHORITY_WORD[d.authority]}</span>
                      </td>
                    )}
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
      {shown.length > 0 && (
        <p className="small muted" style={{ marginTop: 16 }}>
          {visible.length} of {shown.length} shown.{' '}
          {!all && shown.length > PAGE && (
            <button type="button" className="kbd" style={{ fontSize: 15, textDecoration: 'underline' }} onClick={() => setAll(true)}>
              Show all
            </button>
          )}{' '}
          "Broken by" counts the messages, pull requests and documents that go against the decision. "Replaced" means a newer decision took its place.
          "Official" means the person who owns the area decided it, "Proposed" is not agreed yet, and "Claim" is something someone said without the
          standing to decide it.
        </p>
      )}
    </main>
  )
}
