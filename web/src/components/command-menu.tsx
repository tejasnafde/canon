import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { q } from '@/lib/query'
import asks from '@/samples/asks.json'
import { PAGES } from './nav'
import { Command, CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from './ui/command'

const short = (s: string, n = 70) => (s.length > n ? s.slice(0, n - 1).trimEnd() + '...' : s)

/** Cmd+K / Ctrl+K: jump to a page or decision, or ask a question. */
export function CommandMenu({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const decisions = useQuery({ ...q.decisions(), enabled: open })

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key.toLowerCase() === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        onOpenChange(!open)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onOpenChange])

  const go = (to: string) => {
    onOpenChange(false)
    setSearch('')
    void navigate(to)
  }

  return (
    <CommandDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Jump to"
      description="Search pages and decisions, or ask Canon"
      className="sm:max-w-xl"
    >
      <Command>
        <CommandInput placeholder="Search, or ask a question" value={search} onValueChange={setSearch} />
        <CommandList className="max-h-96 p-2">
          <CommandEmpty>Nothing matches. Choose "Ask Canon" to ask instead.</CommandEmpty>
          {search.trim() && (
            <CommandGroup forceMount>
              <CommandItem forceMount value={`ask ${search}`} onSelect={() => go(`/ask?q=${encodeURIComponent(search.trim())}`)}>
                Ask Canon: {short(search.trim(), 60)}
              </CommandItem>
            </CommandGroup>
          )}
          <CommandGroup heading="Pages">
            {PAGES.map(({ to, label }) => (
              <CommandItem key={to} value={`page ${label}`} onSelect={() => go(to)}>
                {label}
              </CommandItem>
            ))}
          </CommandGroup>
          <CommandGroup heading="Questions">
            {asks.map(a => (
              <CommandItem key={a.question} value={`question ${a.question}`} onSelect={() => go(`/ask?q=${encodeURIComponent(a.question)}`)}>
                {a.question}
              </CommandItem>
            ))}
          </CommandGroup>
          {decisions.data && decisions.data.length > 0 && (
            <CommandGroup heading="Decisions">
              {decisions.data.map(d => (
                <CommandItem key={d.id} value={`decision ${d.statement} ${d.topic} ${d.owner}`} onSelect={() => go(`/decisions/${d.id}`)}>
                  <span className="truncate">{d.statement}</span>
                </CommandItem>
              ))}
            </CommandGroup>
          )}
        </CommandList>
      </Command>
    </CommandDialog>
  )
}
