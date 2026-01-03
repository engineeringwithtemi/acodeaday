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
  id: number
  slug: string
  sequence_number: number
  title: string
  difficulty: 'easy' | 'medium' | 'hard'
  pattern: string
  description: string
  constraints: string[]
  examples: ProblemExample[]
  created_at: string
  updated_at: string
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

export interface TodayProblem {
  problem: Problem
  problem_language: ProblemLanguage
  user_progress: UserProgress | null
  review_type?: 'review' | 'new'
}

export interface TodayResponse {
  review_problems: TodayProblem[]
  new_problem: TodayProblem | null
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
