import assert from 'node:assert/strict'
import { test } from 'node:test'
import { cliente } from '../src/mocks/cliente.js'
import { evaluarCambio, gastoDiarioSeguro, peorDia, simular } from '../src/mocks/motor.js'

// Las pantallas solo son creíbles si sus cifras no se contradicen: estas pruebas lo vigilan.

test('el aviso apunta al peor día antes del cobro', () => {
  const minimo = Math.min(...cliente.pronostico.filter((p) => p.fecha < cliente.proximoIngreso.fecha).map((p) => p.banda[0]))
  assert.equal(cliente.riesgo.peorMonto, minimo)
  assert.ok(cliente.riesgo.desde <= cliente.riesgo.peorFecha && cliente.riesgo.peorFecha <= cliente.riesgo.hasta)
})

test('el gasto diario seguro es menor al que la persona gasta hoy', () => {
  assert.ok(cliente.gastoDiarioSeguro < cliente.gastoDiarioActual)
})

test('las recomendaciones van de mayor a menor efecto y cada una mejora el peor caso', () => {
  const mejoras = cliente.recomendaciones.map((r) => r.mejora)
  assert.deepEqual(mejoras, [...mejoras].sort((a, b) => b - a))
  for (const r of cliente.recomendaciones) {
    assert.ok(r.mejora > 0, r.id)
    assert.equal(r.peorAntes, cliente.riesgo.peorMonto)
  }
})

test('con todos los cambios juntos ya no hay días en rojo', () => {
  assert.equal(cliente.conTodos.diasEnRojo, 0)
  assert.ok(cliente.conTodos.peorMonto >= 0)
})

test('el colchón del apartado cuadra con monto por cobros', () => {
  assert.equal(cliente.apartado.total, cliente.apartado.monto * cliente.apartado.cobros)
})

const personaMinima = {
  hoy: '2026-01-01',
  horizonteDias: 10,
  saldoHoy: 500,
  ingreso: { fecha: '2026-01-11', monto: 1000 },
  gastoBaseDiario: 20,
  banda: { inicial: 0, porDia: 0 },
  pagos: [{ id: 'luz', fecha: '2026-01-05', monto: 100 }],
  gastosFrecuentes: [],
}

test('sin banda, el gasto seguro es exactamente lo que alcanza hasta el cobro', () => {
  // 500 de saldo, 100 de pago y 9 días antes del cobro: 400 / 9 = 44.4
  assert.equal(gastoDiarioSeguro(personaMinima), 44)
  const puntos = simular(personaMinima, { gastoDiario: 44 })
  assert.ok(peorDia(personaMinima, puntos).banda[0] >= 0)
})

test('omitir un pago mejora el peor caso en ese mismo monto', () => {
  const r = evaluarCambio(personaMinima, { id: 'x', ajuste: { pagosOmitidos: ['luz'] } })
  assert.equal(r.mejora, 100)
})
