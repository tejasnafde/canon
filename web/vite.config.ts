/// <reference types="vitest/config" />
import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// VITE_API_TARGET=https://canon.tn07.dev npm run dev  -> runs the UI against the live API
const api = { target: process.env.VITE_API_TARGET ?? 'http://127.0.0.1:8080', changeOrigin: true }

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { '@': path.resolve(import.meta.dirname, 'src') } },
  server: { proxy: { '/api': api, '/mcp': api, '/a2a': api, '/health': api } },
  test: { environment: 'jsdom', globals: true, setupFiles: ['src/test/setup.ts'] },
})
