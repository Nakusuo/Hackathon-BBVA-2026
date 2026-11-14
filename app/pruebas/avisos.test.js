import assert from 'node:assert/strict'
import { test } from 'node:test'
import { armarBandeja, candidatos, inicioDeSemana, MAXIMO_POR_SEMANA, urgenciaDeRiesgo } from '../src/lucas/avisos.js'
import { cliente, vistaCon } from '../src/motor/cliente.js'

const HOY = '2026-11-14'

function aviso(id, tipo, impacto, dias = 3) {
  return { id, tipo, impacto, dias, urgencia: 'normal' }
}

test('CP-SIS-28: riesgo a 0, 1 y 2 días es urgente; a 3 y 7 normal; a 8 no hay aviso', () => {
  assert.deepEqual(
    [0, 1, 2, 3, 7, 8].map(urgenciaDeRiesgo),
    ['urgente', 'urgente', 'urgente', 'normal', 'normal', null],
  )
})

test('CP-SIS-28: sin riesgo en el pronóstico no hay aviso de riesgo', () => {
  const sinRiesgo = vistaCon(['musika', 'delivery', 'cafe'])
  assert.equal(sinRiesgo.riesgo, null)
  const { avisos, riesgoLejano } = candidatos(sinRiesgo, HOY)
  assert.ok(avisos.every((a) => a.tipo !== 'riesgo'))
  assert.equal(riesgoLejano, null)
})

test('la persona de la demo tiene su riesgo a 14 días: hoy no se avisa y se dice cuándo es', () => {
  const { avisos, riesgoLejano } = candidatos(cliente, HOY)
  assert.ok(avisos.every((a) => a.tipo !== 'riesgo'))
  assert.deepEqual(riesgoLejano, { fecha: cliente.riesgo.desde, dias: 14 })
})

test('el mismo pronóstico visto el 21 da aviso normal y el 26, urgente', () => {
  const del21 = candidatos(cliente, '2026-11-21').avisos.find((a) => a.tipo === 'riesgo')
  const del26 = candidatos(cliente, '2026-11-26').avisos.find((a) => a.tipo === 'riesgo')
  assert.equal(del21.urgencia, 'normal')
  assert.equal(del26.urgencia, 'urgente')
  assert.equal(del21.id, del26.id)
  assert.equal(del21.impacto, cliente.riesgo.peorMonto)
})

test('los pagos solo avisan dentro de los 7 días y el de una suscripción sin uso lleva al tip', () => {
  const { avisos } = candidatos(cliente, HOY)
  const pagos = avisos.filter((a) => a.tipo === 'pago')
  assert.ok(pagos.length > 0 && pagos.every((a) => a.dias >= 0 && a.dias <= 7))
  const musika = pagos.find((a) => a.id.startsWith('pago-musika'))
  assert.equal(musika.tip.id, 'musika')
  assert.equal(musika.accion.ruta, '/lucas/resumen#tips')
})

test('CP-SIS-05: con 4 eventos en la semana se ven 3, el de riesgo y los 2 de mayor impacto en S/', () => {
  const lista = [aviso('pago-a', 'pago', -40), aviso('riesgo-2026-11-30', 'riesgo', -60), aviso('pago-b', 'pago', -210), aviso('ingreso-c', 'ingreso', 2000)]
  const { avisos, restantes, fueraDelTope } = armarBandeja(lista, {}, HOY)
  assert.deepEqual(avisos.map((a) => a.id).sort(), ['ingreso-c', 'pago-b', 'riesgo-2026-11-30'])
  assert.equal(avisos[0].tipo, 'riesgo')
  assert.equal(restantes, 0)
  assert.equal(fueraDelTope, 1)
})

test('sin riesgo, los otros avisos dejan libre el lugar reservado', () => {
  const lista = [aviso('pago-a', 'pago', -40), aviso('pago-b', 'pago', -210), aviso('pago-c', 'pago', -90)]
  const { avisos, restantes } = armarBandeja(lista, {}, HOY)
  assert.equal(avisos.length, MAXIMO_POR_SEMANA - 1)
  assert.equal(restantes, 1)
})

test('CP-SIS-29: un gasto que mueve el día de riesgo actualiza el mismo aviso y el contador no sube', () => {
  const del21 = candidatos(cliente, '2026-11-21').avisos
  const primera = armarBandeja(del21, {}, '2026-11-21')
  const conGasto = vistaCon([], undefined, [{ id: 'prueba', fecha: '2026-11-22', monto: 300 }])
  const segunda = armarBandeja(candidatos(conGasto, '2026-11-21').avisos, primera.registro, '2026-11-21')

  const riesgos = segunda.avisos.filter((a) => a.tipo === 'riesgo')
  assert.equal(riesgos.length, 1)
  assert.equal(riesgos[0].id, primera.avisos.find((a) => a.tipo === 'riesgo').id)
  assert.ok(riesgos[0].impacto < primera.avisos.find((a) => a.tipo === 'riesgo').impacto)
  assert.equal(segunda.restantes, primera.restantes)
})

test('un aviso ya mostrado esta semana se queda aunque llegue otro de más impacto', () => {
  const registro = { [inicioDeSemana(HOY)]: ['pago-a', 'pago-b'] }
  const lista = [aviso('pago-a', 'pago', -40), aviso('pago-b', 'pago', -50), aviso('pago-grande', 'pago', -900)]
  const { avisos } = armarBandeja(lista, registro, HOY)
  assert.deepEqual(avisos.map((a) => a.id).sort(), ['pago-a', 'pago-b'])
})

test('la semana va de lunes a domingo: el domingo 15 y el lunes 16 están en semanas distintas', () => {
  assert.equal(inicioDeSemana('2026-11-14'), '2026-11-09')
  assert.equal(inicioDeSemana('2026-11-15'), '2026-11-09')
  assert.equal(inicioDeSemana('2026-11-16'), '2026-11-16')
  const lleno = { '2026-11-09': ['pago-a', 'pago-b', 'riesgo-x'] }
  assert.equal(armarBandeja([aviso('pago-c', 'pago', -10)], lleno, '2026-11-15').avisos.length, 0)
  assert.equal(armarBandeja([aviso('pago-c', 'pago', -10)], lleno, '2026-11-16').avisos.length, 1)
})
