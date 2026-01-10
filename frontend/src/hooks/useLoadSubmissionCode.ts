import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiPost } from '../lib/api-client'

interface LoadSubmissionCodeRequest {
  problem_slug: string
  code: string
  language: string
}

interface LoadSubmissionCodeResponse {
  success: boolean
  message: string
}

/**
 * Hook for loading code from a past submission into the editor.
 * Updates user_code on the server with the submission's code.
 */
export function useLoadSubmissionCode() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: LoadSubmissionCodeRequest): Promise<LoadSubmissionCodeResponse> => {
      return apiPost<LoadSubmissionCodeResponse>('/api/code/load-submission', data)
    },
    onSuccess: (_data, variables) => {
      // Invalidate the problem query to refetch with the loaded code
      queryClient.invalidateQueries({ queryKey: ['problem', variables.problem_slug] })
    },
  })
}
