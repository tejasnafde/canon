import { Check, Copy } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { ActivityFeed } from '@/components/activity-feed'
import { PageHeader } from '@/components/page-header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { MCP_URL } from '@/lib/mcp'
import { ToolForm } from './ToolForm'
import { TOOLS } from './tools'

export default function AgentsPage() {
  return (
    <main className="mx-auto max-w-[1440px] px-4 pt-8 pb-12 md:px-8">
      <PageHeader eyebrow="Agents / the same MCP tools Claude Code and Codex call" title="Agents read the record before they act." />

      <Card className="mt-8 border-foreground">
        <CardHeader>
          <CardTitle>
            <h2>Connect your agent</h2>
          </CardTitle>
          <CardDescription className="text-[15px]">Streamable HTTP. No key needed for the demo.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <CopyLine label="MCP URL" value={MCP_URL} />
          <CopyLine label="Claude Code" value={`claude mcp add --transport http canon ${MCP_URL}`} />
          <CopyLine label="Codex" value={`codex mcp add canon --url ${MCP_URL}`} />
        </CardContent>
      </Card>

      <div className="mt-8 grid gap-8 xl:grid-cols-[minmax(0,1fr)_360px]">
        <Tabs defaultValue={TOOLS[0]?.name} orientation="vertical" className="grid gap-6 md:grid-cols-[220px_minmax(0,1fr)]">
          <div>
            <p className="label mb-2" id="tools-label">
              MCP tools
            </p>
            <TabsList aria-labelledby="tools-label" className="h-auto w-full flex-col items-stretch gap-1 bg-transparent p-0">
              {TOOLS.map(t => (
                <TabsTrigger
                  key={t.name}
                  value={t.name}
                  className="h-auto flex-col items-start gap-0.5 rounded-md border border-transparent px-3 py-2 text-left data-[state=active]:border-foreground data-[state=active]:bg-card data-[state=active]:shadow-none"
                >
                  <span className="font-mono text-sm">{t.name}</span>
                  <span className="text-xs text-muted-foreground">{t.blurb}</span>
                </TabsTrigger>
              ))}
            </TabsList>
          </div>
          {TOOLS.map(t => (
            <TabsContent key={t.name} value={t.name} className="min-w-0">
              <ToolForm spec={t} />
            </TabsContent>
          ))}
        </Tabs>
        <aside aria-label="Agent activity">
          <ActivityFeed limit={10} />
        </aside>
      </div>
    </main>
  )
}

function CopyLine({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      toast.success(`${label} copied`)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      toast.error('Copy failed. Select the text and copy it by hand.')
    }
  }
  return (
    <div className="min-w-0">
      <p className="label mb-1.5">{label}</p>
      <div className="flex items-center gap-2 rounded-md bg-primary py-1.5 pr-1.5 pl-3 text-primary-foreground">
        <code className="min-w-0 flex-1 overflow-x-auto font-mono text-sm whitespace-nowrap">{value}</code>
        <Button
          size="icon-xs"
          variant="ghost"
          onClick={() => void copy()}
          aria-label={`Copy ${label}`}
          className="text-primary-foreground hover:bg-primary-foreground/15 hover:text-primary-foreground"
        >
          {copied ? <Check aria-hidden /> : <Copy aria-hidden />}
        </Button>
      </div>
    </div>
  )
}
