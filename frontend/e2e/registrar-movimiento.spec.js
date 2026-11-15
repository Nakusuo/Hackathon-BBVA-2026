import { readFileSync } from 'node:fs'
import { expect, test } from '@playwright/test'

const mock = (nombre) => readFileSync(new URL(`../../data/sample/mocks/${nombre}.json`, import.meta.url), 'utf-8')
const RUTAS_API = {
  '/api/v1/customers/demo-001/health': 'health',
  '/api/v1/customers/demo-001/forecast': 'forecast',
  '/api/v1/customers/demo-001/recommendations': 'recommendations',
  '/api/v1/customers/demo-001/events': 'events',
  '/api/v1/fx': 'fx',
}

// Los gastos que llegan al servidor, para comprobar que viajan una vez y con su id.
let enviados
test.beforeEach(async ({ page }) => {
  enviados = []
  await page.route('**/api/v1/**', (ruta) => {
    const url = new URL(ruta.request().url())
    if (url.pathname.endsWith('/expenses')) {
      const cuerpo = ruta.request().postDataJSON()
      enviados.push(cuerpo)
      return ruta.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ ...cuerpo, customer_id: 'demo-001', created_at: '2026-11-14T10:00:00Z', duplicate: false }),
      })
    }
    const nombre = RUTAS_API[url.pathname]
    return nombre
      ? ruta.fulfill({ contentType: 'application/json', body: mock(nombre) })
      : ruta.fulfill({ status: 404, contentType: 'application/json', body: '{"detail":"No existe"}' })
  })
  await page.addInitScript(() => {
    if (window.sessionStorage.getItem('e2e-preparado')) return
    window.localStorage.setItem('lucas-consentimiento', JSON.stringify({ independiente: '2026-11-14' }))
    window.localStorage.setItem('lucas-guia-vista', 'si')
    window.sessionStorage.setItem('e2e-preparado', 'si')
  })
})

test('registrar un gasto cambia el peor caso en Resumen y Qué viene, viaja una vez al servidor y sobrevive a recargar', async ({
  page,
}) => {
  await page.goto('/lucas/que-viene')
  const panel = page.locator('.panel-grafico')
  const peorAntes = await panel.locator('.panel-cifra').innerText()

  await page.getByRole('button', { name: 'Registrar un movimiento' }).click()
  const hoja = page.getByRole('region', { name: 'Registrar un movimiento' })
  await hoja.getByRole('button', { name: 'Guardar movimiento' }).click()
  await expect(hoja.getByText('Escribe un monto en soles')).toBeVisible()

  await hoja.getByLabel('Monto en S/').fill('300')
  await hoja.getByLabel('Fecha').fill('2026-11-14')
  await hoja.getByLabel('Categoría').selectOption('salidas')
  await hoja.getByLabel('¿Qué es? (opcional)').fill('Cena de cumpleaños')
  await expect(hoja.locator('.impacto')).toContainText('Saldo de hoy')
  await hoja.getByRole('button', { name: 'Guardar movimiento' }).click()

  await expect(page.getByRole('region', { name: 'Registrar un movimiento' })).toHaveCount(0)
  await expect(panel.locator('.panel-cifra')).not.toHaveText(peorAntes)
  await expect(page.locator('.aviso-breve').filter({ hasText: 'Registré Cena de cumpleaños (S/ 300)' })).toBeVisible()
  expect(enviados).toHaveLength(1)
  expect(enviados[0]).toMatchObject({ amount: 300, category: 'salidas', date: '2026-11-14', currency: 'PEN' })
  expect(enviados[0].id).toMatch(/^[A-Za-z0-9_-]{1,40}$/)

  await page.getByRole('link', { name: 'Resumen' }).click()
  await expect(page.getByRole('status', { name: 'Aviso de Lucas' })).toContainText('quedarías en rojo')
  const aviso = await page.getByRole('status', { name: 'Aviso de Lucas' }).innerText()

  await page.reload()
  // innerText con innerText: el aviso tiene párrafo y botón, y toHaveText no pone el salto de línea entre ellos.
  await expect(page.getByRole('status', { name: 'Aviso de Lucas' })).toContainText('quedarías en rojo')
  expect(await page.getByRole('status', { name: 'Aviso de Lucas' }).innerText()).toBe(aviso)
  await page.goto('/banca')
  await expect(page.getByText('Cena de cumpleaños')).toBeVisible()
})

test('un ingreso registrado sube el saldo y no se envía a la API', async ({ page }) => {
  await page.goto('/lucas/que-viene')
  const panel = page.locator('.panel-grafico')
  const peorAntes = await panel.locator('.panel-cifra').innerText()
  await page.getByRole('button', { name: 'Registrar un movimiento' }).click()
  const hoja = page.getByRole('region', { name: 'Registrar un movimiento' })
  await hoja.getByRole('button', { name: 'Ingreso' }).click()
  await expect(hoja.getByLabel('Categoría')).toHaveCount(0)
  await hoja.getByLabel('Monto en S/').fill('500')
  await hoja.getByRole('button', { name: 'Guardar movimiento' }).click()
  await expect(panel.locator('.panel-cifra')).not.toHaveText(peorAntes)
  await expect(panel).toContainText('Con tus cambios llegas a tu cobro sin quedar en rojo')
  expect(enviados).toHaveLength(0)
})

test('si el servidor falla, el registro local vale y se avisa en una línea', async ({ page }) => {
  await page.route('**/api/v1/customers/demo-001/expenses', (ruta) => ruta.abort())
  await page.goto('/lucas/que-viene')
  await page.getByRole('button', { name: 'Registrar un movimiento' }).click()
  const hoja = page.getByRole('region', { name: 'Registrar un movimiento' })
  await hoja.getByLabel('Monto en S/').fill('80')
  await hoja.getByRole('button', { name: 'Guardar movimiento' }).click()
  await expect(page.locator('.aviso-breve').filter({ hasText: 'No pude enviarlo al servidor: queda guardado aquí.' })).toBeVisible()
  await page.reload()
  await page.goto('/banca')
  await expect(page.getByText('Gasto registrado')).toBeVisible()
})
