import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // __dirname is not available in ESM; use import.meta.url instead
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    // Warn if any chunk exceeds 500 kB; helps catch accidental large imports
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        // Use function form — object literal causes TS2769 with this Rollup type version
        manualChunks(id) {
          if (id.includes('react') || id.includes('react-dom') || id.includes('react-router')) {
            return 'react-vendor';
          }
          if (id.includes('@tanstack')) {
            return 'query-vendor';
          }
          if (id.includes('axios')) {
            return 'axios-vendor';
          }
        },
      },
    },
    sourcemap: false,   // no source maps in prod (keeps bundle smaller)
    minify: 'esbuild',  // fast & small
  },
  server: {
    port: 5173,
  },
})
