import examples from '@/samples/agent_playground.json'

export interface Field {
  name: string
  long?: boolean
  kind?: 'persona' | 'number'
}

export interface ToolSpec {
  name: string
  blurb: string
  fields: Field[]
}

export const TOOLS: ToolSpec[] = [
  { name: 'check_intent', blurb: 'allow, warn or block', fields: [{ name: 'intent', long: true }, { name: 'actor' }] },
  { name: 'search_decisions', blurb: 'semantic search', fields: [{ name: 'query' }, { name: 'limit', kind: 'number' }] },
  { name: 'ask_why', blurb: 'cited answer', fields: [{ name: 'question', long: true }, { name: 'actor' }] },
  { name: 'catch_me_up', blurb: 'briefing by persona', fields: [{ name: 'persona', kind: 'persona' }, { name: 'since' }, { name: 'actor' }] },
  {
    name: 'record_decision',
    blurb: 'write and reconcile',
    fields: [{ name: 'statement' }, { name: 'rationale' }, { name: 'source_text', long: true }, { name: 'actor' }],
  },
  { name: 'flag_conflict', blurb: 'raise an alert', fields: [{ name: 'description' }, { name: 'source_text', long: true }, { name: 'actor' }] },
]

/** Example args from src/samples. The playground always calls as actor "playground", so its rows stand out in the feed. */
export function exampleArgs(spec: ToolSpec): Record<string, string> {
  const ex = examples.find(e => e.tool === spec.name)
  const args: Record<string, string> = {}
  for (const [k, v] of Object.entries(ex?.args ?? {})) args[k] = k === 'since' ? String(v).slice(0, 10) : String(v)
  if (spec.fields.some(f => f.name === 'actor')) args.actor = 'playground'
  return args
}

/** Form strings to tool arguments: numbers become numbers. */
export function typedArgs(spec: ToolSpec, args: Record<string, string>): Record<string, unknown> {
  const out: Record<string, unknown> = { ...args }
  for (const f of spec.fields) if (f.kind === 'number') out[f.name] = Number(args[f.name]) || 5
  return out
}
