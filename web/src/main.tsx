import { QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from 'next-themes'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { AppShell } from '@/components/app-shell'
import { ErrorBoundary, ErrorPage, RootFallback, RouteError } from '@/components/error-boundary'
import { TooltipProvider } from '@/components/ui/tooltip'
import AboutPage from '@/features/about/AboutPage'
import AgentsPage from '@/features/agents/AgentsPage'
import AskPage from '@/features/ask/AskPage'
import BenchmarkPage from '@/features/benchmark/BenchmarkPage'
import DecisionListPage from '@/features/decisions/DecisionListPage'
import DecisionPage from '@/features/decisions/DecisionPage'
import HomePage from '@/features/home/HomePage'
import IngestPage from '@/features/ingest/IngestPage'
import { queryClient } from '@/lib/query'
import { installGlobalHandlers } from '@/lib/report'
import './index.css'

installGlobalHandlers()

const router = createBrowserRouter([
  {
    element: <AppShell />,
    errorElement: <RouteError />,
    children: [
      {
        errorElement: <RouteError />,
        children: [
          { path: '/', element: <HomePage /> },
          { path: '/decisions', element: <DecisionListPage /> },
          { path: '/decisions/:id', element: <DecisionPage /> },
          { path: '/ask', element: <AskPage /> },
          { path: '/ingest', element: <IngestPage /> },
          { path: '/agents', element: <AgentsPage /> },
          { path: '/benchmark', element: <BenchmarkPage /> },
          { path: '/about', element: <AboutPage /> },
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
      <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false} disableTransitionOnChange>
        <QueryClientProvider client={queryClient}>
          <TooltipProvider delayDuration={300}>
            <RouterProvider router={router} />
          </TooltipProvider>
        </QueryClientProvider>
      </ThemeProvider>
    </ErrorBoundary>
  </StrictMode>,
)
