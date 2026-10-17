// The org chart and who-decides-what, read from /api/people, /api/decisions and /api/alerts.
import FALLBACK from '@/samples/org.json'
import type { Alert, Authority, Decision, Level, Person } from './schemas'

export const AUTHORITY_WORD: Record<Authority, string> = { official: 'Official', proposed: 'Proposed', claim: 'Claim' }

const RANK: Record<Level, number> = { exec: 0, head: 1, lead: 2, ic: 3 }

type Fallback = Record<string, { reports_to: string | null; level: string; successor: string | null }>

/**
 * People rows written before the org fields existed carry no manager and level `ic` for everyone.
 * Then fill the org from data/people.json (bundled as samples/org.json, keyed by name), so the
 * chart still draws until the people collection is reseeded.
 */
export function withOrg(people: Person[], fallback: Fallback = FALLBACK): Person[] {
  if (people.some(p => p.reports_to || p.level !== 'ic')) return people
  const idOf = new Map(people.map(p => [p.name, p.id]))
  return people.map(p => {
    const f = fallback[p.name]
    if (!f) return p
    const level = (f.level in RANK ? f.level : 'ic') as Level
    return {
      ...p,
      level,
      reports_to: (f.reports_to && idOf.get(f.reports_to)) ?? null,
      successor: (f.successor && idOf.get(f.successor)) ?? null,
    }
  })
}

export interface OrgNode {
  person: Person
  reports: OrgNode[]
}

const byRank = (a: Person, b: Person) =>
  (a.status === 'left' ? 1 : 0) - (b.status === 'left' ? 1 : 0) || RANK[a.level] - RANK[b.level] || a.name.localeCompare(b.name)

/** The org as a tree: the CEO (no manager) on top, then heads, leads and ICs. A broken manager link makes a root. */
export function orgTree(people: Person[]): OrgNode[] {
  const ids = new Set(people.map(p => p.id))
  const kids = new Map<string, Person[]>()
  const roots: Person[] = []
  for (const p of people) {
    if (p.reports_to && p.reports_to !== p.id && ids.has(p.reports_to)) kids.set(p.reports_to, [...(kids.get(p.reports_to) ?? []), p])
    else roots.push(p)
  }
  const seen = new Set<string>()
  const node = (p: Person): OrgNode => {
    seen.add(p.id)
    return {
      person: p,
      reports: (kids.get(p.id) ?? [])
        .filter(c => !seen.has(c.id))
        .sort(byRank)
        .map(node),
    }
  }
  return roots.sort(byRank).map(node)
}

/** Decisions a person owns, by authority. Owners are stored by name. */
export function ownedBy(decisions: Decision[], name: string) {
  const mine = decisions.filter(d => d.owner === name)
  return {
    all: mine,
    official: mine.filter(d => d.authority === 'official'),
    proposed: mine.filter(d => d.authority !== 'official'),
    active: mine.filter(d => d.status === 'active'),
  }
}

/**
 * "Unverified: a claim from X conflicts with ... Mei Tan (Engineering manager) should confirm or dismiss."
 * Returns the person named to confirm, or null for any other alert.
 */
export function confirmer(a: Alert): string | null {
  if (!a.explanation.startsWith('Unverified:')) return null
  const m = /(?:^|[.!?]\s+)([^.!?]+?)\s+should confirm or dismiss/.exec(a.explanation)
  return m?.[1]?.replace(/\s*\([^)]*\)\s*$/, '').trim() || null
}

/** Unverified alerts that name this person to confirm or dismiss. */
export const addressedTo = (alerts: Alert[], name: string) => alerts.filter(a => confirmer(a) === name)

export const personByName = (people: Person[]) => new Map(people.map(p => [p.name, p]))

/** Backend wording "a claim from X conflicts with the official decision" reads better as "X claims ... goes against". */
export const plainUnverified = (text: string) =>
  text
    .replace(/^Unverified: a claim from (.+?) conflicts with the /, 'Unverified: $1 claims something that goes against the ')
    .replace(/^Unverified: a proposed from (.+?) conflicts with the /, 'Unverified: $1 proposes something that goes against the ')
