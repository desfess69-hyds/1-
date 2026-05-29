/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'office-bg': '#1a1a2e',
        'office-floor': '#2a2a3e',
        'office-wall': '#16162a',
      },
      fontFamily: {
        pixel: ['"Press Start 2P"', 'monospace'],
      },
      animation: {
        'bob': 'bob 1.5s ease-in-out infinite',
        'shake': 'shake 0.3s ease-in-out infinite',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
      },
      keyframes: {
        bob: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-3px)' },
        },
        shake: {
          '0%, 100%': { transform: 'translateX(0)' },
          '25%': { transform: 'translateX(-1px)' },
          '75%': { transform: 'translateX(1px)' },
        },
        'pulse-glow': {
          '0%, 100%': { filter: 'drop-shadow(0 0 4px rgba(96, 165, 250, 0.6))' },
          '50%': { filter: 'drop-shadow(0 0 12px rgba(96, 165, 250, 1))' },
        },
      },
    },
  },
  plugins: [],
};
