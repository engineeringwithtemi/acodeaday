import { Link } from '@tanstack/react-router'
import { useState } from 'react'
import {
  Home,
  Menu,
  TrendingUp,
  Award,
  LogOut,
  X,
  Code2,
} from 'lucide-react'
import { useAuth } from '@/hooks'

export default function Header() {
  const [isOpen, setIsOpen] = useState(false)
  const { logout, email } = useAuth()

  const handleLogout = async () => {
    await logout()
    setIsOpen(false)
  }

  return (
    <>
      <header className="p-4 flex items-center justify-between bg-gradient-to-r from-gray-900 to-gray-800 text-white shadow-lg">
        <div className="flex items-center">
          <button
            onClick={() => setIsOpen(true)}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            aria-label="Open menu"
          >
            <Menu size={24} />
          </button>
          <h1 className="ml-4 text-xl font-bold flex items-center gap-2">
            <Link to="/" className="flex items-center gap-2 hover:text-cyan-400 transition-colors">
              <Code2 size={28} className="text-cyan-400" />
              <span>acodeaday</span>
            </Link>
          </h1>
        </div>
        {email && (
          <div className="text-sm text-gray-300">
            <span className="font-semibold text-cyan-400">{email}</span>
          </div>
        )}
      </header>

      <aside
        className={`fixed top-0 left-0 h-full w-80 bg-gradient-to-b from-gray-900 to-gray-800 text-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out flex flex-col ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h2 className="text-xl font-bold text-cyan-400">Navigation</h2>
          <button
            onClick={() => setIsOpen(false)}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
            aria-label="Close menu"
          >
            <X size={24} />
          </button>
        </div>

        <nav className="flex-1 p-4 overflow-y-auto">
          <Link
            to="/"
            onClick={() => setIsOpen(false)}
            className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-800 transition-colors mb-2"
            activeProps={{
              className:
                'flex items-center gap-3 p-3 rounded-lg bg-cyan-600 hover:bg-cyan-700 transition-colors mb-2',
            }}
          >
            <Home size={20} />
            <span className="font-medium">Today's Practice</span>
          </Link>

          <Link
            to="/progress"
            onClick={() => setIsOpen(false)}
            className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-800 transition-colors mb-2"
            activeProps={{
              className:
                'flex items-center gap-3 p-3 rounded-lg bg-cyan-600 hover:bg-cyan-700 transition-colors mb-2',
            }}
          >
            <TrendingUp size={20} />
            <span className="font-medium">Progress Overview</span>
          </Link>

          <Link
            to="/mastered"
            onClick={() => setIsOpen(false)}
            className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-800 transition-colors mb-2"
            activeProps={{
              className:
                'flex items-center gap-3 p-3 rounded-lg bg-cyan-600 hover:bg-cyan-700 transition-colors mb-2',
            }}
          >
            <Award size={20} />
            <span className="font-medium">Mastered Problems</span>
          </Link>

          <div className="border-t border-gray-700 my-4"></div>

          <button
            onClick={handleLogout}
            className="flex items-center gap-3 p-3 rounded-lg hover:bg-red-600/20 text-red-400 transition-colors w-full"
          >
            <LogOut size={20} />
            <span className="font-medium">Logout</span>
          </button>
        </nav>
      </aside>
    </>
  )
}
