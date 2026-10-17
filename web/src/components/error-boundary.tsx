import { QueryErrorResetBoundary } from '@tanstack/react-query'
import { Component, Suspense, useEffect, type ReactNode } from 'react'
import { isRouteErrorResponse, Link, useRouteError } from 'react-router-dom'
import { reportError } from '@/lib/report'
import { Button } from './ui/button'
import { ErrorState } from './states'

interface Props {
  children: ReactNode
  fallback: (p: { error: unknown; reset: () => void }) => ReactNode
  onReset?: () => void
}

/** Catches render errors below it, reports them, and offers a reset. */
export class ErrorBoundary extends Component<Props, { failed: boolean; error: unknown }> {
  state = { failed: false, error: undefined as unknown }

  static getDerivedStateFromError(error: unknown) {
    return { failed: true, error }
  }

  componentDidCatch(error: unknown) {
    reportError(error, 'boundary')
  }

  reset = () => {
    this.props.onReset?.()
    this.setState({ failed: false, error: undefined })
  }

  render() {
    return this.state.failed ? this.props.fallback({ error: this.state.error, reset: this.reset }) : this.props.children
  }
}

/** One data section: skeleton while it loads, a friendly retry if it fails. */
export function Section({ children, fallback }: { children: ReactNode; fallback: ReactNode }) {
  return (
    <QueryErrorResetBoundary>
      {({ reset }) => (
        <ErrorBoundary onReset={reset} fallback={p => <ErrorState error={p.error} retry={p.reset} />}>
          <Suspense fallback={fallback}>{children}</Suspense>
        </ErrorBoundary>
      )}
    </QueryErrorResetBoundary>
  )
}

/** Router errorElement: a 404 reads as "not on record", anything else gets a retry. */
export function RouteError() {
  const error = useRouteError()
  const notFound = isRouteErrorResponse(error) && error.status === 404
  useEffect(() => {
    if (!notFound) reportError(error, 'route')
  }, [error, notFound])
  return <ErrorPage notFound={notFound} />
}

export function ErrorPage({ notFound }: { notFound: boolean }) {
  return (
    <main className="mx-auto max-w-3xl px-6 py-20">
      <p className="label">{notFound ? 'Error 404' : 'Something broke'}</p>
      <h1 className="mt-3 text-4xl font-medium">{notFound ? 'Not on record.' : 'This page did not load.'}</h1>
      <p className="mt-4 text-muted-foreground">
        {notFound ? 'There is no page at this address.' : 'The error was reported. Try again, or go back home.'}
      </p>
      <div className="mt-8 flex gap-3">
        {!notFound && <Button onClick={() => location.reload()}>Try again</Button>}
        <Button variant="outline" asChild>
          <Link to="/">Go home</Link>
        </Button>
      </div>
    </main>
  )
}

/** Last line of defence, outside the router. */
export function RootFallback() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-20">
      <h1 className="text-4xl font-medium">Canon hit an error.</h1>
      <p className="mt-4 text-muted-foreground">The error was reported. Reload to start again.</p>
      <Button className="mt-8" onClick={() => location.reload()}>
        Reload
      </Button>
    </main>
  )
}
