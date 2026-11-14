import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { leerPronostico, leerSalud, leerTipoCambio, pedidoSimulacion } from '../src/api/contrato.js'
import { ErrorApi, pedirJson } from '../src/api/http.js'
import { cargarCliente, origenGeneral, simularCambios } from '../src/api/lucas.js'

const mock = (nombre) => JSON.parse(readFileSync(new URL(`../../data/sample/mocks/${nombre}.json`, import.meta.url)))

const RESPUESTAS_API = {
  '/api/v1/customers/demo-001/health': mock('health'),
  '/api/v1/customers/demo-001/forecast': mock('forecast'),
  '/api/v1/customers/demo-001/recommendations': mock('recommendations'),
  '/api/v1/customers/demo-001/events': mock('events'),
  '/api/v1/fx?base=USD&quote=PEN': { ...mock('fx'), rate: '3.75' },
  '/api/v1/simulations': mock('simulation'),
}

const responde = (cuerpo, estado = 200) => ({ ok: estado < 400, status: estado, json: async () => cuerpo })
const apiSana = async (ruta) => responde(RESPUESTAS_API[ruta])
const apiCaida = async () => {
  throw new TypeError('fetch failed')
}

test('con la API arriba todo viene de la API y en los nombres del front', async () => {
  const fuentes = await cargarCliente('demo-001', { pedir: apiSana })
  assert.equal(origenGeneral(fuentes), 'api')
  assert.equal(fuentes.salud.datos.puntaje, 72)
  assert.deepEqual(fuentes.pronostico.datos.puntos[0], { fecha: '2026-11-15', esperado: 850, banda: [720, 980] })
  assert.equal(fuentes.recomendaciones.datos.length, 3)
  assert.equal(fuentes.eventos.datos.avisosRestantesSemana, 2)
})

test('si la API no responde, cada lectura usa el JSON de ejemplo y dice por qué', async () => {
  const fuentes = await cargarCliente('demo-001', { pedir: apiCaida })
  assert.equal(origenGeneral(fuentes), 'respaldo')
  for (const fuente of Object.values(fuentes)) {
    assert.equal(fuente.origen, 'respaldo')
    assert.equal(fuente.motivo, 'red')
  }
  assert.equal(fuentes.salud.datos.puntaje, mock('health').score)
})

test('una lectura con respuesta rota pasa sola al respaldo y las demás siguen de la API', async () => {
  const pedir = async (ruta) => (ruta.endsWith('/health') ? responde({ score: 'alto' }) : apiSana(ruta))
  const fuentes = await cargarCliente('demo-001', { pedir })
  assert.equal(origenGeneral(fuentes), 'parcial')
  assert.equal(fuentes.salud.origen, 'respaldo')
  assert.equal(fuentes.salud.motivo, 'formato')
  assert.equal(fuentes.pronostico.origen, 'api')
})

test('un 404 o un 500 pasan al respaldo como error http', async () => {
  const fuentes = await cargarCliente('demo-001', { pedir: async () => responde({ detail: 'x' }, 500) })
  assert.equal(fuentes.eventos.motivo, 'http')
})

test('si la API tarda más que la espera, se corta y pasa al respaldo', async () => {
  const lenta = (_ruta, { signal }) =>
    new Promise((_, rechazar) => signal.addEventListener('abort', () => rechazar(new Error('abortado'))))
  await assert.rejects(pedirJson('/api/v1/fx', { pedir: lenta, esperaMs: 20 }), (e) => e.tipo === 'tiempo')
  const fuentes = await cargarCliente('demo-001', { pedir: lenta, esperaMs: 20 })
  assert.equal(fuentes.tipoCambio.motivo, 'tiempo')
})

test('una lista con elementos vacíos no rompe la lectura: pasa al respaldo', async () => {
  const pedir = async (ruta) =>
    ruta.endsWith('/recommendations') ? responde({ ...mock('recommendations'), recommendations: [null] }) : apiSana(ruta)
  const fuentes = await cargarCliente('demo-001', { pedir })
  assert.equal(fuentes.recomendaciones.origen, 'respaldo')
  assert.equal(fuentes.recomendaciones.motivo, 'formato')
})

test('el tipo de cambio sale como número aunque la API lo mande como texto', () => {
  assert.equal(leerTipoCambio({ ...mock('fx'), rate: '3.75' }).tasa, 3.75)
  assert.equal(leerTipoCambio(mock('fx')).tasa, 3.75)
  assert.throws(() => leerTipoCambio({ ...mock('fx'), rate: 'tres' }), ErrorApi)
})

test('el contrato rechaza salud fuera de 0 a 100 y pronósticos vacíos o con montos que no son número', () => {
  assert.throws(() => leerSalud({ ...mock('health'), score: 140 }), ErrorApi)
  assert.throws(() => leerPronostico({ ...mock('forecast'), forecast: [] }), ErrorApi)
  const roto = { ...mock('forecast'), forecast: [{ date: '2026-11-15', predicted_balance: null, lower_bound: 0, upper_bound: 1 }] }
  assert.throws(() => leerPronostico(roto), ErrorApi)
})

test('la simulación manda el pedido en el formato del contrato y lee la diferencia', async () => {
  let enviado
  const pedir = async (ruta, opciones) => {
    enviado = { ruta, metodo: opciones.method, cuerpo: JSON.parse(opciones.body) }
    return apiSana(ruta)
  }
  const cambios = [{ tipo: 'expense', monto: 200, frecuencia: 'once', descripcion: 'Reducir gastos durante el horizonte simulado' }]
  const resultado = await simularCambios(cambios, { pedir })
  assert.deepEqual(enviado, {
    ruta: '/api/v1/simulations',
    metodo: 'POST',
    cuerpo: pedidoSimulacion('demo-001', cambios),
  })
  assert.deepEqual(enviado.cuerpo, mock('simulation-request'))
  assert.equal(resultado.origen, 'api')
  assert.equal(resultado.datos.diferencia, 200)
  assert.equal(resultado.datos.base.diasEnRojo, 3)
})
