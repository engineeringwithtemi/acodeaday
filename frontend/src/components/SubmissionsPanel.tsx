import { Loader2 } from 'lucide-react'
import { useState } from 'react'
import { useSubmissions } from '@/hooks'
import type { SubmissionSchema } from '@/types/api'

interface SubmissionsPanelProps {
  problemId: string
  onSubmissionClick?: (submission: SubmissionSchema) => void
}

export function SubmissionsPanel({ problemId, onSubmissionClick }: SubmissionsPanelProps) {
  const { data: submissions, isLoading } = useSubmissions(problemId)
  const [expandedId, setExpandedId] = useState<string | null>(null)

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

  // Format runtime
  const formatRuntime = (ms: number | null) => {
    if (ms === null || ms === undefined) return 'N/A'
    return `${ms} ms`
  }

  // Format memory (convert KB to MB)
  const formatMemory = (kb?: number | null) => {
    if (!kb) return 'N/A'
    return `${(kb / 1024).toFixed(2)} MB`
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-900 text-white">
      {/* Table Header */}
      <div className="sticky top-0 bg-gray-800 border-b border-gray-700 z-10">
        <div className="grid grid-cols-4 gap-4 px-6 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
          <div>Status</div>
          <div>Language</div>
          <div>Runtime</div>
          <div>Memory</div>
        </div>
      </div>

      {/* Submissions List */}
      <div className="p-6 space-y-2">
        {submissions.map((submission: SubmissionSchema) => {
          const isExpanded = expandedId === submission.id

          return (
            <div key={submission.id} className="bg-gray-800 rounded-lg overflow-hidden">
              {/* Row - Clickable */}
              <button
                onClick={() => {
                  if (onSubmissionClick) {
                    onSubmissionClick(submission)
                  } else {
                    setExpandedId(isExpanded ? null : submission.id)
                  }
                }}
                className="w-full grid grid-cols-4 gap-4 px-6 py-4 text-left hover:bg-gray-700/50 transition-colors"
              >
                <div className={`font-semibold ${
                  submission.passed ? 'text-green-400' : 'text-red-400'
                }`}>
                  {submission.passed ? 'Accepted' : 'Failed'}
                </div>
                <div className="text-gray-300 capitalize">{submission.language}</div>
                <div className="text-gray-300">{formatRuntime(submission.runtime_ms)}</div>
                <div className="text-gray-300">{formatMemory(submission.memory_kb)}</div>
              </button>

              {/* Expanded Details */}
              {isExpanded && (
                <div className="border-t border-gray-700 p-4 bg-gray-900/50">
                  <div className="space-y-3">
                    <div className="text-xs text-gray-400">
                      Submitted: <span className="text-gray-300">{new Date(submission.submitted_at).toLocaleString()}</span>
                    </div>
                    <div>
                      <div className="text-xs text-gray-400 mb-2">Code:</div>
                      <pre className="p-3 bg-gray-900 rounded text-sm text-gray-300 overflow-x-auto">
                        {submission.code}
                      </pre>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
