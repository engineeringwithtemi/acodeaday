import { CheckCircle2, XCircle, Loader2, Clock, AlertCircle, Terminal } from 'lucide-react'
import type { RunCodeResponse, SubmitCodeResponse, TestResult } from '../types/api'

interface TestResultsProps {
  results: RunCodeResponse | SubmitCodeResponse | null
  isRunning?: boolean
}

export function TestResults({
  results,
  isRunning = false,
}: TestResultsProps) {
  if (isRunning) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-800">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-10 h-10 text-cyan-400 animate-spin" />
          <p className="text-gray-400 font-mono text-sm">Running tests...</p>
        </div>
      </div>
    )
  }

  if (!results) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-800">
        <div className="text-center px-8">
          <div className="w-14 h-14 mx-auto mb-4 rounded-full bg-gray-700/50 border border-gray-600 flex items-center justify-center">
            <Clock className="w-7 h-7 text-gray-500" />
          </div>
          <p className="text-gray-500 font-mono text-sm">
            Run your code to see test results
          </p>
        </div>
      </div>
    )
  }

  // Handle compilation errors
  if (results.compile_error) {
    return (
      <div className="h-full overflow-y-auto bg-gray-800 p-4">
        <div className="bg-red-500/10 border border-red-500/40 rounded-lg p-4">
          <div className="flex items-center gap-3 mb-3">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <span className="font-mono font-semibold text-red-400">Compile Error</span>
          </div>
          <pre className="font-mono text-sm text-red-300 bg-gray-900/50 p-4 rounded-lg overflow-x-auto whitespace-pre-wrap">
            {results.compile_error}
          </pre>
        </div>
      </div>
    )
  }

  // Handle runtime errors
  if (results.runtime_error) {
    return (
      <div className="h-full overflow-y-auto bg-gray-800 p-4">
        <div className="bg-red-500/10 border border-red-500/40 rounded-lg p-4">
          <div className="flex items-center gap-3 mb-3">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <span className="font-mono font-semibold text-red-400">Runtime Error</span>
          </div>
          <pre className="font-mono text-sm text-red-300 bg-gray-900/50 p-4 rounded-lg overflow-x-auto whitespace-pre-wrap">
            {results.runtime_error}
          </pre>
        </div>
      </div>
    )
  }

  const allPassed = results.success
  const isSubmitResponse = 'submission_id' in results

  return (
    <div className="h-full overflow-y-auto bg-gray-800">
      <div className="p-4">
        {/* Summary Header */}
        <div className={`rounded-lg p-4 mb-4 border ${
          allPassed
            ? 'bg-green-500/10 border-green-500/40'
            : 'bg-red-500/10 border-red-500/40'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {allPassed ? (
                <CheckCircle2 className="w-6 h-6 text-green-400" />
              ) : (
                <XCircle className="w-6 h-6 text-red-400" />
              )}
              <span className={`text-lg font-bold ${
                allPassed ? 'text-green-400' : 'text-red-400'
              }`}>
                {allPassed ? 'Accepted' : 'Wrong Answer'}
              </span>
            </div>
            <span className="font-mono text-sm text-gray-300">
              {results.summary.passed}/{results.summary.total} tests passed
            </span>
          </div>

          {/* Progress info for Submit responses */}
          {isSubmitResponse && results.times_solved !== undefined && (
            <div className="mt-3 pt-3 border-t border-gray-700 flex items-center gap-4">
              <span className="text-sm text-gray-400">
                Times Solved: <span className="text-cyan-400 font-semibold">{results.times_solved}</span>
              </span>
              {results.is_mastered && (
                <span className="text-green-400 font-semibold text-sm">✓ Mastered!</span>
              )}
              {results.next_review_date && !results.is_mastered && (
                <span className="text-sm text-gray-400">
                  Next Review: {new Date(results.next_review_date).toLocaleDateString()}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Individual Test Results */}
        <div className="space-y-3">
          {results.results.map((result: TestResult, index: number) => (
            <TestCaseResult key={index} result={result} index={index} />
          ))}
        </div>
      </div>
    </div>
  )
}

function TestCaseResult({ result, index }: { result: TestResult; index: number }) {
  return (
    <div className={`rounded-lg border p-4 ${
      result.passed
        ? 'bg-green-500/5 border-green-500/30'
        : 'bg-red-500/5 border-red-500/30'
    }`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {result.passed ? (
            <CheckCircle2 className="w-4 h-4 text-green-400" />
          ) : (
            <XCircle className="w-4 h-4 text-red-400" />
          )}
          <span className="font-mono text-sm font-semibold text-gray-200">
            Case {index + 1}
          </span>
        </div>
        <span className={`text-xs font-mono font-semibold px-2 py-0.5 rounded ${
          result.passed
            ? 'bg-green-500/20 text-green-400'
            : 'bg-red-500/20 text-red-400'
        }`}>
          {result.passed ? 'PASSED' : 'FAILED'}
        </span>
      </div>

      {/* Test Details - LeetCode style */}
      <div className="space-y-3 font-mono text-sm">
        {/* Input */}
        {result.input !== undefined && (
          <div>
            <span className="text-gray-500 text-xs uppercase tracking-wider block mb-1">Input</span>
            <pre className="p-2 bg-gray-900 rounded text-cyan-400 overflow-x-auto">
              {JSON.stringify(result.input, null, 2)}
            </pre>
          </div>
        )}

        {/* Output (User's result) */}
        <div>
          <span className="text-gray-500 text-xs uppercase tracking-wider block mb-1">Output</span>
          <pre className={`p-2 rounded overflow-x-auto ${
            result.passed
              ? 'bg-gray-900 text-green-400'
              : 'bg-gray-900 text-red-400'
          }`}>
            {result.output !== undefined ? JSON.stringify(result.output, null, 2) : 'null'}
          </pre>
        </div>

        {/* Expected */}
        <div>
          <span className="text-gray-500 text-xs uppercase tracking-wider block mb-1">Expected</span>
          <pre className="p-2 bg-gray-900 rounded text-green-400 overflow-x-auto">
            {JSON.stringify(result.expected, null, 2)}
          </pre>
        </div>

        {/* Stdout - if user has print statements */}
        {result.stdout && (
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Terminal className="w-3 h-3 text-gray-500" />
              <span className="text-gray-500 text-xs uppercase tracking-wider">Stdout</span>
            </div>
            <pre className="p-2 bg-gray-900 rounded text-yellow-400 overflow-x-auto whitespace-pre-wrap">
              {result.stdout}
            </pre>
          </div>
        )}

        {/* Error - if there was a runtime error for this test */}
        {result.error && (
          <div>
            <span className="text-red-400 text-xs uppercase tracking-wider block mb-1">Error</span>
            <pre className="p-2 bg-red-900/20 border border-red-500/30 rounded text-red-300 overflow-x-auto whitespace-pre-wrap text-xs">
              {result.error_type && <span className="font-semibold">{result.error_type}: </span>}
              {result.error}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}
