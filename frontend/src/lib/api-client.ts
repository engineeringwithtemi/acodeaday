// API Client for acodeaday
// Handles HTTP requests with Supabase session token authentication

import { supabase } from './supabase'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public statusText: string,
    public data?: any
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/**
 * Check if user is authenticated (has a Supabase session)
 */
export async function isAuthenticated(): Promise<boolean> {
  if (typeof window === 'undefined') return false // Not authenticated on server
  const { data: { session } } = await supabase.auth.getSession()
  return session !== null
}

/**
 * Get the current Supabase session access token
 */
export async function getAccessToken(): Promise<string | null> {
  if (typeof window === 'undefined') return null
  const { data: { session } } = await supabase.auth.getSession()
  return session?.access_token || null
}

/**
 * Create Bearer token authorization header value
 */
function createBearerAuthHeader(accessToken: string): string {
  return `Bearer ${accessToken}`
}

/**
 * Generic API request wrapper with Supabase session token authentication
 * Automatically refreshes Supabase session on 401 errors
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  isRetry: boolean = false
): Promise<T> {
  const accessToken = await getAccessToken()

  if (!accessToken) {
    throw new ApiError('Not authenticated', 401, 'Unauthorized')
  }

  const url = `${API_BASE_URL}${endpoint}`
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'Authorization': createBearerAuthHeader(accessToken),
    ...options.headers,
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    })

    // Handle 401 Unauthorized - attempt token refresh via Supabase
    if (response.status === 401 && !isRetry) {
      try {
        const { data: { session }, error } = await supabase.auth.refreshSession()
        if (error || !session) {
          await supabase.auth.signOut()
          throw new ApiError('Session expired', 401, 'Unauthorized')
        }
        // Retry the original request with refreshed token
        return await apiRequest<T>(endpoint, options, true)
      } catch (refreshError) {
        await supabase.auth.signOut()
        throw new ApiError('Session expired', 401, 'Unauthorized')
      }
    }

    // Handle non-2xx responses
    if (!response.ok) {
      let errorData: any
      try {
        errorData = await response.json()
      } catch {
        errorData = await response.text()
      }

      throw new ApiError(
        errorData.detail || errorData.message || response.statusText,
        response.status,
        response.statusText,
        errorData
      )
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return undefined as T
    }

    // Parse JSON response
    return await response.json()
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }

    // Network or other errors
    throw new ApiError(
      error instanceof Error ? error.message : 'Network request failed',
      0,
      'Network Error'
    )
  }
}

/**
 * GET request helper
 */
export function apiGet<T>(endpoint: string, options?: RequestInit): Promise<T> {
  return apiRequest<T>(endpoint, { ...options, method: 'GET' })
}

/**
 * POST request helper
 */
export function apiPost<T>(
  endpoint: string,
  data?: any,
  options?: RequestInit
): Promise<T> {
  return apiRequest<T>(endpoint, {
    ...options,
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  })
}

/**
 * PUT request helper
 */
export function apiPut<T>(
  endpoint: string,
  data?: any,
  options?: RequestInit
): Promise<T> {
  return apiRequest<T>(endpoint, {
    ...options,
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  })
}

/**
 * DELETE request helper
 */
export function apiDelete<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  return apiRequest<T>(endpoint, { ...options, method: 'DELETE' })
}

/**
 * Login with email and password using Supabase Auth
 */
export async function login(email: string, password: string): Promise<void> {
  const { error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })

  if (error) {
    throw new ApiError(
      error.message || 'Login failed. Please check your Supabase backend configuration.',
      401,
      'Unauthorized',
      error
    )
  }
}

/**
 * Logout - sign out from Supabase
 */
export async function logout(): Promise<void> {
  await supabase.auth.signOut()
}
