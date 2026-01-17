import { useState } from 'react'
import { Lock, Unlock, X, Download, MessageSquare } from 'lucide-react'
import type { ProblemLanguageSchema } from '../types/api'

interface SolutionsPanelProps {
  languages: ProblemLanguageSchema[]
  onLoadToEditor?: (code: string, language: string) => void
  onAskAI?: (solutionCode: string, language: string) => void
}

export function SolutionsPanel({ languages, onLoadToEditor, onAskAI }: SolutionsPanelProps) {
  // Track which language solutions have been unlocked
  const [unlockedLanguages, setUnlockedLanguages] = useState<Set<string>>(new Set())
  // Track which language is pending confirmation
  const [pendingUnlock, setPendingUnlock] = useState<string | null>(null)
  // Track which language solution is currently being viewed
  const [viewingLanguage, setViewingLanguage] = useState<string | null>(null)

  const handleLanguageClick = (language: string) => {
    if (unlockedLanguages.has(language)) {
      // Already unlocked, show the solution
      setViewingLanguage(language)
    } else {
      // Show confirmation modal
      setPendingUnlock(language)
    }
  }

  const handleConfirmUnlock = () => {
    if (pendingUnlock) {
      setUnlockedLanguages(prev => new Set(prev).add(pendingUnlock))
      setViewingLanguage(pendingUnlock)
      setPendingUnlock(null)
    }
  }

  const handleCancelUnlock = () => {
    setPendingUnlock(null)
  }

  const handleCloseViewer = () => {
    setViewingLanguage(null)
  }

  const getLanguageDisplayName = (lang: string) => {
    const names: Record<string, string> = {
      python: 'Python',
      javascript: 'JavaScript',
      typescript: 'TypeScript',
      java: 'Java',
      cpp: 'C++',
      go: 'Go',
      rust: 'Rust',
    }
    return names[lang.toLowerCase()] || lang
  }

  const viewingSolution = viewingLanguage
    ? languages.find(l => l.language === viewingLanguage)?.reference_solution
    : null

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-semibold text-gray-200">Solutions</h2>
        <p className="text-sm text-gray-400 mt-1">
          Click on a language to view the reference solution
        </p>
      </div>

      {/* Language List */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-2">
          {languages.map((lang) => {
            const isUnlocked = unlockedLanguages.has(lang.language)
            return (
              <button
                key={lang.language}
                onClick={() => handleLanguageClick(lang.language)}
                className={`w-full flex items-center justify-between p-4 rounded-lg border transition-colors ${
                  isUnlocked
                    ? 'bg-gray-800 border-gray-600 hover:bg-gray-700'
                    : 'bg-gray-800/50 border-gray-700 hover:bg-gray-800 hover:border-gray-600'
                }`}
              >
                <div className="flex items-center gap-3">
                  {isUnlocked ? (
                    <Unlock className="w-5 h-5 text-green-400" />
                  ) : (
                    <Lock className="w-5 h-5 text-gray-500" />
                  )}
                  <span className={`font-medium ${isUnlocked ? 'text-gray-200' : 'text-gray-400'}`}>
                    {getLanguageDisplayName(lang.language)}
                  </span>
                </div>
                <span className={`text-xs px-2 py-1 rounded ${
                  isUnlocked
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-gray-700 text-gray-500'
                }`}>
                  {isUnlocked ? 'Unlocked' : 'Locked'}
                </span>
              </button>
            )
          })}
        </div>

        {languages.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            No solutions available for this problem
          </div>
        )}
      </div>

      {/* Confirmation Modal */}
      {pendingUnlock && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-gray-900 rounded-xl shadow-2xl w-full max-w-md">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <h3 className="text-lg font-bold text-white">View Solution?</h3>
              <button
                onClick={handleCancelUnlock}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                aria-label="Close"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-4">
              <p className="text-gray-300">
                Are you sure you want to view the{' '}
                <span className="text-cyan-400 font-semibold">
                  {getLanguageDisplayName(pendingUnlock)}
                </span>{' '}
                solution?
              </p>
              <p className="text-gray-500 text-sm mt-2">
                Try solving the problem on your own first for the best learning experience.
              </p>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-gray-700 flex gap-3">
              <button
                onClick={handleCancelUnlock}
                className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white font-semibold rounded-lg transition-colors"
              >
                Keep Trying
              </button>
              <button
                onClick={handleConfirmUnlock}
                className="flex-1 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold rounded-lg transition-colors"
              >
                Show Solution
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Solution Viewer Modal */}
      {viewingLanguage && viewingSolution && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-gray-900 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <div className="flex items-center gap-3">
                <h3 className="text-lg font-bold text-white">Reference Solution</h3>
                <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs font-semibold">
                  {getLanguageDisplayName(viewingLanguage)}
                </span>
              </div>
              <button
                onClick={handleCloseViewer}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                aria-label="Close"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            {/* Solution Code */}
            <div className="flex-1 overflow-y-auto p-4">
              <div className="bg-gray-800 rounded-lg p-4">
                <pre className="font-mono text-sm text-gray-300 whitespace-pre-wrap overflow-x-auto">
                  {viewingSolution}
                </pre>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-gray-700 flex gap-3">
              {onLoadToEditor && (
                <button
                  onClick={() => {
                    onLoadToEditor(viewingSolution, viewingLanguage)
                    handleCloseViewer()
                  }}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white font-semibold rounded-lg transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Load to Editor
                </button>
              )}
              {onAskAI && (
                <button
                  onClick={() => {
                    onAskAI(viewingSolution, viewingLanguage)
                    handleCloseViewer()
                  }}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-lg transition-colors"
                >
                  <MessageSquare className="w-4 h-4" />
                  Ask AI
                </button>
              )}
              <button
                onClick={handleCloseViewer}
                className="flex-1 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
