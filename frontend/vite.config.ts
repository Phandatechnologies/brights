import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // In development, forward /api requests to the Django server.
    // The browser only ever talks to localhost:5173, so no CORS setup is needed yet.
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
