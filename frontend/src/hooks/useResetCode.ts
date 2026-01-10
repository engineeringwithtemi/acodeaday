import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiPost } from '../lib/api-client'

interface ResetCodeRequest {
  problem_slug: string
  language: string
}

interface ResetCodeResponse {
  success: boolean
  message: string
}

/**
 * Hook for resetting user's code to starter code.
 * Deletes the user_code record from the server, so next fetch returns starter_code.
 */
export function useResetCode() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: ResetCodeRequest): Promise<ResetCodeResponse> => {
      return apiPost<ResetCodeResponse>('/api/code/reset', data)
    },
    onSuccess: (_data, variables) => {
      // Invalidate the problem query to refetch with starter_code
      queryClient.invalidateQueries({ queryKey: ['problem', variables.problem_slug] })
    },
  })
}
