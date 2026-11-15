import assert from 'node:assert/strict'
import { test } from 'node:test'
import { CAMBIOS, cliente, persona, vistaCon } from '../src/motor/cliente.js'
import {
  ajusteDe,
  anchoBanda,
  apartadoMaximo,
  apartadoSinRojo,
  evaluarCambio,
  evaluarGastoExtra,
  gastoDiarioSeguro,
  peorDia,
  simular,
  vecesDesde,
  vecesHastaCobro,
} from '../src/motor/motor.js'

// Las pantallas solo son creíbles si sus cifras no se contradicen: estas pruebas lo vigilan.

const TODOS = CAMBIOS.map((c) => c.id)

test('el aviso apunta al peor día antes del primer cobro', () => {
  const antesDelCobro = cliente.pronostico.filter((p) => p.fecha < cliente.proximoIngreso.fecha)
  assert.equal(cliente.riesgo.peorMonto, Math.min(...antesDelCobro.map((p) => p.banda[0])))
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

test('cada tip que se activa con «Lo hago» mejora el peor caso, y con todos ya no hay rojo', () => {
  let anterior = vistaCon([]).peorDia.monto
  for (let i = 1; i <= TODOS.length; i++) {
    const actual = vistaCon(TODOS.slice(0, i)).peorDia.monto
    assert.ok(actual > anterior, `con ${i} tips`)
    anterior = actual
  }
  const conTodos = vistaCon(TODOS)
  assert.equal(conTodos.riesgo, null)
  assert.equal(conTodos.peorDia.monto, cliente.conTodos.peorMonto)
})

test('activar tips nunca reduce lo que se puede apartar', () => {
  const sinTips = vistaCon([]).apartado?.monto ?? 0
  const conTips = vistaCon(TODOS).apartado?.monto ?? 0
  assert.ok(conTips >= sinTips)
  assert.equal(cliente.apartadoConTodos.monto, conTips)
})

test('el apartado propuesto no deja en rojo y S/ 10 más ya sí', () => {
  const { apartado } = cliente
  assert.ok(apartadoSinRojo(persona, apartado.monto))
  assert.ok(!apartadoSinRojo(persona, apartado.monto + 10))
  assert.equal(apartado.total, apartado.monto * apartado.repeticiones)
})

test('un ingreso desconocido ensancha la banda el día del cobro', () => {
  const [cobro] = persona.ingresos
  const diaAntes = cliente.pronostico.findIndex((p) => p.fecha === cobro.fecha) - 1
  const antes = anchoBanda(persona, diaAntes, cliente.pronostico[diaAntes].fecha)
  const enElCobro = anchoBanda(persona, diaAntes + 1, cobro.fecha)
  assert.equal(Math.round(enElCobro - antes - persona.banda.porDia), cobro.variacion)
})

test('un gasto extra empeora el peor caso en ese mismo monto', () => {
  const r = evaluarGastoExtra(persona, 150)
  assert.equal(r.peorDespues, r.peorAntes - 150)
  const conTips = evaluarGastoExtra(persona, 150, ajusteDe(CAMBIOS))
  assert.ok(conTips.peorDespues > r.peorDespues)
})

const personaMinima = {
  hoy: '2026-01-01',
  horizonteDias: 10,
  saldoHoy: 500,
  ingresos: [{ id: 'cobro', fecha: '2026-01-11', monto: 1000, variacion: 0 }],
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

test('sin margen después del cobro no se propone apartar nada', () => {
  // 300 − 10 días × 20 − 100 de luz = 0 el día del cobro, y el cobro es de 0.
  const sinMargen = { ...personaMinima, saldoHoy: 300, ingresos: [{ id: 'cobro', fecha: '2026-01-11', monto: 0, variacion: 0 }] }
  assert.equal(apartadoMaximo(sinMargen), 0)
})

test('el seguimiento de cada tip sale del mismo plan que el tip', () => {
  for (const r of cliente.recomendaciones) {
    const cambio = CAMBIOS.find((c) => c.id === r.id)
    const s = r.seguimiento
    if (s.tipo === 'pausa') {
      assert.equal(persona.pagos.find((p) => p.id === cambio.ajuste.pagosOmitidos[0]).fecha, s.fecha)
      continue
    }
    assert.equal(s.hasta, cliente.proximoIngreso.fecha)
    assert.equal(s.usadas, 0, 'la persona de la demo aún no compra hoy')
    assert.ok(s.limite > 0 && s.limite <= Object.values(cambio.ajuste.frecuencias)[0], r.id)
  }
  // RapiFood 4 veces al mes son 2 en los 16 días que faltan para el cobro.
  assert.equal(cliente.recomendaciones.find((r) => r.id === 'delivery').seguimiento.limite, 2)
})

test('la salud sube con cada día en rojo que se evita y es el promedio de sus partes', () => {
  const sinTips = vistaCon([]).salud
  const conUno = vistaCon(['delivery']).salud
  const conTodos = vistaCon(TODOS).salud
  assert.ok(sinTips.puntaje < conUno.puntaje && conUno.puntaje < conTodos.puntaje)
  assert.equal(cliente.conTodos.salud, conTodos.puntaje)
  for (const s of [sinTips, conUno, conTodos]) {
    const promedio = s.componentes.reduce((t, c) => t + c.valor, 0) / s.componentes.length
    assert.equal(s.puntaje, Math.round(promedio))
  }
  assert.match(sinTips.componentes.at(-1).explicacion, /2 días en rojo/)
  assert.match(conTodos.componentes.at(-1).explicacion, /sin quedar en rojo/)
})

test('«evitas N días en rojo» de un tip por elegir se cumple al elegirlo, con cualquier selección previa', () => {
  const selecciones = [
    [],
    ['delivery'],
    ['musika'],
    ['cafe'],
    ['delivery', 'musika'],
    ['delivery', 'cafe'],
    ['musika', 'cafe'],
  ]
  for (const elegidos of selecciones) {
    const vista = vistaCon(elegidos)
    for (const r of vista.recomendaciones.filter((t) => !elegidos.includes(t.id))) {
      assert.equal(r.diasEvitados, vista.diasEnRojo - vistaCon([...elegidos, r.id]).diasEnRojo, `${elegidos} + ${r.id}`)
    }
  }
  // El caso que vio el juez: con RapiFood y MusiKa queda 1 día, y el café es el que lo quita.
  const dos = vistaCon(['delivery', 'musika'])
  assert.equal(dos.diasEnRojo, 1)
  assert.equal(dos.recomendaciones.find((r) => r.id === 'cafe').diasEvitados, 1)
})

test('las tarjetas de tips no cambian de orden al elegir', () => {
  const orden = cliente.recomendaciones.map((r) => r.id)
  for (const elegidos of [['cafe'], TODOS])
    assert.deepEqual(
      vistaCon(elegidos).recomendaciones.map((r) => r.id),
      orden,
    )
})

test('el seguimiento cuenta las compras desde hoy y nunca pide «0 de 0»', () => {
  const movimientos = [
    { concepto: 'RapiFood', fecha: '2026-11-13' },
    { concepto: 'RapiFood', fecha: '2026-11-14' },
    { concepto: 'Cafetería La Esquina', fecha: '2026-11-14' },
    { concepto: 'RapiFood', fecha: '2026-11-15' },
  ]
  assert.equal(vecesDesde(movimientos, 'RapiFood', '2026-11-14'), 2)
  assert.equal(vecesDesde(movimientos, 'RapiFood', '2026-11-16'), 0)
  const cobroManana = { ...persona, ingresos: [{ ...persona.ingresos[0], fecha: '2026-11-15' }] }
  assert.equal(vecesHastaCobro(cobroManana, 4), 1)
})
