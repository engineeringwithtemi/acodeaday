// Hook for fetching problems grouped by pattern
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../lib/api-client'
import type { PatternsResponse } from '../types/api'

/**
 * Fetch all problems grouped by their primary pattern
 * Query hook for GET /api/patterns
 */
export function usePatterns() {
  return useQuery({
    queryKey: ['patterns'],
    queryFn: () => apiGet<PatternsResponse>('/api/patterns'),
  })
}
