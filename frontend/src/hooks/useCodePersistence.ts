import { useState, useCallback } from 'react'

/**
 * Hook for persisting code in localStorage across page refreshes.
 * Supports multiple languages per problem (separate storage keys).
 *
 * @param problemSlug - The problem identifier
 * @param language - The programming language
 * @param starterCode - Default code to use if no saved draft exists
 * @returns { code, setCode, resetCode }
 */
export function useCodePersistence(
  problemSlug: string,
  language: string,
  starterCode: string
) {
  const storageKey = `acodeaday:draft:${problemSlug}:${language}`

  // Initialize from localStorage or fall back to starter code
  const [code, setCodeState] = useState(() => {
    if (typeof window === 'undefined') return starterCode
    const saved = localStorage.getItem(storageKey)
    return saved || starterCode
  })

  // Update both state and localStorage
  const setCode = useCallback(
    (newCode: string) => {
      setCodeState(newCode)
      if (typeof window !== 'undefined') {
        localStorage.setItem(storageKey, newCode)
      }
    },
    [storageKey]
  )

  // Clear saved draft and reset to starter code
  const resetCode = useCallback(() => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(storageKey)
    }
    setCodeState(starterCode)
  }, [storageKey, starterCode])

  return { code, setCode, resetCode }
}
