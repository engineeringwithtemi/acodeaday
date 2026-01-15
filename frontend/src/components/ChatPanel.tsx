import { useState, useRef, useEffect, useCallback } from 'react'
import {
  MessageSquare,
  Send,
  Loader2,
  Lightbulb,
  Zap,
  Plus,
  ChevronDown,
  X,
  AlertCircle,
  Trash2,
  Copy,
  Check,
  Pencil,
  RefreshCw,
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/cjs/styles/prism'
import {
  useModels,
  useSessions,
  useSession,
  useCreateSession,
  useUpdateSession,
  useDeleteSession,
  useStreamChat,
} from '../hooks'
import type { ChatMode, ChatMessage, ChatSession } from '../types/api'

interface ChatPanelProps {
  problemSlug: string
  currentCode?: string
  testResults?: any
  onClose: () => void
  initialMessage?: string | null
  initialSessionTitle?: string | null
  onInitialMessageSent?: () => void
}

const LAST_MODEL_KEY = 'acodeaday_last_model'

function getLastModel(): string | null {
  try {
    return localStorage.getItem(LAST_MODEL_KEY)
  } catch {
    return null
  }
}

function saveLastModel(model: string): void {
  try {
    localStorage.setItem(LAST_MODEL_KEY, model)
  } catch {
    // Ignore localStorage errors
  }
}

export function ChatPanel({ problemSlug, currentCode, testResults, onClose, initialMessage, initialSessionTitle, onInitialMessageSent }: ChatPanelProps) {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [inputValue, setInputValue] = useState('')
  const [showSessionDropdown, setShowSessionDropdown] = useState(false)
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null)
  const [editingTitle, setEditingTitle] = useState('')

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Queries
  const { data: models } = useModels()
  const { data: sessions } = useSessions(problemSlug)
  const { data: activeSession } = useSession(activeSessionId)

  // Mutations
  const createSession = useCreateSession()
  const updateSession = useUpdateSession()
  const deleteSession = useDeleteSession()

  // Streaming POST chat (simpler than WebSocket - no connection state)
  const { isStreaming, streamingContent, pendingMessage, error, lastFailedMessage, sendMessage, cancelStream, retry, clearError } =
    useStreamChat(activeSessionId)

  // Auto-select first session if available (but not if we have an initial message to send)
  useEffect(() => {
    if (sessions && sessions.length > 0 && !activeSessionId && !initialMessage) {
      setActiveSessionId(sessions[0].id)
    }
  }, [sessions, activeSessionId, initialMessage])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [activeSession?.messages, streamingContent])

  // Track initial message state with refs to avoid dependency issues
  const initialMessageRef = useRef(initialMessage)
  const initialMessageSentRef = useRef(false)
  const isCreatingSessionRef = useRef(false)

  // Update ref when initialMessage changes
  useEffect(() => {
    if (initialMessage && initialMessage !== initialMessageRef.current) {
      // New initial message - reset flags
      initialMessageRef.current = initialMessage
      initialMessageSentRef.current = false
      isCreatingSessionRef.current = false
    }
  }, [initialMessage])

  // Create session and send initial message in one flow (no connection to wait for!)
  useEffect(() => {
    if (!initialMessage || initialMessageSentRef.current || isCreatingSessionRef.current) return
    if (!models) return // Wait for models to load

    const createAndSend = async () => {
      isCreatingSessionRef.current = true
      try {
        // Use last selected model if available, otherwise use default
        const lastModel = getLastModel()
        const modelToUse = lastModel && models.some((m) => m.name === lastModel)
          ? lastModel
          : models.find((m) => m.is_default)?.name
        const session = await createSession.mutateAsync({
          problem_slug: problemSlug,
          mode: 'direct',
          model: modelToUse,
          title: initialSessionTitle || undefined,
        })
        setActiveSessionId(session.id)

        // Send immediately after session is created - no connection to wait for!
        initialMessageSentRef.current = true
        // Small delay to let state update propagate
        setTimeout(() => {
          sendMessage(initialMessage, currentCode, testResults)
          onInitialMessageSent?.()
        }, 50)
      } catch (err) {
        console.error('Failed to create session:', err)
        isCreatingSessionRef.current = false
      }
    }

    createAndSend()
  }, [initialMessage, initialSessionTitle, models, problemSlug, createSession, sendMessage, currentCode, testResults, onInitialMessageSent])

  const handleCreateSession = async (mode: ChatMode) => {
    // Use last selected model if available, otherwise use default
    const lastModel = getLastModel()
    const modelToUse = lastModel && models?.some((m) => m.name === lastModel)
      ? lastModel
      : models?.find((m) => m.is_default)?.name
    const session = await createSession.mutateAsync({
      problem_slug: problemSlug,
      mode,
      model: modelToUse,
    })
    setActiveSessionId(session.id)
    setShowSessionDropdown(false)
  }

  const handleSendMessage = () => {
    if (!inputValue.trim() || isStreaming) return

    sendMessage(inputValue, currentCode, testResults)
    setInputValue('')
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleToggleMode = () => {
    if (!activeSession) return

    const newMode: ChatMode = activeSession.mode === 'socratic' ? 'direct' : 'socratic'
    updateSession.mutate({
      sessionId: activeSession.id,
      request: { mode: newMode },
    })
  }

  const handleDeleteSession = async (sessionId: string) => {
    await deleteSession.mutateAsync(sessionId)
    if (activeSessionId === sessionId) {
      setActiveSessionId(null)
    }
  }

  const handleChangeModel = (model: string) => {
    if (!activeSession) return

    // Don't change model while streaming - would interrupt the response
    if (isStreaming) return

    // Save to localStorage for future sessions
    saveLastModel(model)

    // With streaming POST, model change takes effect on next message (no reconnect needed)
    updateSession.mutate({
      sessionId: activeSession.id,
      request: { model },
    })
  }

  const handleStartEditTitle = (sessionId: string, currentTitle: string) => {
    setEditingSessionId(sessionId)
    setEditingTitle(currentTitle || '')
  }

  const handleSaveTitle = (sessionId: string) => {
    if (editingTitle.trim()) {
      updateSession.mutate({
        sessionId,
        request: { title: editingTitle.trim() },
      })
    }
    setEditingSessionId(null)
    setEditingTitle('')
  }

  const handleCancelEditTitle = () => {
    setEditingSessionId(null)
    setEditingTitle('')
  }

  const handleTitleKeyDown = (e: React.KeyboardEvent, sessionId: string) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSaveTitle(sessionId)
    } else if (e.key === 'Escape') {
      handleCancelEditTitle()
    }
  }

  return (
    <div className="h-full flex flex-col bg-gray-800 border-l border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <MessageSquare size={18} className="text-cyan-400" />
          <span className="font-semibold text-gray-200">AI Assistant</span>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
          aria-label="Close AI Assistant"
        >
          <X size={18} className="text-gray-400" />
        </button>
      </div>

      {/* Session selector & controls */}
      <div className="px-4 py-2 border-b border-gray-700 space-y-2">
        {/* Session dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowSessionDropdown(!showSessionDropdown)}
            className="w-full flex items-center justify-between px-2 py-1 hover:bg-gray-700 rounded transition-colors"
          >
            <span className="text-sm text-gray-200 truncate">
              {activeSession ? (activeSession.title || 'Untitled') : 'Select session...'}
            </span>
            <ChevronDown size={14} className="text-gray-400" />
          </button>

          {showSessionDropdown && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-gray-900 border border-gray-700 rounded-lg shadow-lg z-10 max-h-48 overflow-y-auto">
              <div className="p-2 space-y-1">
                {sessions?.map((session) => (
                  <div key={session.id} className="flex items-center gap-1">
                    {editingSessionId === session.id ? (
                      <div className="flex-1 flex items-center gap-1">
                        <input
                          type="text"
                          value={editingTitle}
                          onChange={(e) => setEditingTitle(e.target.value)}
                          onKeyDown={(e) => handleTitleKeyDown(e, session.id)}
                          onBlur={() => handleSaveTitle(session.id)}
                          autoFocus
                          className="flex-1 px-2 py-1 text-sm bg-gray-800 text-gray-200 rounded border border-cyan-500 focus:outline-none"
                        />
                      </div>
                    ) : (
                      <>
                        <button
                          onClick={() => {
                            setActiveSessionId(session.id)
                            setShowSessionDropdown(false)
                          }}
                          className="flex-1 text-left px-2 py-1 text-sm text-gray-200 hover:bg-gray-700 rounded truncate"
                        >
                          {session.title || 'Untitled'}
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleStartEditTitle(session.id, session.title || '')
                          }}
                          className="p-1 hover:bg-gray-700 rounded"
                          aria-label="Edit session name"
                        >
                          <Pencil size={14} className="text-gray-400" />
                        </button>
                        <button
                          onClick={() => handleDeleteSession(session.id)}
                          className="p-1 hover:bg-red-500/20 rounded"
                          aria-label="Delete session"
                        >
                          <Trash2 size={14} className="text-red-400" />
                        </button>
                      </>
                    )}
                  </div>
                ))}
              </div>

              <div className="border-t border-gray-700 p-2 space-y-1">
                <button
                  onClick={() => handleCreateSession('socratic')}
                  className="w-full flex items-center gap-2 px-2 py-1 text-sm hover:bg-gray-700 rounded transition-colors"
                >
                  <Lightbulb size={14} className="text-yellow-400" />
                  <span className="text-gray-200">New Socratic Session</span>
                </button>
                <button
                  onClick={() => handleCreateSession('direct')}
                  className="w-full flex items-center gap-2 px-2 py-1 text-sm hover:bg-gray-700 rounded transition-colors"
                >
                  <Zap size={14} className="text-cyan-400" />
                  <span className="text-gray-200">New Direct Session</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Mode toggle & model selector */}
        {activeSession && (
          <div className="flex items-center gap-2">
            {/* Mode toggle */}
            <button
              onClick={handleToggleMode}
              className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors ${
                activeSession.mode === 'socratic'
                  ? 'bg-yellow-500/20 text-yellow-400'
                  : 'bg-cyan-500/20 text-cyan-400'
              }`}
            >
              {activeSession.mode === 'socratic' ? (
                <>
                  <Lightbulb size={14} />
                  <span>Socratic</span>
                </>
              ) : (
                <>
                  <Zap size={14} />
                  <span>Direct</span>
                </>
              )}
            </button>

            {/* Model selector */}
            <select
              value={activeSession.model || models?.find((m) => m.is_default)?.name || ''}
              onChange={(e) => handleChangeModel(e.target.value)}
              disabled={isStreaming}
              className="flex-1 px-2 py-1 text-xs bg-gray-900 text-gray-200 rounded border border-gray-700 focus:outline-none focus:ring-1 focus:ring-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {models?.map((model) => (
                <option key={model.name} value={model.name}>
                  {model.display_name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {!activeSession ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-400">
            <MessageSquare size={48} className="mb-4 opacity-50" />
            <p className="text-sm">Select or create a session</p>
          </div>
        ) : activeSession.messages.length === 0 && !streamingContent && !pendingMessage ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-400">
            <MessageSquare size={48} className="mb-4 opacity-50" />
            <p className="text-sm">Start a conversation</p>
          </div>
        ) : (
          <>
            {activeSession.messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {/* Pending user message - shown immediately after sending */}
            {pendingMessage && (
              <div className="bg-cyan-600/20 border-l-2 border-cyan-500 rounded-r-lg px-4 py-3">
                <div className="text-sm text-gray-100">{pendingMessage}</div>
              </div>
            )}
            {/* Thinking indicator - shown while waiting for first chunk */}
            {isStreaming && !streamingContent && (
              <div className="bg-gray-900 border-l-2 border-gray-600 rounded-r-lg px-4 py-3">
                <div className="flex items-center gap-3 text-gray-400">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <span className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                  <span className="text-sm">Thinking...</span>
                </div>
              </div>
            )}
            {/* Streaming content - shown when chunks arrive */}
            {streamingContent && (
              <div className="bg-gray-900 border-l-2 border-gray-600 rounded-r-lg px-4 py-4">
                <div className="text-gray-300">
                  <div className="prose prose-invert prose-sm max-w-none prose-p:text-base prose-p:leading-relaxed prose-p:my-3 prose-headings:text-gray-100 prose-strong:text-gray-100 prose-li:text-base prose-li:leading-relaxed">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        code({ node, inline, className, children, ...props }: any) {
                          const match = /language-(\w+)/.exec(className || '')
                          const codeString = String(children).replace(/\n$/, '')
                          return !inline && match ? (
                            <CodeBlock code={codeString} language={match[1]} />
                          ) : (
                            <code
                              className="bg-gray-800 px-1.5 py-0.5 rounded text-cyan-300 font-mono text-sm"
                              {...props}
                            >
                              {children}
                            </code>
                          )
                        },
                      }}
                    >
                      {streamingContent}
                    </ReactMarkdown>
                    <span className="inline-block w-2 h-5 bg-cyan-400 ml-1 animate-pulse" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Error display */}
      {error && (
        <div className="mx-4 mb-2 bg-red-500/10 border border-red-500/40 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-red-400">
              <AlertCircle size={16} />
              <span className="text-sm font-semibold">Error</span>
            </div>
            <button
              onClick={clearError}
              className="p-1 hover:bg-red-500/20 rounded transition-colors"
              aria-label="Dismiss error"
            >
              <X size={14} className="text-red-400" />
            </button>
          </div>
          <p className="text-sm text-red-300 mt-1">{error}</p>
          {lastFailedMessage && (
            <button
              onClick={retry}
              disabled={isStreaming}
              className="mt-2 flex items-center gap-2 px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-300 text-sm font-medium rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw size={14} />
              Retry with current model
            </button>
          )}
        </div>
      )}

      {/* Input area */}
      <div className="p-4 border-t border-gray-700">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Ask a question..."
            disabled={!activeSession || isStreaming}
            rows={2}
            className="flex-1 p-3 bg-gray-900 rounded-lg text-sm text-gray-100 font-mono focus:outline-none focus:ring-2 focus:ring-cyan-500 resize-none disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <button
            onClick={isStreaming ? cancelStream : handleSendMessage}
            disabled={!activeSession || (!inputValue.trim() && !isStreaming)}
            className="bg-cyan-600 hover:bg-cyan-700 text-white font-semibold rounded-lg px-4 py-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isStreaming ? (
              <X size={18} />
            ) : (
              <Send size={18} />
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

function CodeBlock({ code, language }: { code: string; language: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }, [code])

  return (
    <div className="relative group my-3">
      <button
        onClick={handleCopy}
        className="absolute right-2 top-2 p-1.5 rounded bg-gray-700/80 hover:bg-gray-600 text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity z-10"
        aria-label="Copy code"
      >
        {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
      </button>
      <SyntaxHighlighter
        style={vscDarkPlus}
        language={language}
        PreTag="div"
        className="rounded-lg !mt-0"
      >
        {code}
      </SyntaxHighlighter>
    </div>
  )
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'

  return (
    <div
      className={`rounded-r-lg px-4 py-4 ${
        isUser
          ? 'bg-cyan-600/20 border-l-2 border-cyan-500'
          : 'bg-gray-900 border-l-2 border-gray-600'
      }`}
    >
      <div className={`${isUser ? 'text-gray-100' : 'text-gray-300'}`}>
        {isUser ? (
          <div className="text-base leading-relaxed">{message.content}</div>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none prose-p:text-base prose-p:leading-relaxed prose-p:my-3 prose-headings:text-gray-100 prose-strong:text-gray-100 prose-li:text-base prose-li:leading-relaxed">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ node, inline, className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || '')
                  const codeString = String(children).replace(/\n$/, '')
                  return !inline && match ? (
                    <CodeBlock code={codeString} language={match[1]} />
                  ) : (
                    <code
                      className="bg-gray-800 px-1.5 py-0.5 rounded text-cyan-300 font-mono text-sm"
                      {...props}
                    >
                      {children}
                    </code>
                  )
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
