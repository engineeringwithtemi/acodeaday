import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { Allotment } from 'allotment'
import 'allotment/dist/style.css'
import { Play, Send, Loader2, AlertCircle } from 'lucide-react'
import { useProblem, useSubmitCode } from '@/hooks'
import Editor from '@monaco-editor/react'

export const Route = createFileRoute('/problem/$slug')({
  component: ProblemSolver,
})

function ProblemSolver() {
  const { slug } = Route.useParams()
  const { data: problem, isLoading, error } = useProblem(slug)
  const submitCode = useSubmitCode()

  const [code, setCode] = useState('')
  const [language] = useState('python')
  const [testResults, setTestResults] = useState<any>(null)
  const [isRunning, setIsRunning] = useState(false)

  // Initialize code with starter code when problem loads
  useState(() => {
    if (problem) {
      // Assuming the API returns the problem with language data
      // This might need adjustment based on actual API response
      setCode((problem as any).starter_code || '# Write your solution here')
    }
  })

  const handleRunCode = async () => {
    if (!problem) return
    setIsRunning(true)
    setTestResults(null)

    try {
      // For "Run Code", we might need a different endpoint or use submit with a flag
      // For now, using the same submit endpoint
      const result = await submitCode.mutateAsync({
        problem_id: problem.id,
        language,
        code,
      })
      setTestResults(result)
    } catch (err) {
      setTestResults({
        error: (err as Error).message || 'Failed to run code',
      })
    } finally {
      setIsRunning(false)
    }
  }

  const handleSubmit = async () => {
    if (!problem) return
    setIsRunning(true)
    setTestResults(null)

    try {
      const result = await submitCode.mutateAsync({
        problem_id: problem.id,
        language,
        code,
      })
      setTestResults(result)
    } catch (err) {
      setTestResults({
        error: (err as Error).message || 'Failed to submit code',
      })
    } finally {
      setIsRunning(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400 text-lg">Loading problem...</p>
        </div>
      </div>
    )
  }

  if (error || !problem) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center p-6">
        <div className="max-w-2xl w-full bg-red-500/10 border border-red-500/50 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-2">
            <AlertCircle className="text-red-400" size={24} />
            <h2 className="text-xl font-bold text-red-400">Error Loading Problem</h2>
          </div>
          <p className="text-gray-300">{error ? (error as Error).message : 'Problem not found'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Full-height split pane */}
      <Allotment defaultSizes={[40, 60]}>
        {/* Left Pane: Problem Description */}
        <Allotment.Pane minSize={300}>
          <ProblemDescription problem={problem} />
        </Allotment.Pane>

        {/* Right Pane: Code Editor + Test Results */}
        <Allotment.Pane minSize={400}>
          <Allotment vertical defaultSizes={[70, 30]}>
            {/* Top: Code Editor */}
            <Allotment.Pane minSize={200}>
              <div className="h-full flex flex-col bg-gray-900">
                {/* Editor Header */}
                <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-gray-300">Code Editor</span>
                    <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs font-semibold">
                      Python
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleRunCode}
                      disabled={isRunning}
                      className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isRunning ? (
                        <>
                          <Loader2 size={16} className="animate-spin" />
                          Running...
                        </>
                      ) : (
                        <>
                          <Play size={16} />
                          Run Code
                        </>
                      )}
                    </button>
                    <button
                      onClick={handleSubmit}
                      disabled={isRunning}
                      className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white text-sm font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isRunning ? (
                        <>
                          <Loader2 size={16} className="animate-spin" />
                          Submitting...
                        </>
                      ) : (
                        <>
                          <Send size={16} />
                          Submit
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Monaco Editor */}
                <div className="flex-1">
                  <Editor
                    height="100%"
                    defaultLanguage="python"
                    theme="vs-dark"
                    value={code}
                    onChange={(value) => setCode(value || '')}
                    options={{
                      minimap: { enabled: false },
                      fontSize: 14,
                      lineNumbers: 'on',
                      scrollBeyondLastLine: false,
                      automaticLayout: true,
                      tabSize: 4,
                      wordWrap: 'on',
                    }}
                  />
                </div>
              </div>
            </Allotment.Pane>

            {/* Bottom: Test Results */}
            <Allotment.Pane minSize={100}>
              <TestResults results={testResults} />
            </Allotment.Pane>
          </Allotment>
        </Allotment.Pane>
      </Allotment>
    </div>
  )
}

function ProblemDescription({ problem }: { problem: any }) {
  const difficultyColors = {
    easy: 'text-green-400 bg-green-500/20',
    medium: 'text-yellow-400 bg-yellow-500/20',
    hard: 'text-red-400 bg-red-500/20',
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-900 text-white">
      <div className="p-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-sm font-semibold text-gray-400">
              #{problem.sequence_number}
            </span>
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${difficultyColors[problem.difficulty]}`}>
              {problem.difficulty}
            </span>
          </div>
          <h1 className="text-3xl font-black text-white mb-3">{problem.title}</h1>
          <p className="text-sm text-gray-400">
            Pattern: <span className="text-cyan-400 font-semibold">{problem.pattern}</span>
          </p>
        </div>

        {/* Description */}
        <div className="mb-6">
          <h2 className="text-xl font-bold mb-3 text-cyan-400">Description</h2>
          <div className="text-gray-300 leading-relaxed whitespace-pre-wrap">
            {problem.description}
          </div>
        </div>

        {/* Examples */}
        {problem.examples && problem.examples.length > 0 && (
          <div className="mb-6">
            <h2 className="text-xl font-bold mb-3 text-cyan-400">Examples</h2>
            {problem.examples.map((example: any, index: number) => (
              <div key={index} className="mb-4 bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                <p className="text-sm font-semibold text-gray-400 mb-2">Example {index + 1}:</p>
                <div className="space-y-2">
                  <div>
                    <span className="text-sm font-semibold text-gray-400">Input:</span>
                    <pre className="mt-1 p-2 bg-gray-900 rounded text-cyan-400 text-sm overflow-x-auto">
                      {example.input}
                    </pre>
                  </div>
                  <div>
                    <span className="text-sm font-semibold text-gray-400">Output:</span>
                    <pre className="mt-1 p-2 bg-gray-900 rounded text-green-400 text-sm overflow-x-auto">
                      {example.output}
                    </pre>
                  </div>
                  {example.explanation && (
                    <div>
                      <span className="text-sm font-semibold text-gray-400">Explanation:</span>
                      <p className="mt-1 text-sm text-gray-300">{example.explanation}</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Constraints */}
        {problem.constraints && problem.constraints.length > 0 && (
          <div>
            <h2 className="text-xl font-bold mb-3 text-cyan-400">Constraints</h2>
            <ul className="list-disc list-inside space-y-1 text-gray-300">
              {problem.constraints.map((constraint: string, index: number) => (
                <li key={index} className="text-sm">{constraint}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

function TestResults({ results }: { results: any }) {
  if (!results) {
    return (
      <div className="h-full bg-gray-800 p-4 overflow-y-auto">
        <p className="text-gray-400 text-sm">
          Run your code or submit to see test results...
        </p>
      </div>
    )
  }

  if (results.error) {
    return (
      <div className="h-full bg-gray-800 p-4 overflow-y-auto">
        <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="text-red-400" size={20} />
            <span className="font-semibold text-red-400">Error</span>
          </div>
          <p className="text-sm text-gray-300">{results.error}</p>
        </div>
      </div>
    )
  }

  const passedCount = results.test_results?.filter((r: any) => r.passed).length || 0
  const totalCount = results.test_results?.length || 0
  const allPassed = results.is_passed

  return (
    <div className="h-full bg-gray-800 p-4 overflow-y-auto">
      {/* Summary */}
      <div className={`rounded-lg p-4 mb-4 ${allPassed ? 'bg-green-500/10 border border-green-500/50' : 'bg-red-500/10 border border-red-500/50'}`}>
        <div className="flex items-center justify-between mb-2">
          <span className={`font-bold text-lg ${allPassed ? 'text-green-400' : 'text-red-400'}`}>
            {allPassed ? 'All Tests Passed!' : 'Some Tests Failed'}
          </span>
          <span className="text-sm font-semibold text-gray-300">
            {passedCount} / {totalCount} passed
          </span>
        </div>
        {results.runtime_ms && (
          <p className="text-sm text-gray-400">Runtime: {results.runtime_ms}ms</p>
        )}
      </div>

      {/* Individual Test Results */}
      <div className="space-y-2">
        {results.test_results?.map((result: any, index: number) => (
          <div
            key={index}
            className={`rounded-lg p-3 border ${result.passed ? 'bg-green-500/5 border-green-500/30' : 'bg-red-500/5 border-red-500/30'}`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-gray-300">Test Case {index + 1}</span>
              <span className={`text-xs font-semibold ${result.passed ? 'text-green-400' : 'text-red-400'}`}>
                {result.passed ? 'PASSED' : 'FAILED'}
              </span>
            </div>
            {!result.passed && (
              <div className="text-xs space-y-1">
                <div>
                  <span className="text-gray-400">Expected: </span>
                  <span className="text-gray-300 font-mono">{JSON.stringify(result.expected)}</span>
                </div>
                <div>
                  <span className="text-gray-400">Got: </span>
                  <span className="text-gray-300 font-mono">{JSON.stringify(result.actual)}</span>
                </div>
                {result.error && (
                  <div>
                    <span className="text-red-400">Error: </span>
                    <span className="text-gray-300 font-mono">{result.error}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
