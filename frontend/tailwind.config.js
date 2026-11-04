/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        forest: {
          50: '#f0fdf4',
          100: '#dcfce7',
          500: '#10b981',
          700: '#047857',
          800: '#065f46',
          900: '#0D3B2E',
          950: '#062019',
        },
        naija: {
          green: '#008751',
          light: '#2ecc71',
        },
      },
    },
  },
  plugins: [],
}
