import { lazy, Suspense } from 'react'
import type { editor } from 'monaco-editor'

interface CodeEditorProps {
  language: string
  value: string
  onChange?: (value: string) => void
  readOnly?: boolean
}

// Lazy load Monaco Editor only on client side
const MonacoEditor = lazy(() =>
  import('@monaco-editor/react').then((mod) => ({ default: mod.Editor }))
)

function EditorSkeleton() {
  return (
    <div className="w-full h-full bg-[#1e1e1e] flex items-center justify-center">
      <div className="text-gray-400">Loading editor...</div>
    </div>
  )
}

export function CodeEditor({
  language,
  value,
  onChange,
  readOnly = false,
}: CodeEditorProps) {
  const handleEditorChange = (value: string | undefined) => {
    if (onChange && value !== undefined) {
      onChange(value)
    }
  }

  // Only render on client side
  if (typeof window === 'undefined') {
    return <EditorSkeleton />
  }

  return (
    <div className="relative w-full h-full border border-border bg-[#1e1e1e] overflow-hidden">
      <Suspense fallback={<EditorSkeleton />}>
        <MonacoEditor
          height="100%"
          language={language}
          value={value}
          onChange={handleEditorChange}
          theme="vs-dark"
          options={{
            readOnly,
            minimap: { enabled: false },
            fontSize: 14,
            fontFamily: 'Menlo, Monaco, "Courier New", monospace',
            lineNumbers: 'on',
            renderLineHighlight: 'all',
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 4,
            insertSpaces: true,
            wordWrap: 'off',
            padding: { top: 16, bottom: 16 },
            cursorBlinking: 'smooth',
            cursorSmoothCaretAnimation: 'on',
            smoothScrolling: true,
          }}
        />
      </Suspense>
    </div>
  )
}

// Helper to get current code value from editor ref
export function getEditorValue(
  editorRef: React.RefObject<editor.IStandaloneCodeEditor | null>
): string {
  return editorRef.current?.getValue() || ''
}
