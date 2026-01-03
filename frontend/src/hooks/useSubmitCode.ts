// Hook for submitting code solutions
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiPost } from '../lib/api-client'
import type { SubmitRequest, SubmissionResult } from '../types/api'

/**
 * Submit code for evaluation
 * Mutation hook for POST /api/submit
 * Invalidates 'today' query on success to refresh problem list
 */
export function useSubmitCode() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: SubmitRequest) =>
      apiPost<SubmissionResult>('/api/submit', request),
    onSuccess: () => {
      // Invalidate today's problems query to refresh the list
      queryClient.invalidateQueries({ queryKey: ['today'] })
    },
  })
}
