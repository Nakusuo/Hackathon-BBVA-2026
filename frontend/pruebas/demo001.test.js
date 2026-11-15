import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { generarDemo } from '../scripts/exportar-persona-demo.mjs'
import { leerEventos, leerPronostico, leerRecomendaciones, leerSalud } from '../src/api/contrato.js'
import { vistaCon } from '../src/motor/cliente.js'

const guardado = (nombre) => JSON.parse(readFileSync(new URL(`../../data/sample/demo-001/${nombre}`, import.meta.url)))
const generado = generarDemo()

for (const nombre of Object.keys(generado)) {
  test(`${nombre} de demo-001 sigue al motor: si cambió, corre node scripts/exportar-persona-demo.mjs`, () => {
    assert.deepEqual(guardado(nombre), generado[nombre])
  })
}

test('lo que dice la API de demo-001 es lo que muestra la pantalla', () => {
  const vista = vistaCon([])
  assert.equal(leerSalud(guardado('health.json')).puntaje, vista.salud.puntaje)

  const { puntos } = leerPronostico(guardado('forecast.json'))
  assert.equal(puntos.length, 30)
  assert.equal(guardado('forecast.json').first_risk_date, vista.riesgo.desde)
  const peor = puntos.filter((p) => p.fecha < vista.proximoIngreso.fecha).reduce((a, b) => (b.banda[0] < a.banda[0] ? b : a))
  assert.equal(peor.banda[0], vista.peorDia.monto)
  assert.equal(puntos.filter((p) => p.fecha < vista.proximoIngreso.fecha && p.banda[0] < 0).length, vista.diasEnRojo)

  const tips = leerRecomendaciones(guardado('recommendations.json'))
  assert.deepEqual(
    tips.map((t) => [t.id, t.impacto]),
    vista.recomendaciones.map((r) => [r.id, r.mejora]),
  )
  assert.equal(leerEventos(guardado('events.json')).avisosRestantesSemana >= 0, true)
})
