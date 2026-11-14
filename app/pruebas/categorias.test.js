import assert from 'node:assert/strict'
import { test } from 'node:test'
import { cliente } from '../src/motor/cliente.js'
import { partesDelGrafico, porcentajes } from '../src/lucas/categorias.js'

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
