import { Link } from '@tanstack/react-router'
import {
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  Ban,
  ChevronRight,
} from 'lucide-react'
import { useImportStatus, useCancelImport } from '@/hooks'
import type { ImportJobSummaryResponse, ImportJobStatus } from '@/types/api'

// ── Active import tracker (polls while in progress) ──

interface ActiveImportTrackerProps {
  importId: string
  onDone: () => void
}

export function ActiveImportTracker({ importId, onDone }: ActiveImportTrackerProps) {
  const { data: job, isLoading } = useImportStatus(importId)
  const cancelMutation = useCancelImport()

  // Notify parent when terminal
  const isTerminal = job?.status === 'completed' || job?.status === 'failed' || job?.status === 'cancelled'

  if (isLoading || !job) {
    return (
      <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-xl p-4 flex items-center gap-3">
        <Loader2 className="text-cyan-400 animate-spin" size={20} />
        <span className="text-gray-300 text-sm">Loading import status...</span>
      </div>
    )
  }

  const progressPercent = job.total && job.total > 0
    ? Math.round(((job.progress ?? 0) / job.total) * 100)
    : 0

  return (
    <div className={`border rounded-xl p-4 ${statusBorderClass(job.status)}`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <StatusIcon status={job.status} />
          <span className="text-sm font-semibold text-white">
            {statusLabel(job.status)}
          </span>
        </div>
        {!isTerminal && (
          <button
            onClick={() => cancelMutation.mutate(importId)}
            disabled={cancelMutation.isPending}
            className="text-xs text-gray-400 hover:text-red-400 transition-colors"
          >
            Cancel
          </button>
        )}
        {isTerminal && (
          <button
            onClick={onDone}
            className="text-xs text-gray-400 hover:text-white transition-colors"
          >
            Dismiss
          </button>
        )}
      </div>

      <p className="text-sm text-gray-300 mb-2 truncate" title={job.prompt}>
        {job.prompt}
      </p>

      {job.message && (
        <p className="text-xs text-gray-400 mb-2">{job.message}</p>
      )}

      {/* Progress bar */}
      {job.total && job.total > 0 && (
        <div className="mt-2">
          <div className="w-full h-1.5 bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${progressBarColor(job.status)}`}
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {job.progress ?? 0} / {job.total} problems
          </p>
        </div>
      )}

      {/* Linked problems */}
      {job.problems && job.problems.length > 0 && (
        <div className="mt-3 border-t border-gray-700 pt-3">
          <p className="text-xs text-gray-500 mb-2">Imported problems:</p>
          <div className="space-y-1">
            {job.problems.map((p) => (
              <Link
                key={p.id}
                to="/problem/$slug"
                params={{ slug: p.slug }}
                className="flex items-center gap-2 text-sm text-gray-300 hover:text-cyan-400 transition-colors"
              >
                <ChevronRight size={14} className="text-gray-500" />
                <span className="truncate">{p.title}</span>
                <span className={`text-xs ml-auto ${difficultyColor(p.difficulty)}`}>
                  {p.difficulty}
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Import history list (for recent imports section) ──

interface ImportHistoryListProps {
  imports: ImportJobSummaryResponse[]
  maxItems?: number
}

export function ImportHistoryList({ imports, maxItems = 5 }: ImportHistoryListProps) {
  const visible = imports.slice(0, maxItems)

  if (visible.length === 0) return null

  return (
    <div className="space-y-2">
      {visible.map((job) => (
        <ImportHistoryItem key={job.id} job={job} />
      ))}
    </div>
  )
}

function ImportHistoryItem({ job }: { job: ImportJobSummaryResponse }) {
  const timeAgo = formatTimeAgo(job.created_at)

  return (
    <div className="flex items-center gap-3 bg-gray-800/50 border border-gray-700 rounded-lg px-4 py-3">
      <StatusIcon status={job.status} size={16} />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-300 truncate">{job.prompt}</p>
        <p className="text-xs text-gray-500">
          {job.message || statusLabel(job.status)} &middot; {timeAgo}
        </p>
      </div>
      {job.total !== null && job.total !== undefined && (
        <span className="text-xs text-gray-500 whitespace-nowrap">
          {job.progress ?? 0}/{job.total}
        </span>
      )}
    </div>
  )
}

// ── Helpers ──

function StatusIcon({ status, size = 18 }: { status: ImportJobStatus; size?: number }) {
  switch (status) {
    case 'completed':
      return <CheckCircle2 size={size} className="text-green-400" />
    case 'failed':
      return <XCircle size={size} className="text-red-400" />
    case 'cancelled':
      return <Ban size={size} className="text-gray-400" />
    case 'processing':
      return <Loader2 size={size} className="text-cyan-400 animate-spin" />
    case 'queued':
      return <Clock size={size} className="text-amber-400" />
  }
}

function statusLabel(status: ImportJobStatus): string {
  const labels: Record<ImportJobStatus, string> = {
    queued: 'Queued',
    processing: 'Importing...',
    completed: 'Complete',
    failed: 'Failed',
    cancelled: 'Cancelled',
  }
  return labels[status]
}

function statusBorderClass(status: ImportJobStatus): string {
  switch (status) {
    case 'processing':
    case 'queued':
      return 'bg-cyan-500/5 border-cyan-500/30'
    case 'completed':
      return 'bg-green-500/5 border-green-500/30'
    case 'failed':
      return 'bg-red-500/5 border-red-500/30'
    case 'cancelled':
      return 'bg-gray-500/5 border-gray-500/30'
  }
}

function progressBarColor(status: ImportJobStatus): string {
  switch (status) {
    case 'completed':
      return 'bg-green-500'
    case 'failed':
      return 'bg-red-500'
    case 'cancelled':
      return 'bg-gray-500'
    default:
      return 'bg-cyan-500'
  }
}

function difficultyColor(difficulty: string): string {
  switch (difficulty) {
    case 'easy':
      return 'text-green-400'
    case 'medium':
      return 'text-yellow-400'
    case 'hard':
      return 'text-red-400'
    default:
      return 'text-gray-400'
  }
}

function formatTimeAgo(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMin = Math.floor(diffMs / 60000)

  if (diffMin < 1) return 'just now'
  if (diffMin < 60) return `${diffMin}m ago`

  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr}h ago`

  const diffDay = Math.floor(diffHr / 24)
  return `${diffDay}d ago`
}
