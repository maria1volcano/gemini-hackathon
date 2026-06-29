/**
 * Just Travel - Main Page
 * =======================
 *
 * Dark glassmorphism design with 6-section travel form,
 * floating chat bubble, and full auth integration.
 */

'use client'

import React, { useState, useMemo, useEffect, useRef } from 'react'
import dynamic from 'next/dynamic'
import { motion, AnimatePresence } from 'framer-motion'
import countryList from 'react-select-country-list'
import { useSession, signIn, signOut } from "next-auth/react"
import { ItineraryView } from '../components/ItineraryView'
import TransportBox from '../components/TransportBox'
import FoodBox from '../components/FoodBox'
import { LoadingExperience } from '../components/LoadingExperience'
import { useOnlineStatus } from '../hooks/useOnlineStatus'
import { offlineStorage } from '../lib/offline-storage'
import { syncManager } from '../lib/sync-manager'

const Select = dynamic(() => import('react-select'), { ssr: false })

/**
 * API response type from backend
 */
interface AgentResponse {
  agent: string
  status: string
  message?: string
  profile?: unknown
  data?: { itinerary?: any }
  creative?: { poster_url?: string; video_url?: string; task_id?: string; status?: string }
  type?: 'optimization_update' | 'standard_chat'
}

/**
 * Main page component
 */
export default function JustTravelApp() {
  const { data: session } = useSession()
  const isOnline = useOnlineStatus()
  const [isClient, setIsClient] = useState(false)
  const countryOptions = useMemo(() => countryList().getData(), [])

  // Form state
  const [loading, setLoading] = useState(false)
  const [showResults, setShowResults] = useState(false)
  const [formData, setFormData] = useState({
    originCountry: null as any,
    originCity: '',
    destCountry: null as any,
    destCity: '',
    flexibleDates: false,
    departureDate: '',
    returnDate: '',
    dateRangeText: '',
    flightType: 'direct',
    maxStopoverTime: '2',
    travelers: 1,
    budget: '',
    budgetType: 'per-person',
    eatOutside: 'no',
    dietary: '',
    meals: [] as string[]
  })

  // Chat state
  const [isChatOpen, setIsChatOpen] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [chatMessages, setChatMessages] = useState<Array<{ role: 'user' | 'bot'; text: string }>>([
    { role: 'bot', text: "Hi! I'm your AI guide. Need help planning or have questions about your destination?" }
  ])
  const [chatLoading, setChatLoading] = useState(false)

  // Auth state
  const [authModalOpen, setAuthModalOpen] = useState(false)
  const [isLoginMode, setIsLoginMode] = useState(true)
  const [authEmail, setAuthEmail] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authName, setAuthName] = useState('')
  const [authError, setAuthError] = useState('')
  const [currentUser, setCurrentUser] = useState<{ email: string; full_name?: string } | null>(null)

  // Itinerary state
  const [latestItinerary, setLatestItinerary] = useState<any>(null)
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set())
  const [pendingSave, setPendingSave] = useState<any>(null)
  const [notification, setNotification] = useState('')
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle')

  // Media assets state (for background video generation)
  const [creativeAssets, setCreativeAssets] = useState<{
    trip_poster_url?: string
    video_url?: string
    task_id?: string
    status?: string
  }>({})
  const [mediaTaskId, setMediaTaskId] = useState<string | null>(null)

  // Refs
  const chatContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => { setIsClient(true) }, [])

  // Auto-scroll chat
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [chatMessages])

  // Sync Google Session with Backend
  useEffect(() => {
    // @ts-ignore
    if (session?.id_token) {
      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        // @ts-ignore
        body: JSON.stringify({ id_token: session.id_token })
      }).then(async res => {
        if (res.ok) {
          const data = await res.json()
          setCurrentUser(data.user)
          setAuthModalOpen(false)
        }
      }).catch(console.error)
    }
  }, [session])

  // Check valid session on mount
  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/me`, {
      credentials: 'include'
    }).then(async res => {
      if (res.ok) {
        const user = await res.json()
        setCurrentUser(user)
      }
    }).catch(() => {})
  }, [])

  // Auto-sync pending saves when connection is restored
  useEffect(() => {
    if (isOnline && syncManager.hasPendingSaves()) {
      syncManager.syncPending(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')
        .then(() => {
          if (!syncManager.hasPendingSaves()) {
            setNotification('✅ All offline saves have been synced!')
            setTimeout(() => setNotification(''), 5000)
          }
        })
        .catch(console.error)
    }
  }, [isOnline])

  // Poll for video status when we have a media task
  useEffect(() => {
    if (!mediaTaskId || creativeAssets.status === 'completed') return

    const pollInterval = setInterval(async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/media-status/${mediaTaskId}`,
          { credentials: 'include' }
        )
        if (res.ok) {
          const data = await res.json()
          if (data.status === 'completed') {
            setCreativeAssets(prev => ({
              ...prev,
              video_url: data.video_url,
              trip_poster_url: data.poster_url || prev.trip_poster_url,
              status: 'completed'
            }))
            setNotification('🎬 Your trip video is ready!')
            setTimeout(() => setNotification(''), 5000)
          } else if (data.status === 'failed') {
            setCreativeAssets(prev => ({ ...prev, status: 'failed' }))
          }
        }
      } catch (err) {
        console.error('Media status poll failed:', err)
      }
    }, 5000) // Poll every 5 seconds

    return () => clearInterval(pollInterval)
  }, [mediaTaskId, creativeAssets.status])

  const handleMealChange = (meal: string) => {
    setFormData(prev => ({
      ...prev,
      meals: prev.meals.includes(meal) ? prev.meals.filter(m => m !== meal) : [...prev.meals, meal]
    }))
  }

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault()
    setAuthError('')

    const endpoint = isLoginMode ? '/api/auth/login' : '/api/auth/register'
    const body = isLoginMode
      ? { email: authEmail, password: authPassword }
      : { email: authEmail, password: authPassword, full_name: authName }

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(body)
      })

      if (res.ok) {
        const data = await res.json()
        setCurrentUser(data.user || { email: authEmail, full_name: authName })
        setAuthModalOpen(false)
        setAuthEmail('')
        setAuthPassword('')
        if (pendingSave) {
          const save = pendingSave
          setPendingSave(null)
          setTimeout(() => savePlan(save), 100)
        }
      } else {
        const data = await res.json()
        setAuthError(data.detail || 'Authentication failed')
      }
    } catch {
      setAuthError('Connection error')
    }
  }

  const savePlan = async (itinerary: any) => {
    // Prevent duplicate clicks
    if (saveStatus === 'saving') return

    if (!currentUser) {
      setPendingSave(itinerary)
      setAuthModalOpen(true)
      return
    }

    setSaveStatus('saving')

    try {
      const saveId = `itin-${Date.now()}`
      await offlineStorage.saveItinerary({
        id: saveId,
        destination: itinerary?.destination || formData.destCity || 'Unknown',
        summary: itinerary?.summary || '',
        itinerary_data: itinerary || {},
        creative_assets: {}
      })

      setSavedIds(prev => new Set(prev).add(saveId))

      if (isOnline) {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/itinerary/save`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            destination: itinerary?.destination || formData.destCity || 'Unknown',
            summary: itinerary?.summary || '',
            itinerary_data: itinerary || {},
            creative_assets: {}
          })
        })

        if (res.ok) {
          setSaveStatus('saved')
          setNotification('✅ Your trip has been saved!')
          setTimeout(() => {
            setNotification('')
            setSaveStatus('idle')
          }, 3000)
        } else {
          setSaveStatus('idle')
        }
      } else {
        syncManager.addPendingSave({
          id: saveId,
          data: {
            destination: itinerary?.destination || formData.destCity || 'Unknown',
            summary: itinerary?.summary || '',
            itinerary_data: itinerary || {},
            creative_assets: {}
          }
        })
        setSaveStatus('saved')
        setNotification('💾 Saved offline. Will sync when you\'re back online.')
        setTimeout(() => {
          setNotification('')
          setSaveStatus('idle')
        }, 3000)
      }
    } catch (e) {
      console.error('Save failed:', e)
      setSaveStatus('idle')
    }
  }

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setShowResults(false)

    try {
      // Build date info based on flexible or fixed dates
      const dateInfo = formData.flexibleDates
        ? `Flexible dates: ${formData.dateRangeText || 'anytime'}. Please find optimal dates based on weather, prices, and events.`
        : `Dates: ${formData.departureDate} to ${formData.returnDate}.`

      const message = `I want to travel from ${formData.originCity}, ${formData.originCountry?.label || ''} to ${formData.destCity}, ${formData.destCountry?.label || ''}.
${dateInfo}
${formData.travelers} traveler(s), budget: $${formData.budget} ${formData.budgetType}.
Flight preference: ${formData.flightType}${formData.flightType === 'stops' ? ` (max ${formData.maxStopoverTime}h layover)` : ''}.
${formData.eatOutside === 'yes' ? `Dining: ${formData.dietary || 'Standard'}, meals: ${formData.meals.join(', ')}` : 'No dining recommendations needed.'}`

      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          message,
          preferences: {
            dietary: formData.dietary ? [formData.dietary] : [],
            budget_per_day_usd: parseInt(formData.budget) || 200,
            trip_type: 'exploration',
            destination: formData.destCity,
            origin: formData.originCity,
            travelers: formData.travelers,
            travel_dates: formData.flexibleDates
              ? { flexible: true, range_text: formData.dateRangeText }
              : { departure: formData.departureDate, return: formData.returnDate }
          }
        })
      })

      if (res.ok) {
        const response: AgentResponse = await res.json()
        if (response.data?.itinerary) {
          setLatestItinerary(response.data.itinerary)
        }

        // Extract creative assets from response
        if (response.creative) {
          setCreativeAssets({
            trip_poster_url: response.creative.poster_url,
            video_url: response.creative.video_url,
            task_id: response.creative.task_id,
            status: response.creative.status || 'generating'
          })
          // Start polling if video is still generating
          if (response.creative.task_id && response.creative.status !== 'completed') {
            setMediaTaskId(response.creative.task_id)
          }
        }

        setShowResults(true)
      }
    } catch (error) {
      console.error('Generation error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleChatSubmit = async () => {
    if (!chatInput.trim() || chatLoading) return

    setChatMessages(prev => [...prev, { role: 'user', text: chatInput }])
    setChatInput('')
    setChatLoading(true)

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          message: chatInput,
          preferences: {
            existing_itinerary: latestItinerary,
            // Pass user preferences so chatbot is context-aware
            destination: formData.destCity,
            origin: formData.originCity,
            travelers: formData.travelers,
            budget_per_day_usd: parseInt(formData.budget) || 200,
            dietary: formData.dietary ? [formData.dietary] : [],
            travel_dates: formData.flexibleDates
              ? { flexible: true, range_text: formData.dateRangeText }
              : { departure: formData.departureDate, return: formData.returnDate }
          }
        })
      })

      if (res.ok) {
        const data: AgentResponse = await res.json()
        setChatMessages(prev => [...prev, { role: 'bot', text: data.message || "I'm here to help!" }])

        if (data.type === 'optimization_update' && data.data?.itinerary) {
          setLatestItinerary(data.data.itinerary)
          setNotification('✅ Your itinerary has been updated!')
          setTimeout(() => setNotification(''), 5000)
        }
      }
    } catch {
      setChatMessages(prev => [...prev, { role: 'bot', text: "Sorry, I couldn't connect. Please try again." }])
    } finally {
      setChatLoading(false)
    }
  }

  if (!isClient) return null

  return (
    <main id="plan" className="min-h-screen flex flex-col items-center py-12 px-4 relative">
      {/* Full-screen Loading Experience */}
      <LoadingExperience isLoading={loading} />

      {/* Notification Banner */}
      {notification && (
        <div className="fixed top-20 left-1/2 transform -translate-x-1/2 z-50 bg-gradient-to-r from-orange-500 to-pink-500 text-white px-6 py-3 rounded-full font-bold shadow-lg shadow-orange-500/30 animate-slide-up">
          {notification}
        </div>
      )}

      {/* User Status Bar */}
      <div className="w-full max-w-3xl mb-6 flex justify-end items-center gap-4">
        {currentUser ? (
          <div className="flex items-center gap-3 bg-white/5 backdrop-blur-xl border border-white/10 px-4 py-2 rounded-full">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
            <span className="font-black text-sm text-white/80">{currentUser.full_name || currentUser.email}</span>
            <button
              onClick={async () => {
                await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/logout`, {
                  method: 'POST',
                  credentials: 'include'
                })
                setCurrentUser(null)
                signOut({ redirect: false })
              }}
              className="text-xs font-black text-white/50 hover:text-orange-400 transition-colors"
            >
              Logout
            </button>
            <button
              onClick={async () => {
                if (!window.confirm('Delete your account? This cannot be undone.')) return
                const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/account`, {
                  method: 'DELETE',
                  credentials: 'include'
                })
                if (res.ok) {
                  setCurrentUser(null)
                  signOut({ redirect: false })
                }
              }}
              className="text-xs font-black text-red-400/70 hover:text-red-400 transition-colors"
            >
              Delete
            </button>
          </div>
        ) : (
          <button
            onClick={() => setAuthModalOpen(true)}
            className="bg-gradient-to-r from-orange-500 to-pink-500 text-white font-black font-bold text-sm px-5 py-2.5 rounded-full hover:opacity-90 transition-all shadow-lg shadow-orange-500/25"
          >
            Login / Signup
          </button>
        )}
      </div>

      {/* Header */}
      <header className="mb-10 text-center">
        <h1 className="text-5xl md:text-6xl font-black text-white tracking-tighter uppercase">
          Plan Your <span className="text-orange-400">Journey</span>
        </h1>
        <p className="text-white/50 font-medium tracking-widest mt-2">AI-Powered Travel Planning</p>
        <div className="h-1 w-24 bg-gradient-to-r from-orange-500 to-pink-500 mx-auto mt-4 rounded-full shadow-lg shadow-orange-500/30" />
      </header>

      {/* Main Form - Dark Glassmorphism */}
      <div className="max-w-3xl w-full bg-white/[0.03] backdrop-blur-3xl rounded-[40px] border border-white/10 p-8 md:p-12 shadow-2xl mb-20">
        <form onSubmit={handleGenerate} className="space-y-12">

          {/* 1. Origin & Destination */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
            <div className="space-y-4">
              <label className="text-orange-400 font-black text-sm uppercase tracking-widest">1. From Where</label>
              <Select
                options={countryOptions}
                placeholder="Country..."
                onChange={(val) => setFormData({ ...formData, originCountry: val })}
                styles={darkSelectStyles}
              />
              <input
                required
                type="text"
                placeholder="CITY NAME"
                value={formData.originCity}
                className="w-full bg-transparent border-b-2 border-white/10 py-2 text-2xl text-white outline-none focus:border-orange-500 font-bold uppercase transition-all placeholder:text-white/20"
                onChange={(e) => setFormData({ ...formData, originCity: e.target.value })}
              />
            </div>

            <div className="space-y-4">
              <label className="text-orange-400 font-black text-sm uppercase tracking-widest">2. Destination</label>
              <Select
                options={countryOptions}
                placeholder="Country..."
                onChange={(val) => setFormData({ ...formData, destCountry: val })}
                styles={darkSelectStyles}
              />
              <input
                required
                type="text"
                placeholder="CITY NAME"
                value={formData.destCity}
                className="w-full bg-transparent border-b-2 border-white/10 py-2 text-2xl text-white outline-none focus:border-blue-400 font-bold uppercase transition-all placeholder:text-white/20"
                onChange={(e) => setFormData({ ...formData, destCity: e.target.value })}
              />
            </div>
          </div>

          {/* Travel Dates */}
          <div className="bg-white/5 p-6 rounded-3xl border border-white/10 space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-orange-400 font-black text-sm uppercase tracking-widest">Travel Dates</label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.flexibleDates}
                  onChange={(e) => setFormData({ ...formData, flexibleDates: e.target.checked })}
                  className="w-5 h-5 accent-orange-500 rounded"
                />
                <span className="text-sm text-white/70 font-bold">I'm flexible</span>
              </label>
            </div>

            {formData.flexibleDates ? (
              <div className="space-y-3">
                <input
                  type="text"
                  placeholder="e.g., mid February to late April, or any weekend in March..."
                  value={formData.dateRangeText}
                  className="w-full bg-white/5 border border-white/10 p-4 rounded-2xl text-white font-bold outline-none focus:border-orange-500 transition-all placeholder:text-white/30 placeholder:font-normal"
                  onChange={(e) => setFormData({ ...formData, dateRangeText: e.target.value })}
                />
                <div className="flex items-start gap-2 p-3 bg-gradient-to-r from-orange-500/10 to-pink-500/10 rounded-xl border border-orange-500/20">
                  <span className="text-lg">💬</span>
                  <p className="text-sm text-white/70">
                    <span className="text-orange-400 font-bold">Pro tip:</span> Our AI will find the optimal dates based on weather, prices, and events. Use the chat assistant below to refine your preferences!
                  </p>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-white/60 font-bold text-xs uppercase">Departure</label>
                  <input
                    required={!formData.flexibleDates}
                    type="date"
                    value={formData.departureDate}
                    min={new Date().toISOString().split('T')[0]}
                    className="w-full bg-white/5 border border-white/10 p-4 rounded-2xl text-white font-bold outline-none focus:border-orange-500 transition-all [color-scheme:dark]"
                    onChange={(e) => setFormData({ ...formData, departureDate: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-white/60 font-bold text-xs uppercase">Return</label>
                  <input
                    required={!formData.flexibleDates}
                    type="date"
                    value={formData.returnDate}
                    min={formData.departureDate || new Date().toISOString().split('T')[0]}
                    className="w-full bg-white/5 border border-white/10 p-4 rounded-2xl text-white font-bold outline-none focus:border-pink-500 transition-all [color-scheme:dark]"
                    onChange={(e) => setFormData({ ...formData, returnDate: e.target.value })}
                  />
                </div>
              </div>
            )}
          </div>

          {/* 3. Flight Preference */}
          <div className="bg-white/5 p-6 rounded-3xl border border-white/10 space-y-6">
            <label className="text-orange-400 font-black text-sm uppercase tracking-widest">3. Flight Preference</label>
            <div className="flex gap-4">
              {['direct', 'stops'].map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setFormData({ ...formData, flightType: type })}
                  className={`flex-1 py-4 rounded-2xl font-black text-sm transition-all ${
                    formData.flightType === type
                      ? 'bg-orange-500 text-white shadow-lg shadow-orange-500/30'
                      : 'bg-white/5 text-white/40 hover:bg-white/10'
                  }`}
                >
                  {type === 'direct' ? 'DIRECT FLIGHT' : 'WITH STOPS'}
                </button>
              ))}
            </div>
            {formData.flightType === 'stops' && (
              <div className="pt-2">
                <label className="text-white/60 text-xs font-bold mb-2 block">Max Layover: {formData.maxStopoverTime}h</label>
                <input
                  type="range"
                  min="1"
                  max="24"
                  value={formData.maxStopoverTime}
                  className="w-full accent-orange-500"
                  onChange={(e) => setFormData({ ...formData, maxStopoverTime: e.target.value })}
                />
              </div>
            )}
          </div>

          {/* 4 & 5. Travelers & Budget */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-orange-400 font-black text-xs uppercase">4. Travelers</label>
              <input
                type="number"
                min="1"
                value={formData.travelers}
                className="w-full bg-white/5 border border-white/10 p-4 rounded-2xl text-white font-bold outline-none focus:border-orange-500 transition-all"
                onChange={(e) => setFormData({ ...formData, travelers: parseInt(e.target.value) || 1 })}
              />
            </div>
            <div className="space-y-2">
              <label className="text-orange-400 font-black text-xs uppercase">5. Budget ($)</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Amount"
                  value={formData.budget}
                  className="flex-[2] bg-white/5 border border-white/10 p-4 rounded-2xl text-white font-bold outline-none focus:border-orange-500 placeholder:text-white/30 transition-all"
                  onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
                />
                <select
                  className="flex-1 bg-white/10 border border-white/10 p-4 rounded-2xl text-white text-xs font-bold outline-none"
                  value={formData.budgetType}
                  onChange={(e) => setFormData({ ...formData, budgetType: e.target.value })}
                >
                  <option value="per-person">/ Pers.</option>
                  <option value="total">Total</option>
                </select>
              </div>
            </div>
          </div>

          {/* 6. Dining Plans */}
          <div className="space-y-6">
            <label className="text-orange-400 font-black text-sm uppercase italic tracking-widest">6. Dining Plans</label>
            <div className="flex gap-4">
              {['yes', 'no'].map((opt) => (
                <button
                  key={opt}
                  type="button"
                  onClick={() => setFormData({ ...formData, eatOutside: opt })}
                  className={`flex-1 py-4 rounded-2xl font-black transition-all ${
                    formData.eatOutside === opt
                      ? 'bg-orange-500 text-white shadow-lg shadow-orange-500/30'
                      : 'bg-white/5 text-white/40 hover:bg-white/10'
                  }`}
                >
                  {opt === 'yes' ? 'EAT OUTSIDE' : 'NO THANKS'}
                </button>
              ))}
            </div>

            {formData.eatOutside === 'yes' && (
              <div className="grid grid-cols-1 gap-4 animate-in zoom-in-95">
                <select
                  className="w-full bg-white/10 border border-white/10 p-4 rounded-2xl text-orange-400 font-bold outline-none"
                  value={formData.dietary}
                  onChange={(e) => setFormData({ ...formData, dietary: e.target.value })}
                >
                  <option value="">Select Dietary...</option>
                  <option value="vegan">Vegan</option>
                  <option value="vegetarian">Vegetarian</option>
                  <option value="halal">Halal</option>
                  <option value="kosher">Kosher</option>
                  <option value="gluten-free">Gluten-Free</option>
                </select>
                <div className="grid grid-cols-2 gap-3">
                  {['Breakfast', 'Lunch', 'Dinner', 'Snacks'].map((meal) => (
                    <label key={meal} className="flex items-center gap-3 p-4 bg-white/5 rounded-2xl border border-white/10 cursor-pointer hover:bg-white/10 transition-all">
                      <input
                        type="checkbox"
                        checked={formData.meals.includes(meal)}
                        onChange={() => handleMealChange(meal)}
                        className="w-5 h-5 accent-orange-500"
                      />
                      <span className="text-sm font-bold text-white/80">{meal}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !isOnline}
            className="w-full py-6 rounded-3xl bg-gradient-to-r from-orange-600 to-pink-600 text-white font-black text-xl shadow-2xl shadow-orange-500/30 hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-50"
          >
            {loading ? 'BREWING YOUR ADVENTURE...' : !isOnline ? 'OFFLINE - CONNECT TO PLAN' : 'GENERATE MY JOURNEY'}
          </button>
        </form>

        {/* Results */}
        <AnimatePresence>
          {showResults && (
            <motion.div
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-20 space-y-10"
            >
              <div className="text-center">
                <h2 className="text-4xl font-black text-white italic">YOUR TAILORED JOURNEY</h2>
                <div className="h-1 w-20 bg-gradient-to-r from-orange-500 to-pink-500 mx-auto mt-2 rounded-full" />
              </div>

              <TransportBox data={formData} />
              <FoodBox data={formData} />

              {latestItinerary && (
                <>
                  <ItineraryView
                    itinerary={latestItinerary.daily_itinerary || latestItinerary.itinerary || latestItinerary}
                    summary={latestItinerary}
                    tripTitle={latestItinerary.trip_title}
                    flights={latestItinerary.flights}
                    accommodation={latestItinerary.accommodation}
                    creativeAssets={{
                      trip_poster_url: creativeAssets.trip_poster_url || latestItinerary.creative?.trip_poster_url,
                      video_url: creativeAssets.video_url || latestItinerary.creative?.video_url,
                      daily_posters: latestItinerary.creative?.daily_posters
                    }}
                  />
                  <button
                    onClick={() => savePlan(latestItinerary)}
                    disabled={saveStatus === 'saving' || saveStatus === 'saved'}
                    className={`w-full py-4 text-white font-black text-lg rounded-2xl shadow-lg hover:scale-[1.02] active:scale-95 transition-all ${
                      saveStatus === 'saved'
                        ? 'bg-gradient-to-r from-green-600 to-emerald-600 shadow-green-500/30'
                        : saveStatus === 'saving'
                        ? 'bg-gradient-to-r from-orange-500 to-pink-500 shadow-orange-500/30 opacity-75'
                        : 'bg-gradient-to-r from-green-500 to-emerald-500 shadow-green-500/30'
                    }`}
                  >
                    {saveStatus === 'saving' ? '⏳ SAVING...' :
                     saveStatus === 'saved' ? '✅ TRIP SAVED!' :
                     '💾 SAVE THIS ITINERARY'}
                  </button>
                </>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Floating Chat Bubble */}
      <div className="fixed bottom-6 right-6 z-50">
        <button
          onClick={() => setIsChatOpen(!isChatOpen)}
          className="w-16 h-16 bg-gradient-to-r from-orange-500 to-pink-500 rounded-full shadow-2xl shadow-orange-500/40 flex items-center justify-center hover:scale-110 transition-transform active:scale-90"
        >
          {isChatOpen ? <span className="text-white text-2xl font-bold">✕</span> : <span className="text-2xl">✈️</span>}
        </button>

        <AnimatePresence>
          {isChatOpen && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.8, y: 20 }}
              className="absolute bottom-20 right-0 w-[350px] h-[500px] bg-[#0d0d2b] border border-white/20 rounded-[32px] shadow-2xl overflow-hidden flex flex-col backdrop-blur-xl"
            >
              <div className="p-4 bg-gradient-to-r from-orange-600 to-pink-600 text-white font-bold flex justify-between items-center">
                <span>✈️ TRAVEL ASSISTANT</span>
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              </div>

              <div ref={chatContainerRef} className="flex-1 p-4 text-sm space-y-4 overflow-y-auto">
                {chatMessages.map((m, i) => (
                  <div
                    key={i}
                    className={`p-3 rounded-2xl max-w-[85%] ${
                      m.role === 'user'
                        ? 'bg-orange-500 text-white ml-auto rounded-tr-none'
                        : 'bg-white/10 text-white/80 rounded-tl-none'
                    }`}
                  >
                    {m.text}
                  </div>
                ))}
                {chatLoading && <div className="text-white/50 italic font-mono">Thinking...</div>}
              </div>

              <div className="p-4 border-t border-white/10 bg-white/5">
                <div className="flex gap-2">
                  <input
                    autoFocus
                    type="text"
                    placeholder="Ask me anything..."
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleChatSubmit()}
                    className="flex-1 bg-white/5 border border-white/20 p-3 rounded-2xl text-white outline-none focus:border-orange-500 text-sm placeholder:text-white/30"
                  />
                  <button
                    onClick={handleChatSubmit}
                    disabled={chatLoading}
                    className="bg-gradient-to-r from-orange-500 to-pink-500 text-white px-4 py-2 rounded-2xl font-bold hover:opacity-90 transition-all disabled:opacity-50"
                  >
                    →
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Auth Modal - Dark Theme */}
      {authModalOpen && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-[#0d0d2b] max-w-md w-full rounded-[32px] border border-white/20 shadow-2xl p-8 relative">
            <button
              onClick={() => setAuthModalOpen(false)}
              className="absolute top-4 right-4 text-2xl text-white/40 hover:text-white transition-colors"
            >
              ✕
            </button>

            <h2 className="text-3xl font-black text-white mb-6 text-center">
              {isLoginMode ? 'WELCOME BACK' : 'JOIN THE TRIP'}
            </h2>

            <form onSubmit={handleAuth} className="space-y-4">
              {!isLoginMode && (
                <div>
                  <label className="block font-bold text-sm mb-1 text-white/60">FULL NAME</label>
                  <input
                    type="text"
                    required={!isLoginMode}
                    value={authName}
                    onChange={e => setAuthName(e.target.value)}
                    className="w-full bg-white/5 border border-white/20 p-3 rounded-xl text-white font-mono outline-none focus:border-orange-500 placeholder:text-white/30"
                    placeholder="John Doe"
                  />
                </div>
              )}

              <div>
                <label className="block font-bold text-sm mb-1 text-white/60">EMAIL</label>
                <input
                  type="email"
                  required
                  value={authEmail}
                  onChange={e => setAuthEmail(e.target.value)}
                  className="w-full bg-white/5 border border-white/20 p-3 rounded-xl text-white font-mono outline-none focus:border-orange-500 placeholder:text-white/30"
                  placeholder="traveler@example.com"
                />
              </div>

              <div>
                <label className="block font-bold text-sm mb-1 text-white/60">PASSWORD</label>
                <input
                  type="password"
                  required
                  value={authPassword}
                  onChange={e => setAuthPassword(e.target.value)}
                  className="w-full bg-white/5 border border-white/20 p-3 rounded-xl text-white font-mono outline-none focus:border-orange-500 placeholder:text-white/30"
                  placeholder="••••••••"
                />
              </div>

              {authError && (
                <div className="bg-red-500/20 border border-red-500/50 text-red-400 p-3 font-mono text-sm rounded-xl">
                  {authError}
                </div>
              )}

              <button
                type="submit"
                className="w-full py-4 bg-gradient-to-r from-orange-500 to-pink-500 text-white font-black text-lg rounded-xl hover:opacity-90 transition-all"
              >
                {isLoginMode ? 'LOGIN' : 'REGISTER'}
              </button>
            </form>

            <div className="my-6 flex items-center gap-2">
              <div className="h-px bg-white/20 flex-1"></div>
              <span className="font-mono text-xs text-white/40">OR</span>
              <div className="h-px bg-white/20 flex-1"></div>
            </div>

            <button
              onClick={() => signIn('google')}
              className="w-full py-3 bg-white/10 border border-white/20 rounded-xl flex items-center justify-center gap-2 font-bold text-white hover:bg-white/20 transition-all"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
              </svg>
              Sign in with Google
            </button>

            <div className="mt-4 text-center">
              <button
                onClick={() => setIsLoginMode(!isLoginMode)}
                className="text-sm font-mono underline text-white/50 hover:text-orange-400 transition-colors"
              >
                {isLoginMode ? 'Need an account? Register' : 'Already have an account? Login'}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}

// Dark theme styles for react-select
const darkSelectStyles = {
  control: (base: any) => ({
    ...base,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '16px',
    padding: '4px',
    color: 'white',
    boxShadow: 'none',
    '&:hover': { border: '1px solid rgba(255, 255, 255, 0.3)' }
  }),
  menu: (base: any) => ({
    ...base,
    backgroundColor: '#0a0a2e',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '16px',
    overflow: 'hidden'
  }),
  option: (base: any, state: any) => ({
    ...base,
    backgroundColor: state.isFocused ? 'rgba(255, 165, 0, 0.2)' : 'transparent',
    color: 'white',
    fontSize: '14px',
    cursor: 'pointer'
  }),
  singleValue: (base: any) => ({ ...base, color: 'white', fontWeight: 'bold' }),
  input: (base: any) => ({ ...base, color: 'white' }),
  placeholder: (base: any) => ({ ...base, color: 'rgba(255,255,255,0.3)' })
}
