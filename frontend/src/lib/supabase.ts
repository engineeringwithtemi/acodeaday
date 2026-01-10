// Supabase client for authentication
import { createClient, Session } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'http://127.0.0.1:54321'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0'

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
  },
})

// Promise that resolves when Supabase auth is initialized
// This ensures we wait for session restoration from localStorage before checking auth
let authReadyPromise: Promise<Session | null> | null = null
let authInitialized = false

export const getAuthReady = (): Promise<Session | null> => {
  // Only run on client side
  if (typeof window === 'undefined') {
    return Promise.resolve(null)
  }

  // Return cached promise if already created
  if (authReadyPromise) {
    return authReadyPromise
  }

  // Create new promise that waits for auth state to be ready
  authReadyPromise = new Promise((resolve) => {
    // First try to get session immediately
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        authInitialized = true
        resolve(session)
        return
      }

      // If no session, wait briefly for onAuthStateChange
      // This handles the case where localStorage restoration is async
      const timeout = setTimeout(() => {
        if (!authInitialized) {
          authInitialized = true
          resolve(null)
        }
      }, 100)

      const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
        if (!authInitialized && event === 'INITIAL_SESSION') {
          authInitialized = true
          clearTimeout(timeout)
          resolve(session)
          subscription.unsubscribe()
        }
      })
    })
  })

  return authReadyPromise
}
