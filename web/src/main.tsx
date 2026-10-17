import { QueryClientProvider } from '@tanstack/react-query'
import { StrictMode, type ComponentType } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { AppShell } from '@/components/app-shell'
import { ErrorBoundary, ErrorPage, RootFallback, RouteError } from '@/components/error-boundary'
import { TooltipProvider } from '@/components/ui/tooltip'
import { queryClient } from '@/lib/query'
import { installGlobalHandlers } from '@/lib/report'
import './index.css'

installGlobalHandlers()

// one chunk per page; the shell and the first page load together
const page = (load: () => Promise<{ default: ComponentType }>) => async () => ({ Component: (await load()).default })

const router = createBrowserRouter([
  {
    element: <AppShell />,
    errorElement: <RouteError />,
    HydrateFallback: () => null,
    children: [
      {
        errorElement: <RouteError />,
        children: [
          { path: '/', lazy: page(() => import('@/features/home/HomePage')) },
          { path: '/decisions', lazy: page(() => import('@/features/decisions/DecisionListPage')) },
          { path: '/decisions/:id', lazy: page(() => import('@/features/decisions/DecisionPage')) },
          { path: '/ask', lazy: page(() => import('@/features/ask/AskPage')) },
          { path: '/ingest', lazy: page(() => import('@/features/ingest/IngestPage')) },
          { path: '/agents', lazy: page(() => import('@/features/agents/AgentsPage')) },
          { path: '/benchmark', lazy: page(() => import('@/features/benchmark/BenchmarkPage')) },
          { path: '/about', lazy: page(() => import('@/features/about/AboutPage')) },
          { path: '*', element: <ErrorPage notFound /> },
        ],
      },
    ],
  },
])

const root = document.getElementById('root')
if (!root) throw new Error('index.html has no #root')

createRoot(root).render(
  <StrictMode>
    <ErrorBoundary fallback={() => <RootFallback />}>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider delayDuration={300}>
          <RouterProvider router={router} />
        </TooltipProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  </StrictMode>,
)
