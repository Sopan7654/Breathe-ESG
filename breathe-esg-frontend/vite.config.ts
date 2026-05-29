import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    // Warn if any chunk exceeds 500 kB; helps catch accidental large imports
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        // Split vendor code into a separate chunk so it can be cached independently
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'query-vendor': ['@tanstack/react-query'],
          'axios-vendor': ['axios'],
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
