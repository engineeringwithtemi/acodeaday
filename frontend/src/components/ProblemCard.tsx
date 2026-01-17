import { Link } from '@tanstack/react-router'
import { ArrowRight, RotateCcw, Sparkles } from 'lucide-react'
import type { Problem } from '../types/api'

interface ProblemCardProps {
  problem: Problem
  type: 'review' | 'new'
  daysOverdue?: number
}

const difficultyStyles = {
  easy: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  medium: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
  hard: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
}

const typeStyles = {
  review: {
    border: 'border-amber-500/30 hover:border-amber-500/50',
    glow: 'hover:shadow-amber-500/10',
    accent: 'bg-amber-500/10 text-amber-400',
    icon: RotateCcw,
    label: 'Review',
  },
  new: {
    border: 'border-cyan-500/30 hover:border-cyan-500/50',
    glow: 'hover:shadow-cyan-500/10',
    accent: 'bg-cyan-500/10 text-cyan-400',
    icon: Sparkles,
    label: 'New',
  },
}

export function ProblemCard({
  problem,
  type,
  daysOverdue = 0,
}: ProblemCardProps) {
  const style = typeStyles[type]
  const Icon = style.icon

  return (
    <Link
      to="/problem/$slug"
      params={{ slug: problem.slug }}
      className={`group block bg-gradient-to-br from-zinc-900 via-zinc-900/95 to-zinc-900/90 border rounded-lg p-6 transition-all duration-300 hover:scale-[1.02] ${style.border} ${style.glow} hover:shadow-xl`}
    >
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-zinc-600 font-mono text-xs tracking-wider">
              #{problem.sequence_number.toString().padStart(2, '0')}
            </span>
            <span
              className={`px-2.5 py-0.5 rounded text-xs font-mono font-semibold uppercase tracking-wide border ${difficultyStyles[problem.difficulty]}`}
            >
              {problem.difficulty}
            </span>
            <span
              className={`px-2.5 py-0.5 rounded text-xs font-mono font-semibold uppercase tracking-wide flex items-center gap-1.5 ${style.accent}`}
            >
              <Icon className="w-3 h-3" />
              {style.label}
            </span>
          </div>
          <h3 className="text-lg font-semibold text-white mb-1 group-hover:text-cyan-300 transition-colors">
            {problem.title}
          </h3>
          <p className="text-xs font-mono text-zinc-500 uppercase tracking-widest">
            {problem.pattern}
          </p>
        </div>
        <ArrowRight className="w-5 h-5 text-zinc-600 group-hover:text-cyan-400 group-hover:translate-x-1 transition-all" />
      </div>

      {type === 'review' && daysOverdue > 0 && (
        <div className="pt-3 border-t border-zinc-800">
          <div className="flex items-center gap-2 text-xs">
            <div className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            <span className="font-mono text-amber-400">
              {daysOverdue} day{daysOverdue !== 1 ? 's' : ''} overdue
            </span>
          </div>
        </div>
      )}

      {type === 'new' && (
        <div className="pt-3 border-t border-zinc-800">
          <p className="text-xs font-mono text-zinc-500">
            Master this problem to unlock the next one
          </p>
        </div>
      )}
    </Link>
  )
}
