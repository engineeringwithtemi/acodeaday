import { useState, useEffect, useRef } from 'react'
import { initParsers, codeToMermaid } from '@/lib/code-to-diagram'
import { renderMermaid, THEMES } from 'beautiful-mermaid'
import DOMPurify from 'dompurify'

export interface DiagramState {
  svg: string | null
  reason: string | null
  error: string | null
  isLoading: boolean
}

const THEME = THEMES['tokyo-night'] ?? { bg: '#1a1b26', fg: '#c0caf5' }

export function useDebouncedDiagram(
  code: string,
  language: string,
  debounceMs: number = 2000,
): DiagramState {
  const [state, setState] = useState<DiagramState>({
    svg: null,
    reason: null,
    error: null,
    isLoading: false,
  })
  const initRef = useRef(false)
  const initFailedRef = useRef(false)
  const abortRef = useRef<AbortController | null>(null)

  // Initialize parsers once on first mount
  useEffect(() => {
    if (!initRef.current) {
      initRef.current = true
      initParsers().catch((err) => {
        initFailedRef.current = true
        setState({
          svg: null,
          reason: null,
          error: 'Failed to load code parser',
          isLoading: false,
        })
        console.error('Tree-sitter init failed:', err)
      })
    }
  }, [])

  // Debounced diagram generation
  useEffect(() => {
    if (initFailedRef.current) return

    if (!code.trim()) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- clearing state on empty input is intentional
      setState({ svg: null, reason: null, error: null, isLoading: false })
      return
    }

    setState((prev) => ({ ...prev, isLoading: true }))

    const timer = setTimeout(async () => {
      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller

      try {
        const result = codeToMermaid(code, language)
        if (controller.signal.aborted) return

        if (!result.mermaid) {
          setState({
            svg: null,
            reason: result.reason,
            error: null,
            isLoading: false,
          })
          return
        }

        const svg = await renderMermaid(result.mermaid, THEME)
        if (controller.signal.aborted) return

        const sanitized = DOMPurify.sanitize(svg, {
          USE_PROFILES: { svg: true, svgFilters: true },
        })

        setState({ svg: sanitized, reason: null, error: null, isLoading: false })
      } catch (err) {
        if (controller.signal.aborted) return
        console.error('Diagram render error:', err)
        setState({
          svg: null,
          reason: null,
          error: 'Could not generate diagram',
          isLoading: false,
        })
      }
    }, debounceMs)

    return () => {
      clearTimeout(timer)
      abortRef.current?.abort()
    }
  }, [code, language, debounceMs])

  return state
}
