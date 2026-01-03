import { Editor, OnMount } from '@monaco-editor/react'
import { useRef } from 'react'
import type { editor } from 'monaco-editor'

interface CodeEditorProps {
  language: string
  value: string
  onChange?: (value: string) => void
  readOnly?: boolean
}

export function CodeEditor({
  language,
  value,
  onChange,
  readOnly = false,
}: CodeEditorProps) {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null)

  const handleEditorMount: OnMount = (editor) => {
    editorRef.current = editor
  }

  const handleEditorChange = (value: string | undefined) => {
    if (onChange && value !== undefined) {
      onChange(value)
    }
  }

  return (
    <div className="relative w-full h-full border border-border bg-[#1e1e1e] overflow-hidden">
      <Editor
        height="100%"
        language={language}
        value={value}
        onChange={handleEditorChange}
        onMount={handleEditorMount}
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
    </div>
  )
}

// Helper to get current code value from editor ref
export function getEditorValue(
  editorRef: React.RefObject<editor.IStandaloneCodeEditor | null>
): string {
  return editorRef.current?.getValue() || ''
}
