// Authentication hook
import { useState, useCallback, useEffect } from 'react'
import { supabase } from '../lib/supabase'
import { login as apiLogin, logout as apiLogout } from '../lib/api-client'

interface UseAuthReturn {
  isAuthenticated: boolean
  email: string | null
  userId: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

/**
 * Authentication state management hook using Supabase Auth
 * Manages user authentication state and provides login/logout functions
 */
export function useAuth(): UseAuthReturn {
  const [authState, setAuthState] = useState<{
    isAuthenticated: boolean
    email: string | null
    userId: string | null
  }>({
    isAuthenticated: false,
    email: null,
    userId: null,
  })

  // Initialize and listen to Supabase auth state changes
  useEffect(() => {
    // Only run on client
    if (typeof window === 'undefined') return

    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setAuthState({
        isAuthenticated: session !== null,
        email: session?.user?.email || null,
        userId: session?.user?.id || null,
      })
    })

    // Listen for auth state changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setAuthState({
        isAuthenticated: session !== null,
        email: session?.user?.email || null,
        userId: session?.user?.id || null,
      })
    })

    return () => subscription.unsubscribe()
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    await apiLogin(email, password)
    // Auth state will be updated by onAuthStateChange listener
  }, [])

  const logout = useCallback(async () => {
    await apiLogout()
    // Auth state will be updated by onAuthStateChange listener
  }, [])

  return {
    isAuthenticated: authState.isAuthenticated,
    email: authState.email,
    userId: authState.userId,
    login,
    logout,
  }
}
