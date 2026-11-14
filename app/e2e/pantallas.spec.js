import { expect, test } from '@playwright/test'

const PANTALLAS = [
  { ruta: '/como-estas', titulo: 'Cómo estás' },
  { ruta: '/que-viene', titulo: 'Qué viene' },
  { ruta: '/que-hacer', titulo: 'Qué hacer' },
]

for (const { ruta, titulo } of PANTALLAS) {
  test.describe(titulo, () => {
    test('abre sin errores, sin scroll horizontal y con texto de 16 px o más', async ({ page }, info) => {
      const errores = []
      page.on('pageerror', (e) => errores.push(e.message))
      page.on('console', (m) => m.type() === 'error' && errores.push(m.text()))

      await page.goto(ruta)
      await expect(page.getByRole('heading', { level: 1, name: titulo })).toBeVisible()

      const anchoExtra = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
      expect(anchoExtra).toBeLessThanOrEqual(0)

      // Regla de negocio: texto ≥ 16 px. Se revisa todo texto visible, incluidas las etiquetas del gráfico.
      const textosChicos = await page.evaluate(() => {
        const chicos = []
        const recorrido = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT)
        while (recorrido.nextNode()) {
          const nodo = recorrido.currentNode
          const texto = nodo.textContent.trim()
          const padre = nodo.parentElement
          if (!texto || !padre || padre.closest('[aria-hidden="true"]:not(.circulo)')) continue
          const caja = padre.getBoundingClientRect()
          if (caja.width === 0 || caja.height === 0) continue
          const tamano = parseFloat(getComputedStyle(padre).fontSize)
          if (tamano < 16) chicos.push(`${texto} (${tamano}px)`)
        }
        return chicos
      })
      expect(textosChicos).toEqual([])
      expect(errores).toEqual([])

      await page.screenshot({ path: `capturas/${info.project.name}${ruta.replace('/', '-')}.png`, fullPage: true })
    })
  })
}

test('el aviso anticipado lleva a Qué hacer', async ({ page }) => {
  await page.goto('/como-estas')
  const aviso = page.getByRole('status', { name: 'Aviso de Lucas' })
  await expect(aviso).toContainText('26 de noviembre podrías quedar en rojo')
  await aviso.getByRole('link', { name: 'Ver qué puedo hacer' }).click()
  await expect(page).toHaveURL(/que-hacer/)
})

test('Cómo estás responde cuánto puedo gastar al día', async ({ page }) => {
  await page.goto('/como-estas')
  await expect(page.getByRole('region', { name: 'Cuánto puedes gastar' })).toContainText('S/ 34')
})

test('Qué viene cambia de periodo y muestra los pagos de diciembre', async ({ page }) => {
  await page.goto('/que-viene')
  const pagos = page.getByRole('region', { name: 'Pagos e ingresos que vienen' })
  await expect(pagos).not.toContainText('Tarjeta de crédito')
  await page.getByRole('button', { name: '30 días' }).click()
  await expect(page.getByRole('button', { name: '30 días' })).toHaveAttribute('aria-pressed', 'true')
  await expect(pagos).toContainText('Tarjeta de crédito')
})

test('Qué hacer explica el porqué de cada cambio', async ({ page }) => {
  await page.goto('/que-hacer')
  await page.getByText('¿Por qué?').first().click()
  await expect(page.getByText('No la usaste en 5 semanas')).toBeVisible()
})
