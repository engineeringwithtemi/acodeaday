import { CheckCircle2, XCircle, Loader2, Clock } from 'lucide-react'
import type { TestCaseResult } from '../types/api'

interface TestResultsProps {
  testResults?: TestCaseResult[]
  isRunning?: boolean
  runtime?: number | null
}

export function TestResults({
  testResults,
  isRunning = false,
  runtime,
}: TestResultsProps) {
  if (isRunning) {
    return (
      <div className="h-full flex items-center justify-center bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 text-cyan-400 animate-spin" />
          <p className="text-zinc-400 font-mono text-sm tracking-wide">
            Running tests...
          </p>
        </div>
      </div>
    )
  }

  if (!testResults || testResults.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950">
        <div className="text-center px-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-zinc-800/50 border border-zinc-700 flex items-center justify-center">
            <Clock className="w-8 h-8 text-zinc-600" />
          </div>
          <p className="text-zinc-500 font-mono text-sm">
            Run your code to see test results
          </p>
        </div>
      </div>
    )
  }

  const passedCount = testResults.filter((result) => result.passed).length
  const totalCount = testResults.length
  const allPassed = passedCount === totalCount

  return (
    <div className="h-full overflow-y-auto bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 text-zinc-100">
      <div className="p-6">
        {/* Header */}
        <div className="mb-6 pb-4 border-b border-zinc-800">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-mono font-semibold text-white">
              Test Results
            </h2>
            {runtime !== null && runtime !== undefined && (
              <div className="flex items-center gap-2 text-xs font-mono text-zinc-400">
                <Clock className="w-4 h-4" />
                <span>{runtime}ms</span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-3">
            <div
              className={`px-4 py-2 rounded-lg font-mono text-sm font-semibold ${
                allPassed
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
              }`}
            >
              {passedCount} / {totalCount} Passed
            </div>
            {allPassed && (
              <div className="flex items-center gap-2 text-emerald-400">
                <CheckCircle2 className="w-5 h-5 animate-pulse" />
                <span className="text-sm font-mono">All tests passed!</span>
              </div>
            )}
          </div>
        </div>

        {/* Test Cases */}
        <div className="space-y-4">
          {testResults.map((result, idx) => (
            <div
              key={result.test_case_id}
              className={`rounded-lg p-4 border backdrop-blur-sm transition-all ${
                result.passed
                  ? 'bg-emerald-500/5 border-emerald-500/30 hover:border-emerald-500/50'
                  : 'bg-rose-500/5 border-rose-500/30 hover:border-rose-500/50'
              }`}
            >
              <div className="flex items-start gap-3 mb-3">
                {result.passed ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400 mt-0.5 flex-shrink-0" />
                ) : (
                  <XCircle className="w-5 h-5 text-rose-400 mt-0.5 flex-shrink-0" />
                )}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={`text-sm font-mono font-semibold ${
                        result.passed ? 'text-emerald-300' : 'text-rose-300'
                      }`}
                    >
                      Test Case {idx + 1}
                    </span>
                    <span
                      className={`text-xs font-mono px-2 py-0.5 rounded ${
                        result.passed
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : 'bg-rose-500/20 text-rose-300'
                      }`}
                    >
                      {result.passed ? 'PASS' : 'FAIL'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="pl-8 space-y-2 font-mono text-sm">
                <div className="flex flex-col gap-1">
                  <span className="text-zinc-500 text-xs uppercase tracking-wider">
                    Expected
                  </span>
                  <code className="text-emerald-300 bg-emerald-400/5 px-3 py-1.5 rounded border border-emerald-500/20 block overflow-x-auto">
                    {JSON.stringify(result.expected)}
                  </code>
                </div>
                <div className="flex flex-col gap-1">
                  <span className="text-zinc-500 text-xs uppercase tracking-wider">
                    Actual
                  </span>
                  <code
                    className={`px-3 py-1.5 rounded border block overflow-x-auto ${
                      result.passed
                        ? 'text-emerald-300 bg-emerald-400/5 border-emerald-500/20'
                        : 'text-rose-300 bg-rose-400/5 border-rose-500/20'
                    }`}
                  >
                    {JSON.stringify(result.actual)}
                  </code>
                </div>
                {result.error && (
                  <div className="flex flex-col gap-1 pt-2 border-t border-zinc-800">
                    <span className="text-rose-400 text-xs uppercase tracking-wider">
                      Error
                    </span>
                    <pre className="text-rose-300 bg-rose-400/5 px-3 py-1.5 rounded border border-rose-500/20 text-xs overflow-x-auto">
                      {result.error}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
