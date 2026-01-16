import { createFileRoute } from '@tanstack/react-router'
import { useState, useEffect, useRef } from 'react'
import { Allotment } from 'allotment'
import 'allotment/dist/style.css'
import { Play, Send, Loader2, AlertCircle, RotateCcw, MessageSquare } from 'lucide-react'
import { useProblem, useSubmitCode, useRunCode, useSaveCode, useResetCode, useLoadSubmissionCode } from '@/hooks'
import { ProblemDescription } from '@/components/ProblemDescription'
import { TestCasesPanel } from '@/components/TestCasesPanel'
import { TestResults } from '@/components/TestResults'
import { SubmissionsPanel } from '@/components/SubmissionsPanel'
import { SubmissionResultPanel } from '@/components/SubmissionResultPanel'
import { ChatPanel } from '@/components/ChatPanel'
import { SolutionsPanel } from '@/components/SolutionsPanel'
import Editor from '@monaco-editor/react'
import { useQueryClient } from '@tanstack/react-query'
import type { RunCodeResponse, SubmitCodeResponse, SubmissionSchema, TestResult } from '@/types/api'

export const Route = createFileRoute('/problem/$slug')({
  component: ProblemSolver,
})

function ProblemSolver() {
  const { slug } = Route.useParams()
  const { data: problem, isLoading, error } = useProblem(slug)
  const submitCode = useSubmitCode()
  const runCode = useRunCode()
  const saveCode = useSaveCode()
  const resetCodeMutation = useResetCode()
  const loadSubmissionCode = useLoadSubmissionCode()
  const queryClient = useQueryClient()

  const [language] = useState('python')
  const [testResults, setTestResults] = useState<RunCodeResponse | SubmitCodeResponse | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [leftPaneTab, setLeftPaneTab] = useState<'description' | 'submissions' | 'solutions'>('description')
  const [bottomPaneTab, setBottomPaneTab] = useState<'testcase' | 'result'>('testcase')
  const [customInputs, setCustomInputs] = useState<any[][]>([])
  const [showSubmissionResult, setShowSubmissionResult] = useState(false)
  const [submissionResult, setSubmissionResult] = useState<SubmitCodeResponse | null>(null)
  const [submittedCode, setSubmittedCode] = useState<string>('')
  const [showAIChat, setShowAIChat] = useState(false)
  const [chatInitialMessage, setChatInitialMessage] = useState<string | null>(null)
  const [chatInitialTitle, setChatInitialTitle] = useState<string | null>(null)

  // Get starter code from problem data
  const starterCode = problem?.languages?.[0]?.starter_code || ''

  // Track if we've already handled the initial "due" state for this problem
  // This prevents clearing the editor on subsequent refetches after user actions
  const hasHandledDueState = useRef(false)

  // Get initial code:
  // - If problem is due for review, show starter code (spaced repetition: fresh start)
  // - Otherwise, show user's saved code or starter code
  const getInitialCode = () => {
    if (!problem) return starterCode
    if (problem.is_due && !hasHandledDueState.current) {
      return starterCode
    }
    return problem.user_code ?? starterCode
  }

  const initialCode = getInitialCode()

  // Track code in state
  const [code, setCode] = useState(initialCode)

  // Track the last saved/loaded code to avoid unnecessary saves
  const lastSavedCode = useRef<string | null>(null)

  // Update code when problem data changes (e.g., after reset or load submission)
  useEffect(() => {
    if (problem) {
      // On first load of a due problem, use starter code
      if (problem.is_due && !hasHandledDueState.current) {
        hasHandledDueState.current = true
        setCode(starterCode)
        lastSavedCode.current = starterCode
      } else if (!hasHandledDueState.current) {
        // First load of a non-due problem
        hasHandledDueState.current = true
        const newCode = problem.user_code ?? starterCode
        setCode(newCode)
        lastSavedCode.current = newCode
      }
      // After initial load, don't update code from query (user may have edited)
    }
  }, [problem?.id, problem?.is_due, problem?.user_code, starterCode])

  // Auto-save code to server with 500ms debounce
  useEffect(() => {
    // Skip if no problem loaded yet
    if (!problem) return

    // Skip if code matches last saved (nothing to save)
    if (code === lastSavedCode.current) return

    const timer = setTimeout(() => {
      saveCode.mutate({
        problem_slug: slug,
        language,
        code,
      })
      lastSavedCode.current = code // Update last saved
    }, 500)

    return () => clearTimeout(timer)
  }, [code, slug, language, problem])

  // Reset code to starter code
  const handleResetCode = async () => {
    if (!confirm('Reset code to starter template? Your changes will be lost.')) return

    try {
      await resetCodeMutation.mutateAsync({
        problem_slug: slug,
        language,
      })
      // Update local state directly (don't rely on query refetch)
      setCode(starterCode)
      lastSavedCode.current = starterCode
    } catch (err) {
      console.error('Reset code error:', err)
    }
  }

  // Load code from a past submission
  const handleLoadSubmissionCode = async (submissionCode: string) => {
    try {
      await loadSubmissionCode.mutateAsync({
        problem_slug: slug,
        code: submissionCode,
        language,
      })
      // Update local state directly (don't rely on query refetch)
      setCode(submissionCode)
      lastSavedCode.current = submissionCode
      setShowSubmissionResult(false)
    } catch (err) {
      console.error('Load submission code error:', err)
    }
  }

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

    try {
      const result = await submitCode.mutateAsync({
        problem_slug: slug,
        code,
        language,
      })

      // Show submission result panel (modal)
      setSubmissionResult(result)
      setSubmittedCode(code)
      setShowSubmissionResult(true)

      // Switch to Submissions tab
      setLeftPaneTab('submissions')

      // Refetch submissions list
      queryClient.invalidateQueries({ queryKey: ['submissions', problem.id] })
    } catch (err) {
      console.error('Submit error:', err)
    } finally {
      setIsRunning(false)
    }
  }

  const handleCloseSubmissionResult = () => {
    setShowSubmissionResult(false)
    setSubmissionResult(null)
    setSubmittedCode('')
  }

  const handleSubmissionClick = (submission: SubmissionSchema) => {
    // Build results array from stored first failed test (if any)
    const results: TestResult[] = []
    if (submission.failed_test_number !== null) {
      results.push({
        test_number: submission.failed_test_number,
        passed: false,
        input: submission.failed_input,
        output: submission.failed_output,
        expected: submission.failed_expected,
      })
    }

    // Convert SubmissionSchema to SubmitCodeResponse format
    const resultFromSubmission: SubmitCodeResponse = {
      success: submission.passed,
      results,
      summary: {
        total: submission.passed_count + (submission.failed_test_number !== null ? 1 : 0),
        passed: submission.passed_count,
        failed: submission.failed_test_number !== null ? 1 : 0,
      },
      total_test_cases: submission.total_test_cases,
      submission_id: submission.id,
      runtime_ms: submission.runtime_ms ?? undefined,
      memory_kb: submission.memory_kb ?? undefined,
    }

    setSubmissionResult(resultFromSubmission)
    setSubmittedCode(submission.code)
    setShowSubmissionResult(true)
  }

  // Handle loading reference solution to editor
  const handleLoadSolutionToEditor = (solutionCode: string, solutionLanguage: string) => {
    if (!confirm('Load reference solution to editor? Your current code will be replaced.')) return
    setCode(solutionCode)
    // Save to server
    saveCode.mutate({
      problem_slug: slug,
      language: solutionLanguage,
      code: solutionCode,
    })
  }

  // Handle asking AI about a solution
  const handleAskAIAboutSolution = (solutionCode: string, solutionLanguage: string) => {
    const message = `Please explain this reference solution step by step. Help me understand the approach, time/space complexity, and any key insights:

\`\`\`${solutionLanguage}
${solutionCode}
\`\`\``
    setChatInitialMessage(message)
    setChatInitialTitle('Reference Solution Help')
    setShowAIChat(true)
  }

  // Clear initial message after it's been sent
  const handleInitialMessageSent = () => {
    setChatInitialMessage(null)
    setChatInitialTitle(null)
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
      {/* Full-height split pane - key forces re-render when pane count changes */}
      <Allotment key={showAIChat ? 'with-chat' : 'no-chat'} defaultSizes={showAIChat ? [35, 45, 20] : [40, 60]}>
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
              <button
                onClick={() => setLeftPaneTab('solutions')}
                className={`px-4 py-2 text-sm font-semibold ${
                  leftPaneTab === 'solutions'
                    ? 'text-cyan-400 border-b-2 border-cyan-400'
                    : 'text-gray-400 hover:text-gray-300'
                }`}
              >
                Solutions
              </button>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-hidden">
              {leftPaneTab === 'description' ? (
                <ProblemDescription problem={problem} />
              ) : leftPaneTab === 'submissions' ? (
                <SubmissionsPanel
                  problemId={problem.id}
                  onSubmissionClick={handleSubmissionClick}
                />
              ) : (
                <SolutionsPanel
                  languages={problem.languages || []}
                  onLoadToEditor={handleLoadSolutionToEditor}
                  onAskAI={handleAskAIAboutSolution}
                />
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
                      onClick={() => setShowAIChat(!showAIChat)}
                      className={`flex items-center gap-2 px-3 py-2 text-sm font-semibold rounded-lg transition-colors ${
                        showAIChat
                          ? 'bg-cyan-600 hover:bg-cyan-700 text-white'
                          : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                      }`}
                      title="Toggle AI Assistant"
                    >
                      <MessageSquare size={16} />
                      AI Help
                    </button>
                    <button
                      onClick={handleResetCode}
                      disabled={isRunning || resetCodeMutation.isPending}
                      className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 text-sm font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Reset to starter code"
                    >
                      <RotateCcw size={16} className={resetCodeMutation.isPending ? 'animate-spin' : ''} />
                    </button>
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
                    <TestResults
                      results={testResults}
                      isRunning={isRunning}
                      functionSignature={problem.languages?.[0]?.function_signature}
                    />
                  )}
                </div>
              </div>
            </Allotment.Pane>
          </Allotment>
        </Allotment.Pane>

        {/* Right Pane: AI Chat Assistant (conditional) */}
        {showAIChat && (
          <Allotment.Pane minSize={250}>
            <ChatPanel
              problemSlug={slug}
              currentCode={code}
              testResults={testResults}
              onClose={() => setShowAIChat(false)}
              initialMessage={chatInitialMessage}
              initialSessionTitle={chatInitialTitle}
              onInitialMessageSent={handleInitialMessageSent}
            />
          </Allotment.Pane>
        )}
      </Allotment>

      {/* Submission Result Modal */}
      {showSubmissionResult && submissionResult && (
        <SubmissionResultPanel
          result={submissionResult}
          code={submittedCode}
          language={language}
          problemSlug={slug}
          functionSignature={problem.languages?.[0]?.function_signature}
          onClose={handleCloseSubmissionResult}
          onLoadCode={handleLoadSubmissionCode}
        />
      )}
    </div>
  )
}
