import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { expect, test } from '@playwright/test'
import { conSigno, enSoles, textoDiasEnRojo } from '../src/formato.js'
import { vistaCon } from '../src/motor/cliente.js'
import { PERSONA_INICIAL } from '../src/motor/personas.js'
import { candidatos } from '../src/lucas/avisos.js'

// Recorre demo/GUION.md paso a paso. Las cifras esperadas salen del mismo motor que usa la app,
// así que si el motor cambia, esta prueba avisa que el guion quedó viejo.
const CAPTURAS = fileURLToPath(new URL('../../demo/capturas/', import.meta.url))
const GUION = readFileSync(new URL('../../demo/GUION.md', import.meta.url), 'utf8')

const inicio = vistaCon()
const orden = inicio.recomendaciones.map((r) => r.id)
const pasos = orden.map((_, i) => vistaCon(orden.slice(0, i + 1)))
const final = pasos.at(-1)

// La tarjeta de la banca sigue la regla de avisos: con el rojo a más de 7 días, «Lucas lo ve venir».
const { riesgoLejano } = candidatos(inicio)
const tarjetaBanca = {
  titulo: riesgoLejano ? 'Lucas lo ve venir' : 'Lucas te avisa',
  texto: riesgoLejano
    ? `En ${riesgoLejano.dias} días, ${textoDiasEnRojo(inicio.riesgo).toLowerCase()}`
    : textoDiasEnRojo(inicio.riesgo),
}

const cifras = {
  peorInicial: enSoles(inicio.riesgo.peorMonto),
  diasEnRojo: `Días en rojo ${inicio.diasEnRojo} → ${inicio.conTodos.diasEnRojo}`,
  despuesDeCadaTip: pasos.slice(0, -1).map((v) => enSoles(v.riesgo.peorMonto)),
  mejoraDeCadaTip: inicio.recomendaciones.map((r) => conSigno(r.mejora)),
  peorFinal: conSigno(final.peorDia.monto),
  apartado: enSoles(final.apartado.monto),
  apartadoTotal: enSoles(final.apartado.total),
}

test('el guion cita las cifras que da el motor', () => {
  expect(inicio.riesgo).not.toBeNull()
  expect(final.riesgo).toBeNull()
  expect(GUION).toContain(textoDiasEnRojo(inicio.riesgo).toLowerCase())
  expect(GUION).toContain(`«${tarjetaBanca.titulo}»`)
  for (const cifra of [
    cifras.peorInicial,
    cifras.diasEnRojo,
    ...cifras.mejoraDeCadaTip,
    cifras.peorFinal,
    cifras.apartado,
    cifras.apartadoTotal,
  ]) {
    // La app separa «S/» del número con un espacio que no se corta; en el guion basta un espacio normal.
    const comoEnElGuion = cifra.replaceAll(' ', ' ')
    expect(GUION, `GUION.md no menciona ${comoEnElGuion}`).toContain(comoEnElGuion)
  }
  for (const tip of inicio.recomendaciones) expect(GUION).toContain(tip.titulo)
})

test('guion de 60 s: banca → aviso → «Lo hago» → sin rojo → apartar', async ({ page }, info) => {
  const captura = (nombre) => page.screenshot({ path: `${CAPTURAS}${info.project.name}-${nombre}.png` })

  // Preparación (antes de empezar el reloj), como en el ensayo: persona independiente con su permiso dado,
  // guía ya vista y ningún tip activo.
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.goto('/')
  await page.evaluate((persona) => {
    window.localStorage.clear()
    window.localStorage.setItem('lucas-persona', persona)
    window.localStorage.setItem('lucas-consentimiento', JSON.stringify({ [persona]: '2026-11-14' }))
    window.localStorage.setItem('lucas-guia-vista', 'si')
  }, PERSONA_INICIAL)
  await page.reload()
  await page.getByRole('button', { name: 'Ingresar' }).click()

  // Paso 1: la banca de siempre, con la tarjeta de Lucas.
  await expect(page).toHaveURL(/banca/)
  const tarjeta = page.getByRole('link', { name: new RegExp(tarjetaBanca.titulo) })
  await expect(tarjeta).toContainText(tarjetaBanca.texto)
  await expect(tarjeta).toBeInViewport()
  await captura('01-banca')

  // Paso 2: el aviso con el peor caso.
  await tarjeta.click()
  await expect(page).toHaveURL(/lucas\/resumen/)
  const aviso = page.getByRole('status', { name: 'Aviso de Lucas' })
  const tips = page.getByRole('region', { name: 'Tips para tu día más justo' })
  await expect(aviso).toContainText(cifras.peorInicial)
  await expect(aviso).toBeInViewport()
  await expect(tips.locator('.impacto')).toContainText(cifras.diasEnRojo)
  await captura('02-aviso')

  // Paso 3: «Lo hago» en cada tip; el peor caso sube con cada uno.
  const botones = tips.getByRole('button', { name: 'Lo hago' })
  await expect(botones).toHaveCount(orden.length)
  await tips.scrollIntoViewIfNeeded()
  for (let i = 0; i < orden.length; i++) {
    const tip = tips.locator('.tip').nth(i)
    await expect(tip).toContainText(inicio.recomendaciones[i].titulo)
    // En vivo se desliza el carrusel hasta cada tarjeta; aquí igual, para que la captura la muestre entera.
    await tip.scrollIntoViewIfNeeded()
    await botones.nth(i).click()
    await expect(botones.nth(i)).toHaveAttribute('aria-pressed', 'true')
    // Lo que se dice en voz alta es la mejora de la tarjeta: tiene que estar a la vista, no solo en la página.
    await expect(tip.locator('.cifra')).toContainText(cifras.mejoraDeCadaTip[i])
    await expect(tip.locator('.cifra')).toBeInViewport({ ratio: 1 })
    if (i < orden.length - 1) await expect(aviso).toContainText(cifras.despuesDeCadaTip[i])
    else await expect(aviso).toContainText('Vas bien')
    await captura(`03-lo-hago-${i + 1}`)
  }
  await expect(tips.locator('.impacto')).toContainText(`Días en rojo ${final.diasEnRojo}`)
  await expect(tips.locator('.impacto')).toBeInViewport()

  // Paso 4: el rojo desapareció del pronóstico.
  await page.getByRole('link', { name: 'Qué viene' }).click()
  // El cambio de pestaña conserva el scroll del Resumen; en vivo se sube hasta arriba.
  await page.evaluate(() => window.scrollTo(0, 0))
  const panel = page.locator('.panel-grafico')
  await expect(panel.locator('.panel-cifra')).toHaveText(cifras.peorFinal)
  await expect(panel.locator('.panel-cifra')).toBeInViewport()
  await expect(panel).toContainText('Con tus cambios llegas a tu cobro sin quedar en rojo')
  await captura('04-sin-rojo')

  // Paso 5: lo que puede apartar al cobrar.
  await page.getByRole('link', { name: 'Resumen' }).click()
  const apartado = tips.locator('.tip').last()
  // Centrada, para que la barra inferior no tape el total que se dice en voz alta.
  await apartado.evaluate((tarjeta) => tarjeta.scrollIntoView({ block: 'center', inline: 'center' }))
  await expect(apartado).toContainText(`podrías apartar ${cifras.apartado}`)
  await expect(apartado).toContainText(cifras.apartadoTotal)
  await expect(apartado.getByRole('heading', { level: 3 })).toBeInViewport({ ratio: 1 })
  await expect(apartado.locator('p', { hasText: cifras.apartadoTotal })).toBeInViewport({ ratio: 1 })
  await captura('05-apartar')
})
