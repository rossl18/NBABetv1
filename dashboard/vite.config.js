import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  // Use /NBABetv1/ for production builds (GitHub Pages), / for local dev
  base: mode === 'production' ? '/NBABetv1/' : '/',
  build: {
    outDir: 'dist'
  },
  server: {
    port: 5173,
    open: false
  }
}))
