import { useMutation } from '@tanstack/react-query'
import { apiPost } from '../lib/api-client'

interface SaveCodeRequest {
  problem_slug: string
  language: string
  code: string
}

interface SaveCodeResponse {
  success: boolean
  message: string
}

/**
 * Hook for saving user's code to the server.
 * Used for auto-saving code as the user types (debounced).
 */
export function useSaveCode() {
  return useMutation({
    mutationFn: async (data: SaveCodeRequest): Promise<SaveCodeResponse> => {
      return apiPost<SaveCodeResponse>('/api/code/save', data)
    },
  })
}
