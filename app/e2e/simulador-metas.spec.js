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

// Permiso ya dado y guía vista, una sola vez por pestaña: así una prueba puede retirar el permiso y recargar.
// El simulador está plegado en Qué viene: cada prueba lo abre antes de usarlo.
async function abrirSimulador(page) {
  await page.getByRole('button', { name: 'Simular un gasto o ingreso' }).click()
}

test.beforeEach(async ({ page }) => {
  // La API responde con los JSON del contrato: si FastAPI no está, el aviso de datos movería la página a mitad
  // de un clic.
  await page.route('**/api/v1/**', (ruta) => {
    const nombre = RUTAS_API[new URL(ruta.request().url()).pathname]
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

test('simulador: un gasto de S/ 450 el 5 dic mueve la banda en vivo y se agrega al pronóstico', async ({ page }) => {
  await page.goto('/lucas/que-viene')
  const plan = page.getByRole('region', { name: '¿Y si viene un gasto o un ingreso?' })
  await abrirSimulador(page)
  const panel = page.locator('.panel-grafico')

  await plan.getByLabel('Monto en S/').fill('450')
  await plan.getByLabel('Fecha').fill('2026-12-05')
  await expect(page.getByRole('button', { name: '30 días' })).toHaveAttribute('aria-pressed', 'true')
  await expect(panel.getByRole('heading', { name: 'Así quedaría tu saldo' })).toBeVisible()
  await expect(panel).toContainText('12 días podrías quedar en rojo')
  await expect(plan.locator('.impacto')).toContainText('Días en rojo 2 → 12')
  await expect(plan).toContainText('Hasta S/ 40 el sábado 5 no te suma días en rojo, ni en el peor caso.')
  await expect(plan).toContainText('Es una simulación con tus datos: tú decides.')

  await plan.getByLabel('¿Qué es? (opcional)').fill('Regalo de Navidad')
  await plan.getByRole('button', { name: 'Agregar a mi pronóstico' }).click()
  await expect(plan.getByLabel('Monto en S/')).toHaveValue('')
  const pagos = page.getByRole('region', { name: 'Pagos y cobros' })
  await expect(pagos).toContainText('Regalo de Navidad')
  await expect(pagos).toContainText('lo agregaste tú')
  await expect(panel.getByRole('heading', { name: 'Tu saldo proyectado' })).toBeVisible()
  await expect(panel).toContainText('12 días podrías quedar en rojo')

  await pagos.getByRole('button', { name: /Quitar Regalo de Navidad/ }).click()
  await expect(pagos).not.toContainText('Regalo de Navidad')
  await expect(panel).toContainText('2 días podrías quedar en rojo')
})

test('simulador: con los 3 tips, un gasto planificado en diciembre avisa en el Resumen solo al agregarlo', async ({
  page,
}) => {
  await page.goto('/lucas/resumen')
  const tips = page.getByRole('region', { name: 'Tips para tu día más justo' })
  for (let i = 0; i < 3; i++) await tips.getByRole('button', { name: 'Lo hago' }).nth(i).click()
  const aviso = page.getByRole('status', { name: 'Aviso de Lucas' })
  await expect(aviso).toContainText('Vas bien')

  await page.getByRole('link', { name: 'Qué viene' }).click()
  const plan = page.getByRole('region', { name: '¿Y si viene un gasto o un ingreso?' })
  await abrirSimulador(page)
  await plan.getByLabel('Monto en S/').fill('450')
  await plan.getByLabel('Fecha').fill('2026-12-05')
  await expect(plan.locator('.impacto')).toContainText('Días en rojo 0 → 10')
  await expect(plan).toContainText('Hasta S/ 150 el sábado 5 no te deja en rojo, ni en el peor caso.')
  await expect(plan).toContainText('si lo gastas, ese mes no apartas para tus metas')

  // Simular no guarda: el Resumen sigue igual hasta tocar «Agregar a mi pronóstico».
  await page.getByRole('link', { name: 'Resumen' }).click()
  await expect(aviso).toContainText('Vas bien')

  await page.getByRole('link', { name: 'Qué viene' }).click()
  await abrirSimulador(page)
  await plan.getByLabel('Monto en S/').fill('450')
  await plan.getByLabel('Fecha').fill('2026-12-05')
  await plan.getByRole('button', { name: 'Agregar a mi pronóstico' }).click()

  await page.reload()
  await page.getByRole('link', { name: 'Resumen' }).click()
  await expect(aviso).toContainText('con lo que planificaste el sábado 5 quedarías en rojo')

  await page.getByRole('link', { name: 'Ver en Qué viene' }).click()
  await page.getByRole('button', { name: '30 días' }).click()
  await page.getByRole('region', { name: 'Pagos y cobros' }).getByRole('button', { name: /Quitar Gasto planificado/ }).click()
  await expect(page.locator('.panel-grafico')).toContainText('En estos 30 días no quedas en rojo')
})

test('simulador: un ingreso antes del día más justo quita el rojo', async ({ page }) => {
  await page.goto('/lucas/que-viene')
  const plan = page.getByRole('region', { name: '¿Y si viene un gasto o un ingreso?' })
  await abrirSimulador(page)
  await plan.getByRole('button', { name: 'Ingreso' }).click()
  await plan.getByLabel('Monto en S/').fill('100')
  await plan.getByLabel('Fecha').fill('2026-11-20')
  await expect(page.locator('.panel-grafico')).toContainText('llegas a tu cobro sin quedar en rojo')
  await expect(plan.locator('.impacto')).toContainText('Días en rojo 2 → 0')
})

test('simulador: rechaza montos y fechas inválidos y avisa si el gasto ya está contado', async ({ page }) => {
  await page.goto('/lucas/que-viene')
  const plan = page.getByRole('region', { name: '¿Y si viene un gasto o un ingreso?' })
  await abrirSimulador(page)
  await plan.getByRole('button', { name: 'Agregar a mi pronóstico' }).click()
  await expect(plan.getByLabel('Monto en S/')).toHaveAttribute('aria-invalid', 'true')
  await expect(plan.getByLabel('Monto en S/')).toBeFocused()
  await expect(plan).toContainText('Escribe un monto en soles')
  await expect(plan).toContainText('Elige una fecha entre el 15 nov y el 14 dic')

  await plan.getByLabel('Monto en S/').fill('0')
  await expect(plan).toContainText('El monto debe ser mayor que S/ 0')
  await plan.getByLabel('Monto en S/').fill('abc')
  await expect(plan).toContainText('Usa solo números')

  await plan.getByLabel('Monto en S/').fill('420')
  await plan.getByLabel('Fecha').fill('2026-11-25')
  await plan.getByLabel('¿Qué es? (opcional)').fill('Alquiler')
  await expect(plan.getByRole('status')).toContainText('Ya tengo contado «Alquiler de cuarto»')
})

test('metas: con los 3 tips aparta S/ 150 y la meta de fin de año pasa de creada a cumplida', async ({ page }) => {
  await page.goto('/lucas/resumen')
  const tips = page.getByRole('region', { name: 'Tips para tu día más justo' })
  for (let i = 0; i < 3; i++) await tips.getByRole('button', { name: 'Lo hago' }).nth(i).click()
  await page.getByRole('link', { name: 'Llévalo a una meta' }).click()
  await expect(page).toHaveURL(/lucas\/metas/)

  await expect(page.getByRole('region', { name: 'Tus metas' })).toContainText('puedes apartar S/ 150')
  const nueva = page.getByRole('region', { name: 'Crea tu primera meta' })
  await expect(nueva.getByLabel('¿Para cuándo?')).toHaveValue('2026-12-31')
  await nueva.getByRole('button', { name: 'Crear meta' }).click()
  await expect(nueva).toContainText('Ponle un nombre corto')
  await expect(nueva.getByLabel('¿Para qué ahorras?')).toBeFocused()

  await nueva.getByLabel('¿Para qué ahorras?').fill('Colchón para enero')
  await nueva.getByLabel('Meta en S/').fill('300')
  await nueva.getByRole('button', { name: 'Crear meta' }).click()

  const meta = page.getByRole('listitem', { name: 'Meta Colchón para enero' })
  await expect(meta).toContainText('Creada')
  await expect(meta).toContainText('Aparta S/ 150 al mes, al cobrar el 30 (2 veces hasta el 31 dic), y llegas.')
  await expect(meta).toContainText('Confianza media')

  await meta.getByRole('button', { name: 'Ya aparté S/ 150' }).click()
  await expect(meta).toContainText('En curso')
  await expect(meta).toContainText('S/ 150 de S/ 300')
  await expect(meta).toContainText('50 %')

  await page.reload()
  await meta.getByRole('button', { name: 'Ya aparté S/ 150' }).click()
  await expect(meta).toContainText('Cumplida')
  await expect(meta).toContainText('Cumpliste tu meta')

  await page.getByRole('navigation', { name: 'Secciones de Lucas' }).getByRole('link', { name: 'Resumen' }).click()
  await expect(page.getByRole('link', { name: /Tus metas/ })).toContainText('1 meta')
})

test('metas: sin tips (S/ 40) dice cuánto junta a la fecha y cuándo llegaría', async ({ page }) => {
  await page.goto('/lucas/metas')
  await expect(page.getByRole('region', { name: 'Tus metas' })).toContainText('Con los 3 tips serían S/ 150')
  const nueva = page.getByRole('region', { name: 'Crea tu primera meta' })
  await nueva.getByLabel('¿Para qué ahorras?').fill('Colchón para enero')
  await nueva.getByLabel('Meta en S/').fill('300')
  await nueva.getByRole('button', { name: 'Crear meta' }).click()
  const meta = page.getByRole('listitem', { name: 'Meta Colchón para enero' })
  await expect(meta).toContainText('Con S/ 40 al mes llegas el 30 jun de 2027.')
  await expect(meta).toContainText('Con los 3 tips apartas S/ 150 al mes y llegas el 30 dic.')
  await expect(meta).toContainText('Confianza baja')
})

test('datos rotos guardados en el navegador no tumban la app', async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem('lucas-metas', JSON.stringify([{ id: 'x', nombre: 'Rota' }]))
    window.localStorage.setItem(
      'lucas-planificados',
      JSON.stringify([{ id: 'p', tipo: 'gasto', monto: '450', fecha: '2026-12-05', concepto: 'Roto' }]),
    )
  })
  const errores = []
  page.on('pageerror', (e) => errores.push(e.message))
  await page.goto('/lucas/metas')
  await expect(page.getByRole('region', { name: 'Crea tu primera meta' })).toBeVisible()
  await page.goto('/lucas/que-viene')
  await expect(page.locator('.panel-grafico')).toContainText('−S/ 60')
  await expect(page.getByRole('region', { name: 'Pagos y cobros' })).not.toContainText('Roto')
  expect(errores).toEqual([])
})

test('retirar el permiso olvida lo planificado y las metas', async ({ page }) => {
  await page.goto('/lucas/que-viene')
  const plan = page.getByRole('region', { name: '¿Y si viene un gasto o un ingreso?' })
  await abrirSimulador(page)
  await plan.getByLabel('Monto en S/').fill('100')
  await plan.getByLabel('Fecha').fill('2026-11-20')
  await plan.getByRole('button', { name: 'Agregar a mi pronóstico' }).click()
  await page.goto('/lucas/metas')
  const nueva = page.getByRole('region', { name: 'Crea tu primera meta' })
  await nueva.getByLabel('¿Para qué ahorras?').fill('Colchón')
  await nueva.getByLabel('Meta en S/').fill('300')
  await nueva.getByRole('button', { name: 'Crear meta' }).click()

  await page.goto('/preferencias')
  const privacidad = page.getByRole('region', { name: 'Privacidad' })
  await privacidad.getByRole('button', { name: 'Retirar permiso' }).click()
  await privacidad.getByRole('button', { name: 'Sí, retirar' }).click()
  await expect(privacidad.getByRole('status')).toContainText('Lucas está apagado')
  const guardado = await page.evaluate(() => [localStorage.getItem('lucas-planificados'), localStorage.getItem('lucas-metas')])
  expect(guardado).toEqual(['[]', '[]'])
})

test('metas con la persona formal: aparta al cobrar el 30 con su propio margen', async ({ page }) => {
  await page.goto('/ingresar')
  await page.getByRole('radio', { name: 'Formal con quincena' }).check()
  await page.getByRole('button', { name: 'Ingresar' }).click()
  await page.getByRole('button', { name: 'Acepto, activar Lucas' }).click()
  await page.goto('/lucas/metas')
  await expect(page.getByRole('region', { name: 'Tus metas' })).toContainText('puedes apartar S/ 430')
  const nueva = page.getByRole('region', { name: 'Crea tu primera meta' })
  await nueva.getByLabel('¿Para qué ahorras?').fill('Pasajes de diciembre')
  await nueva.getByLabel('Meta en S/').fill('800')
  await nueva.getByRole('button', { name: 'Crear meta' }).click()
  await expect(page.getByRole('listitem', { name: 'Meta Pasajes de diciembre' })).toContainText(
    'Aparta S/ 400 al mes, al cobrar el 30 (2 veces hasta el 31 dic), y llegas.',
  )
})
