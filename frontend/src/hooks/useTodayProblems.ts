// Hook for fetching today's problems (review + new)
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../lib/api-client'
import type { TodayResponse } from '../types/api'

/**
 * Fetch today's problems (up to 2 reviews + 1 new)
 * Query hook for GET /api/today
 */
export function useTodayProblems() {
  return useQuery({
    queryKey: ['today'],
    queryFn: () => apiGet<TodayResponse>('/api/today'),
  })
}
