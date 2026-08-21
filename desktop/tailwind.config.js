/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        cascade: {
          charcoal: '#1a1a19',
          stone: '#f5f5f4',
          gold: '#92761f',
          'gold-hover': '#7a6219',
          olive: '#4e4732',
          mist: '#e7e5e4',
          sage: '#78716c',
          'soft-white': '#fafaf9',
        },
        semantic: {
          success: '#16a34a',
          warning: '#d97706',
          danger: '#dc2626',
          info: '#2563eb',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      fontSize: {
        'metric': ['48px', { lineHeight: '1', fontWeight: '700', letterSpacing: '-0.03em' }],
      },
      borderRadius: {
        DEFAULT: '8px',
      },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,0.08)',
        elevated: '0 4px 12px rgba(0,0,0,0.1)',
        modal: '0 8px 30px rgba(0,0,0,0.12)',
      },
    },
  },
  plugins: [],
};
