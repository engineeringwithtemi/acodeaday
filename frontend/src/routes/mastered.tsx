import { createFileRoute, Link } from '@tanstack/react-router'
import { Award, RotateCcw, AlertCircle, Calendar, Code } from 'lucide-react'
import { useMasteredProblems } from '@/hooks'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiPost } from '@/lib/api-client'
import type { MasteredProblem } from '@/types/api'

export const Route = createFileRoute('/mastered')({
  component: MasteredProblems,
  head: () => ({
    meta: [
      {
        title: 'Mastered Problems - acodeaday',
      },
    ],
  }),
})

function MasteredProblems() {
  const { data, isLoading, error } = useMasteredProblems()
  const queryClient = useQueryClient()

  const showAgainMutation = useMutation({
    mutationFn: (problemId: string) =>
      apiPost(`/api/mastered/${problemId}/show-again`, {}),
    onSuccess: () => {
      // Invalidate both mastered and today queries to refresh the lists
      queryClient.invalidateQueries({ queryKey: ['mastered'] })
      queryClient.invalidateQueries({ queryKey: ['today'] })
    },
  })

  const handleShowAgain = async (problemId: string, e: React.MouseEvent) => {
    e.preventDefault() // Prevent navigation to problem page
    try {
      await showAgainMutation.mutateAsync(problemId)
    } catch (err) {
      console.error('Failed to mark problem for review:', err)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400 text-lg">Loading mastered problems...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 p-6">
        <div className="max-w-2xl mx-auto mt-12">
          <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-2">
              <AlertCircle className="text-red-400" size={24} />
              <h2 className="text-xl font-bold text-red-400">Error Loading Mastered Problems</h2>
            </div>
            <p className="text-gray-300">{(error as Error).message}</p>
          </div>
        </div>
      </div>
    )
  }

  const masteredProblems = data?.mastered_problems || []

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <Award className="text-purple-400" size={32} />
            <h1 className="text-4xl font-black text-white">Mastered Problems</h1>
          </div>
          <p className="text-gray-400 text-lg">
            Problems you've successfully solved twice. Click "Show Again" to add them back to your review rotation.
          </p>
        </div>

        {/* Stats */}
        <div className="mb-8 bg-gradient-to-br from-purple-500/20 to-pink-500/20 backdrop-blur-sm border border-purple-500/50 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-purple-400 text-4xl font-black mb-2">{masteredProblems.length}</div>
              <div className="text-gray-300 font-semibold">Problems Mastered</div>
            </div>
            <Award className="text-purple-400/30" size={80} />
          </div>
        </div>

        {/* Empty State */}
        {masteredProblems.length === 0 && (
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-2xl p-12 text-center">
            <Award className="text-gray-600 mx-auto mb-4" size={64} />
            <h2 className="text-2xl font-bold text-white mb-3">No Mastered Problems Yet</h2>
            <p className="text-gray-400 mb-6">
              Keep practicing! Solve each problem twice to master it.
            </p>
            <Link
              to="/"
              className="inline-flex items-center gap-2 px-6 py-3 bg-cyan-500 hover:bg-cyan-600 text-white font-semibold rounded-lg transition-colors"
            >
              Start Practicing
            </Link>
          </div>
        )}

        {/* Mastered Problems Grid */}
        {masteredProblems.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {masteredProblems.map((item) => (
              <MasteredProblemCard
                key={item.problem.id}
                masteredProblem={item}
                onShowAgain={handleShowAgain}
                isLoading={showAgainMutation.isPending}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

interface MasteredProblemCardProps {
  masteredProblem: MasteredProblem
  onShowAgain: (problemId: string, e: React.MouseEvent) => Promise<void>
  isLoading: boolean
}

function MasteredProblemCard({ masteredProblem, onShowAgain, isLoading }: MasteredProblemCardProps) {
  const { problem, user_progress, last_submission } = masteredProblem

  const difficultyColors = {
    easy: 'text-green-400 bg-green-500/20',
    medium: 'text-yellow-400 bg-yellow-500/20',
    hard: 'text-red-400 bg-red-500/20',
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  return (
    <Link
      to="/problem/$slug"
      params={{ slug: problem.slug }}
      className="block bg-gradient-to-br from-purple-500/20 to-pink-500/20 backdrop-blur-sm border border-purple-500/50 rounded-xl p-6 hover:scale-[1.02] transition-all duration-300 hover:shadow-xl"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-semibold text-gray-400">
              #{problem.sequence_number}
            </span>
            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${difficultyColors[problem.difficulty]}`}>
              {problem.difficulty}
            </span>
            <span className="px-2 py-1 bg-purple-500/20 text-purple-400 rounded-full text-xs font-semibold flex items-center gap-1">
              <Award size={12} />
              Mastered
            </span>
          </div>
          <h3 className="text-xl font-bold text-white mb-2">{problem.title}</h3>
          <p className="text-sm text-gray-400 mb-3">
            Pattern: <span className="text-cyan-400">{problem.pattern}</span>
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-4 text-sm text-gray-400 mb-4">
        <div className="flex items-center gap-1">
          <Calendar size={14} />
          <span>Last solved: {formatDate(user_progress.last_solved_at)}</span>
        </div>
        {last_submission && (
          <div className="flex items-center gap-1">
            <Code size={14} />
            <span>{last_submission.runtime_ms}ms</span>
          </div>
        )}
      </div>

      {/* Show Again Button */}
      <button
        onClick={(e) => onShowAgain(problem.id, e)}
        disabled={isLoading}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-orange-600/20 hover:bg-orange-600/30 text-orange-400 font-semibold rounded-lg transition-colors border border-orange-500/50 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <RotateCcw size={16} />
        <span>Show Again</span>
      </button>
    </Link>
  )
}
