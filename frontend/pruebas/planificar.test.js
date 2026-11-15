import assert from 'node:assert/strict'
import { test } from 'node:test'
import { CAMBIOS, cliente, cuantoCabe, persona, vistaCon } from '../src/motor/cliente.js'
import { conPlanificados, simular } from '../src/motor/motor.js'
import { esPlanificadoValido, fechaValida, validarPlanificado, yaContado } from '../src/lucas/planificar.js'

// HU-08 y HU-09: lo planificado mueve la banda el día exacto y nada cambia hasta agregarlo.

const gasto = (monto, fecha, concepto = 'Regalo') => ({ id: 'p1', tipo: 'gasto', monto, fecha, concepto })
const ingreso = (monto, fecha) => ({ id: 'p2', tipo: 'ingreso', monto, fecha, concepto: 'Trabajo extra' })
const valido = (borrador) => validarPlanificado(cliente, { tipo: 'gasto', concepto: '', ...borrador })

test('un gasto de S/ 450 se descuenta el día exacto, no hoy', () => {
  const base = simular(persona)
  const con = simular(persona, conPlanificados({}, [gasto(450, '2026-12-05')]))
  const dia = (puntos, fecha) => puntos.find((p) => p.fecha === fecha).esperado
  assert.equal(dia(con, '2026-12-04'), dia(base, '2026-12-04'))
  assert.equal(dia(base, '2026-12-05') - dia(con, '2026-12-05'), 450)
  assert.equal(base.at(-1).esperado - con.at(-1).esperado, 450)
})

test('un gasto después del cobro que deja en rojo aparece en los 30 días, no en el tramo hasta el cobro', () => {
  const vista = vistaCon([], 'independiente', [], [gasto(450, '2026-12-05')])
  assert.deepEqual(vista.riesgo, cliente.riesgo)
  assert.ok(vista.mes.diasEnRojo > cliente.mes.diasEnRojo)
  assert.ok(vista.mes.peorMonto < cliente.mes.peorMonto)
})

test('sin nada planificado, los 30 días y el tramo hasta el cobro cuentan el mismo rojo', () => {
  assert.equal(cliente.mes.diasEnRojo, cliente.diasEnRojo)
  assert.equal(cliente.mes.peorMonto, cliente.riesgo.peorMonto)
})

test('un ingreso planificado antes del día más justo puede quitar el rojo', () => {
  const vista = vistaCon([], 'independiente', [], [ingreso(100, '2026-11-20')])
  assert.equal(vista.riesgo, null)
  assert.equal(vista.mes.diasEnRojo, 0)
  assert.equal(vista.peorDia.monto, cliente.riesgo.peorMonto + 100)
})

test('un gasto antes del cobro baja el gasto diario seguro y lo que se puede apartar', () => {
  const vista = vistaCon([], 'independiente', [], [gasto(200, '2026-11-20')])
  assert.ok(vista.gastoDiarioSeguro < cliente.gastoDiarioSeguro)
  assert.ok((vista.apartado?.monto ?? 0) <= (cliente.apartado?.monto ?? 0))
})

test('simular no guarda nada: la vista sin planificados no cambia', () => {
  const antes = JSON.stringify(vistaCon())
  vistaCon([], 'independiente', [], [gasto(900, '2026-11-20')])
  assert.equal(JSON.stringify(vistaCon()), antes)
})

test('rechaza monto 0, negativo, texto, vacío, más de dos decimales y sobre el tope', () => {
  for (const monto of ['0', '-5', 'abc', '', '12.345', '50001', '1,500']) {
    assert.ok(valido({ monto, fecha: '2026-11-20' }).errores?.monto, monto)
  }
})

test('rechaza fechas de hoy, pasadas, a más de 30 días o que no existen', () => {
  for (const fecha of ['2026-11-14', '2026-11-01', '2026-12-15', '2026-02-30', '', 'mañana']) {
    assert.ok(valido({ monto: '100', fecha }).errores?.fecha, fecha)
  }
})

test('acepta mañana y el último día del pronóstico, con decimales', () => {
  assert.deepEqual(valido({ monto: '45.5', fecha: '2026-11-15' }).movimiento, {
    tipo: 'gasto',
    monto: 45.5,
    fecha: '2026-11-15',
    concepto: 'Gasto planificado',
  })
  assert.ok(valido({ monto: '50000', fecha: '2026-12-14' }).movimiento)
})

test('avisa si el gasto ya es un pago conocido de monto parecido', () => {
  assert.equal(yaContado(persona.pagos, gasto(420, '2026-11-25', 'Alquiler')).id, 'alquiler')
  assert.equal(yaContado(persona.pagos, gasto(400, '2026-11-25', 'alquiler de cuarto')).id, 'alquiler')
  assert.equal(yaContado(persona.pagos, gasto(40, '2026-11-16', 'Streamflix')).id, 'streamflix')
  assert.equal(yaContado(persona.pagos, gasto(900, '2026-11-25', 'Alquiler')), null)
  assert.equal(yaContado(persona.pagos, gasto(420, '2026-11-25', 'Regalo')), null)
  assert.equal(yaContado(persona.pagos, { ...ingreso(420, '2026-11-25'), concepto: 'Alquiler' }), null)
})

test('fechaValida dice que no, sin lanzar error, ante fechas imposibles', () => {
  for (const f of ['2026-13-01', '2026-00-10', '2026-12-32', '2026-02-29', undefined, 20261205]) {
    assert.equal(fechaValida(f), false, String(f))
  }
  assert.equal(fechaValida('2028-02-29'), true)
})

test('cuánto cabe: el tope sugerido no suma rojo y S/ 10 más sí', () => {
  const todos = CAMBIOS.map((c) => c.id)
  const { ese } = cuantoCabe(vistaCon(todos), '2026-12-05')
  assert.equal(ese, 150)
  const rojo = (monto) => vistaCon(todos, 'independiente', [], [gasto(monto, '2026-12-05')]).mes.diasEnRojo
  assert.equal(rojo(ese), 0)
  assert.ok(rojo(ese + 10) > 0)
})

test('cuánto cabe: antes del cobro, con rojo de base, no cabe nada y propone después del cobro', () => {
  const r = cuantoCabe(cliente, '2026-11-20')
  assert.equal(r.ese, 0)
  assert.deepEqual(r.despues, { fecha: '2026-11-30', monto: cliente.apartado.monto })
})

test('descarta movimientos planificados guardados con forma rota', () => {
  assert.ok(esPlanificadoValido(gasto(450, '2026-12-05')))
  for (const roto of [null, { ...gasto(450, '2026-12-05'), monto: '450' }, { ...gasto(450, '2026-12-05'), tipo: 'otro' }, { ...gasto(450, 'x') }, { ...gasto(-5, '2026-12-05') }]) {
    assert.equal(esPlanificadoValido(roto), false)
  }
})
