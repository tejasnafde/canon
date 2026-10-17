import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, ScrollRestoration } from 'react-router-dom'
import { MOCK } from '@/lib/api'
import { q } from '@/lib/query'
import { CommandMenu } from './command-menu'
import { NAV } from './nav'
import { Toaster } from './ui/sonner'

const MAC = /Mac|iPhone|iPad/.test(navigator.userAgent)

export function AppShell() {
  const [cmdOpen, setCmdOpen] = useState(false)
  return (
    <>
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:bg-[var(--paper)] focus:p-3">
        Skip to content
      </a>
      <header className="bar">
        <div className="wrap">
          <Link to="/" className="mark" aria-label="Canon, home">
            <img src="/canon-symbol.svg" alt="" width={20} height={26} />
            Canon
          </Link>
          <nav className="menu" aria-label="Main">
            {NAV.map(n => (
              <NavLink key={n.to} to={n.to} end={n.to === '/'} className={'far' in n ? 'far' : undefined}>
                {n.label}
              </NavLink>
            ))}
            <button type="button" className="kbd far" onClick={() => setCmdOpen(true)} aria-label="Search, shortcut Command K">
              {MAC ? '⌘K' : 'Ctrl K'}
            </button>
          </nav>
        </div>
      </header>
      <Wake />
      <div id="main" tabIndex={-1} className="outline-none" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <Outlet />
      </div>
      <footer className="foot">
        <div className="wrap">
          <span>Canon is the shared memory of a company. Built for the Google Cloud AI Builder Cup 2026.</span>
          <span>Northwind Labs is a made-up company. Every name, customer and quote is invented{MOCK ? '. Mock data' : ''}.</span>
        </div>
      </footer>
      <CommandMenu open={cmdOpen} onOpenChange={setCmdOpen} />
      <Toaster position="bottom-right" />
      <ScrollRestoration />
    </>
  )
}

/** Cloud Run scales to zero; say so instead of showing a blank page on the first request. */
function Wake() {
  const health = useQuery(q.health())
  const [slow, setSlow] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setSlow(true), 1500)
    return () => clearTimeout(t)
  }, [])
  const waking = slow && health.isPending
  if (!waking && !health.isError) return null
  return (
    <div className="wrap wake" role="status" aria-live="polite">
      {health.isError ? (
        <>
          <b>Canon is not answering.</b> It may be restarting.{' '}
          <button type="button" className="kbd" style={{ textDecoration: 'underline' }} onClick={() => void health.refetch()}>
            Try again
          </button>
        </>
      ) : (
        <>
          <b>Waking up Canon.</b> It sleeps when nobody is using it, so the first answer takes a few seconds.
        </>
      )}
    </div>
  )
}
