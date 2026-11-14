import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// La API de FastAPI no tiene CORS: el navegador habla con Vite y Vite le pasa /api al puerto 8000.
const API = process.env.LUCAS_API ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': API },
    // Fuera de app/ solo se abren dos carpetas: los JSON del contrato (respaldo) y los de `make eval` (panel Evidencia).
    fs: { allow: ['.', '../data/sample/mocks', '../models'] },
  },
  preview: { proxy: { '/api': API } },
})
