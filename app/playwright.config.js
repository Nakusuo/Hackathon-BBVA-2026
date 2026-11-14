import { defineConfig, devices } from '@playwright/test'

const PUERTO = 5174

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
    // El chat llama al agente en el mismo origen; las pruebas responden por él con page.route.
    env: { VITE_LUCAS_API: `http://localhost:${PUERTO}` },
  },
  projects: [
    {
      name: 'laptop',
      use: { browserName: 'chromium', viewport: { width: 1366, height: 768 } },
    },
    {
      name: 'celular',
      // 390 px es el ancho más angosto de los celulares que apuntamos.
      use: { ...devices['Pixel 7'], viewport: { width: 390, height: 844 }, browserName: 'chromium' },
    },
  ],
})
