import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  base: '/skill-map/',
  // public/data/ is produced by the pipeline export; fixtures mode serves a hand-written sample instead.
  publicDir: mode === 'fixtures' ? 'fixtures' : 'public',
  plugins: [react()],
}))
