import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from 'tailwindcss'
import autoprefixer from 'autoprefixer'

// Export Vite configuration with explicit postcss and api proxy
export default defineConfig({
  plugins: [react()],
  css: {
    postcss: {
      plugins: [tailwindcss(), autoprefixer()],
    },
  },
  server: {
    host: true, // Listen on all addresses including localhost and 127.0.0.1
    port: 5173,
    proxy: {
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
