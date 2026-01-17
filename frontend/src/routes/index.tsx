import { createFileRoute, Link } from '@tanstack/react-router'
import { Calendar, Clock, Code, AlertCircle } from 'lucide-react'
import { useTodayProblems } from '@/hooks'
import type { TodayProblem } from '@/types/api'

export const Route = createFileRoute('/')({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: "Today's Practice - acodeaday",
      },
    ],
  }),
})

function Dashboard() {
  const { data, isLoading, error } = useTodayProblems()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400 text-lg">Loading today's problems...</p>
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
              <h2 className="text-xl font-bold text-red-400">Error Loading Problems</h2>
            </div>
            <p className="text-gray-300">{(error as Error).message}</p>
          </div>
        </div>
      </div>
    )
  }

  const reviewProblems = data?.review_problems || []
  const newProblem = data?.new_problem

  const hasNoProblems = reviewProblems.length === 0 && !newProblem

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <Calendar className="text-cyan-400" size={32} />
            <h1 className="text-4xl font-black text-white">Today's Practice</h1>
          </div>
          <p className="text-gray-400 text-lg">
            {new Date().toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}
          </p>
        </div>

        {/* Empty State */}
        {hasNoProblems && (
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-2xl p-12 text-center">
            <Code className="text-cyan-400 mx-auto mb-4" size={64} />
            <h2 className="text-2xl font-bold text-white mb-3">All Caught Up!</h2>
            <p className="text-gray-400 mb-6">
              No problems due today. Come back tomorrow for your next challenge.
            </p>
            <Link
              to="/progress"
              className="inline-flex items-center gap-2 px-6 py-3 bg-cyan-500 hover:bg-cyan-600 text-white font-semibold rounded-lg transition-colors"
            >
              View Progress
            </Link>
          </div>
        )}

        {/* Review Problems Section */}
        {reviewProblems.length > 0 && (
          <div className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <Clock className="text-orange-400" size={24} />
              <h2 className="text-2xl font-bold text-white">Review Problems</h2>
              <span className="px-3 py-1 bg-orange-500/20 text-orange-400 rounded-full text-sm font-semibold">
                {reviewProblems.length}
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {reviewProblems.map((problem) => (
                <ProblemCard key={problem.id} problem={problem} type="review" />
              ))}
            </div>
          </div>
        )}

        {/* New Problem Section */}
        {newProblem && (
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Code className="text-green-400" size={24} />
              <h2 className="text-2xl font-bold text-white">New Problem</h2>
            </div>
            <div className="grid grid-cols-1 gap-4">
              <ProblemCard problem={newProblem} type="new" />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

interface ProblemCardProps {
  problem: TodayProblem
  type: 'review' | 'new'
}

function ProblemCard({ problem, type }: ProblemCardProps) {
  const difficultyColors = {
    easy: 'text-green-400 bg-green-500/20',
    medium: 'text-yellow-400 bg-yellow-500/20',
    hard: 'text-red-400 bg-red-500/20',
  }

  const typeColors = {
    review: 'from-orange-500/20 to-orange-600/20 border-orange-500/50',
    new: 'from-green-500/20 to-green-600/20 border-green-500/50',
  }

  return (
    <Link
      to="/problem/$slug"
      params={{ slug: problem.slug }}
      className={`block bg-gradient-to-br ${typeColors[type]} backdrop-blur-sm border rounded-xl p-6 hover:scale-[1.02] transition-all duration-300 hover:shadow-xl`}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-semibold text-gray-400">
              #{problem.sequence_number}
            </span>
            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${difficultyColors[problem.difficulty]}`}>
              {problem.difficulty}
            </span>
            {type === 'review' && (
              <span className="px-2 py-1 bg-orange-500/20 text-orange-400 rounded-full text-xs font-semibold">
                Review {problem.times_solved}/2
              </span>
            )}
          </div>
          <h3 className="text-xl font-bold text-white mb-2">{problem.title}</h3>
          <p className="text-sm text-gray-400 mb-3">
            Pattern: <span className="text-cyan-400">{problem.pattern}</span>
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between text-sm">
        <span className={`font-semibold ${type === 'review' ? 'text-orange-400' : 'text-green-400'}`}>
          {type === 'review' ? 'Continue Practice' : 'Start Problem'} →
        </span>
      </div>
    </Link>
  )
}
