import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App.tsx';
import './index.css';

/**
 * React Query configuration:
 * - staleTime: 30s — data is considered fresh for 30 seconds. No refetch on tab
 *   focus / remount within this window. Eliminates the "every tab switch refetches" problem.
 * - gcTime: 5min — cached data stays in memory for 5 minutes after component unmounts.
 * - retry: 1 — retry failed requests once before showing an error.
 * - refetchOnWindowFocus: false — don't automatically refetch when the window regains focus.
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30 * 1000,        // 30 seconds
      gcTime: 5 * 60 * 1000,       // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
);
