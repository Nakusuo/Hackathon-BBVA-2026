import { expect, test } from '@playwright/test'

const PANTALLAS = [
  { ruta: '/ingresar', titulo: 'Ingresa a tu banca' },
  { ruta: '/banca', titulo: 'Hola' },
  { ruta: '/lucas/resumen', titulo: 'Lucas' },
  { ruta: '/lucas/gastos', titulo: 'Lucas' },
  { ruta: '/lucas/que-viene', titulo: 'Lucas' },
  { ruta: '/lucas/chat', titulo: 'Lucas' },
]

async function sinGuia(page) {
  await page.addInitScript(() => window.localStorage.setItem('lucas-guia-vista', 'si'))
}

for (const { ruta, titulo } of PANTALLAS) {
  test(`${ruta} abre sin errores, sin scroll horizontal y con texto de 16 px o más`, async ({ page }, info) => {
    await sinGuia(page)
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
        if (!texto || !padre || padre.closest('[aria-hidden="true"]:not(.circulo):not(.marca-lucas)')) continue
        const caja = padre.getBoundingClientRect()
        if (caja.width === 0 || caja.height === 0) continue
        const tamano = parseFloat(getComputedStyle(padre).fontSize)
        if (tamano < 16) chicos.push(`${texto} (${tamano}px)`)
      }
      return chicos
    })
    await page.screenshot({ path: `capturas/${info.project.name}${ruta.replaceAll('/', '-')}.png`, fullPage: true })
    expect(textosChicos).toEqual([])
    expect(errores).toEqual([])
  })
}

test('lo importante se ve sin bajar: aviso de Lucas en la banca y gasto diario en Lucas', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/banca')
  await expect(page.getByRole('link', { name: /Lucas te avisa/ })).toBeInViewport()
  await page.goto('/lucas/resumen')
  await expect(page.getByRole('region', { name: 'Cuánto puedes gastar' })).toBeInViewport()
})

test('ingreso, banca, Lucas y guía de primera vez', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Ingresar' }).click()
  await expect(page).toHaveURL(/banca/)

  await page.getByRole('link', { name: /Lucas te avisa/ }).click()
  const guia = page.getByRole('dialog')
  await expect(guia).toContainText('Paso 1 de 3')
  await page.screenshot({ path: `capturas/${test.info().project.name}-guia.png` })
  await guia.getByRole('button', { name: 'Siguiente' }).click()
  await expect(guia).toContainText('Lo que aprendí de ti')
  await guia.getByRole('button', { name: 'Siguiente' }).click()
  await guia.getByRole('button', { name: 'Listo' }).click()
  await expect(guia).toBeHidden()

  await page.reload()
  await expect(page.getByRole('dialog')).toBeHidden()
  await page.getByRole('button', { name: 'Ver la guía' }).click()
  await expect(page.getByRole('dialog')).toContainText('Paso 1 de 3')
  await page.getByRole('button', { name: 'Saltar' }).click()
  await expect(page.getByRole('dialog')).toBeHidden()
})

test('la banca puede ocultar los montos', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/banca')
  await expect(page.getByText('S/ 1,240')).toBeVisible()
  await page.getByRole('button', { name: 'Ocultar montos' }).click()
  await expect(page.getByText('S/ 1,240')).toBeHidden()
  await expect(page.getByRole('button', { name: 'Mostrar montos' })).toHaveAttribute('aria-pressed', 'true')
})

test('Resumen: confirmar lo aprendido y ver todos los tips', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/resumen')
  const primero = page.locator('.aprendido').first()
  await primero.getByRole('button', { name: 'Sí' }).click()
  await expect(primero).toContainText('Gracias, lo sigo usando.')

  const tips = page.getByRole('region', { name: 'Tips para tu día más justo' })
  await expect(tips).toContainText('evitas 2 días en rojo')
  await expect(tips.getByRole('heading', { name: /Toma café/ })).toBeHidden()
  await tips.getByRole('button', { name: 'Ver 1 más' }).click()
  await expect(tips.getByRole('heading', { name: /Toma café/ })).toBeVisible()
})

test('Gastos compara cada categoría con el promedio', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/gastos')
  const categorias = page.getByRole('region', { name: 'Tus gastos por categoría' })
  await expect(categorias.locator('.categoria').first()).toContainText('Comida y delivery')
  await expect(categorias).toContainText('S/ 32 más que tu promedio')
  await expect(categorias).toContainText('Como siempre')
})

test('Qué viene cambia de periodo y muestra los pagos de diciembre', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/que-viene')
  const pagos = page.getByRole('region', { name: 'Pagos y cobros' })
  await expect(pagos).not.toContainText('Tarjeta de crédito')
  await page.getByRole('button', { name: '30 días' }).click()
  await expect(pagos).toContainText('Tarjeta de crédito')
})

test('el chat responde con cifras verificadas y no da asesoría', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/chat')
  await page.getByRole('button', { name: '¿Puedo gastar S/ 150 en un regalo?' }).click()
  const ultima = page.locator('.mensaje-lucas').last()
  await expect(ultima).toContainText('−S/ 210')
  await expect(ultima.getByRole('list', { name: 'Cifras verificadas' })).toBeVisible()

  await page.getByLabel('Escribe tu pregunta').fill('¿Me conviene comprar dólares?')
  await page.getByRole('button', { name: 'Enviar' }).click()
  await expect(page.locator('.mensaje-lucas').last()).toContainText('Eso no lo hago')
})

test('una pregunta sugerida desde el Resumen llega al chat una sola vez', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/resumen')
  await page.getByRole('link', { name: '¿Llego a mi cobro?' }).click()
  await expect(page).toHaveURL(/lucas\/chat$/)
  await expect(page.locator('.mensaje-tu')).toHaveCount(1)
  await expect(page.locator('.mensaje-lucas').last()).toContainText('podrías quedar en rojo')
})

test('el aviso de «solo Lucas» dura completo aunque se toquen dos botones seguidos', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/banca')
  await page.getByRole('button', { name: 'Notificaciones' }).click()
  await page.waitForTimeout(2000)
  await page.getByRole('button', { name: 'Mi perfil' }).click()
  await page.waitForTimeout(800)
  await expect(page.getByText('En esta demo solo está activo Lucas.')).toBeVisible()
})

test('la guía retiene el foco con Tab y lo devuelve al botón «?» al cerrar', async ({ page }) => {
  await page.goto('/lucas/resumen')
  await expect(page.getByRole('dialog')).toBeVisible()
  for (let i = 0; i < 4; i++) await page.keyboard.press('Tab')
  expect(await page.evaluate(() => !!document.activeElement?.closest('.guia'))).toBe(true)
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).toBeHidden()
  await expect(page.getByRole('button', { name: 'Ver la guía' })).toBeFocused()
})

test('responder «No» marca el dato como por revisar y se puede deshacer', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/resumen')
  const dato = page.locator('.aprendido').nth(1)
  await dato.getByRole('button', { name: 'No' }).click()
  await expect(dato).toContainText('Marcado como por revisar.')
  await dato.getByRole('button', { name: 'Deshacer' }).click()
  await expect(dato.getByRole('button', { name: 'No' })).toBeVisible()
})

test('los botones del selector de periodo caben en una línea', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/que-viene')
  const altos = await page.locator('.selector button').evaluateAll((bs) => bs.map((b) => b.getBoundingClientRect().height))
  for (const alto of altos) expect(alto).toBeLessThanOrEqual(40)
})
