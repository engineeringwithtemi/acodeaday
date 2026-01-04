// Hook for submitting code solutions
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiPost } from '../lib/api-client'
import type { SubmitCodeRequest, SubmitCodeResponse } from '../types/api'

/**
 * Submit code for full evaluation (all tests including hidden)
 * Mutation hook for POST /api/submit
 * Invalidates 'today' and 'submissions' queries on success
 */
export function useSubmitCode() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: SubmitCodeRequest) =>
      apiPost<SubmitCodeResponse>('/api/submit', request),
    onSuccess: () => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['today'] })
      queryClient.invalidateQueries({ queryKey: ['submissions'] })
    },
  })
}
