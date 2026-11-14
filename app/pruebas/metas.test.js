import assert from 'node:assert/strict'
import { test } from 'node:test'
import { CAMBIOS, cliente, persona, vistaCon } from '../src/motor/cliente.js'
import { ajusteDe, apartadoSinRojo } from '../src/motor/motor.js'
import {
  aportar,
  crearMeta,
  esMetaValida,
  estadoDe,
  fechasDeApartado,
  planDeMeta,
  repartoDelApartado,
  validarMeta,
} from '../src/lucas/metas.js'

// HU-16: el aporte sale del apartado del motor, así que nunca crea días en rojo.

const contexto = (apartado) => ({
  apartado,
  primerApartado: cliente.proximoIngreso.fecha,
  finPronostico: cliente.finPronostico,
  hoy: cliente.hoy,
})
const fin = crearMeta({ nombre: 'Colchón para enero', objetivo: 300, ahorrado: 0, fecha: '2026-12-31' }, 'm1')

test('se aparta cada mes el día del cobro; en febrero, el último día', () => {
  assert.deepEqual(fechasDeApartado('2026-11-30', '2027-03-31'), [
    '2026-11-30',
    '2026-12-30',
    '2027-01-30',
    '2027-02-28',
    '2027-03-30',
  ])
  assert.deepEqual(fechasDeApartado('2026-11-30', '2026-11-29'), [])
})

test('con los 3 tips el motor deja apartar S/ 150, y con eso la meta de fin de año alcanza', () => {
  const conTips = vistaCon(CAMBIOS.map((c) => c.id))
  assert.equal(conTips.apartado.monto, 150)
  const plan = planDeMeta(fin, contexto(conTips.apartado.monto))
  assert.equal(plan.veces, 2)
  assert.equal(plan.aporte, 150)
  assert.equal(plan.alcanza, true)
  assert.equal(plan.proyectado, 300)
  assert.equal(plan.alFinDeAnio, 300)
})

test('sin tips (S/ 40) dice cuánto junta a la fecha y cuándo llegaría', () => {
  assert.equal(cliente.apartado.monto, 40)
  const plan = planDeMeta(fin, contexto(40))
  assert.equal(plan.alcanza, false)
  assert.equal(plan.aporte, 40)
  assert.equal(plan.proyectado, 80)
  assert.equal(plan.llegaEl, '2027-06-30')
})

test('el aporte propuesto no crea días en rojo en el pronóstico', () => {
  for (const elegidos of [[], CAMBIOS.map((c) => c.id)]) {
    const vista = vistaCon(elegidos)
    const plan = planDeMeta(fin, contexto(vista.apartado.monto))
    const ajuste = ajusteDe(CAMBIOS.filter((c) => elegidos.includes(c.id)))
    assert.ok(apartadoSinRojo(persona, plan.aporte, ajuste), `con ${elegidos.length} tips`)
  }
})

test('nunca propone más de lo necesario ni más de lo que se puede apartar', () => {
  const chica = crearMeta({ nombre: 'Regalo', objetivo: 100, ahorrado: 30, fecha: '2026-12-31' }, 'm2')
  assert.equal(planDeMeta(chica, contexto(150)).aporte, 40)
  const grande = crearMeta({ nombre: 'Laptop', objetivo: 2500, ahorrado: 0, fecha: '2026-12-31' }, 'm3')
  assert.equal(planDeMeta(grande, contexto(150)).aporte, 150)
})

test('con varias metas abiertas el apartado se reparte y la suma no se pasa', () => {
  const otra = crearMeta({ nombre: 'Laptop', objetivo: 2500, ahorrado: 0, fecha: '2027-04-30' }, 'm4')
  const cumplida = aportar(crearMeta({ nombre: 'Ya está', objetivo: 50, ahorrado: 0, fecha: '2026-12-31' }, 'm5'), 50)
  assert.deepEqual(repartoDelApartado(150, [fin, otra]).porMeta, { m1: 70, m4: 70 })
  assert.deepEqual(repartoDelApartado(150, [fin, otra, cumplida]).porMeta, { m1: 70, m4: 70 })
  assert.equal(repartoDelApartado(150, []).conAporte, 0)
})

test('si el apartado no alcanza para S/ 10 a cada meta, reciben las primeras y ninguna queda en S/ 0 por redondeo', () => {
  const metas = ['a', 'b', 'c', 'd', 'e'].map((id) => crearMeta({ nombre: id, objetivo: 300, ahorrado: 0, fecha: '2026-12-31' }, id))
  const reparto = repartoDelApartado(40, metas)
  assert.equal(reparto.conAporte, 4)
  assert.deepEqual(reparto.porMeta, { a: 10, b: 10, c: 10, d: 10, e: 0 })
  const total = Object.values(reparto.porMeta).reduce((s, v) => s + v, 0)
  assert.ok(total <= 40)
})

test('sin cobros antes de la fecha no promete llegar ni propone aporte', () => {
  const chica = crearMeta({ nombre: 'Chica', objetivo: 100, ahorrado: 0, fecha: '2026-12-31' }, 'm8')
  const tras = aportar(aportar(chica, 40), 40)
  const plan = planDeMeta(tras, contexto(40))
  assert.equal(plan.veces, 0)
  assert.equal(plan.sinCobros, true)
  assert.equal(plan.alcanza, false)
  assert.equal(plan.aporte, 0)
  assert.notEqual(plan.confianza, 'alta')
  assert.equal(plan.llegaEl, '2027-01-30')
})

test('el aporte nunca pasa de lo que falta: texto y botón dicen el mismo monto', () => {
  const casi = crearMeta({ nombre: 'Casi', objetivo: 100, ahorrado: 95, fecha: '2026-12-10' }, 'm9')
  const plan = planDeMeta(casi, contexto(150))
  assert.equal(plan.aporte, 5)
  assert.equal(plan.alcanza, true)
})

test('si alcanza, la fecha de llegada sale del aporte que se muestra y no del máximo', () => {
  const cien = crearMeta({ nombre: 'Cien', objetivo: 100, ahorrado: 0, fecha: '2026-12-31' }, 'm12')
  const plan = planDeMeta(cien, contexto(150))
  assert.equal(plan.aporte, 50)
  assert.equal(plan.alcanza, true)
  assert.equal(plan.llegaEl, '2026-12-30')
})

test('el avance redondea hacia abajo: 996 de 1 000 no se muestra como 100 %', () => {
  const meta = crearMeta({ nombre: 'Casi', objetivo: 1000, ahorrado: 996, fecha: '2026-12-31' }, 'm10')
  assert.equal(planDeMeta(meta, contexto(40)).avance, 99)
})

test('cada aporte registrado cubre un cobro: el plan sigue con los que faltan', () => {
  const tras = aportar(fin, 150)
  const plan = planDeMeta(tras, contexto(150))
  assert.equal(plan.veces, 1)
  assert.equal(plan.aporte, 150)
  assert.equal(plan.alcanza, true)
  const lenta = planDeMeta(aportar(fin, 40), contexto(40))
  assert.equal(lenta.proyectado, 80)
  assert.equal(lenta.llegaEl, '2027-06-30')
})

test('la confianza es alta solo si todo apartado cae dentro del pronóstico de 30 días', () => {
  const corta = crearMeta({ nombre: 'Corta', objetivo: 100, ahorrado: 0, fecha: '2026-12-10' }, 'm6')
  assert.equal(planDeMeta(corta, contexto(150)).confianza, 'alta')
  assert.equal(planDeMeta(fin, contexto(150)).confianza, 'media')
})

test('la confianza es baja si la meta o la llegada pasan de unos 3 meses', () => {
  assert.equal(planDeMeta(fin, contexto(40)).confianza, 'baja')
  const lejana = crearMeta({ nombre: 'Laptop', objetivo: 2500, ahorrado: 0, fecha: '2027-06-30' }, 'm11')
  assert.equal(planDeMeta(lejana, contexto(150)).confianza, 'baja')
})

test('descarta metas guardadas con forma rota', () => {
  assert.ok(esMetaValida(fin))
  assert.ok(esMetaValida(aportar(fin, 150)))
  for (const rota of [null, 'x', { ...fin, historial: undefined }, { ...fin, objetivo: '300' }, { ...fin, fecha: '2026-13-01' }, { ...fin, historial: ['otro'] }]) {
    assert.equal(esMetaValida(rota), false)
  }
})

test('una meta pasa de creada a en curso a cumplida, sin saltarse estados', () => {
  assert.deepEqual(fin.historial, ['creada'])
  const enCurso = aportar(fin, 150)
  assert.equal(estadoDe(enCurso), 'en curso')
  assert.deepEqual(aportar(enCurso, 150).historial, ['creada', 'en curso', 'cumplida'])
  assert.deepEqual(aportar(fin, 300).historial, ['creada', 'en curso', 'cumplida'])
  const conAhorro = crearMeta({ nombre: 'Con ahorro', objetivo: 300, ahorrado: 100, fecha: '2026-12-31' }, 'm7')
  assert.deepEqual(conAhorro.historial, ['creada', 'en curso'])
})

test('valida nombre, montos y fecha con mensajes claros', () => {
  const opciones = { hoy: cliente.hoy, primerApartado: cliente.proximoIngreso.fecha }
  const malos = validarMeta({ nombre: ' ', objetivo: '0', ahorrado: 'x', fecha: '2026-11-20' }, opciones).errores
  assert.ok(malos.nombre && malos.objetivo && malos.ahorrado && malos.fecha)
  const mayor = validarMeta({ nombre: 'A', objetivo: '300', ahorrado: '300', fecha: '2026-12-31' }, opciones).errores
  assert.match(mayor.ahorrado, /menor que la meta/)
  assert.ok(validarMeta({ nombre: 'A', objetivo: '300', ahorrado: '', fecha: '2032-01-01' }, opciones).errores.fecha)
  assert.deepEqual(validarMeta({ nombre: ' Colchón ', objetivo: '300', ahorrado: '', fecha: '2026-12-31' }, opciones).datos, {
    nombre: 'Colchón',
    objetivo: 300,
    ahorrado: 0,
    fecha: '2026-12-31',
  })
})
