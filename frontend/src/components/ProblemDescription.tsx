import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ProblemDetailSchema } from '../types/api'

interface ProblemDescriptionProps {
  problem: ProblemDetailSchema
}

const difficultyStyles = {
  easy: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30',
  medium: 'bg-amber-500/10 text-amber-400 border border-amber-500/30',
  hard: 'bg-rose-500/10 text-rose-400 border border-rose-500/30',
}

export function ProblemDescription({ problem }: ProblemDescriptionProps) {
  return (
    <div className="h-full overflow-y-auto bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 text-zinc-100">
      <div className="p-8 max-w-3xl">
        {/* Header */}
        <div className="mb-8 space-y-4 border-b border-zinc-800 pb-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-zinc-500 font-mono text-sm tracking-wider">
                  #{problem.sequence_number.toString().padStart(2, '0')}
                </span>
                <span
                  className={`px-3 py-1 rounded-md text-xs font-mono font-semibold uppercase tracking-wide ${difficultyStyles[problem.difficulty]}`}
                >
                  {problem.difficulty}
                </span>
              </div>
              <h1 className="text-3xl font-bold tracking-tight text-white mb-2">
                {problem.title}
              </h1>
              <div className="flex items-center gap-2">
                <div className="h-px flex-1 bg-gradient-to-r from-zinc-700 to-transparent" />
                <span className="text-xs font-mono text-zinc-500 uppercase tracking-widest">
                  {problem.pattern}
                </span>
                <div className="h-px flex-1 bg-gradient-to-l from-zinc-700 to-transparent" />
              </div>
            </div>
          </div>
        </div>

        {/* Description */}
        <div className="mb-8">
          <h2 className="text-sm font-mono text-zinc-400 uppercase tracking-widest mb-4 flex items-center gap-2">
            <span className="w-1 h-1 bg-cyan-400 rounded-full animate-pulse" />
            Description
          </h2>
          <div className="prose prose-invert prose-zinc max-w-none prose-p:text-zinc-300 prose-p:leading-relaxed prose-code:text-cyan-400 prose-code:bg-cyan-400/10 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:font-mono prose-code:text-sm prose-strong:text-zinc-200 prose-ul:text-zinc-300 prose-ol:text-zinc-300">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {problem.description}
            </ReactMarkdown>
          </div>
        </div>

        {/* Examples */}
        {problem.examples.length > 0 && (
          <div className="mb-8">
            <h2 className="text-sm font-mono text-zinc-400 uppercase tracking-widest mb-4 flex items-center gap-2">
              <span className="w-1 h-1 bg-cyan-400 rounded-full animate-pulse" />
              Examples
            </h2>
            <div className="space-y-4">
              {problem.examples.map((example, idx) => (
                <div
                  key={idx}
                  className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4 backdrop-blur-sm shadow-lg hover:border-zinc-700 transition-colors"
                >
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-6 h-6 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
                      <span className="text-xs font-mono text-cyan-400 font-semibold">
                        {idx + 1}
                      </span>
                    </div>
                    <span className="text-xs font-mono text-zinc-500 uppercase tracking-wide">
                      Example
                    </span>
                  </div>
                  <div className="space-y-2 font-mono text-sm">
                    <div className="flex gap-2">
                      <span className="text-zinc-500 select-none">Input:</span>
                      <code className="text-cyan-300 bg-cyan-400/5 px-2 py-0.5 rounded">
                        {example.input}
                      </code>
                    </div>
                    <div className="flex gap-2">
                      <span className="text-zinc-500 select-none">Output:</span>
                      <code className="text-emerald-300 bg-emerald-400/5 px-2 py-0.5 rounded">
                        {example.output}
                      </code>
                    </div>
                    {example.explanation && (
                      <div className="pt-2 border-t border-zinc-800">
                        <p className="text-zinc-400 text-xs leading-relaxed">
                          {example.explanation}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Constraints */}
        {problem.constraints.length > 0 && (
          <div>
            <h2 className="text-sm font-mono text-zinc-400 uppercase tracking-widest mb-4 flex items-center gap-2">
              <span className="w-1 h-1 bg-cyan-400 rounded-full animate-pulse" />
              Constraints
            </h2>
            <ul className="space-y-2">
              {problem.constraints.map((constraint, idx) => (
                <li
                  key={idx}
                  className="flex items-start gap-3 text-sm text-zinc-400 font-mono"
                >
                  <span className="text-cyan-500 select-none mt-0.5">▸</span>
                  <span className="flex-1">{constraint}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
