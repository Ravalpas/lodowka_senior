# Konfiguracja Tailwind CSS dla projektu Lodówka Senior+

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./backend/app/templates/**/*.html",
    "./backend/app/static/js/**/*.js",
  ],
  theme: {
    extend: {
      // TODO: Dodać customowe kolory dla marki
      colors: {
        // 'primary': '#...',
        // 'secondary': '#...',
      },
      // TODO: Większe fonty dla seniorów
      fontSize: {
        'senior': '1.25rem',
        'senior-lg': '1.5rem',
      },
    },
  },
  plugins: [
    // TODO: Dodać pluginy w razie potrzeby
    // require('@tailwindcss/forms'),
  ],
}
