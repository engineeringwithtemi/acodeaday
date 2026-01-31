import { useEffect, useState } from 'react'
import { renderMermaid, THEMES } from 'beautiful-mermaid'
import DOMPurify from 'dompurify'
import { ZoomIn, ZoomOut, Maximize2, AlertCircle } from 'lucide-react'
import { diagramDataToMermaid } from '@/lib/diagram-to-mermaid'
import { useZoomPan } from '@/hooks/useZoomPan'
import type { DiagramData } from '@/types/diagram'

const THEME = THEMES['tokyo-night'] ?? { bg: '#1a1b26', fg: '#c0caf5' }

interface FlowchartRendererProps {
  data: DiagramData
}

export function FlowchartRenderer({ data }: FlowchartRendererProps) {
  const [svg, setSvg] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const zp = useZoomPan(data)

  useEffect(() => {
    let cancelled = false

    async function render() {
      try {
        const mermaidText = diagramDataToMermaid(data)
        const rawSvg = await renderMermaid(mermaidText, THEME)
        if (cancelled) return

        const sanitized = DOMPurify.sanitize(rawSvg, {
          USE_PROFILES: { svg: true, svgFilters: true },
        })
        setSvg(sanitized)
        setError(null)
      } catch (err) {
        if (cancelled) return
        console.error('FlowchartRenderer render error:', err)
        setSvg(null)
        setError('Failed to render diagram')
      }
    }

    render()
    return () => { cancelled = true }
  }, [data])

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-4">
        <div className="flex items-center gap-2 text-red-400 mb-2">
          <AlertCircle className="w-5 h-5" />
          <p className="text-sm font-medium">Render Error</p>
        </div>
        <p className="text-gray-400 text-sm">{error}</p>
      </div>
    )
  }

  if (!svg) return null

  return (
    <div className="w-full h-full relative">
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
    </div>
  )
}
