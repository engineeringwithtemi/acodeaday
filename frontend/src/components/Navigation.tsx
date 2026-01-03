import { Link } from '@tanstack/react-router'
import { Home, TrendingUp, Trophy, LogOut, Menu, X } from 'lucide-react'
import { useState } from 'react'

interface NavigationProps {
  onLogout?: () => void
}

export function Navigation({ onLogout }: NavigationProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const navLinks = [
    { to: '/', label: 'Dashboard', icon: Home },
    { to: '/progress', label: 'Progress', icon: TrendingUp },
    { to: '/mastered', label: 'Mastered', icon: Trophy },
  ]

  return (
    <>
      <nav className="bg-gradient-to-r from-zinc-950 via-zinc-900 to-zinc-950 border-b border-zinc-800 shadow-xl">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link
              to="/"
              className="flex items-center gap-3 group hover:scale-105 transition-transform"
            >
              <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-lg flex items-center justify-center shadow-lg shadow-cyan-500/20">
                <span className="text-white font-mono font-bold text-lg">A</span>
              </div>
              <div className="hidden sm:block">
                <h1 className="text-xl font-bold font-mono text-white group-hover:text-cyan-300 transition-colors">
                  acodeaday
                </h1>
                <p className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">
                  A code a day keeps rejection away
                </p>
              </div>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-6">
              {navLinks.map(({ to, label, icon: Icon }) => (
                <Link
                  key={to}
                  to={to}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-mono text-zinc-400 hover:text-white hover:bg-zinc-800/50 transition-all"
                  activeProps={{
                    className:
                      'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-mono text-cyan-400 bg-cyan-500/10 border border-cyan-500/30 transition-all',
                  }}
                >
                  <Icon className="w-4 h-4" />
                  <span>{label}</span>
                </Link>
              ))}

              {onLogout && (
                <button
                  onClick={onLogout}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-mono text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/30 transition-all"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              )}
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden p-2 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
              aria-label="Toggle menu"
            >
              {isMobileMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>

          {/* Mobile Navigation */}
          {isMobileMenuOpen && (
            <div className="md:hidden py-4 border-t border-zinc-800 animate-in slide-in-from-top-2 duration-200">
              <div className="flex flex-col gap-2">
                {navLinks.map(({ to, label, icon: Icon }) => (
                  <Link
                    key={to}
                    to={to}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-mono text-zinc-400 hover:text-white hover:bg-zinc-800/50 transition-all"
                    activeProps={{
                      className:
                        'flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-mono text-cyan-400 bg-cyan-500/10 border border-cyan-500/30 transition-all',
                    }}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{label}</span>
                  </Link>
                ))}

                {onLogout && (
                  <button
                    onClick={() => {
                      setIsMobileMenuOpen(false)
                      onLogout()
                    }}
                    className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-mono text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/30 transition-all text-left"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Logout</span>
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </nav>
    </>
  )
}
