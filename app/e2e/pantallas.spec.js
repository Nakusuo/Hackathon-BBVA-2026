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

    // Con movimiento reducido las cifras se muestran ya en su valor final: así las capturas no salen a mitad de animación.
    await page.emulateMedia({ reducedMotion: 'reduce' })
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

test('con movimiento reducido las cifras del resumen salen ya en su valor final', async ({ page }) => {
  await sinGuia(page)
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.goto('/lucas/resumen')
  const recuadros = page.getByRole('region', { name: 'Cuánto puedes gastar' })
  await expect(recuadros.locator('.recuadro-cifra [aria-hidden="true"]').first()).toHaveText('S/ 26')
  await expect(recuadros.locator('.recuadro-cifra [aria-hidden="true"]').nth(1)).toHaveText('S/ 30')
})

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
  const tarjeta = page.locator('.guia-tarjeta')
  // Cada paso debe verse completo: antes el paso 2 quedaba aplastado en 36 px.
  for (const [paso, texto] of [[1, 'Lo que puedes gastar'], [2, 'Lo que aprendí de ti'], [3, 'Pregúntame']]) {
    await expect(guia).toContainText(`Paso ${paso} de 3`)
    await expect(guia).toContainText(texto)
    await page.waitForTimeout(150)
    const caja = await tarjeta.boundingBox()
    expect(caja.height).toBeGreaterThan(120)
    expect(caja.y).toBeGreaterThanOrEqual(0)
    expect(caja.y + caja.height).toBeLessThanOrEqual(page.viewportSize().height)
    await page.screenshot({ path: `capturas/${test.info().project.name}-guia-${paso}.png` })
    await guia.getByRole('button', { name: paso === 3 ? 'Listo' : 'Siguiente' }).click()
  }
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
  const ojo = page.getByRole('button', { name: 'Ocultar montos' })
  await ojo.click()
  await expect(page.getByText('S/ 1,240')).toBeHidden()
  await expect(ojo).toHaveAttribute('aria-pressed', 'true')
})

test('Resumen: confirmar lo aprendido', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/resumen')
  const primero = page.locator('.aprendido').first()
  await primero.getByRole('button', { name: 'Sí' }).click()
  await expect(primero).toContainText('Gracias, lo sigo usando.')
})

test('«Lo hago» recalcula el plan en todas las pantallas y se recuerda', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/resumen')
  const tips = page.getByRole('region', { name: 'Tips para tu día más justo' })
  await expect(tips).toContainText('Si haces los 3')
  const botones = tips.getByRole('button', { name: 'Lo hago' })
  await expect(botones).toHaveCount(3)

  await botones.nth(0).click()
  await expect(botones.nth(0)).toHaveAttribute('aria-pressed', 'true')
  await expect(tips).toContainText('Con tu cambio, tu peor caso del domingo 29 pasa de −S/ 60 a −S/ 29')

  await botones.nth(1).click()
  await botones.nth(2).click()
  await expect(tips).toContainText('Ya no quedas en rojo antes de cobrar')
  await expect(page.getByRole('status', { name: 'Aviso de Lucas' })).toContainText('Vas bien')
  await expect(page.getByText('podrías apartar S/ 150')).toBeVisible()

  await page.getByRole('link', { name: 'Qué viene' }).click()
  await expect(page.locator('.panel-grafico')).toContainText('Con tus cambios llegas a tu cobro')

  await page.goto('/banca')
  await expect(page.getByRole('link', { name: /Con tus cambios llegas/ })).toBeVisible()

  await page.goto('/lucas/resumen')
  await expect(tips.getByRole('button', { name: 'Lo hago' }).first()).toHaveAttribute('aria-pressed', 'true')
  await tips.getByRole('button', { name: 'Lo hago' }).first().click()
  await expect(page.getByRole('status', { name: 'Aviso de Lucas' })).toContainText('Lucas te avisa')
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
  await expect(pagos).not.toContainText('Pago total de tarjeta')
  await page.getByRole('button', { name: '30 días' }).click()
  await expect(pagos).toContainText('Pago total de tarjeta')
})

test('el chat responde con cifras verificadas y no da asesoría', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/chat')
  await page.getByRole('button', { name: '¿Puedo gastar S/ 150 en un regalo?' }).click()
  const ultima = page.locator('.mensaje-lucas').last()
  await expect(ultima).toContainText('−S/ 210')
  await expect(ultima.getByRole('list', { name: 'Calculado con tus datos' })).toBeVisible()

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

test('el botón «?» abre la guía desde cualquier pestaña de Lucas', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/gastos')
  await page.getByRole('button', { name: 'Ver la guía' }).click()
  await expect(page).toHaveURL(/lucas\/resumen/)
  await expect(page.getByRole('dialog')).toContainText('Paso 1 de 3')
})

test('la guía no aparece sola si la primera entrada a Lucas no es el Resumen', async ({ page }) => {
  await page.goto('/lucas/chat')
  await page.getByRole('link', { name: 'Resumen' }).click()
  await expect(page.getByRole('dialog')).toBeHidden()
})
