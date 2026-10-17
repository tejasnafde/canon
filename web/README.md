# Canon web

Vite + React 19 + TypeScript (strict), Tailwind CSS v4 and shadcn/ui (radix, `components.json`).
TanStack Query for all data, zod at the API boundary, react-router v7 data routes.

```sh
npm install
npm run dev        # proxies /api, /mcp, /a2a, /health to http://127.0.0.1:8080
npm run live       # same, proxied to https://canon.tn07.dev (or set VITE_API_TARGET)
npm run mock       # VITE_MOCK=1: canned data, no backend needed
npm run typecheck && npm run lint && npm test -- --run && npm run build
/tmp/pwvenv/bin/python scripts/shots.py [base_url]   # every route at 1280x800 and 1920x1080 into shots/
```

Layout:

- `src/lib/` - `schemas.ts` (zod mirror of `backend/canon/models.py`), `api.ts` (typed client), `query.ts`
  (QueryClient, query options, retry policy), `mcp.ts` (MCP client for the playground), `report.ts`
  (browser errors to `POST /api/client-error`, sampled), `theme.ts`, `mock.ts`.
- `src/lib/record.ts` - plain-language views of the record: persona labels, "away for" dates, source lines,
  which alerts break which decision, eval note figures.
- `src/components/` - app shell, error boundaries, shared states; `ui/` is shadcn restyled to the v2 language.
- `src/pages/` - one file per route (loaded as its own chunk): `/`, `/new-hire`, `/catch-up`, `/agent`, `/paste`,
  `/ask`, `/decisions`, `/decisions/:id`, `/benchmark`. The look follows `mocks/v2/` (styles in `src/index.css`).
- `src/samples/` - sample questions, live-paste sources and playground examples from `data/samples/`.

Every request sends `X-Canon-Workspace: v-<uuid>` (kept in localStorage). "Try it yourself" on /agent calls `check_intent` over the real MCP endpoint (`/mcp`) as actor `playground`.
Press Ctrl K (Cmd K on a Mac) anywhere to jump to a page or decision, or to ask a question.
