import { readFileSync } from 'node:fs'
import { expect, test } from '@playwright/test'

const mock = (nombre) => readFileSync(new URL(`../../data/sample/mocks/${nombre}.json`, import.meta.url), 'utf-8')
const RUTAS_API = {
  '/api/v1/customers/demo-001/health': 'health',
  '/api/v1/customers/demo-001/forecast': 'forecast',
  '/api/v1/customers/demo-001/recommendations': 'recommendations',
  '/api/v1/customers/demo-001/events': 'events',
  '/api/v1/fx': 'fx',
  '/api/v1/simulations': 'simulation',
}

// Las pruebas no dependen de que FastAPI esté levantada: la API responde con los JSON del contrato.
test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/**', (ruta) => {
    const nombre = RUTAS_API[new URL(ruta.request().url()).pathname]
    return nombre
      ? ruta.fulfill({ contentType: 'application/json', body: mock(nombre) })
      : ruta.fulfill({ status: 404, contentType: 'application/json', body: '{"detail":"No existe"}' })
  })
})

const PANTALLAS = [
  { ruta: '/ingresar', titulo: 'Ingresa a tu banca' },
  { ruta: '/consentimiento', titulo: 'Antes de activar Lucas' },
  { ruta: '/banca', titulo: 'Hola' },
  { ruta: '/lucas/resumen', titulo: 'Lucas' },
  { ruta: '/lucas/gastos', titulo: 'Lucas' },
  { ruta: '/lucas/que-viene', titulo: 'Lucas' },
  { ruta: '/lucas/chat', titulo: 'Lucas' },
  { ruta: '/lucas/aprendido', titulo: 'Lucas' },
  { ruta: '/lucas/salud', titulo: 'Lucas' },
  { ruta: '/lucas/gastos-detalle', titulo: 'Lucas' },
  { ruta: '/lucas/avisos', titulo: 'Lucas' },
  { ruta: '/evidencia', titulo: 'Evidencia de Lucas' },
  { ruta: '/preferencias', titulo: 'Preferencias' },
]

// Permiso ya dado para la persona de la demo, como quien ya pasó por el consentimiento.
async function conPermiso(page) {
  await page.addInitScript(() => {
    if (!window.sessionStorage.getItem('e2e-preparado')) {
      window.localStorage.setItem('lucas-consentimiento', JSON.stringify({ independiente: '2026-11-14' }))
      window.sessionStorage.setItem('e2e-preparado', 'si')
    }
  })
}

async function sinGuia(page) {
  await conPermiso(page)
  await page.addInitScript(() => window.localStorage.setItem('lucas-guia-vista', 'si'))
}

for (const { ruta, titulo } of PANTALLAS) for (const tema of ['claro', 'oscuro']) {
  test(`${ruta} en ${tema} abre sin errores, sin scroll horizontal y con texto de 16 px o más`, async ({ page }, info) => {
    await sinGuia(page)
    await page.addInitScript((t) => window.localStorage.setItem('lucas-tema', t), tema)
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
    // Movimiento reducido no apaga los desvanecidos de entrada: sin esperar, la captura salía a medio aparecer.
    await page.waitForFunction(() => document.getAnimations().every((a) => a.playState !== 'running'))
    await page.screenshot({ path: `capturas/${info.project.name}-${tema}${ruta.replaceAll('/', '-')}.png`, fullPage: true })
    expect(textosChicos).toEqual([])
    expect(errores).toEqual([])
  })
}

test('con movimiento reducido las cifras del resumen salen ya en su valor final', async ({ page }) => {
  await sinGuia(page)
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.goto('/lucas/resumen')
  const recuadros = page.getByRole('region', { name: 'Cuánto puedes gastar' })
  await expect(recuadros.locator('.hero-cifra [aria-hidden="true"]')).toHaveText('S/ 26')
  await expect(recuadros.locator('.hero-actual [aria-hidden="true"]')).toHaveText('S/ 30')
})

test('lo importante se ve sin bajar: aviso de Lucas en la banca y gasto diario en Lucas', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/banca')
  await expect(page.getByRole('link', { name: /Lucas lo ve venir/ })).toBeInViewport()
  await page.goto('/lucas/resumen')
  await expect(page.getByRole('region', { name: 'Cuánto puedes gastar' })).toBeInViewport()
})

test('ingreso, permiso, banca, Lucas y guía de primera vez', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Ingresar' }).click()
  await expect(page).toHaveURL(/consentimiento/)
  await page.getByRole('button', { name: 'Acepto, activar Lucas' }).click()
  await expect(page).toHaveURL(/banca/)

  await page.getByRole('link', { name: /Lucas lo ve venir/ }).click()
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

test('Resumen: confirmar lo aprendido desde su bloque', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/resumen')
  await page.getByRole('link', { name: /Lo que aprendí/ }).click()
  await expect(page).toHaveURL(/lucas\/aprendido/)
  const primero = page.locator('.aprendido').first()
  await primero.getByRole('button', { name: 'Sí' }).click()
  await expect(primero).toContainText('Gracias, lo sigo usando.')
})

test('«Lo hago» recalcula el plan en todas las pantallas y se recuerda', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/resumen')
  const tips = page.getByRole('region', { name: 'Tips para tu día más justo' })
  const aviso = page.getByRole('status', { name: 'Aviso de Lucas' })
  await expect(tips.locator('.impacto')).toContainText('Días en rojo 2 → 0')
  const salud = page.getByRole('link', { name: /Tu salud/ })
  await expect(salud).toContainText('55, vas regular · 63 con los tips')
  const botones = tips.getByRole('button', { name: 'Lo hago' })
  await expect(botones).toHaveCount(3)
  await expect(tips.locator('.tip').nth(0)).toContainText('Evitas 1 día en rojo')
  await expect(tips.locator('.tip').nth(2)).not.toContainText('Evitas')

  await botones.nth(0).click()
  await expect(botones.nth(0)).toHaveAttribute('aria-pressed', 'true')
  await expect(aviso).toContainText('−S/ 29')
  await expect(tips.locator('.tip').nth(0)).toContainText('Llevas 0 de 2 veces en RapiFood hasta el 30 nov')

  await expect(tips.locator('.tip').nth(0)).not.toContainText('Evitas')
  await botones.nth(1).click()
  await expect(tips.locator('.impacto')).toContainText('Días en rojo 1 → 0')
  await expect(tips.locator('.tip').nth(2)).toContainText('Evitas 1 día en rojo')
  await botones.nth(2).click()
  await expect(tips.locator('.impacto')).toContainText('Días en rojo 0')
  await expect(aviso).toContainText('Vas bien')
  await expect(page.getByText('podrías apartar S/ 150')).toBeVisible()
  await expect(salud).toContainText('63, vas regular')
  await expect(salud).not.toContainText('con los tips')

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
  await expect(page.locator('.leyenda-gastos li').first()).toContainText('Comida y delivery')
  await page.getByRole('link', { name: 'Ver detalle' }).click()
  const categorias = page.getByRole('region', { name: 'Tus gastos por categoría' })
  await expect(categorias.locator('.categoria').first()).toContainText('Comida y delivery')
  await expect(categorias).toContainText('S/ 32 más que tu promedio')
  await expect(categorias).toContainText('Como siempre')
})

test('MusiKa se pausa desde Suscripciones y queda elegida en los tips', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/gastos-detalle')
  const suscripciones = page.getByRole('region', { name: 'Suscripciones' })
  const pausar = suscripciones.getByRole('button', { name: 'La pausaré hasta mi cobro: MusiKa Plus' })
  await expect(suscripciones.getByRole('button')).toHaveCount(1)
  const fila = suscripciones.locator('.fila').filter({ hasText: 'MusiKa' })
  await expect(fila).toContainText('+S/ 22 el 29 nov. Evitas 1 día en rojo')
  await pausar.click()
  await expect(pausar).toHaveAttribute('aria-pressed', 'true')
  await expect(fila).toContainText('Recuerda pausarla antes del 20 nov')

  await page.goto('/lucas/resumen')
  const tip = page.locator('.tip').filter({ hasText: 'Pausa MusiKa' })
  await expect(tip.getByRole('button', { name: 'Lo hago' })).toHaveAttribute('aria-pressed', 'true')
  await expect(tip).toContainText('antes del 20 nov')
})

test('cada parte de la salud lleva a una acción', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/salud')
  const salud = page.getByRole('region', { name: /Tu salud financiera/ })
  await expect(salud.getByRole('link')).toHaveCount(4)
  await salud.getByRole('link', { name: 'Ver tips para tu día más justo' }).click()
  await expect(page).toHaveURL(/lucas\/resumen#tips/)
  await expect(page.getByRole('region', { name: 'Tips para tu día más justo' })).toBeInViewport()

  await page.goto('/lucas/salud')
  await salud.getByRole('link', { name: 'Ver tus próximos pagos' }).click()
  await expect(page.getByRole('region', { name: 'Pagos y cobros' })).toBeVisible()
})

test('Qué viene cambia de periodo y muestra los pagos de diciembre', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/que-viene')
  const pagos = page.getByRole('region', { name: 'Pagos y cobros' })
  await expect(pagos).not.toContainText('Pago total de tarjeta')
  await page.getByRole('button', { name: '30 días' }).click()
  await expect(pagos).toContainText('Pago total de tarjeta')
})

async function agenteCaido(page) {
  await page.route('**/api/v1/chat', (ruta) => ruta.abort('connectionrefused'))
}

test('el chat responde «Calculado con tus datos» y no da asesoría', async ({ page }) => {
  await sinGuia(page)
  await agenteCaido(page)
  await page.goto('/lucas/chat')
  await page.getByRole('button', { name: '¿Puedo gastar S/ 150 en un regalo?' }).click()
  const ultima = page.locator('.mensaje-lucas').last()
  await expect(ultima).toContainText('−S/ 210')
  await expect(ultima.getByRole('list', { name: 'Calculado con tus datos' })).toBeVisible()

  await page.getByLabel('Escribe tu pregunta').fill('¿Me conviene comprar dólares?')
  await page.getByRole('button', { name: 'Enviar' }).click()
  await expect(page.locator('.mensaje-lucas').last()).toContainText('Eso no lo hago')
})

test('con el agente, el chat muestra «pensando», las cifras verificadas con ✓ y las fuentes', async ({ page }) => {
  await sinGuia(page)
  let soltar
  const espera = new Promise((r) => (soltar = r))
  await page.route('**/api/v1/chat', async (ruta) => {
    await espera
    await ruta.fulfill({
      json: {
        conversation_id: 'conv-001',
        answer: 'Si gastas S/ 150, tu saldo mínimo probable sería -S/ 310. Tú decides.',
        provider: 'ollama',
        verified: true,
        figures: [{ label: 'Saldo mínimo probable', value: -310, unit: 'PEN' }],
        sources: [{ id: 'guia-1', title: 'Guía de presupuesto personal', url: 'https://ejemplo.pe/guia' }],
        tools_used: ['simulate'],
      },
    })
  })
  await page.goto('/lucas/chat')
  await page.getByRole('button', { name: '¿Puedo gastar S/ 150 en un regalo?' }).click()
  await expect(page.getByText('Lucas está pensando')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Enviar' })).toBeDisabled()
  soltar()

  const ultima = page.locator('.mensaje-lucas').last()
  const cifras = ultima.getByRole('list', { name: 'Cifras verificadas con tus datos' })
  await expect(cifras).toContainText('−S/ 310')
  await expect(cifras).toContainText('verificada')
  await expect(ultima.getByRole('link', { name: 'Guía de presupuesto personal' })).toHaveAttribute('href', 'https://ejemplo.pe/guia')
  await expect(page.getByText('Lucas está pensando')).toHaveCount(0)

  const anchoExtra = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
  expect(anchoExtra).toBeLessThanOrEqual(0)
})

test('si el agente falla, el chat lo dice y responde con sus cálculos', async ({ page }) => {
  await sinGuia(page)
  await page.route('**/api/v1/chat', (ruta) => ruta.fulfill({ status: 500, body: 'error' }))
  await page.goto('/lucas/chat')
  await page.getByRole('button', { name: '¿Llego a mi cobro?' }).click()
  const ultima = page.locator('.mensaje-lucas').last()
  await expect(ultima).toContainText('No pude hablar con el agente de Lucas')
  await expect(ultima.getByRole('list', { name: 'Calculado con tus datos' })).toBeVisible()
  await expect(page.getByText('No es asesoría')).toBeVisible()
})

test('si el agente no verificó sus cifras, su texto no se muestra', async ({ page }) => {
  await sinGuia(page)
  await page.route('**/api/v1/chat', (ruta) =>
    ruta.fulfill({ json: { conversation_id: 'c', answer: 'Te quedan S/ 9 999. Tú decides.', verified: false, sources: [] } }),
  )
  await page.goto('/lucas/chat')
  await page.getByRole('button', { name: '¿Llego a mi cobro?' }).click()
  const ultima = page.locator('.mensaje-lucas').last()
  await expect(ultima).toContainText('no pudo comprobar sus cifras')
  await expect(ultima).not.toContainText('9 999')
  await expect(ultima.getByRole('list', { name: 'Calculado con tus datos' })).toBeVisible()
})

test('una pregunta sugerida desde el Resumen llega al chat una sola vez', async ({ page }) => {
  await sinGuia(page)
  await agenteCaido(page)
  await page.goto('/lucas/resumen')
  await page.getByRole('link', { name: '¿Llego a mi cobro?' }).click()
  await expect(page).toHaveURL(/lucas\/chat$/)
  await expect(page.locator('.mensaje-tu')).toHaveCount(1)
  await expect(page.locator('.mensaje-lucas').last()).toContainText('podrías quedar en rojo')
})

test('el aviso de «solo Lucas» dura completo aunque se toquen dos botones seguidos', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/banca')
  await page.getByRole('button', { name: 'Transferir' }).click()
  await page.waitForTimeout(2000)
  await page.getByRole('button', { name: 'Mi perfil' }).click()
  await page.waitForTimeout(800)
  await expect(page.getByText('En esta demo solo está activo Lucas.')).toBeVisible()
})

test('la guía retiene el foco con Tab y lo devuelve al botón «?» al cerrar', async ({ page }) => {
  await conPermiso(page)
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
  await page.goto('/lucas/aprendido')
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
  await conPermiso(page)
  await page.goto('/lucas/chat')
  await page.getByRole('link', { name: 'Resumen' }).click()
  await expect(page.getByRole('dialog')).toBeHidden()
})

test('consentimiento: «Ahora no» deja la banca sin Lucas, y aceptar vuelve a donde se iba', async ({ page }) => {
  await page.addInitScript(() => window.localStorage.setItem('lucas-guia-vista', 'si'))
  await page.goto('/ingresar')
  await page.getByRole('button', { name: 'Ingresar' }).click()
  const permiso = page.getByRole('region', { name: 'Antes de activar Lucas' })
  await expect(permiso).toContainText('Datos sintéticos')
  await expect(permiso).toContainText('Qué uso')
  await expect(permiso).toContainText('Para qué')
  await expect(permiso).toContainText('Más → Preferencias → Privacidad')
  await page.getByRole('button', { name: 'Ahora no' }).click()

  await expect(page).toHaveURL(/banca/)
  await expect(page.getByRole('link', { name: /Activa Lucas/ })).toBeVisible()
  await expect(page.getByText('Lucas te avisa')).toHaveCount(0)

  await page.getByRole('navigation', { name: 'Menú principal' }).getByRole('link', { name: 'Lucas' }).click()
  await expect(page).toHaveURL(/consentimiento/)
  await page.getByRole('button', { name: 'Acepto, activar Lucas' }).click()
  await expect(page).toHaveURL(/lucas\/resumen/)
  await expect(page.getByRole('region', { name: 'Cuánto puedes gastar' })).toBeVisible()
})

test('retirar el permiso desde Preferencias apaga Lucas y borra los tips elegidos', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/resumen')
  await page.getByRole('button', { name: 'Lo hago' }).first().click()

  await page.goto('/preferencias')
  const privacidad = page.getByRole('region', { name: 'Privacidad' })
  await expect(privacidad).toContainText('Activo desde el')
  await privacidad.getByRole('button', { name: 'Retirar permiso' }).click()
  await privacidad.getByRole('button', { name: 'Cancelar' }).click()
  await expect(privacidad).toContainText('Activo desde el')
  await privacidad.getByRole('button', { name: 'Retirar permiso' }).click()
  await privacidad.getByRole('button', { name: 'Sí, retirar' }).click()
  await expect(privacidad.getByRole('status')).toContainText('Lucas está apagado')
  expect(await page.evaluate(() => window.localStorage.getItem('lucas-tips-elegidos'))).toBe('[]')

  await page.goto('/lucas/que-viene')
  await expect(page).toHaveURL(/consentimiento/)
  await page.getByRole('button', { name: 'Acepto, activar Lucas' }).click()
  await expect(page).toHaveURL(/lucas\/que-viene/)
  await page.getByRole('link', { name: 'Resumen' }).click()
  await expect(page.getByRole('button', { name: 'Lo hago' }).first()).toHaveAttribute('aria-pressed', 'false')
})

test('selector de persona: el formal cambia todas las cifras y su banda es angosta', async ({ page }) => {
  await page.addInitScript(() => window.localStorage.setItem('lucas-guia-vista', 'si'))
  await page.goto('/ingresar')
  await page.getByRole('radio', { name: 'Formal con quincena' }).check()
  await expect(page.getByText('Sueldo fijo el 15 y a fin de mes')).toBeVisible()
  await page.getByRole('button', { name: 'Ingresar' }).click()
  await expect(page.getByRole('region', { name: 'Antes de activar Lucas' })).toContainText('Formal con quincena')
  await page.getByRole('button', { name: 'Acepto, activar Lucas' }).click()

  await expect(page.getByText('S/ 1,610')).toBeVisible()
  await page.goto('/lucas/resumen')
  await expect(page.getByRole('region', { name: 'Cuánto puedes gastar' })).toContainText('S/ 1,300')
  await expect(page.getByRole('button', { name: 'Lo hago' })).toHaveCount(3)
  await expect(page.getByText('Pausa FitZona este mes')).toBeVisible()
  await page.getByRole('link', { name: 'Qué viene' }).click()
  await expect(page.getByRole('region', { name: 'Pagos y cobros' })).toContainText('El rango es angosto')

  // Volver al independiente desde Preferencias: su permiso es aparte y su banda se explica distinto.
  await page.goto('/preferencias')
  await page.getByRole('radio', { name: 'Independiente' }).check()
  await page.getByRole('link', { name: 'Inicio' }).first().click()
  await expect(page.getByText('S/ 1,240')).toBeVisible()
  await expect(page.getByRole('link', { name: /Activa Lucas/ })).toBeVisible()
})

for (const { ruta, frase } of [
  { ruta: '/lucas/resumen', frase: 'Lo que puedes gastar' },
  { ruta: '/lucas/que-viene', frase: 'La franja de color' },
]) {
  test(`«Explícamelo fácil» en ${ruta} explica el peor caso y devuelve el foco al cerrar`, async ({ page }) => {
    await sinGuia(page)
    await page.goto(ruta)
    const boton = page.getByRole('button', { name: 'Explícamelo fácil' })
    await expect(boton).toHaveAttribute('aria-expanded', 'false')
    await boton.click()
    const panel = page.getByRole('region', { name: 'Explicación fácil' })
    await expect(panel).toContainText('Peor caso')
    await expect(panel).toContainText(frase)
    await page.screenshot({ path: `capturas/${test.info().project.name}-facil${ruta.replaceAll('/', '-')}.png`, fullPage: true })
    await panel.getByRole('button', { name: 'Entendido' }).click()
    await expect(panel).toBeHidden()
    await expect(boton).toBeFocused()
  })
}

test('con la API arriba no aparece ningún aviso de datos', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/resumen')
  await expect(page.getByText('Puedes gastar al día')).toBeVisible()
  await expect(page.locator('.estado-datos')).toHaveCount(0)
})

test('si la API se cae, Lucas lo dice y las cifras y «Lo hago» siguen funcionando', async ({ page }) => {
  await sinGuia(page)
  const errores = []
  page.on('pageerror', (e) => errores.push(e.message))
  await page.route('**/api/v1/**', (ruta) => ruta.fulfill({ status: 503, body: 'caída' }))
  await page.goto('/lucas/resumen')
  await expect(page.getByRole('status').filter({ hasText: 'No llegaron tus datos del servidor' })).toBeVisible()
  await expect(page.locator('.hero-cifra [aria-hidden="true"]')).toHaveText('S/ 26')
  const primerTip = page.getByRole('region', { name: 'Tips para tu día más justo' }).getByRole('button', { name: 'Lo hago' }).first()
  await primerTip.click()
  await expect(primerTip).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByRole('status', { name: 'Aviso de Lucas' })).toContainText('−S/ 29')
  expect(errores).toEqual([])
})

test('si la API tarda demasiado, Lucas pasa a los datos guardados sin quedarse cargando', async ({ page }) => {
  await sinGuia(page)
  await page.route('**/api/v1/**', () => {})
  await page.goto('/lucas/resumen')
  await expect(page.getByText('Puedes gastar al día')).toBeVisible()
  await expect(page.getByRole('status').filter({ hasText: 'No llegaron tus datos del servidor' })).toBeVisible({ timeout: 8000 })
})

test('Avisos: la campana abre la bandeja; hoy el riesgo está a 14 días y no gasta aviso', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/banca')
  await page.getByRole('link', { name: /^Avisos de Lucas/ }).click()
  await expect(page).toHaveURL(/lucas\/avisos/)
  const avisos = page.locator('.aviso-item')
  await expect(avisos).toHaveCount(1)
  await expect(avisos.first()).toContainText('MusiKa Plus')
  await expect(page.locator('.aviso-item[data-tipo="riesgo"]')).toHaveCount(0)
  await expect(page.getByText(/Tu riesgo de quedar en rojo empieza .* en 14 días/)).toBeVisible()
  for (const aviso of await avisos.all()) {
    await expect(aviso.getByText('Aviso', { exact: true })).toBeVisible()
    await expect(aviso.getByText(/^Impacto:/)).toBeVisible()
  }
})

test('Avisos: a 7 días del riesgo es normal, a 2 días urgente, siempre con texto', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/avisos')
  await page.getByText('Probar la regla en la demo').click()
  const dia = page.getByRole('group', { name: 'Día de la demo' })

  await dia.getByRole('button', { name: '21 nov' }).click()
  const riesgo = page.locator('.aviso-item[data-tipo="riesgo"]')
  await expect(riesgo).toHaveCount(1)
  await expect(riesgo.getByText('Aviso', { exact: true })).toBeVisible()
  await expect(riesgo).toContainText('Podrías quedar en rojo')

  await dia.getByRole('button', { name: '26 nov' }).click()
  await expect(riesgo.getByText('Urgente', { exact: true })).toBeVisible()
  await page.screenshot({ path: `capturas/${test.info().project.name}-avisos-urgente.png`, fullPage: true })

  await riesgo.getByRole('link', { name: 'Ver cómo evitarlo' }).click()
  await expect(page).toHaveURL(/lucas\/resumen#tips/)
})

test('Avisos CP-SIS-29: un gasto que adelanta el rojo actualiza el mismo aviso sin gastar otro lugar', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/avisos')
  await page.getByText('Probar la regla en la demo').click()
  await page.getByRole('group', { name: 'Día de la demo' }).getByRole('button', { name: '21 nov' }).click()
  const riesgo = page.locator('.aviso-item[data-tipo="riesgo"]')
  const contador = page.getByText(/Esta semana van \d de 3/)
  const antes = { contador: await contador.textContent(), texto: await riesgo.textContent() }

  await page.getByRole('group', { name: 'Gasto de prueba' }).getByRole('button', { name: /mañana/ }).click()
  await expect(riesgo).toHaveCount(1)
  await expect(riesgo).not.toHaveText(antes.texto)
  await expect(contador).toHaveText(antes.contador)
})

test('Avisos: «útil / no me sirve» se marca y se recuerda al volver', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/avisos')
  const primero = page.locator('.aviso-item').first()
  const util = primero.getByRole('button', { name: 'Útil' })
  await util.click()
  await expect(util).toHaveAttribute('aria-pressed', 'true')
  await expect(primero.getByRole('status')).toHaveText(/Anotado/)
  await primero.getByRole('button', { name: 'No me sirve' }).click()
  await expect(util).toHaveAttribute('aria-pressed', 'false')
  await page.reload()
  await expect(page.locator('.aviso-item').first().getByRole('button', { name: 'No me sirve' })).toHaveAttribute(
    'aria-pressed',
    'true',
  )
})

test('Evidencia: empieza por el impacto en S/, cada cifra con su fuente y muestra lo que empeora', async ({ page }) => {
  await page.goto('/ingresar')
  await page.getByRole('link', { name: 'Ver la evidencia de los modelos' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Evidencia de Lucas' })).toBeVisible()
  await expect(page.getByRole('heading', { level: 2 }).first()).toHaveText('Impacto en S/ por cliente')
  await expect(page.getByRole('heading', { name: 'Impacto en S/ por cliente' })).toBeInViewport()
  await expect(page.getByText('S/ 322', { exact: true })).toBeVisible()
  expect(await page.locator('.fuente').count()).toBeGreaterThan(20)
  await expect(page.getByText('Peor que el baseline').first()).toBeVisible()
  await expect(page.getByText('Empeora').first()).toBeVisible()
})

test('Avisos: probar la regla en la demo no gasta el tope de la semana real', async ({ page }) => {
  await sinGuia(page)
  await page.goto('/lucas/avisos')
  await expect(page.getByText('Esta semana van 1 de 3')).toBeVisible()
  await page.getByText('Probar la regla en la demo').click()
  await page.getByRole('group', { name: 'Día de la demo' }).getByRole('button', { name: '26 nov' }).click()
  await page.getByRole('group', { name: 'Gasto de prueba' }).getByRole('button', { name: /mañana/ }).click()
  await page.goto('/banca')
  await expect(page.getByRole('link', { name: 'Avisos de Lucas: 1' })).toBeVisible()
  const guardado = await page.evaluate(() => JSON.parse(window.localStorage.getItem('lucas-avisos-semana')))
  expect(Object.keys(guardado)).toEqual(['2026-11-09'])
})
