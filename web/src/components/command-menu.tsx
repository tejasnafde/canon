import { useQuery } from '@tanstack/react-query'
import { FileText, MessageCircleQuestion, Moon, Sun } from 'lucide-react'
import { useTheme } from '@/lib/theme'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { short } from '@/lib/format'
import { q } from '@/lib/query'
import asks from '@/samples/asks.json'
import { NAV } from './nav'
import { Command, CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandSeparator } from './ui/command'

/** Cmd+K / Ctrl+K: jump to a page or decision, or ask a question. */
export function CommandMenu({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const { theme, toggle } = useTheme()
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
        <CommandInput placeholder="Search decisions, pages, or type a question" value={search} onValueChange={setSearch} />
        <CommandList>
          <CommandEmpty>Nothing matches. Press Enter on "Ask Canon" to ask instead.</CommandEmpty>
          {search.trim() && (
            <CommandGroup heading="Ask" forceMount>
              <CommandItem forceMount value={`ask ${search}`} onSelect={() => go(`/ask?q=${encodeURIComponent(search.trim())}`)}>
                <MessageCircleQuestion aria-hidden /> Ask Canon: {short(search.trim(), 60)}
              </CommandItem>
            </CommandGroup>
          )}
          <CommandGroup heading="Pages">
            {NAV.map(({ to, label, Icon }) => (
              <CommandItem key={to} value={`page ${label}`} onSelect={() => go(to)}>
                <Icon aria-hidden /> {label}
              </CommandItem>
            ))}
          </CommandGroup>
          <CommandGroup heading="Sample questions">
            {asks.map(a => (
              <CommandItem key={a.question} value={`question ${a.question}`} onSelect={() => go(`/ask?q=${encodeURIComponent(a.question)}`)}>
                <MessageCircleQuestion aria-hidden /> {a.question}
              </CommandItem>
            ))}
          </CommandGroup>
          {decisions.data && decisions.data.length > 0 && (
            <CommandGroup heading="Decisions">
              {decisions.data.map(d => (
                <CommandItem key={d.id} value={`decision ${d.statement} ${d.topic} ${d.owner}`} onSelect={() => go(`/decisions/${d.id}`)}>
                  <FileText aria-hidden /> <span className="truncate">{d.statement}</span>
                </CommandItem>
              ))}
            </CommandGroup>
          )}
          <CommandSeparator />
          <CommandGroup heading="Settings">
            <CommandItem
              value="theme toggle dark light"
              onSelect={() => {
                toggle()
                onOpenChange(false)
              }}
            >
              {theme === 'dark' ? <Sun aria-hidden /> : <Moon aria-hidden />}
              Switch to {theme === 'dark' ? 'light' : 'dark'} theme
            </CommandItem>
          </CommandGroup>
        </CommandList>
      </Command>
    </CommandDialog>
  )
}
