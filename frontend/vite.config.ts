import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Avoid CORS in local dev: frontend stays on http://localhost:<vitePort>
      // while Vite proxies API calls to the Docker gateway (https://localhost).
      '/auth': {
        target: 'https://localhost',
        changeOrigin: true,
        secure: false,
      },
      '/api': {
        target: 'https://localhost',
        changeOrigin: true,
        secure: false,
      },
      '/health': {
        target: 'https://localhost',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'wss://localhost',
        ws: true,
        changeOrigin: true,
        secure: false,
      },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    globals: false,
  },
})
