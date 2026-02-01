import { useCallback, useEffect, useRef, useState } from 'react'

const MIN_SCALE = 0.1
const MAX_SCALE = 3
const ZOOM_STEP = 0.15

export interface ZoomPanState {
  scale: number
  translate: { x: number; y: number }
  handlers: {
    onWheel: (e: React.WheelEvent) => void
    onPointerDown: (e: React.PointerEvent) => void
    onPointerMove: (e: React.PointerEvent) => void
    onPointerUp: () => void
  }
  zoomIn: () => void
  zoomOut: () => void
  resetView: () => void
  zoomPercent: number
}

export function useZoomPan(resetKey?: unknown): ZoomPanState {
  const [scale, setScale] = useState(1)
  const [translate, setTranslate] = useState({ x: 0, y: 0 })
  const isPanning = useRef(false)
  const panStart = useRef({ x: 0, y: 0 })
  const translateStart = useRef({ x: 0, y: 0 })

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- resetting zoom/pan on key change is intentional
    setScale(1)
    setTranslate({ x: 0, y: 0 })
  }, [resetKey])

  const clampScale = (s: number) => Math.min(MAX_SCALE, Math.max(MIN_SCALE, s))

  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? -ZOOM_STEP : ZOOM_STEP
    setScale((prev) => clampScale(prev + delta))
  }, [])

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    if (e.button !== 0) return
    isPanning.current = true
    panStart.current = { x: e.clientX, y: e.clientY }
    translateStart.current = { ...translate }
    ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
  }, [translate])

  const onPointerMove = useCallback((e: React.PointerEvent) => {
    if (!isPanning.current) return
    const dx = e.clientX - panStart.current.x
    const dy = e.clientY - panStart.current.y
    setTranslate({
      x: translateStart.current.x + dx,
      y: translateStart.current.y + dy,
    })
  }, [])

  const onPointerUp = useCallback(() => {
    isPanning.current = false
  }, [])

  const zoomIn = () => setScale((s) => clampScale(s + ZOOM_STEP))
  const zoomOut = () => setScale((s) => clampScale(s - ZOOM_STEP))
  const resetView = () => {
    setScale(1)
    setTranslate({ x: 0, y: 0 })
  }

  return {
    scale,
    translate,
    handlers: { onWheel, onPointerDown, onPointerMove, onPointerUp },
    zoomIn,
    zoomOut,
    resetView,
    zoomPercent: Math.round(scale * 100),
  }
}
