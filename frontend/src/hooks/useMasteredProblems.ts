// Hook for fetching mastered problems
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../lib/api-client'
import type { MasteredProblemsResponse } from '../types/api'

/**
 * Fetch all mastered problems
 * Query hook for GET /api/mastered
 */
export function useMasteredProblems() {
  return useQuery({
    queryKey: ['mastered'],
    queryFn: () => apiGet<MasteredProblemsResponse>('/api/mastered'),
  })
}
