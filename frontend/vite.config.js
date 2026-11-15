import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// La API de FastAPI no tiene CORS: el navegador habla con Vite y Vite le pasa /api al puerto 8000.
const API = process.env.LUCAS_API ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': API },
    // Fuera de app/ solo se abre lo necesario: los JSON del contrato (respaldo), los de `make eval` (panel Evidencia) y el catálogo de campañas.
    fs: { allow: ['.', '../data/sample/mocks', '../models', '../data/catalogo_campanas.json'] },
  },
  preview: { proxy: { '/api': API } },
})
