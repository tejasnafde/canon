import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '@/lib/api'
import { ErrorBoundary } from './error-boundary'
import { ErrorState } from './states'

afterEach(() => vi.restoreAllMocks())

let fail = true
function Flaky() {
  if (fail) throw new ApiError(503, '503 unavailable')
  return <p>Loaded</p>
}

describe('ErrorBoundary', () => {
  it('shows a friendly retry and recovers when retried', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response())
    render(
      <ErrorBoundary fallback={p => <ErrorState error={p.error} retry={p.reset} />}>
        <Flaky />
      </ErrorBoundary>,
    )
    expect(screen.getByRole('alert')).toHaveTextContent('Canon had a problem on its side')
    fail = false
    await userEvent.click(screen.getByRole('button', { name: /try again/i }))
    expect(screen.getByText('Loaded')).toBeInTheDocument()
  })
})
