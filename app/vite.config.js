import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// La API de FastAPI no tiene CORS: el navegador habla con Vite y Vite le pasa /api al puerto 8000.
const API = process.env.LUCAS_API ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': API },
    // El respaldo lee los JSON del contrato en data/sample/mocks/, fuera de app/.
    fs: { allow: ['.', '../data/sample/mocks'] },
  },
  preview: { proxy: { '/api': API } },
})
