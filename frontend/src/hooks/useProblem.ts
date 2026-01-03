// Hook for fetching individual problem details
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../lib/api-client'
import type { Problem } from '../types/api'

/**
 * Fetch a specific problem by slug
 * Query hook for GET /api/problems/:slug
 */
export function useProblem(slug: string) {
  return useQuery({
    queryKey: ['problem', slug],
    queryFn: () => apiGet<Problem>(`/api/problems/${slug}`),
    // Only fetch if slug is provided
    enabled: !!slug,
  })
}
