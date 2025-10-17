// shop/shop-frontend/tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{html,ts}'],
  theme: {
    container: {
      center: true,
      padding: {
        DEFAULT: '1rem',
        sm: '2rem',
        lg: '4rem',
        xl: '5rem',
      },
    },
    extend: {
      colors: {
        background: '#0A121E', // A slightly darker, richer background
        surface: '#121E2E', // A noticeably lighter surface for cards
        primary: {
          DEFAULT: '#5A89E6', // A more vibrant blue for primary actions
          light: '#7DA5EC',
        },
        secondary: {
          DEFAULT: '#334155', // A subtle grey-blue for borders and secondary elements
          light: '#475569',
        },
        accent: {
          DEFAULT: '#E2E8F0', // A clean, bright off-white for main text
        },
        'text-muted': '#94A3B8', // A softer grey for secondary text
      },
      fontFamily: {
        sans: ['"Inter"', 'sans-serif'],
      },
      borderRadius: {
        xl: '0.75rem',
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
    },
  },
  plugins: [],
};  