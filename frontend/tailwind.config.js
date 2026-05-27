/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: {
          deep: '#070a1e',
          card: 'rgba(13, 17, 45, 0.45)',
          sidebar: '#0c0f2b',
        },
        primary: {
          DEFAULT: '#6366f1', // Indigo
          glow: 'rgba(99, 102, 241, 0.15)',
        },
        secondary: {
          DEFAULT: '#a855f7', // Purple
          glow: 'rgba(168, 85, 247, 0.15)',
        },
        accent: {
          pink: '#ec4899',
          cyan: '#06b6d4',
        }
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        'glass-hover': '0 8px 32px 0 rgba(99, 102, 241, 0.25)',
      },
      backdropBlur: {
        'glass': '16px',
      }
    },
  },
  plugins: [],
}
