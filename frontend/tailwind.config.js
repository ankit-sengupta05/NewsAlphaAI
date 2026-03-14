/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          primary:   '#0a0c10',
          secondary: '#0f1218',
          card:      '#141820',
          hover:     '#1a2030',
          border:    '#1e2535',
        },
        accent: {
          green:  '#00e676',
          red:    '#ff3d57',
          blue:   '#2196f3',
          gold:   '#ffd54f',
          purple: '#7c4dff',
          cyan:   '#00bcd4',
        },
        text: {
          primary:   '#e8eaf0',
          secondary: '#8892a4',
          muted:     '#4a5568',
        },
      },
      fontFamily: {
        display: ['"DM Mono"', 'monospace'],
        body:    ['"Inter"', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
      },
      animation: {
        'pulse-green': 'pulseGreen 2s ease-in-out infinite',
        'fade-in':     'fadeIn 0.4s ease-out',
        'slide-up':    'slideUp 0.35s ease-out',
        'ticker-scroll':'tickerScroll 30s linear infinite',
        'glow-up':     'glowUp 1s ease-out',
        'glow-down':   'glowDown 1s ease-out',
        'spin-slow':   'spin 3s linear infinite',
      },
      keyframes: {
        pulseGreen: {
          '0%,100%': { opacity: 1 },
          '50%':     { opacity: 0.4 },
        },
        fadeIn:  { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp: { from: { opacity: 0, transform: 'translateY(12px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
        tickerScroll: { from: { transform: 'translateX(0)' }, to: { transform: 'translateX(-50%)' } },
        glowUp:   { '0%': { boxShadow: '0 0 0 rgba(0,230,118,0)' }, '100%': { boxShadow: '0 0 24px rgba(0,230,118,0.3)' } },
        glowDown: { '0%': { boxShadow: '0 0 0 rgba(255,61,87,0)' },  '100%': { boxShadow: '0 0 24px rgba(255,61,87,0.3)' } },
      },
      backgroundImage: {
        'grid-pattern': 'linear-gradient(rgba(30,37,53,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(30,37,53,0.5) 1px, transparent 1px)',
        'gradient-radial': 'radial-gradient(ellipse at center, var(--tw-gradient-stops))',
      },
      backgroundSize: {
        'grid': '32px 32px',
      },
    },
  },
  plugins: [],
}
