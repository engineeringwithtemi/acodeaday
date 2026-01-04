import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../lib/api-client'
import type { SubmissionSchema } from '../types/api'

/**
 * Fetch submission history for a specific problem
 * Query hook for GET /api/submissions/{problemId}
 */
export function useSubmissions(problemId: string) {
  return useQuery({
    queryKey: ['submissions', problemId],
    queryFn: () => apiGet<SubmissionSchema[]>(`/api/submissions/${problemId}`),
    enabled: !!problemId,
  })
}
