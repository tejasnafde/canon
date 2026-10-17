import { QueryClientProvider } from '@tanstack/react-query'
import { StrictMode, type ComponentType } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, Navigate, RouterProvider } from 'react-router-dom'
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
          { path: '/', lazy: page(() => import('@/pages/HomePage')) },
          { path: '/new-hire', lazy: page(() => import('@/pages/NewHirePage')) },
          { path: '/catch-up', lazy: page(() => import('@/pages/CatchUpPage')) },
          { path: '/agent', lazy: page(() => import('@/pages/AgentPage')) },
          { path: '/paste', lazy: page(() => import('@/pages/PastePage')) },
          { path: '/ask', lazy: page(() => import('@/pages/AskPage')) },
          { path: '/decisions', lazy: page(() => import('@/pages/DecisionListPage')) },
          { path: '/decisions/:id', lazy: page(() => import('@/pages/DecisionPage')) },
          { path: '/org', lazy: page(() => import('@/pages/OrgPage')) },
          { path: '/org/:id', lazy: page(() => import('@/pages/PersonPage')) },
          { path: '/people', element: <Navigate to="/org" replace /> },
          { path: '/benchmark', lazy: page(() => import('@/pages/BenchmarkPage')) },
          // old addresses from the first build
          { path: '/agents', element: <Navigate to="/agent" replace /> },
          { path: '/ingest', element: <Navigate to="/paste" replace /> },
          { path: '/about', element: <Navigate to="/" replace /> },
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
