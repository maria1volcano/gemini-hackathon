/**
 * useOnlineStatus Hook - Detect online/offline status
 * Tracks network connectivity changes in real-time
 */

'use client'

import { useState, useEffect } from 'react'

export function useOnlineStatus(): boolean {
  // Initialize with current status (defaulting to true on server)
  const [isOnline, setIsOnline] = useState<boolean>(
    typeof window !== 'undefined' ? window.navigator.onLine : true
  )

  useEffect(() => {
    // Skip if running on server
    if (typeof window === 'undefined') {
      return
    }

    // Update state based on current status
    setIsOnline(window.navigator.onLine)

    // Handler for when connection is restored
    const handleOnline = () => {
      console.log('📡 Connection restored')
      setIsOnline(true)
    }

    // Handler for when connection is lost
    const handleOffline = () => {
      console.log('📴 Connection lost')
      setIsOnline(false)
    }

    // Add event listeners
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // Cleanup listeners on unmount
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return isOnline
}
