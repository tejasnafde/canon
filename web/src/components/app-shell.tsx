import { useQuery } from '@tanstack/react-query'
import { Menu, Moon, Search, Sun } from 'lucide-react'
import { useTheme } from '@/lib/theme'
import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, ScrollRestoration } from 'react-router-dom'
import { MOCK } from '@/lib/api'
import { q } from '@/lib/query'
import { cn } from '@/lib/utils'
import { CommandMenu } from './command-menu'
import { NAV } from './nav'
import { Button } from './ui/button'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from './ui/sheet'
import { Toaster } from './ui/sonner'
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip'

const MAC = /Mac|iPhone|iPad/.test(navigator.userAgent)

export function AppShell() {
  const [cmdOpen, setCmdOpen] = useState(false)
  return (
    <>
      <a
        href="#main"
        className="sr-only z-50 rounded-md bg-primary px-4 py-2 text-primary-foreground focus:not-sr-only focus:fixed focus:top-3 focus:left-3"
      >
        Skip to content
      </a>
      <Header onSearch={() => setCmdOpen(true)} />
      <WakeBanner />
      <div id="main" tabIndex={-1} className="outline-none">
        <Outlet />
      </div>
      <Footer />
      <CommandMenu open={cmdOpen} onOpenChange={setCmdOpen} />
      <Toaster position="bottom-right" />
      <ScrollRestoration />
    </>
  )
}

function Wordmark() {
  return (
    <Link to="/" className="flex items-baseline gap-2 font-heading text-[26px] font-semibold tracking-tight" aria-label="Canon home">
      <span className="inline-block size-2.5 -translate-y-0.5 bg-signal" aria-hidden />
      Canon
    </Link>
  )
}

const navClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    'rounded-md px-3 py-1.5 text-[15px] font-medium whitespace-nowrap transition-colors duration-150',
    isActive ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-accent hover:text-foreground',
  )

function Header({ onSearch }: { onSearch: () => void }) {
  const [menu, setMenu] = useState(false)
  return (
    <header className="sticky top-0 z-40 border-b border-foreground bg-card/95 backdrop-blur supports-backdrop-filter:bg-card/85">
      <div className="mx-auto flex h-16 max-w-[1440px] items-center gap-6 px-4 md:px-8">
        <Wordmark />
        <nav aria-label="Main" className="hidden items-center gap-1 lg:flex">
          {NAV.map(({ to, label }) => (
            <NavLink key={to} to={to} end={to === '/'} className={navClass}>
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onSearch} className="text-muted-foreground" aria-label="Search, shortcut Command K">
            <Search aria-hidden />
            <span className="hidden xl:inline">Search</span>
            <kbd className="hidden rounded-sm border bg-muted px-1.5 font-mono text-xs xl:inline">{MAC ? '\u2318K' : 'Ctrl K'}</kbd>
          </Button>
          <Health />
          <ThemeToggle />
          <Sheet open={menu} onOpenChange={setMenu}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon-sm" className="lg:hidden" aria-label="Open menu">
                <Menu aria-hidden />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-72">
              <SheetHeader>
                <SheetTitle>Canon</SheetTitle>
              </SheetHeader>
              <nav aria-label="Main" className="flex flex-col gap-1 px-4">
                {NAV.map(({ to, label, Icon }) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={to === '/'}
                    className={p => cn(navClass(p), 'flex items-center gap-3 py-2.5')}
                    onClick={() => setMenu(false)}
                  >
                    <Icon className="size-4" aria-hidden /> {label}
                  </NavLink>
                ))}
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  )
}

function Health() {
  const health = useQuery(q.health())
  const state = health.isSuccess ? 'online' : health.isError ? 'offline' : 'waking'
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          onClick={() => void health.refetch()}
          aria-label={`Canon is ${state}. Check again`}
          className={cn(
            'hidden items-center gap-1.5 rounded-md px-2 py-1 hover:bg-muted font-mono text-xs tracking-wide uppercase sm:inline-flex',
            state === 'online' ? 'text-ok-ink' : state === 'offline' ? 'text-signal-ink' : 'text-warn-ink',
          )}
        >
          <span className={cn('size-2 rounded-full bg-current', state !== 'offline' && 'motion-safe:animate-pulse')} aria-hidden />
          {state}
        </button>
      </TooltipTrigger>
      <TooltipContent>
        {state === 'online'
          ? `Canon is up. Model ${health.data?.model ?? ''}${MOCK ? ' (mock data)' : ''}`
          : state === 'offline'
            ? 'Canon is not answering'
            : 'Canon is starting'}
        . Click to check again.
      </TooltipContent>
    </Tooltip>
  )
}

function ThemeToggle() {
  const { theme, toggle } = useTheme()
  const dark = theme === 'dark'
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="ghost" size="icon-sm" onClick={toggle} aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}>
          {dark ? <Sun aria-hidden /> : <Moon aria-hidden />}
        </Button>
      </TooltipTrigger>
      <TooltipContent>{dark ? 'Light theme' : 'Dark theme'}</TooltipContent>
    </Tooltip>
  )
}

/** Cloud Run scales to zero; say so instead of showing a blank page on the first request. */
function WakeBanner() {
  const health = useQuery(q.health())
  const [slow, setSlow] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setSlow(true), 1500)
    return () => clearTimeout(t)
  }, [])
  const waking = slow && health.isPending
  const offline = health.isError
  if (!waking && !offline) return null
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        'border-b motion-safe:animate-in motion-safe:fade-in-0',
        offline ? 'bg-signal-soft text-signal-ink' : 'bg-warn-soft text-warn-ink',
      )}
    >
      <div className="mx-auto flex max-w-[1440px] flex-wrap items-center gap-x-4 gap-y-1 px-4 py-2.5 text-[15px] md:px-8">
        <b className="font-medium">{offline ? 'Canon is not answering.' : 'Waking up Canon.'}</b>
        <span>
          {offline ? 'It may be restarting. Try again in a moment.' : 'It scales to zero when idle, so the first request takes a few seconds.'}
        </span>
        {offline && (
          <Button size="xs" variant="outline" className="ml-auto" onClick={() => void health.refetch()}>
            Try again
          </Button>
        )}
      </div>
    </div>
  )
}

function Footer() {
  return (
    <footer className="mt-16 border-t">
      <div className="mx-auto flex max-w-[1440px] flex-wrap items-center justify-between gap-3 px-4 py-6 text-sm text-muted-foreground md:px-8">
        <span>
          Workspace <b className="font-medium text-foreground">Northwind Labs</b>. All data is synthetic{MOCK ? ', mock mode' : ''}.
        </span>
        <span>Gemini on Vertex AI, Firestore, Cloud Run, Firebase Hosting.</span>
      </div>
    </footer>
  )
}
