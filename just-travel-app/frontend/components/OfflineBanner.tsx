/**
 * OfflineBanner - Shows notification when offline
 * Neo-brutalist style with yellow background
 */

'use client'

import { useOnlineStatus } from '../hooks/useOnlineStatus'

export default function OfflineBanner() {
  const isOnline = useOnlineStatus()

  // Don't render if online
  if (isOnline) {
    return null
  }

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-brutal-yellow text-brutal-black py-3 px-4 text-center font-mono font-bold border-b-4 border-orange-400 shadow-brutal">
      <div className="flex items-center justify-center gap-2">
        <span className="text-2xl">📡</span>
        <span className="uppercase tracking-wide">You're offline. Some features are limited.</span>
      </div>
    </div>
  )
}
