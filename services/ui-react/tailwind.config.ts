import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      typography: {
        DEFAULT: {
          css: {
            maxWidth: 'none',
            color: 'inherit',
            a: { color: 'inherit' },
            strong: { color: 'inherit' },
            code: { color: 'inherit' },
          },
        },
      },
    },
  },
  plugins: [],
} satisfies Config
