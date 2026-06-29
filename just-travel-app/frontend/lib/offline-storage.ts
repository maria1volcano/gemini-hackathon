/**
 * Offline Storage - IndexedDB wrapper for persisting itineraries locally
 * Enables offline access to saved travel plans
 */

export interface StoredItinerary {
  id: string
  destination: string
  summary: string
  itinerary_data: any
  creative_assets: any
  saved_at: number
  last_accessed: number
}

const DB_NAME = 'just-travel-db'
const DB_VERSION = 1
const STORE_NAME = 'itineraries'
const MAX_ENTRIES = 50
const MAX_AGE_DAYS = 30

class OfflineStorage {
  private db: IDBDatabase | null = null
  private initPromise: Promise<void> | null = null

  /**
   * Initialize IndexedDB connection
   */
  async init(): Promise<void> {
    // Return existing init promise if already initializing
    if (this.initPromise) {
      return this.initPromise
    }

    // Return immediately if already initialized
    if (this.db) {
      return Promise.resolve()
    }

    this.initPromise = new Promise((resolve, reject) => {
      if (typeof window === 'undefined') {
        reject(new Error('IndexedDB not available (server-side)'))
        return
      }

      const request = indexedDB.open(DB_NAME, DB_VERSION)

      request.onerror = () => {
        console.error('Failed to open IndexedDB:', request.error)
        reject(request.error)
      }

      request.onsuccess = () => {
        this.db = request.result
        console.log('✅ IndexedDB initialized')
        resolve()
      }

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result

        // Create object store if it doesn't exist
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const store = db.createObjectStore(STORE_NAME, { keyPath: 'id' })

          // Create indexes for efficient querying
          store.createIndex('destination', 'destination', { unique: false })
          store.createIndex('saved_at', 'saved_at', { unique: false })
          store.createIndex('last_accessed', 'last_accessed', { unique: false })

          console.log('📦 Created IndexedDB object store')
        }
      }
    })

    return this.initPromise
  }

  /**
   * Save itinerary to local storage
   */
  async saveItinerary(itinerary: Omit<StoredItinerary, 'saved_at' | 'last_accessed'>): Promise<void> {
    await this.init()

    if (!this.db) {
      throw new Error('Database not initialized')
    }

    const now = Date.now()
    const storedItinerary: StoredItinerary = {
      ...itinerary,
      saved_at: now,
      last_accessed: now,
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite')
      const store = transaction.objectStore(STORE_NAME)
      const request = store.put(storedItinerary)

      request.onsuccess = () => {
        console.log(`💾 Saved itinerary: ${itinerary.destination}`)
        this.clearOldEntries() // Clean up old entries asynchronously
        resolve()
      }

      request.onerror = () => {
        console.error('Failed to save itinerary:', request.error)
        reject(request.error)
      }
    })
  }

  /**
   * Get all stored itineraries
   */
  async getAllItineraries(): Promise<StoredItinerary[]> {
    await this.init()

    if (!this.db) {
      throw new Error('Database not initialized')
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readonly')
      const store = transaction.objectStore(STORE_NAME)
      const index = store.index('saved_at')
      const request = index.openCursor(null, 'prev') // Newest first

      const results: StoredItinerary[] = []

      request.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest).result
        if (cursor) {
          results.push(cursor.value)
          cursor.continue()
        } else {
          console.log(`📂 Retrieved ${results.length} itineraries`)
          resolve(results)
        }
      }

      request.onerror = () => {
        console.error('Failed to retrieve itineraries:', request.error)
        reject(request.error)
      }
    })
  }

  /**
   * Get single itinerary by ID
   */
  async getItinerary(id: string): Promise<StoredItinerary | null> {
    await this.init()

    if (!this.db) {
      throw new Error('Database not initialized')
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite')
      const store = transaction.objectStore(STORE_NAME)
      const request = store.get(id)

      request.onsuccess = () => {
        const itinerary = request.result as StoredItinerary | undefined

        if (itinerary) {
          // Update last_accessed timestamp
          itinerary.last_accessed = Date.now()
          store.put(itinerary)
        }

        resolve(itinerary || null)
      }

      request.onerror = () => {
        console.error('Failed to retrieve itinerary:', request.error)
        reject(request.error)
      }
    })
  }

  /**
   * Delete itinerary by ID
   */
  async deleteItinerary(id: string): Promise<void> {
    await this.init()

    if (!this.db) {
      throw new Error('Database not initialized')
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite')
      const store = transaction.objectStore(STORE_NAME)
      const request = store.delete(id)

      request.onsuccess = () => {
        console.log(`🗑️ Deleted itinerary: ${id}`)
        resolve()
      }

      request.onerror = () => {
        console.error('Failed to delete itinerary:', request.error)
        reject(request.error)
      }
    })
  }

  /**
   * Clear all stored itineraries
   */
  async clearAll(): Promise<void> {
    await this.init()

    if (!this.db) {
      throw new Error('Database not initialized')
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite')
      const store = transaction.objectStore(STORE_NAME)
      const request = store.clear()

      request.onsuccess = () => {
        console.log('🧹 Cleared all itineraries')
        resolve()
      }

      request.onerror = () => {
        console.error('Failed to clear itineraries:', request.error)
        reject(request.error)
      }
    })
  }

  /**
   * Clear old entries to manage storage quota
   * Removes entries older than MAX_AGE_DAYS and keeps only MAX_ENTRIES newest
   */
  private async clearOldEntries(): Promise<void> {
    if (!this.db) return

    try {
      const allItineraries = await this.getAllItineraries()

      if (allItineraries.length <= MAX_ENTRIES) {
        return // No cleanup needed
      }

      const now = Date.now()
      const maxAge = MAX_AGE_DAYS * 24 * 60 * 60 * 1000

      const toDelete: string[] = []

      // Delete entries older than MAX_AGE_DAYS
      for (const item of allItineraries) {
        if (now - item.saved_at > maxAge) {
          toDelete.push(item.id)
        }
      }

      // If still over limit, delete oldest entries
      if (allItineraries.length - toDelete.length > MAX_ENTRIES) {
        const sortedByDate = [...allItineraries].sort((a, b) => a.saved_at - b.saved_at)
        const excess = allItineraries.length - toDelete.length - MAX_ENTRIES

        for (let i = 0; i < excess; i++) {
          if (!toDelete.includes(sortedByDate[i].id)) {
            toDelete.push(sortedByDate[i].id)
          }
        }
      }

      // Delete old entries
      for (const id of toDelete) {
        await this.deleteItinerary(id)
      }

      if (toDelete.length > 0) {
        console.log(`🧹 Cleaned up ${toDelete.length} old itineraries`)
      }
    } catch (error) {
      console.error('Failed to clean old entries:', error)
    }
  }

  /**
   * Get storage usage estimate
   */
  async getStorageInfo(): Promise<{ usage: number; quota: number; percentage: number } | null> {
    if (typeof navigator === 'undefined' || !navigator.storage) {
      return null
    }

    try {
      const estimate = await navigator.storage.estimate()
      const usage = estimate.usage || 0
      const quota = estimate.quota || 0
      const percentage = quota > 0 ? (usage / quota) * 100 : 0

      return { usage, quota, percentage }
    } catch (error) {
      console.error('Failed to get storage info:', error)
      return null
    }
  }
}

// Export singleton instance
export const offlineStorage = new OfflineStorage()
