import assert from 'node:assert/strict'
import { test } from 'node:test'
import { cliente } from '../src/motor/cliente.js'
import { diferenciaConPromedio, ICONOS_CATEGORIA, partesDelGrafico, porcentajes, UMBRAL } from '../src/lucas/categorias.js'

const suma = (lista) => lista.reduce((s, n) => s + n, 0)

test('porcentajes: suman 100 aunque redondear cada parte diera 99', () => {
  const partes = partesDelGrafico(cliente.categorias)
  const porSeparado = partes.map((p) => Math.round((p.total / suma(partes.map((x) => x.total))) * 100))
  assert.equal(suma(porSeparado), 99, 'la persona de la demo es justo el caso que se corrige')
  assert.equal(suma(porcentajes(partes)), 100)
})

test('porcentajes: el punto que falta va a la parte con mayor resto, y los que sobran no existen', () => {
  assert.deepEqual(porcentajes([{ total: 1 }, { total: 1 }, { total: 1 }]), [34, 33, 33])
  assert.deepEqual(porcentajes([{ total: 50 }, { total: 50 }]), [50, 50])
  assert.deepEqual(porcentajes([{ total: 0 }, { total: 0 }]), [0, 0])
})

test('diferenciaConPromedio: hasta S/ 5 cuenta como «como siempre»; más allá, redondeada al sol', () => {
  assert.equal(UMBRAL, 5)
  assert.equal(diferenciaConPromedio({ total: 105, promedio3m: 100 }), 0)
  assert.equal(diferenciaConPromedio({ total: 95, promedio3m: 100 }), 0)
  assert.equal(diferenciaConPromedio({ total: 106.4, promedio3m: 100 }), 6)
  assert.equal(diferenciaConPromedio({ total: 80, promedio3m: 100 }), -20)
})

test('partesDelGrafico: hasta 6 partes tal cual; con más, las chicas se juntan en «Otros» sin perder plata', () => {
  const pocas = cliente.categorias.slice(0, 6)
  assert.equal(partesDelGrafico(pocas), pocas)

  const partes = partesDelGrafico(cliente.categorias)
  assert.equal(partes.length, 6)
  assert.deepEqual(
    partes.slice(0, 5).map((p) => p.id),
    cliente.categorias.slice(0, 5).map((c) => c.id),
  )
  const otros = partes.at(-1)
  assert.equal(otros.nombre, 'Otros')
  const resto = cliente.categorias.slice(5)
  assert.equal(otros.total, suma(resto.map((c) => c.total)))
  assert.equal(otros.promedio3m, suma(resto.map((c) => c.promedio3m)))
  assert.equal(suma(partes.map((p) => p.total)), suma(cliente.categorias.map((c) => c.total)))
})

test('cada categoría de la persona tiene ícono propio', () => {
  for (const c of cliente.categorias) assert.ok(ICONOS_CATEGORIA[c.id], c.id)
})
