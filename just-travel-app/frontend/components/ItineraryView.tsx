"use client";

import React from 'react'

interface Activity {
    name: string
    type: string
    location: string | object
    duration: number
    price_level?: number
    notes?: string
}

interface TimeSlot {
    start_time: string
    end_time: string
    activity_type: string
    activity: Activity
    location: string
    notes: string
}

interface DayPlan {
    date: string
    day_number: number
    theme: string
    daily_highlight?: string
    visual_theme?: string
    key_locations?: string[]
    time_slots: TimeSlot[]
    total_travel_time: number
    estimated_cost: number
}

interface DailyPoster {
    day: number
    poster_url: string
}

interface CreativeAssets {
    trip_poster_url?: string
    daily_posters?: DailyPoster[]
    video_url?: string
}

interface FlightInfo {
    airline: string
    flight_number: string
    departure_airport: string
    arrival_airport: string
    departure_time: string
    arrival_time: string
    price_estimate?: number
}

interface Flights {
    outbound?: FlightInfo
    return?: FlightInfo
}

interface Accommodation {
    name: string
    type: string
    address: string
    check_in: string
    check_out: string
    price_per_night?: number
    total_nights?: number
    notes?: string
}

interface ItineraryProps {
    itinerary: DayPlan[]
    summary?: {
        total_days: number
        total_activities: number
        estimated_total_cost: number
        day_themes: string[]
    }
    creativeAssets?: CreativeAssets
    tripTitle?: string
    flights?: Flights
    accommodation?: Accommodation
}

// Helper function to get activity type icon
const getActivityIcon = (type: string) => {
    switch(type) {
        case 'arrival': return '🛬'
        case 'departure': return '🛫'
        case 'transport': return '🚕'
        case 'accommodation': return '🏨'
        case 'meal': return '🍽️'
        case 'attraction': return '📍'
        default: return '📌'
    }
}

// Helper function to calculate flight duration
const calculateFlightDuration = (departure: string, arrival: string): string => {
    try {
        const dep = new Date(departure)
        const arr = new Date(arrival)
        const diffMs = arr.getTime() - dep.getTime()
        if (diffMs < 0) return ''
        const hours = Math.floor(diffMs / (1000 * 60 * 60))
        const mins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))
        return `${hours}h ${mins}m`
    } catch {
        return ''
    }
}

// Helper function to calculate cost breakdown
const calculateCostBreakdown = (
    flights?: Flights,
    accommodation?: Accommodation,
    itinerary?: DayPlan[]
) => {
    // Flight costs
    const flightTotal = (flights?.outbound?.price_estimate || 0) + (flights?.return?.price_estimate || 0)

    // Hotel costs
    const hotelTotal = (accommodation?.price_per_night || 0) * (accommodation?.total_nights || 1)

    // Estimate meals and transport from price_level
    // Price level estimates: 1=$15, 2=$35, 3=$75 for meals
    // Transport: 1=$10, 2=$25, 3=$50
    const mealPrices: Record<number, number> = { 1: 15, 2: 35, 3: 75 }
    const transportPrices: Record<number, number> = { 1: 10, 2: 25, 3: 50 }

    let mealTotal = 0
    let transportTotal = 0

    itinerary?.forEach((day) => {
        day.time_slots?.forEach((slot) => {
            const priceLevel = slot.activity?.price_level || 2
            if (slot.activity_type === 'meal') {
                mealTotal += mealPrices[priceLevel] || 35
            } else if (slot.activity_type === 'transport') {
                transportTotal += transportPrices[priceLevel] || 25
            }
        })
    })

    return { flightTotal, hotelTotal, mealTotal, transportTotal }
}

export function ItineraryView({ itinerary, summary, creativeAssets, tripTitle, flights, accommodation }: ItineraryProps) {
    const [activeDay, setActiveDay] = React.useState(1)

    // Defensive check: ensure itinerary is an array
    // Handle cases where full itinerary object is passed instead of daily_itinerary array
    const dailyItinerary = Array.isArray(itinerary)
        ? itinerary
        : (itinerary as unknown as { daily_itinerary?: DayPlan[] })?.daily_itinerary || []

    if (!dailyItinerary || dailyItinerary.length === 0) return null

    // Derive stats from itinerary if summary not provided
    const totalDays = summary?.total_days || dailyItinerary.length
    const totalActivities = summary?.total_activities || dailyItinerary.reduce((sum, day) => sum + (day.time_slots?.length || 0), 0)

    // Use consistent cost calculation (same as Cost Breakdown card)
    const costs = calculateCostBreakdown(flights, accommodation, dailyItinerary)
    const totalCost = costs.flightTotal + costs.hotelTotal + costs.mealTotal + costs.transportTotal

    const currentDay = dailyItinerary.find(d => d.day_number === activeDay) || dailyItinerary[0]

    // Get daily poster for current day
    const currentDayPoster = creativeAssets?.daily_posters?.find(p => p.day === activeDay)?.poster_url

    return (
        <div className="space-y-6 mt-4 animate-slide-up">
            {/* Trip Poster & Video Hero */}
            {(creativeAssets?.trip_poster_url || creativeAssets?.video_url) && (
                <div className="bg-white/[0.03] backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden">
                    {creativeAssets?.trip_poster_url && (
                        <div className="relative">
                            <img
                                src={creativeAssets.trip_poster_url}
                                alt={tripTitle || "Trip Poster"}
                                className="w-full h-64 md:h-80 object-cover"
                            />
                            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-6">
                                <h2 className="text-2xl md:text-3xl font-black text-white">
                                    {tripTitle || "Your Adventure Awaits"}
                                </h2>
                            </div>
                        </div>
                    )}
                    {creativeAssets?.video_url && (
                        <div className="p-4 border-t border-white/10">
                            <p className="text-xs text-orange-400 font-mono uppercase mb-2">🎬 Trip Preview</p>
                            <video
                                src={creativeAssets.video_url}
                                controls
                                className="w-full rounded-lg"
                                poster={creativeAssets.trip_poster_url}
                            />
                        </div>
                    )}
                    {/* Download Buttons */}
                    {(creativeAssets?.trip_poster_url || creativeAssets?.video_url) && (
                        <div className="flex flex-wrap gap-2 p-4 border-t border-white/10">
                            {creativeAssets?.trip_poster_url && (
                                <a
                                    href={creativeAssets.trip_poster_url}
                                    download="trip-poster.png"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-orange-500 to-pink-500 text-white font-bold rounded-xl hover:scale-105 transition-transform text-sm"
                                >
                                    📥 Download Poster
                                </a>
                            )}
                            {creativeAssets?.video_url && (
                                <a
                                    href={creativeAssets.video_url}
                                    download="trip-video.mp4"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-bold rounded-xl hover:scale-105 transition-transform text-sm"
                                >
                                    📥 Download Video
                                </a>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* Summary Card */}
            <div className="bg-white/[0.03] backdrop-blur-xl p-6 rounded-2xl border border-white/10">
                <h3 className="text-xl font-mono font-bold mb-4 text-orange-400 uppercase">
                    Trip Summary
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="p-3 bg-white/5 rounded-xl border border-white/10 text-center">
                        <span className="block text-2xl font-bold text-white">{totalDays}</span>
                        <span className="text-xs font-mono uppercase text-white/60">Days</span>
                    </div>
                    <div className="p-3 bg-white/5 rounded-xl border border-white/10 text-center">
                        <span className="block text-2xl font-bold text-white">{totalActivities}</span>
                        <span className="text-xs font-mono uppercase text-white/60">Activities</span>
                    </div>
                    <div className="p-3 bg-white/5 rounded-xl border border-white/10 text-center">
                        <span className="block text-2xl font-bold text-pink-400">${totalCost}</span>
                        <span className="text-xs font-mono uppercase text-white/60">Est. Cost</span>
                    </div>
                    <div className="p-3 bg-white/5 rounded-xl border border-white/10 text-center">
                        <span className="block text-2xl font-bold text-orange-400">∞</span>
                        <span className="text-xs font-mono uppercase text-white/60">Memories</span>
                    </div>
                </div>
            </div>

            {/* Flights Card */}
            {flights && (flights.outbound || flights.return) && (
                <div className="bg-white/[0.03] backdrop-blur-xl p-6 rounded-2xl border border-white/10">
                    <h3 className="text-xl font-mono font-bold mb-4 text-pink-400 uppercase">
                        ✈️ Flights
                    </h3>
                    <div className="grid md:grid-cols-2 gap-4">
                        {flights.outbound && (
                            <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                                <span className="text-xs text-white/50 uppercase font-mono">Outbound</span>
                                <p className="font-bold text-white mt-1">{flights.outbound.airline} {flights.outbound.flight_number}</p>
                                <p className="text-sm text-white/70 font-mono">
                                    {flights.outbound.departure_airport} → {flights.outbound.arrival_airport}
                                </p>
                                <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-white/50">
                                    <span>🛫 {new Date(flights.outbound.departure_time).toLocaleString()}</span>
                                    <span>🛬 {new Date(flights.outbound.arrival_time).toLocaleString()}</span>
                                </div>
                                {calculateFlightDuration(flights.outbound.departure_time, flights.outbound.arrival_time) && (
                                    <p className="text-orange-400 font-mono text-sm mt-2">
                                        Duration: {calculateFlightDuration(flights.outbound.departure_time, flights.outbound.arrival_time)}
                                    </p>
                                )}
                                {flights.outbound.price_estimate && (
                                    <p className="text-green-400 font-mono text-sm mt-1">${flights.outbound.price_estimate}</p>
                                )}
                            </div>
                        )}
                        {flights.return && (
                            <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                                <span className="text-xs text-white/50 uppercase font-mono">Return</span>
                                <p className="font-bold text-white mt-1">{flights.return.airline} {flights.return.flight_number}</p>
                                <p className="text-sm text-white/70 font-mono">
                                    {flights.return.departure_airport} → {flights.return.arrival_airport}
                                </p>
                                <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-white/50">
                                    <span>🛫 {new Date(flights.return.departure_time).toLocaleString()}</span>
                                    <span>🛬 {new Date(flights.return.arrival_time).toLocaleString()}</span>
                                </div>
                                {calculateFlightDuration(flights.return.departure_time, flights.return.arrival_time) && (
                                    <p className="text-orange-400 font-mono text-sm mt-2">
                                        Duration: {calculateFlightDuration(flights.return.departure_time, flights.return.arrival_time)}
                                    </p>
                                )}
                                {flights.return.price_estimate && (
                                    <p className="text-green-400 font-mono text-sm mt-1">${flights.return.price_estimate}</p>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Accommodation Card */}
            {accommodation && (
                <div className="bg-white/[0.03] backdrop-blur-xl p-6 rounded-2xl border border-white/10">
                    <h3 className="text-xl font-mono font-bold mb-4 text-purple-400 uppercase">
                        🏨 Accommodation
                    </h3>
                    <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                        <p className="font-bold text-lg text-white">{accommodation.name}</p>
                        <p className="text-sm text-white/60 font-mono">📍 {accommodation.address}</p>
                        <div className="flex flex-wrap gap-4 mt-3 text-sm">
                            <span className="text-green-400 font-mono">
                                Check-in: {new Date(accommodation.check_in + 'T00:00:00').toLocaleDateString()}
                            </span>
                            <span className="text-orange-400 font-mono">
                                Check-out: {new Date(accommodation.check_out + 'T00:00:00').toLocaleDateString()}
                            </span>
                        </div>
                        {accommodation.price_per_night && (
                            <p className="text-pink-400 font-mono mt-2">
                                ${accommodation.price_per_night}/night × {accommodation.total_nights || '?'} nights
                                = ${(accommodation.price_per_night * (accommodation.total_nights || 1))}
                            </p>
                        )}
                        {accommodation.notes && (
                            <p className="text-sm text-white/50 mt-2 italic">{accommodation.notes}</p>
                        )}
                    </div>
                </div>
            )}

            {/* Cost Breakdown Card */}
            {(() => {
                const costs = calculateCostBreakdown(flights, accommodation, dailyItinerary)
                const grandTotal = costs.flightTotal + costs.hotelTotal + costs.mealTotal + costs.transportTotal
                const hasAnyCosts = grandTotal > 0

                if (!hasAnyCosts) return null

                return (
                    <div className="bg-white/[0.03] backdrop-blur-xl p-6 rounded-2xl border border-white/10">
                        <h3 className="text-xl font-mono font-bold mb-4 text-green-400 uppercase">
                            💰 Trip Cost Estimate
                        </h3>
                        <div className="space-y-3">
                            {costs.flightTotal > 0 && (
                                <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl border border-white/10">
                                    <span className="text-white/60 font-mono">✈️ Flights (round trip)</span>
                                    <span className="text-white font-bold font-mono">${costs.flightTotal}</span>
                                </div>
                            )}
                            {costs.hotelTotal > 0 && (
                                <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl border border-white/10">
                                    <span className="text-white/60 font-mono">🏨 Hotel ({accommodation?.total_nights || 1} nights)</span>
                                    <span className="text-white font-bold font-mono">${costs.hotelTotal}</span>
                                </div>
                            )}
                            {costs.mealTotal > 0 && (
                                <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl border border-white/10">
                                    <span className="text-white/60 font-mono">🍽️ Meals (estimated)</span>
                                    <span className="text-white font-bold font-mono">${costs.mealTotal}</span>
                                </div>
                            )}
                            {costs.transportTotal > 0 && (
                                <div className="flex justify-between items-center p-3 bg-white/5 rounded-xl border border-white/10">
                                    <span className="text-white/60 font-mono">🚕 Transport (estimated)</span>
                                    <span className="text-white font-bold font-mono">${costs.transportTotal}</span>
                                </div>
                            )}
                            <div className="border-t border-white/10 pt-4 mt-4">
                                <div className="flex justify-between items-center">
                                    <span className="text-white font-bold text-lg">Total Estimate</span>
                                    <span className="text-green-400 font-black text-2xl font-mono">
                                        ${grandTotal}
                                    </span>
                                </div>
                                <p className="text-xs text-white/40 mt-2 italic">
                                    * Meal and transport costs are estimates based on activity price levels
                                </p>
                            </div>
                        </div>
                    </div>
                )
            })()}

            {/* Day Tabs */}
            <div className="flex overflow-x-auto gap-2 pb-2 scrollbar-hide">
                {dailyItinerary.map((day) => {
                    const hasPoster = creativeAssets?.daily_posters?.some(p => p.day === day.day_number && p.poster_url)
                    return (
                        <button
                            key={day.day_number}
                            onClick={() => setActiveDay(day.day_number)}
                            className={`
                                flex-shrink-0 px-4 py-2 font-mono font-bold rounded-xl transition-all
                                ${activeDay === day.day_number
                                    ? 'bg-gradient-to-r from-orange-500 to-pink-500 text-white'
                                    : 'bg-white/5 text-white/70 hover:bg-white/10 border border-white/10'}
                            `}
                        >
                            Day {day.day_number}
                            {hasPoster && <span className="ml-1 text-xs">📷</span>}
                        </button>
                    )
                })}
            </div>

            {/* Daily Schedule */}
            <div className="bg-white/[0.03] backdrop-blur-xl p-6 rounded-2xl border border-white/10">
                {/* Daily Poster (if available) */}
                {currentDayPoster && (
                    <div className="mb-6 -mx-6 -mt-6">
                        <img
                            src={currentDayPoster}
                            alt={`Day ${currentDay.day_number} - ${currentDay.theme}`}
                            className="w-full h-48 object-cover rounded-t-2xl"
                        />
                    </div>
                )}

                <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-2 border-b border-white/10 pb-4">
                    <div>
                        <span className="text-sm font-mono text-white/50 block">
                            {new Date(currentDay.date + 'T00:00:00').toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}
                        </span>
                        <h2 className="text-2xl font-bold text-white">
                            Day {currentDay.day_number}
                        </h2>
                        {currentDay.daily_highlight && (
                            <p className="text-sm text-orange-400/80 mt-1">✨ {currentDay.daily_highlight}</p>
                        )}
                    </div>
                    <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 text-white px-3 py-1 font-mono font-bold text-sm rounded-full border border-purple-500/30">
                        {currentDay.theme}
                    </div>
                </div>

                <div className="space-y-4">
                    {currentDay.time_slots?.map((slot, index) => (
                        <div key={index} className="flex gap-4 group hover:bg-white/5 p-2 rounded-lg transition-colors border-b border-white/5 last:border-0">
                            {/* Time Column */}
                            <div className="w-16 flex-shrink-0 font-mono text-sm font-bold text-orange-400 pt-1">
                                {slot.start_time}
                            </div>

                            {/* Timeline Dot */}
                            <div className="relative flex flex-col items-center">
                                <div className={`w-4 h-4 rounded-full border-2 border-white/20 z-10
                                    ${slot.activity_type === 'meal' ? 'bg-orange-500' :
                                    slot.activity_type === 'transport' ? 'bg-pink-500' :
                                    slot.activity_type === 'arrival' ? 'bg-green-500' :
                                    slot.activity_type === 'departure' ? 'bg-red-500' :
                                    slot.activity_type === 'accommodation' ? 'bg-purple-500' : 'bg-blue-500'}`}
                                />
                                <div className="w-0.5 h-full bg-white/10 absolute top-4 group-last:hidden" />
                            </div>

                            {/* Content Column */}
                            <div className="flex-1 pb-4">
                                <div className="flex justify-between items-start">
                                    <h4 className="font-bold text-lg text-white leading-none mb-1">
                                        <span className="mr-2">{getActivityIcon(slot.activity_type)}</span>
                                        {slot.activity?.name || slot.activity_type}
                                    </h4>
                                    <span className="text-xs font-mono bg-white/10 text-white/70 px-2 py-0.5 ml-2 rounded">
                                        {slot.end_time}
                                    </span>
                                </div>

                                <p className="text-sm text-white/60 mb-1 font-mono">
                                    📍 {slot.location}
                                </p>

                                {slot.notes && (
                                    <div className="text-sm italic bg-orange-500/10 text-orange-300 p-2 border-l-2 border-orange-500 mt-2 rounded-r">
                                        {slot.notes}
                                    </div>
                                )}

                                {/* Tags */}
                                <div className="flex gap-2 mt-2">
                                    <span className="text-[10px] uppercase font-bold border border-white/20 px-2 py-0.5 rounded text-white/60">
                                        {slot.activity_type}
                                    </span>
                                    {slot.activity?.price_level !== undefined && slot.activity.price_level > 0 && (
                                        <span className="text-[10px] uppercase font-bold border border-green-500/30 px-2 py-0.5 rounded text-green-400">
                                            {Array(slot.activity.price_level).fill('$').join('')}
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Day Footer */}
                <div className="mt-6 pt-4 border-t border-white/10 flex justify-between items-center">
                    <div className="font-mono text-sm text-white/70">
                        Est. Day Cost: <span className="font-bold text-lg text-pink-400">${currentDay.estimated_cost || 0}</span>
                    </div>
                    <div className="font-mono text-sm text-white/70">
                        Travel Time: <span className="font-bold text-orange-400">{currentDay.total_travel_time || 0}m</span>
                    </div>
                </div>
            </div>
        </div>
    )
}
