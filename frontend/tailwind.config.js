/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        primary: {
          50:  '#eef2ff',
          100: '#e0e7ff',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
        },
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      boxShadow: {
        'glass':  '0 8px 32px rgba(99,102,241,0.08), 0 2px 8px rgba(0,0,0,0.04)',
        'glass-lg': '0 16px 48px rgba(99,102,241,0.12), 0 4px 16px rgba(0,0,0,0.06)',
        'indigo': '0 8px 24px rgba(99,102,241,0.25)',
      },
    },
  },
  plugins: [],
}
