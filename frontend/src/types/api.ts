// API Types for acodeaday

// Authentication types
export interface LoginRequest {
  email: string
  password: string
}

export interface SignupRequest {
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  user_id: string
  email: string
}

export interface RefreshRequest {
  refresh_token: string
}

export interface Problem {
  id: string
  slug: string
  sequence_number: number
  title: string
  difficulty: 'easy' | 'medium' | 'hard'
  pattern: string
  description: string
  constraints: string[]
  examples: ProblemExample[]
  languages: ProblemLanguage[]
  test_cases: TestCase[]
  created_at: string
  updated_at?: string
  // User's saved code (from user_code table) - null means use starter_code
  user_code?: string | null
}

export interface ProblemExample {
  input: string
  output: string
  explanation?: string
}

export interface ProblemLanguage {
  id: number
  problem_id: number
  language: string
  starter_code: string
  reference_solution: string
  function_signature: FunctionSignature
  created_at: string
  updated_at: string
}

export interface FunctionSignature {
  name: string
  params: Array<{
    name: string
    type: string
  }>
  return_type: string
}

export interface TestCase {
  id: number
  problem_id: number
  sequence: number
  input: Record<string, any>
  expected: any
  is_hidden: boolean
  created_at: string
  updated_at: string
}

export interface UserProgress {
  id: number
  user_id: string
  problem_id: number
  times_solved: number
  next_review_date: string | null
  is_mastered: boolean
  show_again: boolean
  last_solved_at: string | null
  created_at: string
  updated_at: string
}

export interface Submission {
  id: number
  user_id: string
  problem_id: number
  language: string
  code: string
  is_passed: boolean
  runtime_ms: number | null
  submitted_at: string
}

// Flat structure returned by backend for today's problems
export interface TodayProblem {
  id: number
  title: string
  slug: string
  difficulty: 'easy' | 'medium' | 'hard'
  pattern: string
  sequence_number: number
  times_solved: number
  last_solved_at: string | null
  next_review_date: string | null
  is_mastered: boolean
}

export interface TodayResponse {
  review_problems: TodayProblem[]
  new_problem: TodayProblem | null
  total_mastered: number
  total_attempted: number
}

export interface SubmitRequest {
  problem_id: number
  language: string
  code: string
}

export interface TestCaseResult {
  test_case_id: number
  passed: boolean
  expected: any
  actual: any
  error?: string
}

export interface SubmissionResult {
  is_passed: boolean
  test_results: TestCaseResult[]
  runtime_ms: number | null
  submission_id: number
  user_progress: UserProgress
}

export interface MasteredProblem {
  problem: Problem
  user_progress: UserProgress
  last_submission: Submission | null
}

export interface MasteredProblemsResponse {
  mastered_problems: MasteredProblem[]
}

// New types matching backend schemas

// Test result from backend (for both Run and Submit)
export interface TestResult {
  test_number: number
  passed: boolean
  input: any  // Input arguments for this test case
  output: any
  expected: any
  stdout?: string  // User's print() output
  error?: string
  error_type?: string
  is_hidden: boolean
}

// Run Code request (visible tests only, or custom input)
export interface RunCodeRequest {
  problem_slug: string
  code: string
  language: string
  custom_input?: any[][]  // Optional custom test inputs
}

// Run Code response (visible tests only)
export interface RunCodeResponse {
  success: boolean
  results: TestResult[]
  summary: {
    total: number
    passed: number
    failed: number
  }
  stdout?: string
  stderr?: string
  compile_error?: string
  runtime_error?: string
}

// Submit Code request (all tests + saves)
export interface SubmitCodeRequest {
  problem_slug: string
  code: string
  language: string
}

// Submit Code response (all tests + progress)
export interface SubmitCodeResponse {
  success: boolean
  results: TestResult[]
  summary: {
    total: number    // Tests actually executed (may be less than total_test_cases due to early_exit)
    passed: number
    failed: number
  }
  total_test_cases?: number  // Total tests in problem (for "X / Y testcases passed" display). Optional for old submissions.
  submission_id: string
  runtime_ms?: number
  memory_kb?: number
  compile_error?: string
  runtime_error?: string
  times_solved?: number
  is_mastered?: boolean
  next_review_date?: string
}

// Submission history schema
export interface SubmissionSchema {
  id: string
  problem_id: string
  problem_title: string
  code: string
  language: string
  passed: boolean
  runtime_ms: number | null
  memory_kb?: number | null
  submitted_at: string
  // Test result summary
  total_test_cases: number
  passed_count: number
  // First failed test details (null if all passed)
  failed_test_number: number | null
  failed_input: any | null
  failed_output: any | null
  failed_expected: any | null
  failed_is_hidden: boolean
}

// Chat types
export type ChatMode = 'socratic' | 'direct'
export type MessageRole = 'user' | 'assistant' | 'system'

export interface ChatMessage {
  id: string
  session_id: string
  role: MessageRole
  content: string
  code_snapshot?: string | null
  test_results_snapshot?: any
  created_at: string
}

export interface ChatSession {
  id: string
  user_id: string
  problem_id: string
  title?: string | null
  mode: ChatMode
  model?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ChatSessionWithMessages extends ChatSession {
  messages: ChatMessage[]
}

export interface CreateSessionRequest {
  problem_slug: string
  mode?: ChatMode
  model?: string | null
}

export interface UpdateSessionRequest {
  title?: string | null
  mode?: ChatMode
  model?: string | null
  is_active?: boolean
}

export interface ModelInfo {
  name: string
  display_name: string
  is_default: boolean
}

// WebSocket message types
export interface ChatWSMessage {
  type: 'message' | 'cancel'
  content?: string
  current_code?: string
  test_results?: any
}

export interface ChatWSResponse {
  type: 'chunk' | 'done' | 'error'
  content?: string
  message_id?: string
  error?: string
}
