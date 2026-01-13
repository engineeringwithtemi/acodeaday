// Hook for chat functionality with WebSocket support
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useRef, useState } from 'react'
import { apiGet, apiPost, apiPatch, apiDelete } from '../lib/api-client'
import { getAccessToken } from '../lib/api-client'
import type {
  ChatSession,
  ChatSessionWithMessages,
  CreateSessionRequest,
  UpdateSessionRequest,
  ModelInfo,
  ChatWSMessage,
  ChatWSResponse,
} from '../types/api'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const WS_BASE_URL = API_BASE_URL.replace('http://', 'ws://').replace('https://', 'wss://')

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
    queryFn: () => apiGet<ChatSession[]>(`/api/chat/sessions/${problemSlug}`),
    enabled: !!problemSlug,
  })
}

/**
 * Get a specific session with messages
 */
export function useSession(sessionId: string | null) {
  return useQuery({
    queryKey: ['chat', 'session', sessionId],
    queryFn: () => apiGet<ChatSessionWithMessages>(`/api/chat/session/${sessionId}`),
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
      apiPost<ChatSession>('/api/chat/sessions', request),
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
      apiPatch<ChatSession>(`/api/chat/session/${sessionId}`, request),
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
 * WebSocket chat hook for streaming responses
 */
export function useWebSocketChat(sessionId: string | null) {
  const [isConnected, setIsConnected] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [pendingMessage, setPendingMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lastFailedMessage, setLastFailedMessage] = useState<{
    content: string
    code?: string
    testResults?: any
  } | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const isLLMErrorRef = useRef(false) // Track if error is from LLM (not connection)
  const lastSentMessageRef = useRef<{ content: string; code?: string; testResults?: any } | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const sessionIdRef = useRef(sessionId)
  const intentionalCloseRef = useRef(false)
  const queryClient = useQueryClient()

  // Keep sessionId ref in sync
  useEffect(() => {
    sessionIdRef.current = sessionId
  }, [sessionId])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (wsRef.current) {
      intentionalCloseRef.current = true
      wsRef.current.close()
      wsRef.current = null
    }
    setIsConnected(false)
  }, [])

  const connect = useCallback(async () => {
    const currentSessionId = sessionIdRef.current
    if (!currentSessionId) return

    try {
      const token = await getAccessToken()
      if (!token) {
        setError('Not authenticated')
        return
      }

      // Close existing connection (mark as intentional to prevent auto-reconnect)
      if (wsRef.current) {
        intentionalCloseRef.current = true
        wsRef.current.close()
        wsRef.current = null
      }

      const ws = new WebSocket(`${WS_BASE_URL}/api/chat/ws/${currentSessionId}?token=${token}`)
      wsRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
        // Only clear connection errors, not LLM errors (user may want to retry with different model)
        if (!isLLMErrorRef.current) {
          setError(null)
        }
        reconnectAttemptsRef.current = 0
        intentionalCloseRef.current = false
      }

      ws.onmessage = (event) => {
        const response: ChatWSResponse = JSON.parse(event.data)

        if (response.type === 'chunk') {
          setStreamingContent((prev) => prev + (response.content || ''))
        } else if (response.type === 'done') {
          setIsStreaming(false)
          setStreamingContent('')
          setPendingMessage(null)
          // Invalidate session to refresh messages
          queryClient.invalidateQueries({ queryKey: ['chat', 'session', currentSessionId] })
        } else if (response.type === 'error') {
          setError(response.error || 'Unknown error')
          isLLMErrorRef.current = true // Mark as LLM error so it persists across reconnect
          // Save the failed message for retry
          if (lastSentMessageRef.current) {
            setLastFailedMessage(lastSentMessageRef.current)
          }
          setIsStreaming(false)
          setStreamingContent('')
          setPendingMessage(null)
        }
      }

      ws.onerror = (event) => {
        console.error('WebSocket error:', event)
        setError('Connection error')
      }

      ws.onclose = (event) => {
        setIsConnected(false)
        setIsStreaming(false)

        // Only auto-reconnect if not intentional close, sessionId hasn't changed, and not unauthorized
        if (
          !intentionalCloseRef.current &&
          event.code !== 4001 &&
          reconnectAttemptsRef.current < 5 &&
          sessionIdRef.current === currentSessionId
        ) {
          const delay = Math.min(3000 * Math.pow(2, reconnectAttemptsRef.current), 30000)
          reconnectAttemptsRef.current += 1

          reconnectTimeoutRef.current = setTimeout(() => {
            // Double-check sessionId hasn't changed before reconnecting
            if (sessionIdRef.current === currentSessionId) {
              connect()
            }
          }, delay)
        } else if (event.code === 4001) {
          setError('Unauthorized - please refresh the page')
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed')
    }
  }, [queryClient])

  const sendMessage = useCallback(
    (content: string, currentCode?: string, testResults?: any) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        setError('Not connected')
        return
      }

      const message: ChatWSMessage = {
        type: 'message',
        content,
        current_code: currentCode,
        test_results: testResults,
      }

      // Store message for potential retry
      lastSentMessageRef.current = { content, code: currentCode, testResults }

      wsRef.current.send(JSON.stringify(message))
      setPendingMessage(content)
      setIsStreaming(true)
      setStreamingContent('')
      // Clear previous error and failed message state
      setError(null)
      isLLMErrorRef.current = false
      setLastFailedMessage(null)
    },
    []
  )

  const cancelStream = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return

    const message: ChatWSMessage = {
      type: 'cancel',
    }

    wsRef.current.send(JSON.stringify(message))
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
    isLLMErrorRef.current = false
    setLastFailedMessage(null)
  }, [])

  // Connect when sessionId changes
  useEffect(() => {
    if (sessionId) {
      // Reset reconnect attempts when sessionId changes
      reconnectAttemptsRef.current = 0
      connect()
    } else {
      disconnect()
    }

    return () => {
      disconnect()
    }
  }, [sessionId]) // Only depend on sessionId, not on connect/disconnect

  return {
    isConnected,
    isStreaming,
    streamingContent,
    pendingMessage,
    error,
    lastFailedMessage,
    sendMessage,
    cancelStream,
    retry,
    clearError,
    reconnect: connect,
  }
}
