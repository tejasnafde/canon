import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { ErrorState, ListSkeleton, TextSkeleton } from '@/components/states'
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { q } from '@/lib/query'
import { AWAY, FEATURED, PERSONA_GROUPS, PERSONA_LABEL, sinceFor, srcLine, type Away } from '@/lib/record'
import { Persona } from '@/lib/schemas'
import { useTitle } from '@/lib/title'

export default function CatchUpPage() {
  useTitle('What changed while I was away')
  const [params, setParams] = useSearchParams()
  const persona = Persona.catch('engineer').parse(params.get('role'))
  const away: Away = AWAY.find(a => a.key === params.get('away'))?.key ?? '3m'
  const set = (k: string, v: string) =>
    setParams(
      p => {
        p.set(k, v)
        return p
      },
      { replace: true },
    )
  const briefing = useQuery(q.briefing(persona, sinceFor(away)))
  const featured = FEATURED.some(f => f.id === persona)

  return (
    <main className="wrap">
      <Link to="/" className="back">
        &larr; Stories
      </Link>
      <h1 style={{ marginTop: 16 }}>What changed while you were away?</h1>
      <p className="lede">
        Pick your role and how long you were gone. Canon reads everything that happened and tells you what matters to you, most urgent first.
      </p>

      <div className="picker">
        <div>
          <span className="label" id="role-label">
            My role
          </span>
          <div className="choices" role="group" aria-labelledby="role-label">
            {FEATURED.map(f => (
              <button key={f.id} type="button" aria-pressed={persona === f.id} onClick={() => set('role', f.id)}>
                {f.label}
              </button>
            ))}
            <Select value={featured ? '' : persona} onValueChange={v => set('role', v)}>
              <SelectTrigger className={featured ? 'seltrigger' : 'seltrigger on'} aria-label="All roles">
                <SelectValue placeholder="More roles" />
              </SelectTrigger>
              <SelectContent position="popper" align="start">
                {PERSONA_GROUPS.map(g => (
                  <SelectGroup key={g.label}>
                    <SelectLabel>{g.label}</SelectLabel>
                    {g.ids.map(id => (
                      <SelectItem key={id} value={id}>
                        {PERSONA_LABEL[id]}
                      </SelectItem>
                    ))}
                  </SelectGroup>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <div>
          <span className="label" id="away-label">
            I was away for
          </span>
          <div className="choices" role="group" aria-labelledby="away-label">
            {AWAY.map(a => (
              <button key={a.key} type="button" aria-pressed={away === a.key} onClick={() => set('away', a.key)}>
                {a.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {briefing.isError ? (
        <ErrorState error={briefing.error} retry={() => void briefing.refetch()} />
      ) : (
        <>
          <div className="section" style={{ marginTop: 44 }}>
            {briefing.isPending ? (
              <TextSkeleton lines={2} h={26} label="Reading what happened" />
            ) : (
              <p className="summary">{briefing.data.summary}</p>
            )}
          </div>

          <div className="section" style={{ marginTop: 44 }}>
            <div className="head">
              <h2>Your to-do list</h2>
              <span className="label">Urgency, 0 to 100</span>
            </div>
            {briefing.isPending ? (
              <div style={{ marginTop: 20 }}>
                <ListSkeleton rows={5} label="Ranking your to-do list" />
              </div>
            ) : briefing.data.actions.length === 0 ? (
              <p className="muted" style={{ marginTop: 20 }}>
                Nothing changed that needs you in this time. Try a longer time.
              </p>
            ) : (
              <ol className="todo">
                {briefing.data.actions.map((a, i) => (
                  <li key={`${a.title}-${i}`} className={a.priority > 80 ? 'hot' : undefined}>
                    <span className="n">{i + 1}</span>
                    <div>
                      <h3>{a.title}</h3>
                      <p>{a.why}</p>
                      {a.citations.length > 0 && (
                        <p className="src">
                          {[...new Map(a.citations.map(c => [c.source_id, c])).values()].map(c => (
                            <span key={c.source_id}>
                              {c.decision_id ? <Link to={`/decisions/${c.decision_id}`}>{srcLine(c)}</Link> : srcLine(c)}.{' '}
                            </span>
                          ))}
                        </p>
                      )}
                    </div>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <button type="button" className="u" aria-label={`Urgency ${a.priority}. Why: ${a.reasons.join(', ')}`}>
                          {a.priority}
                        </button>
                      </TooltipTrigger>
                      <TooltipContent side="left">{a.reasons.join('. ')}</TooltipContent>
                    </Tooltip>
                  </li>
                ))}
              </ol>
            )}
            <p className="small muted" style={{ marginTop: 20 }}>
              Canon ranks by how serious the rule is, how recent the change is, and how close it is to your work. An open conflict stays on the list
              until someone resolves it, however old it is. The demo history ends on 17 October 2026, so the time counts back from that day.
            </p>
          </div>
        </>
      )}
    </main>
  )
}
