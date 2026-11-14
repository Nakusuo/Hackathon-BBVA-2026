import assert from 'node:assert/strict'
import { test } from 'node:test'
import { PREGUNTAS_SUGERIDAS, responder } from '../src/lucas/respuestas.js'
import { cliente, persona } from '../src/motor/cliente.js'
import { evaluarGastoExtra } from '../src/motor/motor.js'

const NBSP = ' '
const preguntar = (texto) => responder(texto, cliente, persona)

test('cada pregunta sugerida tiene una respuesta propia, no la de «no entiendo»', () => {
  for (const p of PREGUNTAS_SUGERIDAS) {
    assert.doesNotMatch(preguntar(p).texto, /Todavía no sé/, p)
  }
})

test('las cifras de un gasto extra salen del motor y no del texto de la pregunta', () => {
  const esperado = evaluarGastoExtra(persona, 40)
  const r = preguntar('¿puedo gastar 40 en cine?')
  assert.ok(r.cifras.some((c) => c.valor === `−S/${NBSP}${Math.abs(esperado.peorDespues)}`))
  assert.ok(r.cifras.some((c) => c.valor === `S/${NBSP}${esperado.gastoDiarioSeguro}`))
})

test('montos con separador de miles se leen bien', () => {
  const r = preguntar('¿Puedo comprar algo de S/ 1,200?')
  assert.equal(r.cifras[0].valor, `S/${NBSP}1,200`)
})

test('no da asesoría de inversión ni ofrece mover plata', () => {
  for (const p of ['¿compro dólares?', '¿en qué acciones invierto?', 'transfiere 100 a mi mamá']) {
    assert.match(preguntar(p).texto, /no lo hago/, p)
  }
})

test('lo que no entiende lo dice sin inventar cifras', () => {
  const r = preguntar('hola')
  assert.match(r.texto, /Todavía no sé/)
  assert.deepEqual(r.cifras, [])
})

test('lectura de montos: con «S/», con «soles», con punto de miles y sin confundir días', async () => {
  const { montoEn } = await import('../src/lucas/respuestas.js')
  assert.equal(montoEn('¿puedo gastar s/ 150?'), 150)
  assert.equal(montoEn('un regalo de 80 soles'), 80)
  assert.equal(montoEn('algo de s/ 1.500'), 1500)
  assert.equal(montoEn('algo de s/ 12.50'), 12.5)
  assert.equal(montoEn('pagar la tarjeta el 1'), null)
  assert.equal(montoEn('el 15 gasto 40'), 40)
})

test('un gasto mayor que el saldo dice que no alcanza, sin decir «Puedes»', () => {
  const r = preguntar('¿puedo gastar 100000?')
  assert.match(r.texto, /^No te alcanza/)
  assert.doesNotMatch(r.texto, /Puedes/)
})

test('un gasto igual al saldo no se rechaza por saldo; un sol más, sí', () => {
  const justo = preguntar(`¿puedo gastar ${cliente.saldoHoy}?`).texto
  const pasado = preguntar(`¿puedo gastar ${cliente.saldoHoy + 1}?`).texto
  assert.doesNotMatch(justo, /^No te alcanza/)
  assert.match(pasado, /^No te alcanza/)
})

test('si el peor caso ya está en rojo, nunca responde «Sí, te alcanza»', () => {
  assert.doesNotMatch(preguntar('¿puedo gastar 5 en un chocolate?').texto, /Sí, te alcanza/)
})

test('con los tips activos el chat usa ese plan', async () => {
  const { vistaCon, CAMBIOS } = await import('../src/motor/cliente.js')
  const conTips = vistaCon(CAMBIOS.map((c) => c.id))
  assert.match(responder('¿puedo gastar 5?', conTips, persona).texto, /Sí, te alcanza/)
  assert.match(responder('¿Llego a mi cobro?', conTips, persona).texto, /^Sí/)
})

test('preguntar por un ahorro concreto lo comprueba contra los pagos', () => {
  assert.match(preguntar('¿Puedo ahorrar 30?').texto, /^Sí/)
  assert.match(preguntar('¿Puedo ahorrar 900?').texto, /^Es mucho/)
})
