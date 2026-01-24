import { useState } from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import { Calendar, Clock, Code, AlertCircle, Layers, ChevronDown, ChevronRight, CheckCircle2, Circle } from 'lucide-react'
import { useTodayProblems, usePatterns } from '@/hooks'
import type { ProblemProgressSchema, PatternGroupSchema, ProblemWithProgressSchema } from '@/types/api'

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
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-2xl p-12 text-center mb-8">
            <Code className="text-cyan-400 mx-auto mb-4" size={64} />
            <h2 className="text-2xl font-bold text-white mb-3">All Caught Up!</h2>
            <p className="text-gray-400 mb-6">
              No problems due today. Browse by pattern below or come back tomorrow.
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
          <div className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <Code className="text-green-400" size={24} />
              <h2 className="text-2xl font-bold text-white">New Problem</h2>
            </div>
            <div className="grid grid-cols-1 gap-4">
              <ProblemCard problem={newProblem} type="new" />
            </div>
          </div>
        )}

        {/* Browse by Pattern Section */}
        <PatternBrowser />
      </div>
    </div>
  )
}

interface ProblemCardProps {
  problem: ProblemProgressSchema
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
            Pattern: <span className="text-cyan-400">{problem.pattern.join(', ')}</span>
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

function PatternBrowser() {
  const { data, isLoading, error } = usePatterns()
  const [expandedPatterns, setExpandedPatterns] = useState<Set<string>>(new Set())

  const togglePattern = (pattern: string) => {
    setExpandedPatterns(prev => {
      const newSet = new Set(prev)
      if (newSet.has(pattern)) {
        newSet.delete(pattern)
      } else {
        newSet.add(pattern)
      }
      return newSet
    })
  }

  if (isLoading) {
    return (
      <div className="mt-8">
        <div className="flex items-center gap-2 mb-4">
          <Layers className="text-purple-400" size={24} />
          <h2 className="text-2xl font-bold text-white">Browse by Pattern</h2>
        </div>
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl p-8 text-center">
          <div className="w-8 h-8 border-2 border-purple-400 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-gray-400 mt-3">Loading patterns...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="mt-8">
        <div className="flex items-center gap-2 mb-4">
          <Layers className="text-purple-400" size={24} />
          <h2 className="text-2xl font-bold text-white">Browse by Pattern</h2>
        </div>
        <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4">
          <p className="text-red-400">Failed to load patterns</p>
        </div>
      </div>
    )
  }

  const patterns = data?.patterns || []

  return (
    <div className="mt-8">
      <div className="flex items-center gap-2 mb-4">
        <Layers className="text-purple-400" size={24} />
        <h2 className="text-2xl font-bold text-white">Browse by Pattern</h2>
        <span className="px-3 py-1 bg-purple-500/20 text-purple-400 rounded-full text-sm font-semibold">
          {patterns.length} patterns
        </span>
      </div>
      <p className="text-gray-400 mb-6">
        Focus on specific concepts by exploring problems grouped by their primary pattern.
        <span className="text-gray-500 text-sm block mt-1">
          Note: Each problem appears under its primary pattern only, even if it uses multiple techniques.
        </span>
      </p>

      <div className="space-y-2">
        {patterns.map((patternGroup) => (
          <PatternAccordion
            key={patternGroup.pattern}
            patternGroup={patternGroup}
            isExpanded={expandedPatterns.has(patternGroup.pattern)}
            onToggle={() => togglePattern(patternGroup.pattern)}
          />
        ))}
      </div>
    </div>
  )
}

interface PatternAccordionProps {
  patternGroup: PatternGroupSchema
  isExpanded: boolean
  onToggle: () => void
}

function PatternAccordion({ patternGroup, isExpanded, onToggle }: PatternAccordionProps) {
  const progressPercentage = patternGroup.total_count > 0
    ? Math.round((patternGroup.solved_count / patternGroup.total_count) * 100)
    : 0

  // Format pattern name for display (convert kebab-case to Title Case)
  const formatPatternName = (pattern: string) => {
    return pattern
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  }

  return (
    <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl overflow-hidden">
      {/* Header */}
      <button
        onClick={onToggle}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-700/30 transition-colors"
      >
        <div className="flex items-center gap-4">
          {isExpanded ? (
            <ChevronDown className="text-purple-400" size={20} />
          ) : (
            <ChevronRight className="text-gray-400" size={20} />
          )}
          <div className="text-left">
            <h3 className="text-lg font-semibold text-white">
              {formatPatternName(patternGroup.pattern)}
            </h3>
            <p className="text-sm text-gray-400">
              {patternGroup.solved_count}/{patternGroup.total_count} solved
              {patternGroup.mastered_count > 0 && (
                <span className="text-green-400 ml-2">
                  • {patternGroup.mastered_count} mastered
                </span>
              )}
            </p>
          </div>
        </div>

        {/* Progress bar */}
        <div className="flex items-center gap-3">
          <div className="w-32 h-2 bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-purple-500 to-cyan-500 transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
          <span className="text-sm text-gray-400 w-12 text-right">
            {progressPercentage}%
          </span>
        </div>
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t border-gray-700 px-6 py-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {patternGroup.problems.map((item) => (
              <PatternProblemCard key={item.problem.id} item={item} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

interface PatternProblemCardProps {
  item: ProblemWithProgressSchema
}

function PatternProblemCard({ item }: PatternProblemCardProps) {
  const { problem, user_progress } = item

  const difficultyColors = {
    easy: 'text-green-400',
    medium: 'text-yellow-400',
    hard: 'text-red-400',
  }

  const getStatusIcon = () => {
    if (user_progress?.is_mastered) {
      return <CheckCircle2 className="text-green-400" size={16} />
    }
    if (user_progress && user_progress.times_solved > 0) {
      return <Circle className="text-yellow-400 fill-yellow-400/30" size={16} />
    }
    return <Circle className="text-gray-500" size={16} />
  }

  const getStatusText = () => {
    if (user_progress?.is_mastered) {
      return 'Mastered'
    }
    if (user_progress && user_progress.times_solved > 0) {
      return `Solved ${user_progress.times_solved}x`
    }
    return 'Not started'
  }

  return (
    <Link
      to="/problem/$slug"
      params={{ slug: problem.slug }}
      className="block bg-gray-900/50 border border-gray-600/50 rounded-lg p-4 hover:border-purple-500/50 hover:bg-gray-800/50 transition-all"
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <span className="text-xs text-gray-500">#{problem.sequence_number}</span>
        </div>
        <span className={`text-xs font-medium ${difficultyColors[problem.difficulty]}`}>
          {problem.difficulty}
        </span>
      </div>
      <h4 className="text-sm font-medium text-white mb-1 line-clamp-1">
        {problem.title}
      </h4>
      <p className="text-xs text-gray-500">
        {getStatusText()}
      </p>
    </Link>
  )
}
