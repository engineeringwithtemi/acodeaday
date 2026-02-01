import { useCallback, useEffect, useRef, useState } from 'react'
import { useDebouncedDiagram } from '@/hooks/useDebouncedDiagram'
import { useZoomPan } from '@/hooks/useZoomPan'
import { FlowchartRenderer } from '@/components/FlowchartRenderer'
import { apiPost } from '@/lib/api-client'
import { Loader2, GitBranch, AlertCircle, ZoomIn, ZoomOut, Maximize2, Sparkles, RefreshCw } from 'lucide-react'
import type { DiagramData } from '@/types/diagram'

type ViewMode = 'code' | 'pseudocode'

interface DiagramPanelProps {
  code: string
  language: string
  chatDiagramData?: DiagramData | null
  chatDiagramLoading?: boolean
  onChatDiagramShown?: () => void
}

const COOLDOWN_MS = 5000

export function DiagramPanel({ code, language, chatDiagramData, chatDiagramLoading, onChatDiagramShown }: DiagramPanelProps) {
  const { svg, reason, error, isLoading } = useDebouncedDiagram(code, language)

  const [viewMode, setViewMode] = useState<ViewMode>('code')

  // Pseudocode state
  const [pseudoData, setPseudoData] = useState<DiagramData | null>(null)
  const [pseudoError, setPseudoError] = useState<string | null>(null)
  const [pseudoLoading, setPseudoLoading] = useState(false)
  const [codeStale, setCodeStale] = useState(false)
  const [cooldownSecs, setCooldownSecs] = useState(0)
  const abortRef = useRef<AbortController | null>(null)
  const lastCodeRef = useRef<string | null>(null)
  const cooldownRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Code view zoom/pan (uses shared hook)
  const zp = useZoomPan(svg)

  // Mark pseudocode as stale when code changes
  useEffect(() => {
    if (pseudoData && lastCodeRef.current !== null && lastCodeRef.current !== code) {
      setCodeStale(true)
    }
  }, [code, pseudoData])

  // Cancel in-flight request on unmount or view switch away
  useEffect(() => {
    return () => {
      abortRef.current?.abort()
    }
  }, [viewMode])

  const startCooldown = useCallback(() => {
    const totalSecs = Math.ceil(COOLDOWN_MS / 1000)
    setCooldownSecs(totalSecs)
    if (cooldownRef.current) clearInterval(cooldownRef.current)
    cooldownRef.current = setInterval(() => {
      setCooldownSecs((prev) => {
        if (prev <= 1) {
          if (cooldownRef.current) clearInterval(cooldownRef.current)
          cooldownRef.current = null
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }, [])

  // Clean up cooldown interval on unmount
  useEffect(() => {
    return () => {
      if (cooldownRef.current) clearInterval(cooldownRef.current)
    }
  }, [])

  // Show loading state when chat diagram generation starts
  useEffect(() => {
    if (chatDiagramLoading) {
      setViewMode('pseudocode')
      setPseudoData(null)
      setPseudoError(null)
      setPseudoLoading(true)
    }
  }, [chatDiagramLoading])

  // Accept diagram data from chat when it arrives
  useEffect(() => {
    if (chatDiagramData) {
      setPseudoData(chatDiagramData)
      setPseudoError(null)
      setPseudoLoading(false)
      setViewMode('pseudocode')
      setCodeStale(false)
      lastCodeRef.current = code
      onChatDiagramShown?.()
    }
  }, [chatDiagramData, code, onChatDiagramShown])

  const generatePseudocode = useCallback(async () => {
    if (!code.trim() || cooldownSecs > 0) return

    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setPseudoLoading(true)
    setPseudoError(null)
    setCodeStale(false)

    try {
      const result = await apiPost<DiagramData>('/api/diagram/pseudocode', {
        code,
        language,
      }, { signal: controller.signal })

      if (controller.signal.aborted) return

      setPseudoData(result)
      lastCodeRef.current = code
    } catch (err: unknown) {
      if (controller.signal.aborted) return
      if (err instanceof Error && err.name === 'AbortError') return

      console.error('Pseudocode diagram error:', err)
      setPseudoError(err instanceof Error ? err.message : 'Failed to generate pseudocode diagram')
    } finally {
      if (!controller.signal.aborted) {
        setPseudoLoading(false)
      }
    }

    startCooldown()
  }, [code, language, cooldownSecs, startCooldown])

  return (
    <div className="h-full flex flex-col overflow-hidden bg-gray-900">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-semibold text-gray-200">Flowchart</h2>
        </div>

        <div className="flex items-center gap-1">
          {/* View toggle pills */}
          <div className="flex bg-gray-800 rounded-md p-0.5">
            <button
              onClick={() => setViewMode('code')}
              className={`px-2.5 py-1 text-xs font-medium rounded transition-colors ${
                viewMode === 'code'
                  ? 'bg-gray-600 text-white'
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              Code
            </button>
            <button
              onClick={() => setViewMode('pseudocode')}
              className={`px-2.5 py-1 text-xs font-medium rounded transition-colors ${
                viewMode === 'pseudocode'
                  ? 'bg-gray-600 text-white'
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              Pseudocode
            </button>
          </div>

          {/* Loading indicator for code view */}
          {viewMode === 'code' && isLoading && (
            <Loader2 className="w-4 h-4 text-gray-400 animate-spin ml-2" />
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden relative">
        {viewMode === 'code' ? (
          /* ---------- Code View ---------- */
          svg ? (
            <>
              <div
                className="w-full h-full cursor-grab active:cursor-grabbing"
                onWheel={zp.handlers.onWheel}
                onPointerDown={zp.handlers.onPointerDown}
                onPointerMove={zp.handlers.onPointerMove}
                onPointerUp={zp.handlers.onPointerUp}
                onPointerCancel={zp.handlers.onPointerUp}
              >
                <div
                  className="diagram-svg w-full h-full flex items-start justify-center [&_svg]:h-auto"
                  style={{
                    transform: `translate(${zp.translate.x}px, ${zp.translate.y}px) scale(${zp.scale})`,
                    transformOrigin: 'top center',
                    paddingTop: '1rem',
                  }}
                  dangerouslySetInnerHTML={{ __html: svg }}
                />
              </div>

              {/* Zoom controls */}
              <div className="absolute bottom-4 right-4 flex items-center gap-1 bg-gray-800/90 backdrop-blur-sm border border-gray-700 rounded-lg px-1 py-1 shadow-lg">
                <button
                  onClick={zp.zoomIn}
                  className="p-1.5 rounded hover:bg-gray-700 text-gray-300 hover:text-white transition-colors"
                  title="Zoom in"
                >
                  <ZoomIn className="w-4 h-4" />
                </button>
                <span className="text-xs text-gray-400 min-w-[3ch] text-center select-none">
                  {zp.zoomPercent}%
                </span>
                <button
                  onClick={zp.zoomOut}
                  className="p-1.5 rounded hover:bg-gray-700 text-gray-300 hover:text-white transition-colors"
                  title="Zoom out"
                >
                  <ZoomOut className="w-4 h-4" />
                </button>
                <div className="w-px h-4 bg-gray-600 mx-0.5" />
                <button
                  onClick={zp.resetView}
                  className="p-1.5 rounded hover:bg-gray-700 text-gray-300 hover:text-white transition-colors"
                  title="Reset view"
                >
                  <Maximize2 className="w-4 h-4" />
                </button>
              </div>
            </>
          ) : error ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-4">
              <div className="flex items-center gap-2 text-red-400 mb-2">
                <AlertCircle className="w-5 h-5" />
                <p className="text-sm font-medium">Error</p>
              </div>
              <p className="text-gray-400 text-sm">{error}</p>
            </div>
          ) : reason ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-4">
              <GitBranch className="w-10 h-10 text-gray-700 mb-3" />
              <p className="text-gray-400 text-sm">{reason}</p>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center px-4">
              <GitBranch className="w-10 h-10 text-gray-700 mb-3" />
              <p className="text-gray-500 text-sm">Write some code to see its flowchart</p>
              <p className="text-gray-600 text-xs mt-1">Diagram updates automatically as you type</p>
            </div>
          )
        ) : (
          /* ---------- Pseudocode View ---------- */
          pseudoLoading ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-4">
              <Loader2 className="w-8 h-8 text-cyan-400 animate-spin mb-3" />
              <p className="text-gray-400 text-sm">Generating pseudocode diagram...</p>
              <p className="text-gray-600 text-xs mt-1">This may take a few seconds</p>
            </div>
          ) : pseudoError ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-4">
              <div className="flex items-center gap-2 text-red-400 mb-2">
                <AlertCircle className="w-5 h-5" />
                <p className="text-sm font-medium">Error</p>
              </div>
              <p className="text-gray-400 text-sm mb-3">{pseudoError}</p>
              <button
                onClick={generatePseudocode}
                disabled={cooldownSecs > 0}
                className="px-3 py-1.5 text-xs font-medium rounded-md bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {cooldownSecs > 0 ? `Retry (${cooldownSecs}s)` : 'Retry'}
              </button>
            </div>
          ) : pseudoData ? (
            <div className="w-full h-full flex flex-col">
              {codeStale && (
                <div className="px-4 py-2 bg-yellow-900/30 border-b border-yellow-700/40 flex items-center justify-between">
                  <p className="text-yellow-400/80 text-xs">Code has changed since this diagram was generated</p>
                  <button
                    onClick={generatePseudocode}
                    disabled={cooldownSecs > 0 || !code.trim()}
                    className="flex items-center gap-1 px-2 py-1 text-xs font-medium rounded bg-yellow-800/50 text-yellow-300 hover:bg-yellow-700/50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <RefreshCw className="w-3 h-3" />
                    {cooldownSecs > 0 ? `Regenerate (${cooldownSecs}s)` : 'Regenerate'}
                  </button>
                </div>
              )}
              <div className="flex-1 overflow-hidden">
                <FlowchartRenderer data={pseudoData} />
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center px-4">
              <Sparkles className="w-10 h-10 text-gray-700 mb-3" />
              <p className="text-gray-400 text-sm mb-1">AI-generated pseudocode flowchart</p>
              <p className="text-gray-600 text-xs mb-4">Translates your code into plain-English steps</p>
              <button
                onClick={generatePseudocode}
                disabled={!code.trim() || cooldownSecs > 0}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-cyan-600 text-white hover:bg-cyan-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Sparkles className="w-4 h-4" />
                {cooldownSecs > 0 ? `Generate Pseudocode (${cooldownSecs}s)` : 'Generate Pseudocode'}
              </button>
            </div>
          )
        )}
      </div>
    </div>
  )
}
