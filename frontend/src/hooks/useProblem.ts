// Hook for fetching individual problem details
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../lib/api-client'
import type { ProblemDetailSchema } from '../types/api'

/**
 * Fetch a specific problem by slug
 * Query hook for GET /api/problems/:slug
 */
export function useProblem(slug: string) {
  return useQuery({
    queryKey: ['problem', slug],
    queryFn: () => apiGet<ProblemDetailSchema>(`/api/problems/${slug}`),
    // Only fetch if slug is provided
    enabled: !!slug,
    // Always refetch on mount to get fresh is_due status
    // This ensures editor isn't cleared when user returns after rating
    staleTime: 0,
    refetchOnMount: true,
  })
}
