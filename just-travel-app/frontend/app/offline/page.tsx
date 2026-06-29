/**
 * Offline Page - Fallback page when navigating while offline
 * Shows friendly message and link to saved itineraries
 */

'use client'

export default function OfflinePage() {
  const handleRetry = () => {
    window.location.reload()
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="bg-white/[0.03] backdrop-blur-3xl rounded-[40px] border border-white/10 p-12 text-center max-w-md shadow-2xl">
        {/* Airplane Icon */}
        <div className="text-8xl mb-8 animate-bounce">✈️</div>

        {/* Title */}
        <h1 className="text-4xl font-black text-orange-400 mb-4 uppercase tracking-wider">
          You're Offline
        </h1>

        {/* Message */}
        <p className="text-white/70 text-lg mb-8">
          No internet connection detected. Your saved itineraries are still available!
        </p>

        {/* Actions */}
        <div className="flex flex-col gap-4">
          <button
            onClick={handleRetry}
            className="bg-gradient-to-r from-orange-500 to-pink-500 text-white px-6 py-3 text-lg font-bold rounded-full hover:scale-105 transition-transform shadow-lg shadow-orange-500/25"
          >
            TRY AGAIN
          </button>

          <a
            href="/my-itineraries"
            className="bg-white/5 border border-white/10 text-orange-400 px-6 py-3 text-lg font-bold rounded-full hover:scale-105 transition-transform hover:bg-white/10"
          >
            VIEW SAVED TRIPS
          </a>

          <a
            href="/"
            className="text-white/50 hover:text-orange-400 transition-colors mt-2"
          >
            Go to Home
          </a>
        </div>
      </div>
    </div>
  )
}
