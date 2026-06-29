/**
 * MeshBackground Component
 *
 * Animated gradient background with floating blobs
 * - Purple/blue blob in top-left
 * - Orange/pink blob in bottom-right
 * - Continuous 20-25s animation loops
 * - Creates atmospheric depth for glassmorphism UI
 */

'use client';

import { motion } from 'framer-motion';

export default function MeshBackground() {
  return (
    <div className="fixed inset-0 -z-10 bg-background overflow-hidden">
      {/* Purple-Blue blob (top-left) */}
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          x: [0, 50, 0],
          y: [0, 30, 0]
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "linear"
        }}
        className="absolute top-[-10%] left-[-10%] w-[70vw] h-[70vw] rounded-full bg-gradient-to-br from-purple-600/20 to-blue-400/10 blur-[100px]"
      />

      {/* Orange-Pink blob (bottom-right) */}
      <motion.div
        animate={{
          scale: [1, 1.3, 1],
          x: [0, -50, 0],
          y: [0, 60, 0]
        }}
        transition={{
          duration: 25,
          repeat: Infinity,
          ease: "linear"
        }}
        className="absolute bottom-[-20%] right-[-20%] w-[60vw] h-[60vw] rounded-full bg-gradient-to-tr from-orange-500/20 to-pink-600/10 blur-[120px]"
      />
    </div>
  );
}
