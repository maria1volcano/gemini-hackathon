/**
 * InstallPrompt - PWA installation prompt
 * Glassmorphism style matching the website design
 */

'use client'

import { useState, useEffect } from 'react'
import { usePWAInstall } from '../hooks/usePWAInstall'

export default function InstallPrompt() {
  const { isInstallable, isDismissed, install, dismiss } = usePWAInstall()
  const [showPrompt, setShowPrompt] = useState(false)

  // Show prompt after 3 seconds delay (only if not previously dismissed)
  useEffect(() => {
    if (isInstallable && !isDismissed) {
      const timer = setTimeout(() => {
        setShowPrompt(true)
      }, 3000)
      return () => clearTimeout(timer)
    }
  }, [isInstallable, isDismissed])

  const handleInstall = async () => {
    const success = await install()
    if (success) {
      setShowPrompt(false)
    }
  }

  const handleDismiss = () => {
    setShowPrompt(false)
    dismiss()
  }

  // Don't render if no prompt or already dismissed
  if (!showPrompt || !isInstallable) {
    return null
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 max-w-sm animate-in slide-in-from-bottom-5">
      <div className="bg-white/[0.03] backdrop-blur-3xl p-6 rounded-3xl border border-white/10 shadow-2xl shadow-orange-500/10">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-orange-500 to-pink-500 flex items-center justify-center text-2xl shadow-lg shadow-orange-500/30">
            ✈️
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-black text-white mb-1">
              Install Just Travel
            </h3>
            <p className="text-sm text-white/60 mb-4">
              Add to home screen for quick access and offline itineraries!
            </p>
            <div className="flex gap-3">
              <button
                onClick={handleInstall}
                className="bg-gradient-to-r from-orange-500 to-pink-500 text-white px-5 py-2.5 text-sm font-bold rounded-xl shadow-lg shadow-orange-500/30 hover:scale-105 transition-transform"
              >
                Install
              </button>
              <button
                onClick={handleDismiss}
                className="bg-white/10 text-white/80 px-5 py-2.5 text-sm font-bold rounded-xl border border-white/10 hover:bg-white/20 transition-colors"
              >
                Not Now
              </button>
            </div>
          </div>
          <button
            onClick={handleDismiss}
            className="text-white/40 hover:text-white/80 transition-colors"
          >
            ✕
          </button>
        </div>
      </div>
    </div>
  )
}
