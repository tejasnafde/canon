import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const api = 'http://127.0.0.1:8080'

export default defineConfig({
  plugins: [react()],
  server: { proxy: { '/api': api, '/mcp': api, '/a2a': api, '/healthz': api } },
})
