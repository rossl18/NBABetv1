import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/NBABetv1/',  // Update this to match your GitHub repo name
  build: {
    outDir: 'dist'
  }
})
