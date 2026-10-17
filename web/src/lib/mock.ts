// VITE_MOCK=1 only: canned data shaped like the real API, so the UI can be shown without a backend.
// Names and quotes follow the synthetic Northwind Labs corpus in data/.
import type {
  Activity,
  Alert,
  AskResult,
  Briefing,
  CheckResult,
  Citation,
  Decision,
  DecisionDetail,
  EvalReport,
  IngestResult,
  Person,
  Persona,
  ResolveAction,
  Source,
} from './schemas'

const now = Date.now()

/** Pick a fixture element that is known to exist. */
const at = <T>(xs: T[], i: number): T => xs[i] as T
const ago = (min: number) => new Date(now - min * 60_000).toISOString()

const q = (source_id: string, quote: string) => ({ source_id, quote })

const src = (s: Pick<Source, 'id' | 'kind' | 'title' | 'author' | 'ts'>): Source => ({
  workspace: 'acme',
  url: null,
  text: '',
  synthetic: true,
  image_b64: null,
  ...s,
})

const sources: Source[] = [
  src({ id: 'src_inc042', kind: 'meeting', title: 'INC-042 review: the Friday release', author: 'Mei Tan', ts: '2026-03-16T05:00:00Z' }),
  src({ id: 'src_relcal', kind: 'slack', title: 'Release calendar pilot', author: 'Anika Rao', ts: '2025-11-04T08:00:00Z' }),
  src({ id: 'src_relwiki', kind: 'wiki', title: 'Release process', author: 'Anika Rao', ts: '2025-11-05T08:00:00Z' }),
  src({ id: 'src_pager', kind: 'email', title: 'Re: responder coverage for production changes', author: 'Mei Tan', ts: '2026-06-02T04:00:00Z' }),
  src({ id: 'src_price2', kind: 'meeting', title: 'Commercial review, September', author: 'Nur Aziz', ts: '2026-09-08T06:00:00Z' }),
  src({ id: 'src_faq', kind: 'wiki', title: 'Route Lens sales FAQ', author: 'Arjun Desai', ts: '2026-02-11T06:00:00Z' }),
]

const dec = (d: Partial<Decision> & Pick<Decision, 'id' | 'statement' | 'owner' | 'ts' | 'topic'>): Decision => ({
  workspace: 'acme',
  rationale: '',
  assumptions: [],
  status: 'active',
  version: 1,
  supersedes: [],
  superseded_by: null,
  quotes: [],
  created_by: 'human',
  ...d,
})

const decisions: Decision[] = [
  dec({
    id: 'dec_nofri',
    statement: 'No production deploys on Fridays, including scheduled jobs and configuration-only releases.',
    rationale:
      'INC-042 started with a Friday afternoon release. Only one responder was online and the rollback took three hours. Shipping earlier in the week leaves a full team to fix what breaks.',
    assumptions: [
      'Weekend on-call is one person.',
      'Configuration changes have no automated rollback.',
      'Most customers are active Monday to Friday.',
    ],
    owner: 'Mei Tan',
    ts: '2026-03-16T05:00:00Z',
    topic: 'release',
    version: 2,
    supersedes: ['dec_relwin'],
    quotes: [
      q('src_inc042', 'No production deploys on Fridays, including scheduled jobs and configuration-only releases.'),
      q('src_pager', 'Every production change needs a primary and a secondary responder online for the next two hours.'),
    ],
  }),
  dec({
    id: 'dec_relwin',
    statement: 'For now the production release window is Friday afternoon, 14:00 to 16:00 Singapore time.',
    rationale: 'Release calendar pilot.',
    owner: 'Anika Rao',
    ts: '2025-11-04T08:00:00Z',
    topic: 'release',
    status: 'superseded',
    superseded_by: 'dec_nofri',
    quotes: [q('src_relcal', 'For now the production release window is Friday afternoon, 14:00 to 16:00 Singapore time.')],
  }),
  dec({
    id: 'dec_price2',
    statement: 'New Route Lens subscriptions cost USD 149 per workspace per month.',
    rationale: 'A second inference pass raised serving cost per workspace.',
    owner: 'Nur Aziz',
    ts: '2026-09-08T06:00:00Z',
    topic: 'pricing',
    version: 2,
    quotes: [q('src_price2', 'New Route Lens subscriptions cost USD 149 per workspace per month.')],
  }),
  dec({
    id: 'dec_pager',
    statement: 'Every production change needs a primary and a secondary responder online for the next two hours.',
    rationale: 'Two people are needed for a rollback.',
    owner: 'Mei Tan',
    ts: '2026-06-02T04:00:00Z',
    topic: 'release',
    quotes: [q('src_pager', 'Every production change needs a primary and a secondary responder online for the next two hours.')],
  }),
  dec({
    id: 'dec_sso',
    statement: 'SAML SSO is included in Enterprise and is not a paid add-on.',
    rationale: 'Enterprise buyers expect it.',
    owner: 'Aisha Rahman',
    ts: '2026-01-20T04:00:00Z',
    topic: 'pricing',
    quotes: [],
  }),
]

let alerts: Alert[] = [
  {
    id: 'al_1',
    workspace: 'acme',
    kind: 'stale_doc',
    severity: 'high',
    decision_id: 'dec_nofri',
    source_id: 'src_relwiki',
    status: 'open',
    resolution: null,
    created_by: 'canon',
    created_at: ago(300),
    related_decision_id: null,
    explanation: 'Wiki "Release process" says Friday afternoon is the production release window. A newer decision bans Friday deploys.',
    quotes: [
      q('src_relwiki', 'Friday afternoon, 14:00 to 16:00 SGT, is our production release window.'),
      q('src_inc042', 'No production deploys on Fridays, including scheduled jobs and configuration-only releases.'),
    ],
  },
  {
    id: 'al_2',
    workspace: 'acme',
    kind: 'stale_doc',
    severity: 'medium',
    decision_id: 'dec_price2',
    source_id: 'src_faq',
    status: 'open',
    resolution: null,
    created_by: 'canon',
    created_at: ago(1500),
    related_decision_id: null,
    explanation: 'Route Lens sales FAQ still quotes USD 99 per workspace. The September commercial review set USD 149.',
    quotes: [q('src_faq', 'Route Lens costs USD 99 per workspace per month at GA.')],
  },
  {
    id: 'al_3',
    workspace: 'acme',
    kind: 'premise_changed',
    severity: 'low',
    decision_id: 'dec_nofri',
    source_id: null,
    status: 'open',
    resolution: null,
    created_by: 'canon',
    created_at: ago(4200),
    related_decision_id: null,
    explanation: 'A new runbook adds automated rollback for configuration changes. That breaks an assumption behind the Friday ban.',
    quotes: [],
  },
]

let activity: Activity[] = [
  {
    id: 'a1',
    workspace: 'agents',
    actor: 'agent:release-bot',
    action: 'check',
    verdict: 'block',
    explanation: 'A Friday production change breaks the active no-Friday-deploys decision. Scheduled jobs are explicitly in scope.',
    created_at: ago(3),
    summary: 'check: "Deploy the production dispatch service this Friday at 15:00 SGT using a cron job."',
    ref_ids: ['dec_nofri'],
    ref_titles: ['No production deploys on Fridays, including scheduled jobs and configuration-only releases.'],
  },
  {
    id: 'a2',
    workspace: 'agents',
    actor: 'agent:claude-code',
    action: 'check',
    verdict: 'allow',
    explanation: null,
    created_at: ago(7),
    summary: 'check: "Deploy on Tuesday morning with two responders online for two hours."',
    ref_ids: ['dec_pager'],
    ref_titles: ['Two responders online for two hours'],
  },
  {
    id: 'a3',
    workspace: 'agents',
    actor: 'agent:pm-bot',
    action: 'check',
    verdict: 'warn',
    explanation: null,
    created_at: ago(14),
    summary: 'check: "Email the Meridian prospect the USD 99 Route Lens price."',
    ref_ids: ['dec_price2'],
    ref_titles: ['Route Lens costs USD 149 per workspace'],
  },
  {
    id: 'a4',
    workspace: 'agents',
    actor: 'agent:claude-code',
    action: 'ask',
    verdict: null,
    explanation: null,
    created_at: ago(22),
    summary: 'ask: "Why can we no longer deploy production on Fridays?"',
    ref_ids: [],
    ref_titles: [],
  },
  {
    id: 'a5',
    workspace: 'agents',
    actor: 'agent:procurement-bot',
    action: 'record',
    verdict: null,
    explanation: null,
    created_at: ago(40),
    summary: 'record: "Use matte thermal labels for all new depot scanner kits." reconciled: new',
    ref_ids: [],
    ref_titles: [],
  },
  {
    id: 'a6',
    workspace: 'acme',
    actor: 'human:web',
    action: 'ingest',
    verdict: null,
    explanation: null,
    created_at: ago(58),
    summary: 'ingest: Commercial review, September. 2 decisions',
    ref_ids: [],
    ref_titles: [],
  },
  {
    id: 'a7',
    workspace: 'agents',
    actor: 'agent:codex',
    action: 'search',
    verdict: null,
    explanation: null,
    created_at: ago(75),
    summary: 'search: "webhook retry horizon"',
    ref_ids: [],
    ref_titles: [],
  },
]

const people: Person[] = [
  { id: 'mei-tan', name: 'Mei Tan', role: 'Engineering manager', team: 'Platform', status: 'active', left_at: null },
  { id: 'nur-aziz', name: 'Nur Aziz', role: 'Finance lead', team: 'Finance', status: 'active', left_at: null },
  { id: 'jiwon-park', name: 'Jiwon Park', role: 'Security engineer', team: 'Security', status: 'active', left_at: null },
  { id: 'anika-rao', name: 'Anika Rao', role: 'Staff platform engineer', team: 'Platform', status: 'left', left_at: '2026-06-30T09:00:00Z' },
]

const cite = (s: Source, quote: string, decision_id: string | null): Citation => ({
  source_id: s.id ?? '',
  decision_id,
  quote,
  title: s.title,
  kind: s.kind,
  ts: s.ts,
  url: null,
})

const fridayCites = [
  cite(at(sources, 1), 'For now the production release window is Friday afternoon, 14:00 to 16:00 Singapore time.', 'dec_relwin'),
  cite(at(sources, 0), 'No production deploys on Fridays, including scheduled jobs and configuration-only releases.', 'dec_nofri'),
  cite(at(sources, 3), 'Every production change needs a primary and a secondary responder online for the next two hours.', 'dec_pager'),
]

const timeline = [
  {
    ts: '2025-11-04T08:00:00Z',
    decision_id: 'dec_relwin',
    statement: 'Release window is Friday 14:00 to 16:00 SGT (Anika Rao)',
    status: 'superseded',
    relation: 'new' as const,
  },
  {
    ts: '2026-03-16T05:00:00Z',
    decision_id: 'dec_nofri',
    statement: 'No production deploys on Fridays, scheduled jobs included',
    status: 'active',
    relation: 'update' as const,
  },
  {
    ts: '2026-06-02T04:00:00Z',
    decision_id: 'dec_pager',
    statement: 'Two responders online for two hours after every change',
    status: 'active',
    relation: 'new' as const,
  },
  {
    ts: ago(3),
    decision_id: 'dec_nofri',
    statement: 'release-bot tries a Friday cron. Blocked.',
    status: 'active',
    relation: 'contradiction' as const,
  },
]

function ask(question: string): AskResult {
  if (/revenue|acquired|password|replaces|offsite/i.test(question))
    return { answer: 'I do not know. Nothing in the record covers this.', citations: [], timeline: [], refused: true, latency_ms: 640 }
  return {
    answer:
      'Because a Friday release caused INC-042. Until March the release window was Friday afternoon [1]. After the incident review, Mei Tan ruled that nothing goes to production on a Friday, scheduled jobs and configuration-only releases included [2]. Every change also needs two responders online for two hours [3].',
    citations: fridayCites,
    timeline,
    refused: false,
    latency_ms: 1420,
  }
}

function check(intent: string): CheckResult {
  const fri = /fri/i.test(intent)
  return {
    verdict: fri ? 'block' : 'allow',
    latency_ms: 612,
    explanation: fri
      ? 'A Friday production change breaks the active no-Friday-deploys decision. Scheduled jobs are explicitly in scope.'
      : 'No active decision forbids this.',
    decisions: fri ? [at(decisions, 0)] : [],
    citations: fri ? [at(fridayCites, 1)] : [],
  }
}

function briefing(persona: Briefing['persona'], since: string): Briefing {
  return {
    persona,
    since,
    latency_ms: 2100,
    summary:
      'Two things matter this week. An agent tried to schedule a Friday production cron, which breaks the no-Friday-deploys rule set after INC-042. And Route Lens now costs USD 149 per workspace for new customers, but the sales FAQ still says USD 99.',
    highlights: [
      'New Route Lens subscriptions cost USD 149 per workspace. Nur Aziz, 8 Sep.',
      'The "Release process" wiki still names Friday afternoon as the release window.',
      'release-bot was blocked from a Friday production cron.',
      'Anika Rao left in June. Mei Tan owns release policy.',
    ],
    actions: [
      {
        priority: 94,
        title: 'Stop the Friday dispatch cron before it runs',
        why: 'release-bot scheduled a production job for Friday 15:00 SGT. That contradicts an active decision.',
        deadline: null,
        reasons: ['contradicts active decision', 'runs this Friday', 'blocks nothing'],
        citations: [at(fridayCites, 1)],
        chip: 'view_decision',
      },
      {
        priority: 81,
        title: 'Update the Route Lens sales FAQ to USD 149',
        why: 'The FAQ still quotes USD 99. Sales is sending it to the Meridian prospect.',
        deadline: null,
        reasons: ['stale doc', 'customer facing'],
        citations: [cite(at(sources, 4), 'New Route Lens subscriptions cost USD 149 per workspace per month.', 'dec_price2')],
        chip: 'resolve_alert',
      },
      {
        priority: 62,
        title: 'Fix the stale "Release process" wiki page',
        why: 'New hires read it first. Its author, Anika Rao, has left.',
        deadline: null,
        reasons: ['contradicted by decision', 'owner left company'],
        citations: [at(fridayCites, 1)],
        chip: 'resolve_alert',
      },
      {
        priority: 38,
        title: 'Ask Mei Tan about the new rollback runbook',
        why: 'It changes an assumption behind the Friday rule.',
        deadline: null,
        reasons: ['premise changed', 'low effort'],
        citations: [],
        chip: 'ask_person',
      },
    ],
    who_to_ask: persona === 'new_hire' ? people : [],
  }
}

function ingest(source: Source): IngestResult {
  const contra = /fri/i.test(source.text)
  const d = dec({
    id: `dec_new_${Math.round(Math.random() * 1e6)}`,
    workspace: 'v-mock',
    statement: source.text.split(/[.:]/).slice(1, 2).join('').trim() || source.title,
    owner: source.author,
    ts: source.ts,
    topic: 'paste',
    quotes: [q('src_new', source.text.slice(0, 120))],
  })
  const al: Alert[] = contra
    ? [
        {
          id: `al_new_${d.id}`,
          workspace: 'v-mock',
          kind: 'contradiction',
          severity: 'high',
          decision_id: 'dec_nofri',
          related_decision_id: null,
          source_id: 'src_new',
          status: 'open',
          resolution: null,
          created_by: 'canon',
          created_at: new Date().toISOString(),
          explanation: `"${source.title}" schedules production work on a Friday. That contradicts the no-Friday-deploys decision.`,
          quotes: [],
        },
      ]
    : []
  alerts = [...al, ...alerts]
  activity = [
    {
      id: `a${Date.now()}`,
      workspace: 'v-mock',
      actor: 'human:web',
      action: 'ingest',
      verdict: null,
      explanation: null,
      created_at: new Date().toISOString(),
      summary: `ingest: ${source.title}. 1 decision`,
      ref_ids: [d.id],
      ref_titles: [d.statement],
    },
    ...activity,
  ]
  return {
    source: { ...source, id: 'src_new' },
    decisions: [
      {
        decision: d,
        relation: contra ? 'contradiction' : 'new',
        related_decision_id: contra ? 'dec_nofri' : null,
        explanation: contra ? 'Schedules production work on a Friday.' : '',
      },
    ],
    alerts: al,
    rejected_quotes: 1,
    latency_ms: 3800,
  }
}

const evalReport: EvalReport = {
  run_at: '2026-10-17T11:10:00Z',
  model: 'gemini-3.5-flash-lite',
  decisions_planted: 30,
  decisions_found: 28,
  contradictions_planted: 12,
  contradictions_found: 11,
  false_positives: 2,
  check_cases: 15,
  check_correct: 14,
  unanswerable: 5,
  refused_correctly: 5,
  p50_ms: 1300,
  p95_ms: 3900,
  notes: ['Mock numbers. The real report comes from the last committed eval run.'],
}

const sleep = (ms: number) => new Promise(r => setTimeout(r, ms))

interface Body {
  question?: string
  intent?: string
  persona?: Persona
  since?: string
  source?: Source
  action?: ResolveAction
  actor?: string
  query?: string
  limit?: number
  statement?: string
  source_text?: string
  description?: string
}

export async function mockApi(method: string, path: string, raw: unknown): Promise<unknown> {
  const body = (raw ?? {}) as Body
  await sleep(method === 'POST' ? 700 : 150)
  const p = path.split('?')[0] ?? ''
  if (p === '/health') return { ok: true, model: 'gemini-3.5-flash-lite' }
  if (p === '/api/activity') return activity
  if (p === '/api/alerts') return alerts.filter(a => a.status === 'open')
  if (p === '/api/people') return people
  if (p === '/api/eval') return evalReport
  if (p === '/api/decisions') return decisions
  if (p.startsWith('/api/decisions/')) {
    const id = decodeURIComponent(p.split('/').pop() ?? '')
    const d = decisions.find(x => x.id === id)
    if (!d) throw new Error('404 not_found: ' + id)
    const detail: DecisionDetail = {
      decision: d,
      timeline: id === 'dec_nofri' ? timeline : [],
      sources,
      alerts: alerts.filter(a => a.decision_id === id),
    }
    return detail
  }
  if (p === '/api/ask') return ask(body.question ?? '')
  if (p === '/api/check') return check(body.intent ?? '')
  if (p === '/api/briefing') return briefing(body.persona ?? 'engineer', body.since ?? '')
  if (p === '/api/ingest') {
    await sleep(3000)
    return ingest(body.source ?? src({ id: null, kind: 'paste', title: '', author: '', ts: new Date().toISOString() }))
  }
  if (p.startsWith('/api/alerts/')) {
    const id = p.split('/')[3] ?? ''
    alerts = alerts.map(a => (a.id === id ? { ...a, status: 'resolved', resolution: body.action ?? null } : a))
    return alerts.find(a => a.id === id)
  }
  if (p === '/api/workspace/reset') return { ok: true }
  throw new Error('404 mock has no ' + p)
}

export async function mockTool(name: string, rawArgs: Record<string, unknown>): Promise<unknown> {
  const args = rawArgs as Body
  await sleep(600)
  const actor = 'agent:' + (args.actor || 'playground')
  const log = (
    action: Activity['action'],
    summary: string,
    verdict: Activity['verdict'] = null,
    refs: Decision[] = [],
    explanation: string | null = null,
  ) => {
    activity = [
      {
        id: `a${Date.now()}`,
        workspace: 'agents',
        actor,
        action,
        summary,
        verdict,
        explanation,
        created_at: new Date().toISOString(),
        ref_ids: refs.map(d => d.id),
        ref_titles: refs.map(d => d.statement),
      },
      ...activity,
    ]
  }
  switch (name) {
    case 'check_intent': {
      const r = check(args.intent ?? '')
      log('check', `check: "${args.intent}"`, r.verdict, r.decisions, r.explanation)
      return r
    }
    case 'search_decisions':
      log('search', `search: "${args.query}"`)
      return decisions.filter(d => d.status === 'active').slice(0, args.limit ?? 5)
    case 'ask_why':
      log('ask', `ask: "${args.question}"`)
      return ask(args.question ?? '')
    case 'catch_me_up':
      log('briefing', `briefing: ${args.persona}`)
      return briefing(args.persona ?? 'engineer', args.since ?? '')
    case 'record_decision':
      log('record', `record: "${args.statement}"`)
      return ingest({
        ...src({ id: null, kind: 'agent', title: args.statement ?? '', author: actor, ts: new Date().toISOString() }),
        text: args.source_text ?? '',
      })
    case 'flag_conflict': {
      const d = decisions.find(x => x.status === 'active')
      const a: Alert = {
        id: `al${Date.now()}`,
        workspace: 'agents',
        kind: 'agent_violation',
        severity: 'medium',
        decision_id: d?.id ?? null,
        related_decision_id: null,
        source_id: null,
        explanation: args.description ?? '',
        quotes: [],
        status: 'open',
        resolution: null,
        created_by: actor,
        created_at: new Date().toISOString(),
      }
      alerts = [a, ...alerts]
      log('flag', `Flagged: ${args.description}`, null, d ? [d] : [], args.description ?? null)
      return a
    }
  }
  throw new Error('Unknown tool ' + name)
}
