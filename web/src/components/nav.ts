export const NAV = [
  { to: '/', label: 'Home' },
  { to: '/ask', label: 'Ask why' },
  { to: '/decisions', label: 'Decisions' },
  { to: '/org', label: 'People' },
  { to: '/agent', label: 'For agents' },
  { to: '/benchmark', label: 'How well does it work?', far: true },
] as const

/** Every route, for the command palette. */
export const PAGES = [
  ...NAV,
  { to: '/new-hire', label: 'I am new here' },
  { to: '/catch-up', label: 'What changed while I was away?' },
  { to: '/paste', label: 'Paste a new message' },
] as const
