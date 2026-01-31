import { useState } from 'react'
import { X, Download, Loader2 } from 'lucide-react'
import { useStartImport } from '@/hooks'

interface ImportModalProps {
  isOpen: boolean
  onClose: () => void
  onImportStarted: (importId: string) => void
}

export function ImportModal({ isOpen, onClose, onImportStarted }: ImportModalProps) {
  const [prompt, setPrompt] = useState('')
  const startImport = useStartImport()

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!prompt.trim() || startImport.isPending) return

    try {
      const job = await startImport.mutateAsync({ prompt: prompt.trim() })
      setPrompt('')
      onImportStarted(job.id)
      onClose()
    } catch {
      // Error is available via startImport.error
    }
  }

  const examples = [
    'Add Two Sum from LeetCode',
    '5 sliding window problems',
    '3 easy dynamic programming problems',
    'LeetCode #146 LRU Cache',
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-lg mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <Download className="text-cyan-400" size={22} />
            <h2 className="text-xl font-bold text-white">Import Problems</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 hover:bg-gray-700 rounded-lg transition-colors text-gray-400 hover:text-white"
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-5">
          <label htmlFor="import-prompt" className="block text-sm font-medium text-gray-300 mb-2">
            Describe what you want to import
          </label>
          <textarea
            id="import-prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g., Add 5 binary search problems from LeetCode"
            rows={3}
            maxLength={500}
            className="w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 resize-none"
            autoFocus
          />
          <div className="flex justify-between items-center mt-1.5 mb-4">
            <p className="text-xs text-gray-500">
              {prompt.length}/500
            </p>
            {startImport.isError && (
              <p className="text-xs text-red-400">
                {(startImport.error as Error).message || 'Failed to start import'}
              </p>
            )}
          </div>

          {/* Examples */}
          <div className="mb-5">
            <p className="text-xs text-gray-500 mb-2">Try these examples:</p>
            <div className="flex flex-wrap gap-2">
              {examples.map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => setPrompt(example)}
                  className="px-3 py-1.5 bg-gray-800 border border-gray-600 rounded-lg text-xs text-gray-300 hover:border-cyan-500/50 hover:text-cyan-400 transition-colors"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!prompt.trim() || prompt.trim().length < 3 || startImport.isPending}
              className="flex items-center gap-2 px-5 py-2 bg-cyan-500 hover:bg-cyan-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors text-sm"
            >
              {startImport.isPending ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Starting...
                </>
              ) : (
                <>
                  <Download size={16} />
                  Import
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
