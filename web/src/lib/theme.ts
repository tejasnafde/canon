import { useSyncExternalStore } from 'react'

// ponytail: index.html sets the class before first paint; this hook only flips it and remembers the choice.
export type Theme = 'light' | 'dark'
const KEY = 'theme'
const listeners = new Set<() => void>()

const current = (): Theme => (document.documentElement.classList.contains('dark') ? 'dark' : 'light')

export function setTheme(t: Theme) {
  document.documentElement.classList.toggle('dark', t === 'dark')
  try {
    localStorage.setItem(KEY, t)
  } catch {
    // private mode: the choice lasts for this page only
  }
  listeners.forEach(l => l())
}

const subscribe = (l: () => void) => {
  listeners.add(l)
  return () => listeners.delete(l)
}

export function useTheme() {
  const theme = useSyncExternalStore(subscribe, current)
  return { theme, toggle: () => setTheme(theme === 'dark' ? 'light' : 'dark') }
}
