import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ErrorState } from '@/components/states'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { callTool } from '@/lib/mcp'
import { invalidateRecord } from '@/lib/query'
import { CheckResult, Persona } from '@/lib/schemas'
import { jsonTokens } from '@/lib/format'
import { cn } from '@/lib/utils'
import { exampleArgs, typedArgs, type ToolSpec } from './tools'

interface Out {
  ms: number
  data: unknown
}

export function ToolForm({ spec }: { spec: ToolSpec }) {
  const [args, setArgs] = useState(() => exampleArgs(spec))
  const call = useMutation({
    mutationFn: async (): Promise<Out> => {
      const t0 = performance.now()
      const data = await callTool(spec.name, typedArgs(spec, args))
      return { ms: Math.round(performance.now() - t0), data }
    },
    // the call shows in the feed; record and flag also write
    onSettled: () => {
      void invalidateRecord()
    },
  })
  const set = (k: string, v: string) => setArgs(a => ({ ...a, [k]: v }))
  const check = spec.name === 'check_intent' && call.data ? CheckResult.safeParse(call.data.data) : undefined

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <form
          onSubmit={e => {
            e.preventDefault()
            call.mutate()
          }}
          className="contents"
        >
          <CardHeader>
            <CardTitle className="font-mono text-lg">
              <h2>{spec.name}</h2>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {spec.fields.map(f => {
              const id = `${spec.name}-${f.name}`
              return (
                <div key={f.name} className="flex flex-col gap-2">
                  <Label htmlFor={id} className="label">
                    {f.name}
                  </Label>
                  {f.kind === 'persona' ? (
                    <Select value={args[f.name] ?? 'engineer'} onValueChange={v => set(f.name, v)}>
                      <SelectTrigger id={id} className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {Persona.options.map(p => (
                          <SelectItem key={p} value={p}>
                            {p}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  ) : f.long ? (
                    <Textarea id={id} rows={3} value={args[f.name] ?? ''} onChange={e => set(f.name, e.target.value)} />
                  ) : (
                    <Input
                      id={id}
                      type={f.kind === 'number' ? 'number' : 'text'}
                      value={args[f.name] ?? ''}
                      onChange={e => set(f.name, e.target.value)}
                    />
                  )}
                </div>
              )
            })}
          </CardContent>
          <CardFooter className="justify-between gap-3">
            <span className="label">POST /mcp / tools/call</span>
            <Button type="submit" disabled={call.isPending}>
              {call.isPending ? 'Calling' : 'Call tool'}
            </Button>
          </CardFooter>
        </form>
      </Card>

      <div aria-live="polite">
        {call.isPending && (
          <div className="flex flex-col gap-2" role="status" aria-label={`Calling ${spec.name} over MCP`}>
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-40 w-full" />
          </div>
        )}
        {call.isError && <ErrorState title="The tool call failed" error={call.error} retry={() => call.mutate()} />}
        {call.data && (
          <div className="flex flex-col gap-3 motion-safe:animate-in motion-safe:fade-in-0 motion-safe:duration-200">
            {check?.success && <VerdictBanner r={check.data} ms={call.data.ms} />}
            {!check?.success && <p className="label">Response / {call.data.ms} ms round trip</p>}
            <JsonPanel value={call.data.data} />
          </div>
        )}
      </div>
    </div>
  )
}

const TOK = { key: 'text-sky-300', str: 'text-emerald-300', num: 'text-amber-300', lit: 'text-fuchsia-300', punct: 'text-zinc-400' } as const

function JsonPanel({ value }: { value: unknown }) {
  return (
    <pre
      tabIndex={0}
      role="region"
      aria-label="Raw tool response"
      className="max-h-96 overflow-auto rounded-lg bg-zinc-950 p-4 font-mono text-[13px] leading-relaxed text-zinc-100"
    >
      {jsonTokens(JSON.stringify(value, null, 2)).map((k, i) => (
        <span key={i} className={TOK[k.t]}>
          {k.s}
        </span>
      ))}
    </pre>
  )
}

const BANNER = { block: 'bg-signal text-white', warn: 'bg-warn-soft text-warn-ink', allow: 'bg-ok-soft text-ok-ink' } as const

function VerdictBanner({ r, ms }: { r: CheckResult; ms: number }) {
  const d = r.decisions[0]
  return (
    <div className={cn('flex flex-col gap-2 rounded-lg px-5 py-4', BANNER[r.verdict])}>
      <div className="flex items-baseline justify-between gap-4">
        <span className="label text-current">Verdict</span>
        <span className="font-mono text-xs tnum">{ms} ms</span>
      </div>
      <p className="font-heading text-5xl leading-none font-semibold tracking-tight uppercase md:text-6xl">{r.verdict}</p>
      <p className="text-[15px]">{r.explanation}</p>
      <span className="min-w-0 text-[15px]">
        {d ? (
          <>
            Deciding:{' '}
            <Link to={`/decisions/${d.id}`} className="underline underline-offset-4">
              {d.statement}
            </Link>{' '}
            ({d.owner})
          </>
        ) : null}
      </span>
    </div>
  )
}
