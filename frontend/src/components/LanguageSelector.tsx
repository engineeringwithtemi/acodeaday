import { ChevronDown } from 'lucide-react'

interface LanguageSelectorProps {
  value: string
  onChange: (lang: string) => void
  availableLanguages: string[]
  disabled?: boolean
}

const languageLabels: Record<string, string> = {
  python: 'Python',
  javascript: 'JavaScript',
  java: 'Java',
  cpp: 'C++',
  go: 'Go',
  rust: 'Rust',
}

export function LanguageSelector({
  value,
  onChange,
  availableLanguages,
  disabled = false,
}: LanguageSelectorProps) {
  const getLabel = (lang: string) => languageLabels[lang] || lang

  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled || availableLanguages.length <= 1}
        className="appearance-none bg-zinc-800 border border-zinc-700 rounded-md pl-3 pr-8 py-1.5 text-sm font-medium text-zinc-200 cursor-pointer hover:border-zinc-600 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {availableLanguages.map((lang) => (
          <option key={lang} value={lang}>
            {getLabel(lang)}
          </option>
        ))}
      </select>
      <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 pointer-events-none" />
    </div>
  )
}
