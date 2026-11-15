import assert from 'node:assert/strict'
import { test } from 'node:test'
import { vistaCon } from '../src/motor/cliente.js'
import { PERSONAS, personaPorId } from '../src/motor/personas.js'
import { anchoBanda, peorDia, simular } from '../src/motor/motor.js'

// El selector de persona solo es honesto si todas pasan por el mismo motor y cumplen las mismas reglas.

for (const { id, cambios } of PERSONAS) {
  const todos = cambios.map((c) => c.id)

  test(`${id}: el aviso apunta al peor día antes del cobro y el gasto seguro es menor al actual`, () => {
    const v = vistaCon([], id)
    const antes = v.pronostico.filter((p) => p.fecha < v.proximoIngreso.fecha)
    assert.equal(v.riesgo.peorMonto, Math.min(...antes.map((p) => p.banda[0])))
    assert.ok(v.gastoDiarioSeguro < v.gastoDiarioActual)
  })

  test(`${id}: cada tip mejora el peor caso, van de mayor a menor y con todos no queda rojo`, () => {
    const v = vistaCon([], id)
    const mejoras = v.recomendaciones.map((r) => r.mejora)
    assert.deepEqual(mejoras, [...mejoras].sort((a, b) => b - a))
    let anterior = v.peorDia.monto
    for (let i = 1; i <= todos.length; i++) {
      const actual = vistaCon(todos.slice(0, i), id).peorDia.monto
      assert.ok(actual > anterior, `con ${i} tips`)
      anterior = actual
    }
    assert.equal(vistaCon(todos, id).riesgo, null)
  })

  test(`${id}: los tips que solo tiene otra persona no cambian nada`, () => {
    const propios = new Set(todos)
    const ajenos = PERSONAS.flatMap((p) => p.cambios.map((c) => c.id)).filter((x) => !propios.has(x))
    assert.ok(ajenos.length > 0)
    assert.deepEqual(vistaCon(ajenos, id).pronostico, vistaCon([], id).pronostico)
  })

  test(`${id}: las cifras de la vista salen del motor con los datos de esa persona`, () => {
    const p = personaPorId(id).persona
    const v = vistaCon([], id)
    assert.deepEqual(v.pronostico, simular(p))
    assert.equal(v.saldoHoy, p.saldoHoy)
    assert.equal(v.peorDia.monto, peorDia(p, simular(p)).banda[0])
  })
}

test('el mismo día, la banda del independiente es más ancha que la del formal (HU-03)', () => {
  const independiente = personaPorId('independiente').persona
  const formal = personaPorId('formal').persona
  const fechas = simular(formal).map((p) => p.fecha)
  for (let dia = 1; dia < fechas.length; dia++) {
    assert.ok(anchoBanda(independiente, dia, fechas[dia]) > anchoBanda(formal, dia, fechas[dia]), `día ${dia}`)
  }
})

test('cambiar de persona cambia las cifras de la banca y de Lucas', () => {
  const a = vistaCon([], 'independiente')
  const b = vistaCon([], 'formal')
  assert.notEqual(a.saldoHoy, b.saldoHoy)
  assert.notEqual(a.gastoDiarioSeguro, b.gastoDiarioSeguro)
  assert.notEqual(a.proximoIngreso.monto, b.proximoIngreso.monto)
  assert.equal(a.ingresoVariable, true)
  assert.equal(b.ingresoVariable, false)
})

test('una persona desconocida cae en la de la demo y no rompe', () => {
  assert.equal(vistaCon([], 'no-existe').personaId, 'independiente')
})

test('el peso de las cuotas se mide contra el ingreso del mes, no solo contra los cobros del horizonte', () => {
  const deudas = (id) => vistaCon([], id).salud.componentes.find((c) => c.nombre === 'Deudas')
  // Formal: S/ 180 de cuota frente a 2 quincenas de S/ 1,300 = 7 %; el horizonte solo ve una quincena.
  assert.match(deudas('formal').explicacion, /el 7 %/)
  assert.equal(deudas('formal').valor, 86)
  assert.match(deudas('independiente').explicacion, /el 8 %/)
})
