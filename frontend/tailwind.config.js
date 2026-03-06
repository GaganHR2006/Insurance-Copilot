/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        syne: ['Syne', 'sans-serif'],
        dm: ['DM Sans', 'sans-serif'],
      },
      colors: {
        primary:   '#0A0F1E',
        secondary: '#111827',
        card:      '#1A2235',
        accent:    '#00D4AA',
        danger:    '#FF4757',
        warning:   '#FFB800',
      },
      animation: {
        'fade-up':    'fadeUp 0.3s ease forwards',
        'scale-in':   'scaleIn 0.4s cubic-bezier(0.34,1.56,0.64,1) forwards',
        'bounce-dot': 'bounceDot 1s infinite ease-in-out',
        'pulse-ring':  'pulseRing 1.5s infinite',
        'fill-arc':   'fillArc 1.2s ease forwards',
        shimmer:      'shimmer 1.5s infinite linear',
      },
      keyframes: {
        fadeUp: {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          from: { opacity: '0', transform: 'scale(0)' },
          to:   { opacity: '1', transform: 'scale(1)' },
        },
        bounceDot: {
          '0%, 80%, 100%': { transform: 'translateY(0)' },
          '40%':           { transform: 'translateY(-8px)' },
        },
        pulseRing: {
          '0%':   { transform: 'scale(0.9)', opacity: '1' },
          '70%':  { transform: 'scale(1.3)', opacity: '0' },
          '100%': { transform: 'scale(0.9)', opacity: '0' },
        },
        shimmer: {
          from: { backgroundPosition: '-400px 0' },
          to:   { backgroundPosition:  '400px 0' },
        },
      },
    },
  },
  plugins: [],
};
