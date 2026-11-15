import { defineConfig, devices } from '@playwright/test'

// PW_PUERTO deja correr las pruebas de una rama mientras otra carpeta del repo ya usa el 5174.
const PUERTO = Number(process.env.PW_PUERTO ?? 5174)

// Sin PW_CHROMIUM se usa el Chromium de Playwright (`npx playwright install chromium`).
// Con PW_CHROMIUM se usa un navegador ya instalado, por ejemplo Brave, y no se descarga nada.
const lanzamiento = process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {}

export default defineConfig({
  testDir: './e2e',
  outputDir: './test-results',
  reporter: 'list',
  use: {
    baseURL: `http://localhost:${PUERTO}`,
    launchOptions: lanzamiento,
  },
  webServer: {
    command: `npm run dev -- --port ${PUERTO} --strictPort`,
    url: `http://localhost:${PUERTO}`,
    reuseExistingServer: !process.env.CI,
    // Enciende el chat contra el agente; las pruebas responden por /api/v1/chat con page.route.
    env: { VITE_CHAT_AGENTE: 'si' },
  },
  projects: [
    {
      name: 'laptop',
      use: { browserName: 'chromium', viewport: { width: 1366, height: 768 } },
    },
    {
      name: 'celular',
      // 390 px: el ancho más común de celular en la demo; más angosto que el Pixel 7 que usa de base.
      use: { ...devices['Pixel 7'], viewport: { width: 390, height: 844 }, browserName: 'chromium' },
    },
  ],
})
