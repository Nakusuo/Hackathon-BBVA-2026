import assert from 'node:assert/strict'
import { test } from 'node:test'
import { AVISOS, CLIENTE_ID, desdeAgente, preguntarALucas } from '../src/lucas/clienteChat.js'
import { cliente, persona } from '../src/mocks/cliente.js'

const NBSP = ' '
const RESPUESTA = {
  conversation_id: 'conv-001',
  answer: 'Si gastas S/ 150, tu saldo mínimo probable sería -S/ 310. Tú decides.',
  provider: 'ollama',
  verified: true,
  figures: [
    { label: 'Gasto que consultas', value: 150, unit: 'PEN', text: 'S/ 150' },
    { label: 'Saldo mínimo probable', value: -310, unit: 'PEN', text: '-S/ 310' },
  ],
  sources: [{ id: 'sbs-1', title: 'Guía de presupuesto', url: 'https://ejemplo.pe/guia' }],
  tools_used: ['simulate'],
}

function falsoFetch(respuesta, registro = []) {
  return async (url, opciones) => {
    registro.push({ url, cuerpo: JSON.parse(opciones.body) })
    if (respuesta instanceof Error) throw respuesta
    return { ok: respuesta.status === undefined, status: respuesta.status ?? 200, json: async () => respuesta }
  }
}

const opciones = (extra) => ({ cliente, persona, base: 'http://api.local/', ...extra })

test('sin dirección de la API responde con plantillas y no llama a la red', async () => {
  const registro = []
  const r = await preguntarALucas('¿Llego a mi cobro?', { cliente, persona, base: '', fetchImpl: falsoFetch(RESPUESTA, registro) })
  assert.equal(r.origen, 'plantilla')
  assert.equal(r.aviso, null)
  assert.equal(registro.length, 0)
})

test('manda el contrato mínimo y conserva la conversación', async () => {
  const registro = []
  await preguntarALucas('¿Puedo gastar S/ 150?', opciones({ conversacion: 'conv-9', fetchImpl: falsoFetch(RESPUESTA, registro) }))
  assert.equal(registro[0].url, 'http://api.local/api/v1/chat')
  assert.deepEqual(registro[0].cuerpo, { customer_id: CLIENTE_ID, message: '¿Puedo gastar S/ 150?', conversation_id: 'conv-9' })
})

test('las cifras verificadas del agente se muestran con el formato de la app', async () => {
  const r = await preguntarALucas('¿Puedo gastar S/ 150?', opciones({ fetchImpl: falsoFetch(RESPUESTA) }))
  assert.equal(r.origen, 'agente')
  assert.equal(r.verificado, true)
  assert.equal(r.conversacion, 'conv-001')
  assert.deepEqual(r.cifras[1], { etiqueta: 'Saldo mínimo probable', valor: `−S/${NBSP}310` })
  assert.deepEqual(r.fuentes, [{ id: 'sbs-1', titulo: 'Guía de presupuesto', enlace: 'https://ejemplo.pe/guia' }])
})

test('si el agente no verificó, su texto no se muestra y responde la plantilla con aviso', async () => {
  const r = await preguntarALucas('¿Llego a mi cobro?', opciones({ fetchImpl: falsoFetch({ ...RESPUESTA, verified: false }) }))
  assert.equal(r.origen, 'plantilla')
  assert.equal(r.aviso, AVISOS.sinVerificar)
  assert.doesNotMatch(r.texto, /310/)
  assert.equal(r.conversacion, 'conv-001')
})

test('sin `unit`, una cifra en soles usa el mismo signo «−» de la app', () => {
  const r = desdeAgente({ ...RESPUESTA, figures: [{ label: 'Saldo mínimo probable', value: -310, text: '-S/ 310' }] })
  assert.equal(r.cifras[0].valor, `−S/${NBSP}310`)
})

test('una fuente con enlace que no es http(s) se muestra sin enlace', () => {
  const r = desdeAgente({ ...RESPUESTA, sources: [{ titulo: 'Malicioso', enlace: 'javascript:alert(1)' }] })
  assert.equal(r.fuentes[0].enlace, null)
})

test('error de red, HTTP 500 o respuesta sin texto caen a la plantilla con aviso claro', async () => {
  const casos = [
    [new TypeError('Failed to fetch'), AVISOS.sinConexion],
    [{ status: 500 }, AVISOS.sinConexion],
    [{ verified: true }, AVISOS.ilegible],
  ]
  for (const [respuesta, aviso] of casos) {
    const r = await preguntarALucas('¿Llego a mi cobro?', opciones({ fetchImpl: falsoFetch(respuesta) }))
    assert.equal(r.origen, 'plantilla')
    assert.equal(r.aviso, aviso)
    assert.match(r.texto, /cobro/)
  }
})

test('preguntas normales con «transacción» o «mueve» no se confunden con pedir operaciones', async () => {
  const registro = []
  for (const p of ['¿Cuántas transacciones hice?', '¿Qué mueve mi gasto?']) {
    await preguntarALucas(p, opciones({ fetchImpl: falsoFetch(RESPUESTA, registro) }))
  }
  assert.equal(registro.length, 2)
})

test('si el agente tarda demasiado, se corta y responde la plantilla', async () => {
  const lento = (_url, { signal }) =>
    new Promise((_, rechazar) => signal.addEventListener('abort', () => rechazar(Object.assign(new Error('abort'), { name: 'AbortError' }))))
  const r = await preguntarALucas('¿Llego a mi cobro?', opciones({ fetchImpl: lento, esperaMs: 20 }))
  assert.equal(r.aviso, AVISOS.demora)
})

test('pedir comprar dólares o mover plata no sale al servidor', async () => {
  const registro = []
  for (const p of ['¿compro dólares?', 'transfiere 100 a mi mamá']) {
    const r = await preguntarALucas(p, opciones({ fetchImpl: falsoFetch(RESPUESTA, registro) }))
    assert.match(r.texto, /no lo hago/)
  }
  assert.equal(registro.length, 0)
})
