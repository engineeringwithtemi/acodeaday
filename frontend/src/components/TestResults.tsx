import { CheckCircle2, XCircle, Loader2, Clock, AlertCircle, Terminal, Copy, Check } from 'lucide-react'
import { useState } from 'react'
import type { RunCodeResponse, SubmitCodeResponse, TestResult, FunctionSignature } from '../types/api'

interface TestResultsProps {
  results: RunCodeResponse | SubmitCodeResponse | null
  isRunning?: boolean
  functionSignature?: FunctionSignature
}

export function TestResults({
  results,
  isRunning = false,
  functionSignature,
}: TestResultsProps) {
  const [activeTab, setActiveTab] = useState(0)

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
    <div className="h-full flex flex-col bg-gray-800">
      {/* Summary Header */}
      <div className="p-4 border-b border-gray-700">
        <div className={`rounded-lg p-4 border ${
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
      </div>

      {/* Test Case Tabs - LeetCode style */}
      <div className="flex items-center border-b border-gray-700 bg-gray-800 px-2 overflow-x-auto">
        {results.results.map((result: TestResult, index: number) => (
          <button
            key={index}
            onClick={() => setActiveTab(index)}
            className={`px-3 py-2 text-xs font-semibold whitespace-nowrap transition-colors flex items-center gap-2 ${
              activeTab === index
                ? 'text-cyan-400 border-b-2 border-cyan-400'
                : 'text-gray-400 hover:text-gray-300'
            }`}
          >
            {result.passed ? (
              <CheckCircle2 className="w-3 h-3 text-green-400" />
            ) : (
              <XCircle className="w-3 h-3 text-red-400" />
            )}
            Case {index + 1}
          </button>
        ))}
      </div>

      {/* Active Test Case Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {results.results[activeTab] && (
          <TestCaseResult
            result={results.results[activeTab]}
            index={activeTab}
            functionSignature={functionSignature}
          />
        )}
      </div>
    </div>
  )
}

interface TestCaseResultProps {
  result: TestResult
  index: number
  functionSignature?: FunctionSignature
}

function TestCaseResult({ result, index, functionSignature }: TestCaseResultProps) {
  const [copiedField, setCopiedField] = useState<string | null>(null)

  const formatValue = (value: any): string => {
    return JSON.stringify(value)
  }

  const copyToClipboard = async (value: string, field: string) => {
    await navigator.clipboard.writeText(value)
    setCopiedField(field)
    setTimeout(() => setCopiedField(null), 2000)
  }

  // Get param names from function signature
  const paramNames = functionSignature?.params?.map(p => p.name) || []

  return (
    <div className="space-y-3 font-mono text-sm">
      {/* Input - each param displayed separately */}
      {result.input !== undefined && (
        <div>
          <span className="text-gray-500 text-xs uppercase tracking-wider block mb-2">Input</span>
          <div className="space-y-2">
            {Array.isArray(result.input) ? (
              result.input.map((value, i) => {
                const paramName = paramNames[i] || `arg${i}`
                const formattedValue = formatValue(value)
                return (
                  <div key={i} className="relative group">
                    <div className="p-3 bg-gray-900 rounded">
                      <span className="text-gray-400">{paramName} =</span>
                      <div className="mt-1 text-white">{formattedValue}</div>
                    </div>
                    <button
                      onClick={() => copyToClipboard(formattedValue, `input-${i}`)}
                      className="absolute top-2 right-2 p-1 text-gray-500 hover:text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Copy"
                    >
                      {copiedField === `input-${i}` ? (
                        <Check className="w-4 h-4 text-green-400" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                )
              })
            ) : (
              <div className="p-3 bg-gray-900 rounded text-white">
                {formatValue(result.input)}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Output (User's result) */}
      <div>
        <span className="text-gray-500 text-xs uppercase tracking-wider block mb-2">Output</span>
        <div className="p-3 bg-gray-900 rounded">
          <span className={result.passed ? 'text-green-400' : 'text-red-400'}>
            {result.output !== undefined ? formatValue(result.output) : 'null'}
          </span>
        </div>
      </div>

      {/* Expected */}
      <div>
        <span className="text-gray-500 text-xs uppercase tracking-wider block mb-2">Expected</span>
        <div className="p-3 bg-gray-900 rounded">
          <span className="text-green-400">{formatValue(result.expected)}</span>
        </div>
      </div>

      {/* Stdout - if user has print statements */}
      {result.stdout && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Terminal className="w-3 h-3 text-gray-500" />
            <span className="text-gray-500 text-xs uppercase tracking-wider">Stdout</span>
          </div>
          <pre className="p-3 bg-gray-900 rounded text-yellow-400 overflow-x-auto whitespace-pre-wrap">
            {result.stdout}
          </pre>
        </div>
      )}

      {/* Error - if there was a runtime error for this test */}
      {result.error && (
        <div>
          <span className="text-red-400 text-xs uppercase tracking-wider block mb-2">Error</span>
          <pre className="p-3 bg-red-900/20 border border-red-500/30 rounded text-red-300 overflow-x-auto whitespace-pre-wrap text-xs">
            {result.error_type && <span className="font-semibold">{result.error_type}: </span>}
            {result.error}
          </pre>
        </div>
      )}
    </div>
  )
}
