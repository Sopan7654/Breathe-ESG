/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        // Enterprise slate palette
        surface: {
          DEFAULT: '#0f1117',
          1: '#161b22',
          2: '#1c2128',
          3: '#22272e',
          4: '#2d333b',
        },
        border: {
          DEFAULT: '#30363d',
          subtle: '#21262d',
        },
        accent: {
          blue: '#388bfd',
          green: '#3fb950',
          yellow: '#d29922',
          red: '#f85149',
          purple: '#bc8cff',
        },
        text: {
          primary: '#e6edf3',
          secondary: '#8b949e',
          muted: '#6e7681',
        }
      },
      boxShadow: {
        'card': '0 1px 0 0 rgba(48,54,61,0.8)',
        'modal': '0 16px 32px rgba(1,4,9,0.8)',
      }
    },
  },
  plugins: [],
}
