# Canon web

Vite + React + TypeScript. Styles are `src/canon.css` (one global sheet, from `mocks/`).

```sh
npm install
npm run dev     # proxies /api, /mcp, /a2a, /healthz to http://127.0.0.1:8080
npm run mock    # VITE_MOCK=1: canned data, no backend needed
npm run build   # web/dist, served by Firebase Hosting with SPA fallback
/tmp/pwvenv/bin/python scripts/shots.py [base_url] [suffix]   # 1280x800 screenshots into shots/
```

Every request sends `X-Canon-Workspace: v-<uuid>` (kept in localStorage). The Agents
playground calls the six tools over the real MCP endpoint (`/mcp`, streamable HTTP) as actor `playground`.
