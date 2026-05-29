import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Use import.meta.url — __dirname is not available in ESM
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    // Warn if any chunk exceeds 500 kB
    chunkSizeWarningLimit: 500,
    sourcemap: false,
    minify: 'esbuild',
  },
  server: {
    port: 5173,
  },
})
