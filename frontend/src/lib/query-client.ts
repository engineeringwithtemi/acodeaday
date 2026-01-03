// TanStack Query Client Configuration
import { QueryClient } from '@tanstack/react-query'

/**
 * Create and configure the TanStack Query client
 * Used for server state management and caching
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Data is considered fresh for 5 minutes
      staleTime: 5 * 60 * 1000, // 5 minutes

      // Only retry failed requests once
      retry: 1,

      // Don't refetch on window focus to avoid unnecessary requests
      refetchOnWindowFocus: false,

      // Refetch on mount only if data is stale
      refetchOnMount: true,

      // Keep unused/inactive cache data for 10 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (previously cacheTime)
    },
    mutations: {
      // Retry mutations once on failure
      retry: 1,
    },
  },
})
