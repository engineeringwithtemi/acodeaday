import { useState } from 'react'
import { X, CheckCircle2, XCircle, AlertCircle, Download, RotateCcw, Frown, Smile, Trophy } from 'lucide-react'
import type { SubmitCodeResponse, FunctionSignature, Rating, RatingResponse } from '../types/api'
import { useRateSubmission } from '../hooks/useRateSubmission'

interface SubmissionResultPanelProps {
  result: SubmitCodeResponse
  code: string
  language: string
  problemSlug: string
  functionSignature?: FunctionSignature
  onClose?: () => void
  onLoadCode?: (code: string) => void
}

export function SubmissionResultPanel({
  result,
  code,
  language,
  problemSlug,
  functionSignature,
  onClose,
  onLoadCode,
}: SubmissionResultPanelProps) {
  const [ratingResult, setRatingResult] = useState<RatingResponse | null>(null)
  const [ratingError, setRatingError] = useState<string | null>(null)
  const rateSubmission = useRateSubmission()

  // Handle rating selection
  const handleRating = async (rating: Rating) => {
    setRatingError(null)
    try {
      const response = await rateSubmission.mutateAsync({
        problem_slug: problemSlug,
        rating,
      })
      setRatingResult(response)
    } catch (error) {
      console.error('Failed to submit rating:', error)
      setRatingError('Failed to save rating. Please try again.')
    }
  }

  // Show rating buttons if needed and not yet rated
  const showRatingButtons = result.needs_rating && !ratingResult

  // Determine status
  const getStatus = () => {
    if (result.compile_error) return { text: 'Compile Error', color: 'red' }
    if (result.runtime_error) return { text: 'Runtime Error', color: 'red' }
    if (!result.success) return { text: 'Wrong Answer', color: 'red' }
    return { text: 'Accepted', color: 'green' }
  }

  const status = getStatus()
  const statusColorClass = status.color === 'green' ? 'text-green-400' : 'text-red-400'
  const borderColorClass = status.color === 'green' ? 'border-green-500/40' : 'border-red-500/40'
  const bgColorClass = status.color === 'green' ? 'bg-green-500/10' : 'bg-red-500/10'

  // Find first failed test case
  const firstFailedTest = result.results?.find(r => !r.passed)

  // Format memory (convert KB to MB)
  const formatMemory = (kb?: number) => {
    if (!kb) return 'N/A'
    return `${(kb / 1024).toFixed(2)} MB`
  }

  // Format input params
  const formatInputParams = (input: any) => {
    if (input === undefined || input === null) return 'N/A'

    const paramNames = functionSignature?.params?.map(p => p.name) || []

    if (Array.isArray(input)) {
      return input.map((value, i) => {
        const paramName = paramNames[i] || `arg${i}`
        return `${paramName} = ${JSON.stringify(value)}`
      }).join('\n')
    }

    return JSON.stringify(input)
  }

  // Calculate test counts
  // summary.passed = tests that passed (use this for X in "X / Y")
  // total_test_cases = total tests in problem (use this for Y in "X / Y")
  const testsPassed = result.summary?.passed ?? 0
  const totalTests = result.total_test_cases ?? result.summary?.total ?? 0

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-gray-900 rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h2 className="text-xl font-bold text-white">Submission Result</h2>
          {onClose && (
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              aria-label="Close"
            >
              <X className="w-5 h-5 text-gray-400" />
            </button>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Status Banner */}
          <div className={`rounded-lg p-4 border ${bgColorClass} ${borderColorClass}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {status.color === 'green' ? (
                  <CheckCircle2 className="w-6 h-6 text-green-400" />
                ) : (
                  <XCircle className="w-6 h-6 text-red-400" />
                )}
                <span className={`text-lg font-bold ${statusColorClass}`}>
                  {status.text}
                </span>
              </div>
              {totalTests > 0 && (
                <span className="font-mono text-sm text-gray-300">
                  {testsPassed} / {totalTests} testcases passed
                </span>
              )}
            </div>
          </div>

          {/* Compile Error */}
          {result.compile_error && (
            <div className="bg-red-500/10 border border-red-500/40 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="w-5 h-5 text-red-400" />
                <span className="text-sm font-semibold text-red-400">Compilation Error</span>
              </div>
              <pre className="font-mono text-sm text-red-300 bg-gray-900/50 p-4 rounded-lg overflow-x-auto whitespace-pre-wrap">
                {result.compile_error}
              </pre>
            </div>
          )}

          {/* Runtime Error */}
          {result.runtime_error && (
            <div className="bg-red-500/10 border border-red-500/40 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="w-5 h-5 text-red-400" />
                <span className="text-sm font-semibold text-red-400">Runtime Error</span>
              </div>
              <pre className="font-mono text-sm text-red-300 bg-gray-900/50 p-4 rounded-lg overflow-x-auto whitespace-pre-wrap">
                {result.runtime_error}
              </pre>
            </div>
          )}

          {/* Failed Test Case Details */}
          {firstFailedTest && !firstFailedTest.is_hidden && (
            <div className="space-y-3">
              {/* Test Case Number */}
              {firstFailedTest.test_number && (
                <div className="text-sm text-gray-400">
                  Failed on <span className="text-red-400 font-semibold">Test Case {firstFailedTest.test_number}</span>
                </div>
              )}

              {/* Input */}
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2">Input</h3>
                <div className="bg-gray-800 rounded-lg p-4">
                  <pre className="font-mono text-sm text-gray-300 whitespace-pre-wrap">
                    {formatInputParams(firstFailedTest.input)}
                  </pre>
                </div>
              </div>

              {/* Output (User's result) */}
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2">Output</h3>
                <div className="bg-gray-800 rounded-lg p-4">
                  <pre className="font-mono text-sm text-red-300 whitespace-pre-wrap">
                    {JSON.stringify(firstFailedTest.output)}
                  </pre>
                </div>
              </div>

              {/* Expected */}
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2">Expected</h3>
                <div className="bg-gray-800 rounded-lg p-4">
                  <pre className="font-mono text-sm text-green-300 whitespace-pre-wrap">
                    {JSON.stringify(firstFailedTest.expected)}
                  </pre>
                </div>
              </div>
            </div>
          )}

          {/* Stats (Runtime and Memory) */}
          {(result.runtime_ms !== undefined || result.memory_kb !== undefined) && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2">Runtime</h3>
                <div className="bg-gray-800 rounded-lg p-4">
                  <span className="font-mono text-lg text-cyan-400">
                    {result.runtime_ms !== undefined ? `${result.runtime_ms} ms` : 'N/A'}
                  </span>
                </div>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-400 mb-2">Memory</h3>
                <div className="bg-gray-800 rounded-lg p-4">
                  <span className="font-mono text-lg text-cyan-400">
                    {formatMemory(result.memory_kb)}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Code Section */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <h3 className="text-sm font-semibold text-gray-400">Code</h3>
              <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs font-semibold">
                {language}
              </span>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 max-h-64 overflow-y-auto">
              <pre className="font-mono text-sm text-gray-300">
                {code}
              </pre>
            </div>
          </div>

          {/* Rating Buttons (Anki-style) */}
          {showRatingButtons && (
            <div className="bg-gradient-to-r from-cyan-500/10 to-purple-500/10 border border-cyan-500/30 rounded-lg p-6">
              <h3 className="text-center text-lg font-semibold text-white mb-4">
                How did that feel?
              </h3>
              <div className="grid grid-cols-4 gap-3">
                <button
                  onClick={() => handleRating('again')}
                  disabled={rateSubmission.isPending}
                  className="flex flex-col items-center gap-2 p-4 bg-red-500/20 hover:bg-red-500/30 border border-red-500/40 rounded-lg transition-colors disabled:opacity-50"
                >
                  <RotateCcw className="w-6 h-6 text-red-400" />
                  <span className="text-red-400 font-semibold">Again</span>
                  <span className="text-xs text-gray-400">1 day</span>
                </button>
                <button
                  onClick={() => handleRating('hard')}
                  disabled={rateSubmission.isPending}
                  className="flex flex-col items-center gap-2 p-4 bg-orange-500/20 hover:bg-orange-500/30 border border-orange-500/40 rounded-lg transition-colors disabled:opacity-50"
                >
                  <Frown className="w-6 h-6 text-orange-400" />
                  <span className="text-orange-400 font-semibold">Hard</span>
                  <span className="text-xs text-gray-400">
                    {result.interval_days ? `${Math.max(1, Math.round(result.interval_days * 1.2))}d` : '1d'}
                  </span>
                </button>
                <button
                  onClick={() => handleRating('good')}
                  disabled={rateSubmission.isPending}
                  className="flex flex-col items-center gap-2 p-4 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/40 rounded-lg transition-colors disabled:opacity-50"
                >
                  <Smile className="w-6 h-6 text-blue-400" />
                  <span className="text-blue-400 font-semibold">Good</span>
                  <span className="text-xs text-gray-400">
                    {result.interval_days && result.ease_factor
                      ? `${Math.round(result.interval_days * result.ease_factor)}d`
                      : '3d'}
                  </span>
                </button>
                <button
                  onClick={() => handleRating('mastered')}
                  disabled={rateSubmission.isPending}
                  className="flex flex-col items-center gap-2 p-4 bg-green-500/20 hover:bg-green-500/30 border border-green-500/40 rounded-lg transition-colors disabled:opacity-50"
                >
                  <Trophy className="w-6 h-6 text-green-400" />
                  <span className="text-green-400 font-semibold">Mastered</span>
                  <span className="text-xs text-gray-400">Done!</span>
                </button>
              </div>
              {rateSubmission.isPending && (
                <p className="text-center text-gray-400 mt-3 text-sm">Saving...</p>
              )}
              {ratingError && (
                <p className="text-center text-red-400 mt-3 text-sm">{ratingError}</p>
              )}
            </div>
          )}

          {/* Rating Result (after rating submitted) */}
          {ratingResult && (
            <div className="bg-gradient-to-r from-green-500/10 to-cyan-500/10 border border-green-500/30 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <div className="text-sm text-gray-400">
                    Times Solved: <span className="text-cyan-400 font-semibold">{ratingResult.times_solved}</span>
                  </div>
                  {ratingResult.is_mastered ? (
                    <div className="text-green-400 font-semibold text-sm flex items-center gap-2">
                      <Trophy className="w-4 h-4" />
                      Mastered! Problem removed from rotation.
                    </div>
                  ) : (
                    <div className="text-sm text-gray-400">
                      Next Review: <span className="text-cyan-400 font-semibold">
                        {ratingResult.next_review_date
                          ? new Date(ratingResult.next_review_date).toLocaleDateString()
                          : `in ${ratingResult.interval_days} day${ratingResult.interval_days !== 1 ? 's' : ''}`}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Progress Info (for already mastered or failed submissions) */}
          {!showRatingButtons && !ratingResult && result.times_solved !== undefined && (
            <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <div className="text-sm text-gray-400">
                    Times Solved: <span className="text-cyan-400 font-semibold">{result.times_solved}</span>
                  </div>
                  {result.is_mastered && (
                    <div className="text-green-400 font-semibold text-sm flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4" />
                      Mastered!
                    </div>
                  )}
                  {result.next_review_date && !result.is_mastered && (
                    <div className="text-sm text-gray-400">
                      Next Review: <span className="text-cyan-400">{new Date(result.next_review_date).toLocaleDateString()}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-700 flex gap-3">
          {onLoadCode && (
            <button
              onClick={() => onLoadCode(code)}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white font-semibold rounded-lg transition-colors"
            >
              <Download className="w-4 h-4" />
              Load Code
            </button>
          )}
          {/* Only show Close button if no rating is needed OR rating is done */}
          {(!showRatingButtons || ratingResult) && (
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold rounded-lg transition-colors"
            >
              Close
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
