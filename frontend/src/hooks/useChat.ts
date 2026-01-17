// Hook for chat functionality with streaming POST
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useRef, useState } from 'react'
import { apiGet, apiPost, apiPatch, apiDelete } from '../lib/api-client'
import { getAccessToken } from '../lib/api-client'
import type {
  ChatSessionSchema,
  ChatSessionWithMessagesSchema,
  CreateSessionRequest,
  UpdateSessionRequest,
  ModelInfo,
} from '../types/api'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Get list of available LLM models
 */
export function useModels() {
  return useQuery({
    queryKey: ['chat', 'models'],
    queryFn: () => apiGet<ModelInfo[]>('/api/chat/models'),
  })
}

/**
 * Get list of chat sessions for a problem
 */
export function useSessions(problemSlug: string) {
  return useQuery({
    queryKey: ['chat', 'sessions', problemSlug],
    queryFn: () => apiGet<ChatSessionSchema[]>(`/api/chat/sessions/${problemSlug}`),
    enabled: !!problemSlug,
  })
}

/**
 * Get a specific session with messages
 */
export function useSession(sessionId: string | null) {
  return useQuery({
    queryKey: ['chat', 'session', sessionId],
    queryFn: () => apiGet<ChatSessionWithMessagesSchema>(`/api/chat/session/${sessionId}`),
    enabled: !!sessionId,
  })
}

/**
 * Create a new chat session
 */
export function useCreateSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: CreateSessionRequest) =>
      apiPost<ChatSessionSchema>('/api/chat/sessions', request),
    onSuccess: (_, variables) => {
      // Invalidate sessions list for this problem
      queryClient.invalidateQueries({ queryKey: ['chat', 'sessions', variables.problem_slug] })
    },
  })
}

/**
 * Update a chat session
 */
export function useUpdateSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sessionId, request }: { sessionId: string; request: UpdateSessionRequest }) =>
      apiPatch<ChatSessionSchema>(`/api/chat/session/${sessionId}`, request),
    onSuccess: (data) => {
      // Invalidate this specific session and sessions list (for title updates in dropdown)
      queryClient.invalidateQueries({ queryKey: ['chat', 'session', data.id] })
      queryClient.invalidateQueries({ queryKey: ['chat', 'sessions'] })
    },
  })
}

/**
 * Delete a chat session
 */
export function useDeleteSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (sessionId: string) => apiDelete(`/api/chat/session/${sessionId}`),
    onSuccess: (_, sessionId) => {
      // Invalidate all sessions queries
      queryClient.invalidateQueries({ queryKey: ['chat', 'sessions'] })
      // Remove the deleted session from cache
      queryClient.removeQueries({ queryKey: ['chat', 'session', sessionId] })
    },
  })
}

/**
 * Streaming POST chat hook for streaming responses
 *
 * Uses a single HTTP request that both saves the user message and streams the AI response.
 * No persistent connection, no race conditions.
 */
export function useStreamChat(sessionId: string | null) {
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [pendingMessage, setPendingMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lastFailedMessage, setLastFailedMessage] = useState<{
    content: string
    code?: string
    testResults?: any
  } | null>(null)

  const abortControllerRef = useRef<AbortController | null>(null)
  const queryClient = useQueryClient()

  const sendMessage = useCallback(
    async (content: string, currentCode?: string, testResults?: any) => {
      if (!sessionId || isStreaming) return

      // Cancel any existing stream
      abortControllerRef.current?.abort()

      setIsStreaming(true)
      setStreamingContent('')
      setPendingMessage(content)
      setError(null)
      setLastFailedMessage(null)

      const abortController = new AbortController()
      abortControllerRef.current = abortController

      try {
        const token = await getAccessToken()

        const response = await fetch(`${API_BASE_URL}/api/chat/session/${sessionId}/message`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            content,
            current_code: currentCode,
            test_results: testResults,
          }),
          signal: abortController.signal,
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const reader = response.body?.getReader()
        if (!reader) throw new Error('No response body')

        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })

          // Parse SSE format: "data: {...}\n\n"
          const lines = buffer.split('\n\n')
          buffer = lines.pop() || '' // Keep incomplete line in buffer

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const jsonStr = line.slice(6)
              try {
                const event = JSON.parse(jsonStr)

                if (event.type === 'chunk') {
                  setStreamingContent((prev) => prev + (event.content || ''))
                } else if (event.type === 'done') {
                  // Success - refresh messages
                  queryClient.invalidateQueries({ queryKey: ['chat', 'session', sessionId] })
                } else if (event.type === 'error') {
                  setError(event.error || 'Unknown error')
                  setLastFailedMessage({ content, code: currentCode, testResults })
                }
              } catch (e) {
                console.error('Failed to parse SSE event:', e)
              }
            }
          }
        }
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') {
          // Cancelled by user - not an error
          console.log('Stream cancelled')
        } else {
          const errorMessage = err instanceof Error ? err.message : 'Stream failed'
          setError(errorMessage)
          setLastFailedMessage({ content, code: currentCode, testResults })
        }
      } finally {
        setIsStreaming(false)
        setStreamingContent('')
        setPendingMessage(null)
      }
    },
    [sessionId, isStreaming, queryClient]
  )

  const cancelStream = useCallback(() => {
    abortControllerRef.current?.abort()
    setIsStreaming(false)
    setStreamingContent('')
    setPendingMessage(null)
  }, [])

  const retry = useCallback(() => {
    if (!lastFailedMessage) return
    sendMessage(lastFailedMessage.content, lastFailedMessage.code, lastFailedMessage.testResults)
  }, [lastFailedMessage, sendMessage])

  const clearError = useCallback(() => {
    setError(null)
    setLastFailedMessage(null)
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort()
    }
  }, [])

  return {
    isConnected: true, // No persistent connection needed - always "connected"
    isStreaming,
    streamingContent,
    pendingMessage,
    error,
    lastFailedMessage,
    sendMessage,
    cancelStream,
    retry,
    clearError,
    reconnect: () => {}, // No-op for API compatibility
  }
}
