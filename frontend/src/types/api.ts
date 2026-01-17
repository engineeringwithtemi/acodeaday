// frontend/src/types/api.ts
// Re-export generated types from OpenAPI schema

import type { components } from './api.generated'

// ============================================
// Schema type extractions
// ============================================

// Today/Dashboard types
export type TodaySessionResponse = components['schemas']['TodaySessionResponse']
export type ProblemProgressSchema = components['schemas']['ProblemProgressSchema']

// Problem types
export type ProblemSchema = components['schemas']['ProblemSchema']
export type ProblemDetailSchema = components['schemas']['ProblemDetailSchema']
export type ProblemBasicSchema = components['schemas']['ProblemBasicSchema']
export type ProblemExampleSchema = components['schemas']['ProblemExampleSchema']
export type ProblemLanguageSchema = components['schemas']['ProblemLanguageSchema']
export type TestCaseSchema = components['schemas']['TestCaseSchema']

// Progress types
export type ProgressResponse = components['schemas']['ProgressResponse']
export type ProblemWithProgressSchema = components['schemas']['ProblemWithProgressSchema']
export type UserProgressBasicSchema = components['schemas']['UserProgressBasicSchema']

// Mastered types
export type MasteredProblemsResponse = components['schemas']['MasteredProblemsResponse']
export type MasteredProblemSchema = components['schemas']['MasteredProblemSchema']
export type ShowAgainResponse = components['schemas']['ShowAgainResponse']

// Execution types
export type RunCodeRequest = components['schemas']['RunCodeRequest']
export type RunCodeResponse = components['schemas']['RunCodeResponse']
export type SubmitCodeRequest = components['schemas']['SubmitCodeRequest']
export type SubmitCodeResponse = components['schemas']['SubmitCodeResponse']
export type TestResult = components['schemas']['TestResult']

// Rating types
export type RatingRequest = components['schemas']['RatingRequest']
export type RatingResponse = components['schemas']['RatingResponse']

// Submission types
export type SubmissionSchema = components['schemas']['SubmissionSchema']
export type SubmissionBasicSchema = components['schemas']['SubmissionBasicSchema']

// Code management types
export type SaveCodeRequest = components['schemas']['SaveCodeRequest']
export type SaveCodeResponse = components['schemas']['SaveCodeResponse']
export type ResetCodeRequest = components['schemas']['ResetCodeRequest']
export type ResetCodeResponse = components['schemas']['ResetCodeResponse']
export type LoadSubmissionRequest = components['schemas']['LoadSubmissionRequest']

// Chat types
export type ChatSessionSchema = components['schemas']['ChatSessionSchema']
export type ChatSessionWithMessagesSchema = components['schemas']['ChatSessionWithMessagesSchema']
export type ChatMessageSchema = components['schemas']['ChatMessageSchema']
export type CreateSessionRequest = components['schemas']['CreateSessionRequest']
export type UpdateSessionRequest = components['schemas']['UpdateSessionRequest']
export type SendMessageRequest = components['schemas']['SendMessageRequest']
export type ModelInfo = components['schemas']['ModelInfo']

// Enums
export type Difficulty = components['schemas']['Difficulty']
export type Language = components['schemas']['Language']
export type ChatMode = components['schemas']['ChatMode']
export type MessageRole = components['schemas']['MessageRole']

// ============================================
// Types NOT in OpenAPI (keep manual definitions)
// ============================================

// FunctionSignature is used in frontend but generated as { [key: string]: unknown }
// Keep a proper typed version for better DX
export interface FunctionSignature {
  name: string
  params: Array<{
    name: string
    type: string
  }>
  return_type: string
}

// Rating enum (backend uses string, but we want type safety)
export type Rating = 'again' | 'hard' | 'good' | 'mastered'
