'use client'

import { useState, useEffect, useCallback } from 'react'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

/**
 * Shared hook for PWA installation functionality.
 * Used by both the header install button and the popup prompt.
 */
export function usePWAInstall() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [isInstallable, setIsInstallable] = useState(false)
  const [isDismissed, setIsDismissed] = useState(false)

  useEffect(() => {
    // Check dismissal status (for popup only, not header button)
    const dismissed = localStorage.getItem('pwa-install-dismissed')
    setIsDismissed(!!dismissed)

    // Check if event was already captured before React loaded (by layout.tsx script)
    const preCapture = (window as any).__PWA_DEFERRED_PROMPT
    if (preCapture) {
      setDeferredPrompt(preCapture)
      setIsInstallable(true)
    }

    // Also listen for future events (component remounts, navigation, etc.)
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e as BeforeInstallPromptEvent)
      setIsInstallable(true)
      // Update global for other components
      ;(window as any).__PWA_DEFERRED_PROMPT = e
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    return () => window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
  }, [])

  const install = useCallback(async () => {
    if (!deferredPrompt) return false

    await deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice

    if (outcome === 'accepted') {
      setIsInstallable(false)
      setDeferredPrompt(null)
      localStorage.setItem('pwa-install-dismissed', 'true')
    }

    return outcome === 'accepted'
  }, [deferredPrompt])

  const dismiss = useCallback(() => {
    setIsInstallable(false)
    localStorage.setItem('pwa-install-dismissed', 'true')
  }, [])

  return { isInstallable, isDismissed, install, dismiss }
}
