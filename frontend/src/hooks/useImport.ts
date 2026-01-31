import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiGet, apiPost } from '@/lib/api-client'
import type {
  ImportRequest,
  ImportJobResponse,
  ImportJobDetailResponse,
  ImportJobSummaryResponse,
} from '@/types/api'

/**
 * Start a new import job. Returns the created job on success.
 * Invalidates import history on success.
 */
export function useStartImport() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (request: ImportRequest) =>
      apiPost<ImportJobResponse>('/api/imports/', request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['imports'] })
    },
  })
}

/**
 * Poll an import job's detail (with linked problems) while it's active.
 * Polls every 2 seconds while status is queued/processing, stops when terminal.
 */
export function useImportStatus(importId: string | null) {
  return useQuery({
    queryKey: ['imports', importId],
    queryFn: () =>
      apiGet<ImportJobDetailResponse>(`/api/imports/${importId}`),
    enabled: !!importId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'queued' || status === 'processing') {
        return 2000
      }
      return false
    },
  })
}

/**
 * List all import jobs for the current user (most recent first).
 */
export function useImportHistory() {
  return useQuery({
    queryKey: ['imports'],
    queryFn: () =>
      apiGet<ImportJobSummaryResponse[]>('/api/imports/'),
  })
}

/**
 * Cancel an in-progress import job.
 */
export function useCancelImport() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (importId: string) =>
      apiPost<{ status: string; message: string }>(`/api/imports/${importId}/cancel`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['imports'] })
    },
  })
}
