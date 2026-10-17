import { ArrowRight } from 'lucide-react'
import { useDeferredValue, useState } from 'react'
import { Link } from 'react-router-dom'
import { ActivityFeed } from '@/components/activity-feed'
import { Section } from '@/components/error-boundary'
import { PageHeader } from '@/components/page-header'
import { RowsSkeleton } from '@/components/states'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import type { Persona } from '@/lib/schemas'
import { AlertsList } from './AlertsList'
import { BlockCard } from './BlockCard'
import { BriefingView } from './BriefingView'
import { SINCE, type Since } from './since'

const PERSONAS: [Persona, string][] = [
  ['engineer', 'Engineer'],
  ['pm', 'PM'],
  ['new_hire', 'New hire'],
]

const today = () => new Date().toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'short', year: 'numeric' })

export default function HomePage() {
  const [persona, setPersona] = useState<Persona>('engineer')
  const [since, setSince] = useState<Since>('7')
  // the old briefing stays on screen, dimmed, while the new one loads
  const viewPersona = useDeferredValue(persona)
  const viewSince = useDeferredValue(since)
  const stale = viewPersona !== persona || viewSince !== since

  const choose = (p: string) => {
    if (!p) return
    setPersona(p as Persona)
    if (p === 'new_hire') setSince('all') // onboarding reads the whole record
  }

  return (
    <>
      <div className="border-b bg-card/70">
        <p className="mx-auto max-w-[1440px] px-4 py-3 font-heading text-lg md:px-8 md:text-xl">
          Canon is the shared memory of a company. People and AI agents read it, write it, and get blocked when they break a decision.
        </p>
      </div>
      <main className="mx-auto max-w-[1440px] px-4 pt-8 pb-12 md:px-8">
        <PageHeader eyebrow={`Catch me up / ${today()}`} title="Here is what changed." quiet="And what to do about it.">
          <div className="flex flex-col gap-2">
            <span className="label" id="persona-label">
              I am a
            </span>
            <ToggleGroup type="single" variant="outline" value={persona} onValueChange={choose} aria-labelledby="persona-label">
              {PERSONAS.map(([p, t]) => (
                <ToggleGroupItem
                  key={p}
                  value={p}
                  className="h-10 px-4 text-[15px] data-[state=on]:bg-primary data-[state=on]:text-primary-foreground"
                >
                  {t}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="since" className="label">
              Since
            </Label>
            <Select value={since} onValueChange={v => setSince(v as Since)}>
              <SelectTrigger id="since" className="w-44 bg-card">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(SINCE).map(([k, t]) => (
                  <SelectItem key={k} value={k}>
                    {t}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </PageHeader>

        <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="flex min-w-0 flex-col gap-10">
            <BlockCard />
            <Section fallback={<BriefingSkeleton />}>
              <BriefingView persona={viewPersona} since={viewSince} stale={stale} />
            </Section>
            <AlertsList />
          </div>
          <aside className="flex flex-col gap-3" aria-label="Agent activity">
            <ActivityFeed />
            <Button variant="outline" asChild>
              <Link to="/agents">
                Open the agent playground <ArrowRight aria-hidden />
              </Link>
            </Button>
          </aside>
        </div>
      </main>
    </>
  )
}

function BriefingSkeleton() {
  return (
    <div className="flex flex-col gap-6" role="status" aria-label="Reading the record for your briefing">
      <div className="grid gap-6 rounded-lg border bg-card p-6 md:grid-cols-[1.3fr_1fr]">
        <div className="flex flex-col gap-3">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-7 w-full" />
          <Skeleton className="h-7 w-11/12" />
          <Skeleton className="h-7 w-3/4" />
        </div>
        <RowsSkeleton rows={3} />
      </div>
      <RowsSkeleton rows={3} />
    </div>
  )
}
