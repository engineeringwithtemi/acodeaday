import { createFileRoute } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { Allotment } from 'allotment'
import 'allotment/dist/style.css'
import { Play, Send, Loader2, AlertCircle } from 'lucide-react'
import { useProblem, useSubmitCode, useRunCode, useSubmissions } from '@/hooks'
import { ProblemDescription } from '@/components/ProblemDescription'
import { TestCasesPanel } from '@/components/TestCasesPanel'
import { TestResults } from '@/components/TestResults'
import Editor from '@monaco-editor/react'
import type { RunCodeResponse, SubmitCodeResponse, SubmissionSchema } from '@/types/api'

export const Route = createFileRoute('/problem/$slug')({
  component: ProblemSolver,
})

function ProblemSolver() {
  const { slug } = Route.useParams()
  const { data: problem, isLoading, error } = useProblem(slug)
  const submitCode = useSubmitCode()
  const runCode = useRunCode()

  const [code, setCode] = useState('')
  const [language] = useState('python')
  const [testResults, setTestResults] = useState<RunCodeResponse | SubmitCodeResponse | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [leftPaneTab, setLeftPaneTab] = useState<'description' | 'submissions'>('description')
  const [bottomPaneTab, setBottomPaneTab] = useState<'testcase' | 'result'>('testcase')
  const [customInputs, setCustomInputs] = useState<any[][]>([])

  // Initialize code with starter code when problem loads
  useEffect(() => {
    if (problem?.languages?.[0]?.starter_code) {
      setCode(problem.languages[0].starter_code)
    }
  }, [problem])

  const handleRunCode = async () => {
    if (!problem) return
    setIsRunning(true)
    setTestResults(null)
    setBottomPaneTab('result') // Switch to result tab

    try {
      const result = await runCode.mutateAsync({
        problem_slug: slug,
        code,
        language,
        custom_input: customInputs.length > 0 ? customInputs : undefined,
      })
      setTestResults(result)
    } catch (err) {
      console.error('Run code error:', err)
    } finally {
      setIsRunning(false)
    }
  }

  const handleSubmit = async () => {
    if (!problem) return
    setIsRunning(true)
    setTestResults(null)
    setBottomPaneTab('result') // Switch to result tab

    try {
      const result = await submitCode.mutateAsync({
        problem_slug: slug,
        code,
        language,
      })
      setTestResults(result)
    } catch (err) {
      console.error('Submit error:', err)
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
        {/* Left Pane: Description + Submissions */}
        <Allotment.Pane minSize={300}>
          <div className="h-full flex flex-col bg-gray-900">
            {/* Tab Header */}
            <div className="flex border-b border-gray-700 bg-gray-800">
              <button
                onClick={() => setLeftPaneTab('description')}
                className={`px-4 py-2 text-sm font-semibold ${
                  leftPaneTab === 'description'
                    ? 'text-cyan-400 border-b-2 border-cyan-400'
                    : 'text-gray-400 hover:text-gray-300'
                }`}
              >
                Description
              </button>
              <button
                onClick={() => setLeftPaneTab('submissions')}
                className={`px-4 py-2 text-sm font-semibold ${
                  leftPaneTab === 'submissions'
                    ? 'text-cyan-400 border-b-2 border-cyan-400'
                    : 'text-gray-400 hover:text-gray-300'
                }`}
              >
                Submissions
              </button>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-hidden">
              {leftPaneTab === 'description' ? (
                <ProblemDescription problem={problem} />
              ) : (
                <SubmissionsPanel problemId={problem.id} />
              )}
            </div>
          </div>
        </Allotment.Pane>

        {/* Right Pane: Code Editor + Test Cases/Results */}
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

            {/* Bottom: Test Cases / Results (LeetCode style tabs) */}
            <Allotment.Pane minSize={100}>
              <div className="h-full flex flex-col bg-gray-800">
                {/* Bottom Tabs */}
                <div className="flex border-b border-gray-700 bg-gray-800">
                  <button
                    onClick={() => setBottomPaneTab('testcase')}
                    className={`px-4 py-2 text-sm font-semibold ${
                      bottomPaneTab === 'testcase'
                        ? 'text-cyan-400 border-b-2 border-cyan-400'
                        : 'text-gray-400 hover:text-gray-300'
                    }`}
                  >
                    Testcase
                  </button>
                  <button
                    onClick={() => setBottomPaneTab('result')}
                    className={`px-4 py-2 text-sm font-semibold ${
                      bottomPaneTab === 'result'
                        ? 'text-cyan-400 border-b-2 border-cyan-400'
                        : 'text-gray-400 hover:text-gray-300'
                    }`}
                  >
                    Test Result
                  </button>
                </div>

                {/* Bottom Content */}
                <div className="flex-1 overflow-hidden">
                  {bottomPaneTab === 'testcase' ? (
                    <TestCasesPanel
                      testCases={problem.test_cases || []}
                      onCustomTestCasesChange={setCustomInputs}
                    />
                  ) : (
                    <TestResults results={testResults} isRunning={isRunning} />
                  )}
                </div>
              </div>
            </Allotment.Pane>
          </Allotment>
        </Allotment.Pane>
      </Allotment>
    </div>
  )
}

// Submissions Panel Component
function SubmissionsPanel({ problemId }: { problemId: string }) {
  const { data: submissions, isLoading } = useSubmissions(problemId)

  if (isLoading) {
    return (
      <div className="h-full overflow-y-auto bg-gray-900 text-white p-6 flex items-center justify-center">
        <Loader2 className="animate-spin text-cyan-400" size={24} />
      </div>
    )
  }

  if (!submissions || submissions.length === 0) {
    return (
      <div className="h-full overflow-y-auto bg-gray-900 text-white p-6">
        <p className="text-gray-400">No submissions yet. Submit your code to see history here.</p>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-900 text-white p-6">
      <h2 className="text-xl font-bold mb-4 text-cyan-400">Submission History</h2>
      <div className="space-y-3">
        {submissions.map((submission: SubmissionSchema) => (
          <div
            key={submission.id}
            className={`rounded-lg p-4 border ${
              submission.passed
                ? 'bg-green-500/5 border-green-500/30'
                : 'bg-red-500/5 border-red-500/30'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className={`text-sm font-semibold ${
                submission.passed ? 'text-green-400' : 'text-red-400'
              }`}>
                {submission.passed ? 'Accepted' : 'Failed'}
              </span>
              <span className="text-xs text-gray-400">
                {new Date(submission.submitted_at).toLocaleString()}
              </span>
            </div>
            <div className="text-xs text-gray-400 space-y-1">
              <div>Language: <span className="text-gray-300">{submission.language}</span></div>
              {submission.runtime_ms && (
                <div>Runtime: <span className="text-gray-300">{submission.runtime_ms} ms</span></div>
              )}
            </div>
            <details className="mt-2">
              <summary className="text-xs text-cyan-400 cursor-pointer hover:text-cyan-300">
                View Code
              </summary>
              <pre className="mt-2 p-2 bg-gray-900 rounded text-xs text-gray-300 overflow-x-auto">
                {submission.code}
              </pre>
            </details>
          </div>
        ))}
      </div>
    </div>
  )
}
