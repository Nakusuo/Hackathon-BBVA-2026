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
  },
  projects: [
    {
      name: 'laptop-claro',
      use: { browserName: 'chromium', viewport: { width: 1366, height: 768 }, colorScheme: 'light' },
    },
    {
      name: 'laptop-oscuro',
      use: { browserName: 'chromium', viewport: { width: 1366, height: 768 }, colorScheme: 'dark' },
    },
    {
      name: 'celular',
      use: { ...devices['Pixel 7'], browserName: 'chromium', colorScheme: 'light' },
    },
  ],
})
