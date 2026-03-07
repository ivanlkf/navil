import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8484',
        timeout: 120000,       // 2 min — LLM calls can be slow
        proxyTimeout: 120000,
      },
    },
  },
})
