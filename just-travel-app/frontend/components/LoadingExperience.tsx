"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface LoadingExperienceProps {
  isLoading: boolean;
}

// Pipeline stages with timing (cumulative seconds)
const stages = [
  { id: 'profiler', label: 'Understanding your preferences', icon: '🧠', startTime: 0 },
  { id: 'research', label: 'Researching destinations & flights', icon: '🔍', startTime: 5 },
  { id: 'optimizer', label: 'Crafting your perfect itinerary', icon: '✨', startTime: 12 },
  { id: 'creative', label: 'Creating visual previews', icon: '🎬', startTime: 20 },
];

// Rotating destination backgrounds
const destinations = [
  { name: 'Paris', gradient: 'from-purple-600 via-pink-500 to-orange-400' },
  { name: 'Tokyo', gradient: 'from-red-500 via-pink-500 to-purple-600' },
  { name: 'Bali', gradient: 'from-green-500 via-teal-500 to-blue-500' },
  { name: 'Dubai', gradient: 'from-orange-500 via-amber-500 to-yellow-400' },
  { name: 'Iceland', gradient: 'from-blue-600 via-cyan-500 to-green-400' },
];

export function LoadingExperience({ isLoading }: LoadingExperienceProps) {
  const [currentStage, setCurrentStage] = useState(0);
  const [destinationIndex, setDestinationIndex] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);

  // Progress timer
  useEffect(() => {
    if (!isLoading) {
      setCurrentStage(0);
      setElapsedTime(0);
      return;
    }

    const timer = setInterval(() => {
      setElapsedTime((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [isLoading]);

  // Update stage based on elapsed time
  useEffect(() => {
    if (!isLoading) return;

    const stageIndex = stages.findIndex((stage, idx) => {
      const nextStage = stages[idx + 1];
      if (!nextStage) return true;
      return elapsedTime >= stage.startTime && elapsedTime < nextStage.startTime;
    });

    if (stageIndex !== -1 && stageIndex !== currentStage) {
      setCurrentStage(stageIndex);
    }
  }, [elapsedTime, isLoading, currentStage]);

  // Rotate destinations
  useEffect(() => {
    if (!isLoading) return;

    const interval = setInterval(() => {
      setDestinationIndex((prev) => (prev + 1) % destinations.length);
    }, 3000);

    return () => clearInterval(interval);
  }, [isLoading]);

  if (!isLoading) return null;

  const currentDest = destinations[destinationIndex];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0a0a2e]/95 backdrop-blur-xl">
      {/* Animated gradient background */}
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          key={currentDest.name}
          initial={{ opacity: 0, scale: 1.2 }}
          animate={{ opacity: 0.3, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          transition={{ duration: 1 }}
          className={`absolute inset-0 bg-gradient-to-br ${currentDest.gradient}`}
        />
      </div>

      {/* Content */}
      <div className="relative z-10 text-center max-w-lg px-6">
        {/* Destination preview */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentDest.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="mb-8"
          >
            <span className="text-white/50 text-sm font-mono uppercase tracking-widest">
              Dreaming of
            </span>
            <h2 className={`text-5xl md:text-6xl font-black bg-gradient-to-r ${currentDest.gradient} bg-clip-text text-transparent mt-2`}>
              {currentDest.name}
            </h2>
          </motion.div>
        </AnimatePresence>

        {/* Progress stages */}
        <div className="space-y-4 mb-8">
          {stages.map((stage, idx) => {
            const isActive = idx === currentStage;
            const isCompleted = idx < currentStage;

            return (
              <motion.div
                key={stage.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{
                  opacity: isActive ? 1 : isCompleted ? 0.8 : 0.4,
                  x: 0,
                  scale: isActive ? 1.05 : 1
                }}
                transition={{ delay: idx * 0.1 }}
                className={`flex items-center gap-4 p-4 rounded-2xl transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-orange-500/20 to-pink-500/20 border border-orange-500/30'
                    : isCompleted
                    ? 'bg-white/5 border border-green-500/30'
                    : 'bg-white/5 border border-white/10'
                }`}
              >
                <div className={`text-2xl ${isActive ? 'animate-bounce' : ''}`}>
                  {isCompleted ? '✅' : stage.icon}
                </div>
                <div className="flex-1 text-left">
                  <p className={`font-bold ${isActive ? 'text-white' : isCompleted ? 'text-green-400' : 'text-white/50'}`}>
                    {stage.label}
                  </p>
                </div>
                {isActive && (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    className="w-5 h-5 border-2 border-orange-500 border-t-transparent rounded-full"
                  />
                )}
              </motion.div>
            );
          })}
        </div>

        {/* Timer */}
        <div className="text-white/40 font-mono text-sm">
          <span className="text-orange-400">{elapsedTime}s</span> elapsed
        </div>

        {/* Pro tip */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2 }}
          className="mt-6 p-4 bg-white/5 rounded-xl border border-white/10"
        >
          <p className="text-sm text-white/60">
            <span className="text-orange-400 font-bold">Pro tip:</span> Our AI is analyzing weather, prices, and local events to create your perfect itinerary
          </p>
        </motion.div>
      </div>
    </div>
  );
}
