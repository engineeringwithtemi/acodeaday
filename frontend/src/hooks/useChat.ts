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
      // Invalidate this specific session
      queryClient.invalidateQueries({ queryKey: ['chat', 'session', data.id] })
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
    onSuccess: () => {
      // Invalidate all sessions queries
      queryClient.invalidateQueries({ queryKey: ['chat', 'sessions'] })
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

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const queryClient = useQueryClient()

  const connect = useCallback(async () => {
    if (!sessionId) return

    try {
      const token = await getAccessToken()
      if (!token) {
        setError('Not authenticated')
        return
      }

      // Close existing connection
      if (wsRef.current) {
        wsRef.current.close()
      }

      const ws = new WebSocket(`${WS_BASE_URL}/api/chat/ws/${sessionId}?token=${token}`)
      wsRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
        setError(null)
        reconnectAttemptsRef.current = 0
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
          queryClient.invalidateQueries({ queryKey: ['chat', 'session', sessionId] })
        } else if (response.type === 'error') {
          setError(response.error || 'Unknown error')
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

        // Auto-reconnect with exponential backoff (unless code 4001 = unauthorized)
        if (event.code !== 4001 && reconnectAttemptsRef.current < 5) {
          const delay = Math.min(3000 * Math.pow(2, reconnectAttemptsRef.current), 30000)
          reconnectAttemptsRef.current += 1

          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, delay)
        } else if (event.code === 4001) {
          setError('Unauthorized - please refresh the page')
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Connection failed')
    }
  }, [sessionId, queryClient])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setIsConnected(false)
  }, [])

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

      wsRef.current.send(JSON.stringify(message))
      setPendingMessage(content)
      setIsStreaming(true)
      setStreamingContent('')
      setError(null)
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

  // Connect on mount and when sessionId changes
  useEffect(() => {
    if (sessionId) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [sessionId, connect, disconnect])

  return {
    isConnected,
    isStreaming,
    streamingContent,
    pendingMessage,
    error,
    sendMessage,
    cancelStream,
    reconnect: connect,
  }
}
