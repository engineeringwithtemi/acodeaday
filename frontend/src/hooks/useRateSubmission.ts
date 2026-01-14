// Hook for rating submission difficulty (Anki-style spaced repetition)
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiPost } from '../lib/api-client'
import type { RatingRequest, RatingResponse } from '../types/api'

/**
 * Rate the difficulty of a successfully solved problem
 * Mutation hook for POST /api/rate-submission
 * Implements Anki SM-2 spaced repetition algorithm
 */
export function useRateSubmission() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: RatingRequest) =>
      apiPost<RatingResponse>('/api/rate-submission', request),
    onSuccess: () => {
      // Invalidate queries to refresh progress data
      queryClient.invalidateQueries({ queryKey: ['today'] })
      queryClient.invalidateQueries({ queryKey: ['progress'] })
      queryClient.invalidateQueries({ queryKey: ['mastered'] })
    },
  })
}
