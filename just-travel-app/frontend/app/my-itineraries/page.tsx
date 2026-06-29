/**
 * My Itineraries Page - View all saved itineraries
 * Glassmorphism design with offline support
 */

'use client'

import { useEffect, useState } from 'react'
import { useOnlineStatus } from '../../hooks/useOnlineStatus'
import { offlineStorage, StoredItinerary } from '../../lib/offline-storage'
import { ItineraryView } from '../../components/ItineraryView'

export default function MyItinerariesPage() {
  const [itineraries, setItineraries] = useState<StoredItinerary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const isOnline = useOnlineStatus()

  useEffect(() => {
    loadItineraries()
  }, [isOnline])

  const loadItineraries = async () => {
    try {
      setLoading(true)
      setError(null)

      // Load from IndexedDB (works offline)
      const localItineraries = await offlineStorage.getAllItineraries()
      setItineraries(localItineraries)

      // If online, also fetch from backend and merge
      if (isOnline) {
        try {
          const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
          const response = await fetch(`${apiUrl}/api/itinerary/list`, {
            credentials: 'include',
          })

          if (response.ok) {
            const data = await response.json()
            const backendItineraries = data.itineraries || []

            // Merge backend and local data (prefer backend)
            const merged = new Map<string, StoredItinerary>()

            // Add local itineraries first
            localItineraries.forEach((itin) => {
              merged.set(itin.id, itin)
            })

            // Update with backend data (overwrites local if duplicate)
            for (const itin of backendItineraries) {
              const stored: StoredItinerary = {
                id: itin.id.toString(),
                destination: itin.destination,
                summary: itin.summary,
                itinerary_data: itin.data,
                creative_assets: itin.creative_assets,
                saved_at: new Date(itin.created_at).getTime(),
                last_accessed: Date.now(),
              }

              merged.set(stored.id, stored)

              // Also save to IndexedDB for offline access
              await offlineStorage.saveItinerary(stored)
            }

            setItineraries(Array.from(merged.values()).sort((a, b) => b.saved_at - a.saved_at))
          }
        } catch (err) {
          console.warn('Failed to fetch from backend:', err)
          // Continue with local data
        }
      }
    } catch (err) {
      console.error('Failed to load itineraries:', err)
      setError('Failed to load itineraries')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this itinerary? This cannot be undone.')) {
      return
    }

    try {
      await offlineStorage.deleteItinerary(id)
      setItineraries((prev) => prev.filter((itin) => itin.id !== id))

      // If online, also delete from backend
      if (isOnline) {
        try {
          const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
          await fetch(`${apiUrl}/api/itinerary/${id}`, {
            method: 'DELETE',
            credentials: 'include',
          })
        } catch (err) {
          console.warn('Failed to delete from backend:', err)
        }
      }
    } catch (err) {
      console.error('Failed to delete itinerary:', err)
      alert('Failed to delete itinerary')
    }
  }

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center bg-white/[0.03] backdrop-blur-3xl p-12 rounded-3xl border border-white/10 shadow-2xl shadow-orange-500/10">
          <div className="text-6xl mb-4 animate-bounce">✈️</div>
          <p className="text-white/70 text-lg font-bold">Loading your trips...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-white/[0.03] backdrop-blur-3xl p-8 rounded-3xl border border-red-500/30 shadow-2xl shadow-red-500/10 text-center max-w-md">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-black text-red-400 mb-4">Error</h2>
          <p className="text-white/60 mb-6">{error}</p>
          <button
            onClick={loadItineraries}
            className="bg-gradient-to-r from-orange-500 to-pink-500 text-white px-6 py-3 font-bold rounded-xl shadow-lg shadow-orange-500/30 hover:scale-105 transition-transform"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-5xl font-black text-white mb-4 uppercase tracking-wider">
            My <span className="text-orange-400">Trips</span>
          </h1>
          <div className="h-1 w-24 bg-gradient-to-r from-orange-500 to-pink-500 mx-auto mb-4 rounded-full" />

          {/* Online/Offline Status */}
          {!isOnline && (
            <div className="bg-white/[0.03] backdrop-blur-xl p-4 rounded-2xl border border-yellow-500/30 shadow-lg shadow-yellow-500/10 mb-6 inline-block">
              <div className="flex items-center gap-2 text-yellow-400 font-bold">
                <span className="text-2xl">📱</span>
                <span>Viewing offline. You can access all saved itineraries!</span>
              </div>
            </div>
          )}

          <p className="text-white/50">
            {itineraries.length} {itineraries.length === 1 ? 'trip' : 'trips'} saved
          </p>
        </div>

        {/* No Itineraries */}
        {itineraries.length === 0 && (
          <div className="bg-white/[0.03] backdrop-blur-3xl p-12 rounded-3xl border border-white/10 shadow-2xl shadow-orange-500/10 text-center max-w-xl mx-auto">
            <div className="text-6xl mb-4">🗺️</div>
            <h2 className="text-2xl font-black text-orange-400 mb-4">No Saved Trips Yet</h2>
            <p className="text-white/60 mb-6">
              Start planning your next adventure to save itineraries here!
            </p>
            <a
              href="/"
              className="bg-gradient-to-r from-orange-500 to-pink-500 text-white px-6 py-3 font-bold rounded-xl shadow-lg shadow-orange-500/30 hover:scale-105 transition-transform inline-block"
            >
              Plan a Trip
            </a>
          </div>
        )}

        {/* Itinerary List */}
        <div className="space-y-6">
          {itineraries.map((itinerary) => (
            <div
              key={itinerary.id}
              className="bg-white/[0.03] backdrop-blur-3xl rounded-3xl border border-white/10 shadow-2xl shadow-orange-500/5 overflow-hidden hover:border-orange-500/30 transition-all"
            >
              {/* Header */}
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-2xl font-black text-orange-400 mb-2">
                      {itinerary.destination}
                    </h3>
                    <p className="text-white/60">{itinerary.summary}</p>
                  </div>
                  <button
                    onClick={() => handleDelete(itinerary.id)}
                    className="text-red-400 hover:text-red-300 transition-colors p-2 text-2xl hover:scale-110"
                    title="Delete itinerary"
                  >
                    🗑️
                  </button>
                </div>

                <div className="flex items-center gap-4 text-sm text-white/40 mb-4">
                  <span>Saved {new Date(itinerary.saved_at).toLocaleDateString()}</span>
                  <span>•</span>
                  <span>Last viewed {new Date(itinerary.last_accessed).toLocaleDateString()}</span>
                </div>

                <button
                  onClick={() => toggleExpand(itinerary.id)}
                  className="bg-white/10 text-white/80 px-5 py-2.5 text-sm font-bold rounded-xl border border-white/10 hover:bg-white/20 transition-all"
                >
                  {expandedId === itinerary.id ? '▲ Hide Details' : '▼ View Details'}
                </button>
              </div>

              {/* Expanded Content */}
              {expandedId === itinerary.id && (
                <div className="border-t border-white/10 p-6 bg-white/[0.02]">
                  <ItineraryView itinerary={itinerary.itinerary_data} />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
