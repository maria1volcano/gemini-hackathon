/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'brutal': {
          'black': '#000000',
          'white': '#FFFFFF',
          'yellow': '#FFE135',
          'pink': '#FF6B9D',
          'blue': '#00D4FF',
          'green': '#00FF85',
          'purple': '#B967FF',
          'orange': '#FF9F43',
          'red': '#FF4757',
        },
        'background': '#0a0a2e',  // Updated from #0f0f23
      },
      boxShadow: {
        // Neo-brutalist hard shadows
        'brutal': '4px 4px 0px 0px #000000',
        'brutal-lg': '8px 8px 0px 0px #000000',
        'brutal-xl': '12px 12px 0px 0px #000000',
        'brutal-hover': '2px 2px 0px 0px #000000',
        // Soft shadows with glow
        'brutal-soft': '0 4px 24px rgba(0,0,0,0.4), 0 0 1px rgba(255,255,255,0.08)',
        'brutal-soft-lg': '0 8px 40px rgba(0,0,0,0.5), 0 0 20px rgba(255,159,67,0.12)',
        // Neon glow effects
        'glow-orange': '0 0 15px rgba(249,115,22,0.5)',
        'glow-pink': '0 0 15px rgba(255,107,157,0.5)',
        'glow-yellow': '0 0 15px rgba(255,225,53,0.5)',
      },
      borderWidth: {
        '3': '3px',
        '4': '4px',
      },
      borderRadius: {
        '4xl': '2rem',
        '5xl': '2.5rem',
        '40': '40px',  // Custom large radius
      },
      fontFamily: {
        'mono': ['Space Mono', 'Courier New', 'monospace'],
        'sans': ['Space Grotesk', 'Arial', 'sans-serif'],
      },
      animation: {
        'bounce-brutal': 'bounce-brutal 0.3s ease-in-out',
        'glow-pulse': 'glow-pulse 3s ease-in-out infinite',
      },
      keyframes: {
        'bounce-brutal': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-4px)' },
        },
        'glow-pulse': {
          '0%, 100%': { opacity: '0.5' },
          '50%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
