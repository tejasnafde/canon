import { describe, expect, it } from 'vitest'
import { addressedTo, confirmer, orgTree, ownedBy, plainUnverified, withOrg } from './org'
import { Alert, Decision, Person } from './schemas'

const person = (p: Partial<Person> & { id: string; name: string }) => Person.parse({ role: 'Engineer', team: 'Platform', ...p })
const alert = (explanation: string, status = 'open') =>
  Alert.parse({ id: 'a', workspace: 'acme', kind: 'contradiction', severity: 'low', explanation, status, created_at: '2026-10-01T00:00:00Z' })

const UNVERIFIED =
  'Unverified: a claim from guest42 conflicts with the official decision "No production deploys on Fridays." (Mei Tan, 2026-03-09). ' +
  'The message says Friday deploys are fine. Mei Tan (Engineering manager) should confirm or dismiss.'

describe('org tree', () => {
  it('puts the CEO on top, then heads before leads before ICs, and people who left last', () => {
    const tree = orgTree([
      person({ id: 'ic', name: 'Zed', reports_to: 'ceo' }),
      person({ id: 'gone', name: 'Abe', reports_to: 'ceo', status: 'left', level: 'head' }),
      person({ id: 'head', name: 'Yan', reports_to: 'ceo', level: 'head' }),
      person({ id: 'lead', name: 'Xi', reports_to: 'head', level: 'lead' }),
      person({ id: 'ceo', name: 'Hana', level: 'exec' }),
    ])
    expect(tree.map(n => n.person.id)).toEqual(['ceo'])
    expect(tree[0]?.reports.map(n => n.person.id)).toEqual(['head', 'ic', 'gone'])
    expect(tree[0]?.reports[0]?.reports.map(n => n.person.id)).toEqual(['lead'])
  })

  it('survives a manager link to nobody and a cycle', () => {
    const tree = orgTree([person({ id: 'a', name: 'A', reports_to: 'missing' }), person({ id: 'b', name: 'B', reports_to: 'b' })])
    expect(tree.map(n => n.person.id).sort()).toEqual(['a', 'b'])
  })

  it('fills the org from the bundled people.json when the API rows predate the org fields', () => {
    const live = [
      person({ id: 'acme4-hana-okafor', name: 'Hana Okafor' }),
      person({ id: 'acme4-mei-tan', name: 'Mei Tan' }),
      person({ id: 'acme4-anika-rao', name: 'Anika Rao', status: 'left' }),
    ]
    const filled = withOrg(live)
    expect(filled.find(p => p.name === 'Mei Tan')).toMatchObject({ level: 'head', reports_to: 'acme4-hana-okafor' })
    expect(filled.find(p => p.name === 'Anika Rao')).toMatchObject({ successor: 'acme4-mei-tan' })
    expect(orgTree(filled).map(n => n.person.name)).toEqual(['Hana Okafor'])
  })

  it('keeps real org fields untouched', () => {
    const rows = [person({ id: 'x', name: 'Mei Tan', level: 'lead' })]
    expect(withOrg(rows)).toBe(rows)
  })
})

describe('authority', () => {
  it('reads who should confirm an unverified claim', () => {
    expect(confirmer(alert(UNVERIFIED))).toBe('Mei Tan')
    expect(confirmer(alert('Unverified: something. Aisha Rahman should confirm or dismiss.'))).toBe('Aisha Rahman')
    expect(confirmer(alert('The wiki still says Friday.'))).toBeNull()
    expect(addressedTo([alert(UNVERIFIED), alert('other')], 'Mei Tan')).toHaveLength(1)
  })

  it('rewrites the claim wording in plain words', () => {
    expect(plainUnverified(UNVERIFIED)).toMatch(/^Unverified: guest42 claims something that goes against the official decision/)
  })

  it('splits owned decisions by authority', () => {
    const d = (id: string, authority: string) =>
      Decision.parse({
        id,
        workspace: 'acme',
        statement: id,
        rationale: '',
        owner: 'Mei Tan',
        ts: '2026-01-01T00:00:00Z',
        topic: 't',
        quotes: [],
        authority,
      })
    const legacy = Decision.parse({
      id: 'old',
      workspace: 'acme',
      statement: 'o',
      rationale: '',
      owner: 'Mei Tan',
      ts: '2025-01-01T00:00:00Z',
      topic: 't',
      quotes: [],
    })
    const m = ownedBy([d('a', 'official'), d('b', 'proposed'), d('c', 'claim'), legacy], 'Mei Tan')
    expect(m.official.map(x => x.id)).toEqual(['a', 'old'])
    expect(m.proposed.map(x => x.id)).toEqual(['b', 'c'])
  })
})
