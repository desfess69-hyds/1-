/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // 따뜻한 오피스 톤
        'office-bg': '#fef3e2',       // 크림 (바깥)
        'office-wall': '#f5d9a5',     // 살구 벽
        'office-floor': '#d4a574',    // 나무 바닥
        'office-trim': '#8b5a3c',     // 진한 갈색 (책상·테두리)
        'office-accent': '#f59e0b',   // 노란 액센트
        'office-soft': '#fff8eb',     // 부드러운 흰
      },
      animation: {
        'bob': 'bob 2s ease-in-out infinite',
        'shake': 'shake 0.4s ease-in-out infinite',
        'pulse-glow': 'pulse-glow 2.5s ease-in-out infinite',
        'blink': 'blink 4s ease-in-out infinite',
        'sway': 'sway 3s ease-in-out infinite',
      },
      keyframes: {
        bob: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-4px)' },
        },
        shake: {
          '0%, 100%': { transform: 'translateX(0) rotate(0)' },
          '25%': { transform: 'translateX(-1px) rotate(-2deg)' },
          '75%': { transform: 'translateX(1px) rotate(2deg)' },
        },
        'pulse-glow': {
          '0%, 100%': { filter: 'drop-shadow(0 0 6px rgba(251, 191, 36, 0.5))' },
          '50%': { filter: 'drop-shadow(0 0 16px rgba(251, 191, 36, 1))' },
        },
        blink: {
          '0%, 95%, 100%': { transform: 'scaleY(1)' },
          '97%': { transform: 'scaleY(0.1)' },
        },
        sway: {
          '0%, 100%': { transform: 'rotate(-3deg)' },
          '50%': { transform: 'rotate(3deg)' },
        },
      },
    },
  },
  plugins: [],
};
