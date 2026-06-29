/**
 * Sync Manager - Background sync for pending offline saves
 * Automatically syncs itineraries to backend when connection is restored
 */

interface PendingSave {
  id: string
  timestamp: number
  data: {
    destination: string
    summary: string
    itinerary_data: any
    creative_assets: any
    media_task_id?: string
  }
}

const STORAGE_KEY = 'just-travel-pending-saves'
const MAX_PENDING = 20

class SyncManager {
  /**
   * Add a save operation to the pending queue
   */
  addPendingSave(save: Omit<PendingSave, 'timestamp'>): void {
    try {
      const pending = this.getPendingSaves()

      // Add timestamp
      const saveWithTimestamp: PendingSave = {
        ...save,
        timestamp: Date.now(),
      }

      // Add to queue
      pending.push(saveWithTimestamp)

      // Keep only the most recent MAX_PENDING saves
      const trimmed = pending.slice(-MAX_PENDING)

      // Save to localStorage
      localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed))

      console.log(`📥 Queued save for sync: ${save.data.destination} (ID: ${save.id})`)
    } catch (error) {
      console.error('Failed to queue pending save:', error)
    }
  }

  /**
   * Get all pending saves
   */
  getPendingSaves(): PendingSave[] {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (!stored) {
        return []
      }

      const parsed = JSON.parse(stored)
      return Array.isArray(parsed) ? parsed : []
    } catch (error) {
      console.error('Failed to retrieve pending saves:', error)
      return []
    }
  }

  /**
   * Remove a save from the pending queue
   */
  removePendingSave(id: string): void {
    try {
      const pending = this.getPendingSaves()
      const filtered = pending.filter((save) => save.id !== id)

      localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered))
      console.log(`✅ Removed pending save: ${id}`)
    } catch (error) {
      console.error('Failed to remove pending save:', error)
    }
  }

  /**
   * Clear all pending saves
   */
  clearPendingSaves(): void {
    try {
      localStorage.removeItem(STORAGE_KEY)
      console.log('🧹 Cleared all pending saves')
    } catch (error) {
      console.error('Failed to clear pending saves:', error)
    }
  }

  /**
   * Sync all pending saves to backend
   */
  async syncPending(apiUrl: string): Promise<void> {
    const pending = this.getPendingSaves()

    if (pending.length === 0) {
      console.log('✨ No pending saves to sync')
      return
    }

    console.log(`🔄 Syncing ${pending.length} pending saves...`)

    const results = {
      success: 0,
      failed: 0,
      errors: [] as Array<{ id: string; error: string }>,
    }

    // Sync each pending save
    for (const save of pending) {
      try {
        const response = await fetch(`${apiUrl}/api/itinerary/save`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include', // Include cookies for auth
          body: JSON.stringify(save.data),
        })

        if (response.ok) {
          // Successfully synced - remove from queue
          this.removePendingSave(save.id)
          results.success++
          console.log(`✅ Synced: ${save.data.destination}`)
        } else {
          // Failed to sync - keep in queue
          results.failed++
          const errorText = await response.text()
          results.errors.push({
            id: save.id,
            error: `HTTP ${response.status}: ${errorText}`,
          })
          console.error(`❌ Failed to sync ${save.data.destination}:`, errorText)
        }
      } catch (error) {
        // Network error - keep in queue
        results.failed++
        results.errors.push({
          id: save.id,
          error: error instanceof Error ? error.message : 'Unknown error',
        })
        console.error(`❌ Failed to sync ${save.data.destination}:`, error)
      }
    }

    // Log summary
    if (results.success > 0) {
      console.log(`✅ Successfully synced ${results.success} itineraries`)
    }

    if (results.failed > 0) {
      console.warn(`⚠️ Failed to sync ${results.failed} itineraries`)
      console.warn('Errors:', results.errors)
    }

    return
  }

  /**
   * Check if there are pending saves
   */
  hasPendingSaves(): boolean {
    return this.getPendingSaves().length > 0
  }

  /**
   * Get count of pending saves
   */
  getPendingCount(): number {
    return this.getPendingSaves().length
  }
}

// Export singleton instance
export const syncManager = new SyncManager()
