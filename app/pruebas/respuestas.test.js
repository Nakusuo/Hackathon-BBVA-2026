import assert from 'node:assert/strict'
import { test } from 'node:test'
import { PREGUNTAS_SUGERIDAS, responder } from '../src/lucas/respuestas.js'
import { cliente, persona } from '../src/mocks/cliente.js'
import { evaluarGastoExtra } from '../src/mocks/motor.js'

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
