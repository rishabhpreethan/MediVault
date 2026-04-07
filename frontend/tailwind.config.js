/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Manrope', 'sans-serif'],
      },
      colors: {
        primary: '#006b5f',
        'primary-container': '#2dd4bf',
        'primary-fixed': '#62fae3',
        secondary: '#006b5e',
        'secondary-container': '#96f3e1',
        tertiary: '#8d4f00',
        'tertiary-container': '#ffac5a',
        error: '#ba1a1a',
        'error-container': '#ffdad6',
        surface: '#f8f9ff',
        'surface-container-low': '#eff4ff',
        'surface-container': '#e6eeff',
        'surface-container-high': '#dce9ff',
        'surface-container-lowest': '#ffffff',
        'on-surface': '#0d1c2e',
        'on-surface-variant': '#3c4a46',
        'outline-variant': '#bacac5',
      },
    },
  },
  plugins: [],
}
