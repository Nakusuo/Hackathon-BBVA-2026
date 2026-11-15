import assert from 'node:assert/strict'
import { test } from 'node:test'
import { diasEntre, enSoles } from '../src/formato.js'
import { explicarQueViene, explicarResumen } from '../src/lucas/explicaciones.js'
import { vistaCon } from '../src/motor/cliente.js'
import { PERSONAS } from '../src/motor/personas.js'

// HU-23: «explícamelo fácil» no trae cifras nuevas. Cada número del texto tiene que estar ya en la pantalla.

function numeros(texto) {
  return [...texto.matchAll(/\d[\d,.]*\d|\d/g)].map((m) => Number(m[0].replace(/,/g, '')))
}

const dia = (fecha) => Number(fecha.slice(8, 10))

function enPantallaResumen(v) {
  const r = v.riesgo
  return [
    v.gastoDiarioSeguro,
    v.gastoDiarioActual,
    v.gastoDiarioActual - v.gastoDiarioSeguro,
    v.proximoIngreso.monto,
    dia(v.proximoIngreso.fecha),
    diasEntre(v.hoy, v.proximoIngreso.fecha),
    ...(r ? [dia(r.desde), dia(r.hasta), Math.abs(r.peorMonto)] : []),
  ]
}

function enPantallaQueViene(v) {
  const r = v.riesgo
  return [
    v.saldoHoy,
    dia(v.proximoIngreso.fecha),
    ...(r ? [dia(r.peorFecha), dia(r.desde), dia(r.hasta), Math.abs(r.peorMonto)] : []),
  ]
}

const casos = PERSONAS.flatMap((p) => [
  { nombre: `${p.id} sin tips`, v: vistaCon([], p.id) },
  { nombre: `${p.id} con todos los tips`, v: vistaCon(p.cambios.map((c) => c.id), p.id) },
])

const textoDe = (puntos) => puntos.map((p) => p.texto).join(' ')

for (const { nombre, v } of casos) {
  test(`${nombre}: el Resumen fácil solo repite cifras de la pantalla y explica «peor caso»`, () => {
    const puntos = explicarResumen(v)
    const permitidos = new Set(enPantallaResumen(v))
    for (const n of numeros(textoDe(puntos))) assert.ok(permitidos.has(n), `${n} no está en el Resumen`)
    assert.ok(puntos.some((p) => p.termino === 'Peor caso'))
  })

  test(`${nombre}: Qué viene fácil solo repite cifras de la pantalla y explica «peor caso»`, () => {
    const puntos = explicarQueViene(v)
    const permitidos = new Set(enPantallaQueViene(v))
    for (const n of numeros(textoDe(puntos))) assert.ok(permitidos.has(n), `${n} no está en Qué viene`)
    assert.ok(puntos.some((p) => p.termino === 'Peor caso'))
  })
}

test('con riesgo, Qué viene fácil nombra el monto del peor día igual que el gráfico', () => {
  const v = vistaCon([], 'independiente')
  assert.ok(textoDe(explicarQueViene(v)).includes(enSoles(v.riesgo.peorMonto)))
})

test('la explicación de la banda depende del ingreso variable, no del nombre de la persona', () => {
  const franja = (id) => explicarQueViene(vistaCon([], id)).find((p) => p.termino === 'La franja de color').texto
  assert.match(franja('independiente'), /más ancha/)
  assert.match(franja('formal'), /angosta/)
})

test('el texto fácil no usa palabras de asesoría ni de crédito', () => {
  for (const { v } of casos) {
    const texto = textoDe([...explicarResumen(v), ...explicarQueViene(v)]).toLowerCase()
    assert.doesNotMatch(texto, /préstamo|crédito|invier|invert|asesor/)
  }
})

test('con gasto seguro 0 el «explícame fácil» del Resumen no promete «hasta S/ 0 al día y llegas»', async () => {
  const { vistaCon } = await import('../src/motor/cliente.js')
  const sinMargen = vistaCon([], 'independiente', [], [{ id: 'grande', tipo: 'gasto', fecha: '2026-11-20', monto: 9000 }])
  const [puedes] = explicarResumen(sinMargen)
  assert.match(puedes.texto, /^Ni sin gastar nada llegas/)
  assert.doesNotMatch(puedes.texto, /S\/.0 al día/)
})
