import { useMutation } from '@tanstack/react-query'
import { apiPost } from '../lib/api-client'
import type { RunCodeRequest, RunCodeResponse } from '../types/api'

export function useRunCode() {
  return useMutation({
    mutationFn: (request: RunCodeRequest) =>
      apiPost<RunCodeResponse>('/api/run', request),
  })
}
