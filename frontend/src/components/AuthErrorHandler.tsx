// AuthErrorHandler - Global handler for 401 authentication errors
// Subscribes to React Query cache and redirects to login on auth errors

import { useEffect } from 'react'
import { useNavigate, useLocation } from '@tanstack/react-router'
import { useQueryClient } from '@tanstack/react-query'
import { ApiError, logout } from '../lib/api-client'

/**
 * Component that monitors React Query cache for 401 errors
 * and automatically redirects to login page when authentication fails.
 *
 * This catches errors that occur AFTER initial route navigation,
 * such as when a session expires while the user is on a page.
 */
export function AuthErrorHandler({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  const location = useLocation()
  const queryClient = useQueryClient()

  useEffect(() => {
    // Skip on login page
    if (location.pathname === '/login') {
      return
    }

    // Subscribe to query cache events
    const unsubscribe = queryClient.getQueryCache().subscribe((event) => {
      // Only handle query errors (not loading/success states)
      if (event.type !== 'updated' || event.action.type !== 'error') {
        return
      }

      const error = event.query.state.error

      // Check if it's a 401 authentication error
      if (error instanceof ApiError && error.status === 401) {
        // Sign out and redirect to login
        logout().then(() => {
          navigate({
            to: '/login',
            search: {
              redirect: location.href,
            },
          })
        })
      }
    })

    return () => {
      unsubscribe()
    }
  }, [navigate, location, queryClient])

  return <>{children}</>
}
