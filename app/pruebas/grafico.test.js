import assert from 'node:assert/strict'
import { test } from 'node:test'
import { marcasDelEje } from '../src/grafico.js'

const punto = (bajo, alto) => ({ banda: [bajo, alto] })

test('un rojo pequeño no estira el eje hasta -1000', () => {
  const { dominio, marcas } = marcasDelEje([punto(-60, 400), punto(900, 2900)])
  assert.deepEqual(dominio, [-250, 3000])
  assert.deepEqual(marcas, [-250, 0, 1000, 2000, 3000])
})

test('sin rojo el eje empieza en cero', () => {
  const { dominio, marcas } = marcasDelEje([punto(100, 900)])
  assert.deepEqual(dominio, [0, 1000])
  assert.deepEqual(marcas, [0, 500, 1000])
})

test('saldo en cero todo el periodo no rompe el eje', () => {
  const { dominio } = marcasDelEje([punto(0, 0)])
  assert.deepEqual(dominio, [0, 500])
})
