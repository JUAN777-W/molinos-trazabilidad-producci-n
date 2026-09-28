/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,ts}"],
  theme: {
    extend: {
      colors: {
        brand: {
          blue: {
            DEFAULT: '#0B3D91',
            dark: '#062350',
            light: '#3B6FD1',
            50: '#EEF3FC',
          },
          red: {
            DEFAULT: '#D62828',
            dark: '#A61E1E',
            light: '#F2545B',
            50: '#FDECEC',
          },
          green: {
            DEFAULT: '#059669',
            dark: '#047857',
            light: '#34D399',
            50: '#ECFDF5',
          },
          gold: {
            DEFAULT: '#F59E0B',
            dark: '#B45309',
            light: '#FCD34D',
            50: '#FFFBEB',
          },
        },
      },
      // "Industrial Clarity" (rediseño 2026-09) — IBM Plex Sans para todo el
      // texto de interfaz, JetBrains Mono para números/telemetría/códigos.
      fontFamily: {
        sans: ['"IBM Plex Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        card: '0 1px 3px rgba(11,61,145,0.08), 0 1px 2px rgba(11,61,145,0.06)',
        cardHover: '0 8px 24px rgba(11,61,145,0.12)',
      },
    }
  },
  plugins: []
};
