import { createFileRoute, Link } from '@tanstack/react-router'
import { TrendingUp, CheckCircle2, Circle, Clock, AlertCircle } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/lib/api-client'
import type { ProgressResponse, ProblemBasic, UserProgressBasic } from '@/types/api'

export const Route = createFileRoute('/progress')({
  component: ProgressOverview,
  head: () => ({
    meta: [
      {
        title: 'Progress Overview - acodeaday',
      },
    ],
  }),
})

function ProgressOverview() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['progress'],
    queryFn: () => apiGet<ProgressResponse>('/api/progress'),
  })

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400 text-lg">Loading progress...</p>
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
              <h2 className="text-xl font-bold text-red-400">Error Loading Progress</h2>
            </div>
            <p className="text-gray-300">{(error as Error).message}</p>
          </div>
        </div>
      </div>
    )
  }

  const { problems = [], total_problems = 0, completed_problems = 0, mastered_problems = 0 } = data || {}
  const progressPercentage = total_problems > 0 ? Math.round((completed_problems / total_problems) * 100) : 0
  const masteredPercentage = total_problems > 0 ? Math.round((mastered_problems / total_problems) * 100) : 0

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <TrendingUp className="text-cyan-400" size={32} />
            <h1 className="text-4xl font-black text-white">Progress Overview</h1>
          </div>
          <p className="text-gray-400 text-lg">Track your journey through the Blind 75</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-gradient-to-br from-cyan-500/20 to-blue-500/20 backdrop-blur-sm border border-cyan-500/50 rounded-xl p-6">
            <div className="text-cyan-400 text-4xl font-black mb-2">{total_problems}</div>
            <div className="text-gray-300 font-semibold">Total Problems</div>
          </div>

          <div className="bg-gradient-to-br from-green-500/20 to-emerald-500/20 backdrop-blur-sm border border-green-500/50 rounded-xl p-6">
            <div className="text-green-400 text-4xl font-black mb-2">
              {completed_problems}
              <span className="text-2xl ml-2 text-gray-400">({progressPercentage}%)</span>
            </div>
            <div className="text-gray-300 font-semibold">Completed</div>
          </div>

          <div className="bg-gradient-to-br from-purple-500/20 to-pink-500/20 backdrop-blur-sm border border-purple-500/50 rounded-xl p-6">
            <div className="text-purple-400 text-4xl font-black mb-2">
              {mastered_problems}
              <span className="text-2xl ml-2 text-gray-400">({masteredPercentage}%)</span>
            </div>
            <div className="text-gray-300 font-semibold">Mastered</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-8 bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-6">
          <div className="flex items-center justify-between mb-3">
            <span className="text-lg font-semibold text-white">Overall Progress</span>
            <span className="text-sm font-semibold text-gray-400">
              {completed_problems} / {total_problems} problems
            </span>
          </div>
          <div className="w-full h-4 bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-500"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>

        {/* Problems List */}
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl overflow-hidden">
          <div className="p-4 bg-gray-800 border-b border-gray-700">
            <h2 className="text-xl font-bold text-white">All Problems</h2>
          </div>
          <div className="divide-y divide-gray-700">
            {problems.map(({ problem, user_progress }) => (
              <ProblemRow key={problem.id} problem={problem} progress={user_progress} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

interface ProblemRowProps {
  problem: ProblemBasic
  progress: UserProgressBasic | null
}

function ProblemRow({ problem, progress }: ProblemRowProps) {
  const difficultyColors = {
    easy: 'text-green-400 bg-green-500/20',
    medium: 'text-yellow-400 bg-yellow-500/20',
    hard: 'text-red-400 bg-red-500/20',
  }

  const getStatusIcon = () => {
    if (!progress || progress.times_solved === 0) {
      return <Circle className="text-gray-500" size={20} />
    }
    if (progress.is_mastered) {
      return <CheckCircle2 className="text-purple-400" size={20} />
    }
    return <Clock className="text-orange-400" size={20} />
  }

  const getStatusText = () => {
    if (!progress || progress.times_solved === 0) {
      return <span className="text-gray-500 text-sm">Not Started</span>
    }
    if (progress.is_mastered) {
      return <span className="text-purple-400 text-sm font-semibold">Mastered</span>
    }
    return (
      <span className="text-orange-400 text-sm font-semibold">
        In Progress ({progress.times_solved}/2)
      </span>
    )
  }

  return (
    <Link
      to={`/problem/${problem.slug}`}
      className="flex items-center gap-4 p-4 hover:bg-gray-700/50 transition-colors"
    >
      {/* Status Icon */}
      <div className="flex-shrink-0">{getStatusIcon()}</div>

      {/* Problem Number */}
      <div className="flex-shrink-0 w-12 text-center">
        <span className="text-sm font-semibold text-gray-400">#{problem.sequence_number}</span>
      </div>

      {/* Problem Title */}
      <div className="flex-1 min-w-0">
        <h3 className="text-white font-semibold truncate">{problem.title}</h3>
        <p className="text-sm text-gray-400">Pattern: {problem.pattern}</p>
      </div>

      {/* Difficulty Badge */}
      <div className="flex-shrink-0">
        <span
          className={`px-3 py-1 rounded-full text-xs font-semibold ${difficultyColors[problem.difficulty]}`}
        >
          {problem.difficulty}
        </span>
      </div>

      {/* Status */}
      <div className="flex-shrink-0 w-32 text-right">{getStatusText()}</div>
    </Link>
  )
}
