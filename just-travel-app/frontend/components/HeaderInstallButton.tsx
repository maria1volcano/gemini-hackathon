'use client'

import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { usePWAInstall } from '../hooks/usePWAInstall'

/**
 * Install button for the header navigation.
 * Always visible - shows install popup when clicked.
 */
export default function HeaderInstallButton() {
  const { isInstallable, install } = usePWAInstall()
  const [isStandalone, setIsStandalone] = useState(false)
  const [showPopup, setShowPopup] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    // Check if already running as installed PWA
    const standalone = window.matchMedia('(display-mode: standalone)').matches
      || (window.navigator as any).standalone === true
    setIsStandalone(standalone)
  }, [])

  // Hide only if already installed as PWA
  if (isStandalone) return null

  const handleInstall = async () => {
    const success = await install()
    if (success) {
      setShowPopup(false)
    }
  }

  const popup = showPopup && mounted ? createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-[#0d0d2b] p-6 rounded-3xl border border-white/10 shadow-2xl shadow-orange-500/20 max-w-sm mx-4">
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
            {isInstallable ? (
              <div className="flex gap-3">
                <button
                  onClick={handleInstall}
                  className="bg-gradient-to-r from-orange-500 to-pink-500 text-white px-5 py-2.5 text-sm font-bold rounded-xl shadow-lg shadow-orange-500/30 hover:scale-105 transition-transform"
                >
                  Install Now
                </button>
                <button
                  onClick={() => setShowPopup(false)}
                  className="bg-white/10 text-white/80 px-5 py-2.5 text-sm font-bold rounded-xl border border-white/10 hover:bg-white/20 transition-colors"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-orange-400 font-medium">
                  Manual install required:
                </p>
                <ul className="text-sm text-white/70 space-y-1">
                  <li>• <strong>Chrome/Edge:</strong> Click install icon in address bar</li>
                  <li>• <strong>Safari iOS:</strong> Tap Share → Add to Home Screen</li>
                  <li>• <strong>Safari Mac:</strong> File → Add to Dock</li>
                </ul>
                <button
                  onClick={() => setShowPopup(false)}
                  className="w-full bg-white/10 text-white/80 px-5 py-2.5 text-sm font-bold rounded-xl border border-white/10 hover:bg-white/20 transition-colors"
                >
                  Got it
                </button>
              </div>
            )}
          </div>
          <button
            onClick={() => setShowPopup(false)}
            className="text-white/40 hover:text-white/80 transition-colors text-xl"
          >
            ✕
          </button>
        </div>
      </div>
    </div>,
    document.body
  ) : null

  return (
    <>
      <button
        onClick={() => setShowPopup(true)}
        className="bg-gradient-to-r from-orange-500 to-pink-500 text-white font-black font-bold text-sm px-5 py-2.5 rounded-full hover:opacity-90 transition-all shadow-lg shadow-orange-500/25 flex items-center gap-2"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        Get App
      </button>
      {popup}
    </>
  )
}
