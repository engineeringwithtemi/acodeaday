// Hook for fetching supported programming languages
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '../lib/api-client'

interface LanguagesResponse {
  languages: string[]
}

/**
 * Fetch supported programming languages for code execution
 * Query hook for GET /api/problems/languages/supported
 */
export function useLanguages() {
  return useQuery({
    queryKey: ['languages'],
    queryFn: () => apiGet<LanguagesResponse>('/api/problems/languages/supported'),
    // Languages don't change often, cache for longer
    staleTime: 1000 * 60 * 60, // 1 hour
  })
}
