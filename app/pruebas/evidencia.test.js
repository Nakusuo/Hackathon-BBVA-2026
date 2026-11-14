import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { cifra } from '../src/evidencia/cifras.js'
import { agente, estrategias, impactoPorCliente, perturbaciones, tecnicas, valorBanco, veredicto } from '../src/evidencia/secciones.js'

const impacto = JSON.parse(readFileSync(new URL('../../models/metricas_impacto.json', import.meta.url)))

test('cada cifra del panel existe en models/metricas*.json y es un número', () => {
  const todas = [
    ...impactoPorCliente().filas.flatMap((f) => [f.valor, ...f.intervalo]),
    ...estrategias().flatMap((e) => [e.diasRojo, e.colchon]),
    ...tecnicas().flatMap((f) => [f.lucas, f.base]),
    ...agente().plantillas.map((m) => m.valor),
    ...perturbaciones().pruebas.flatMap((f) => [f.lucas, f.base]),
    ...Object.values(valorBanco()).filter((c) => typeof c.valor === 'number'),
  ]
  assert.ok(todas.length > 40)
  for (const c of todas) {
    assert.ok(Number.isFinite(c.valor), c.fuente)
    assert.match(c.fuente, /^models\/metricas[a-z_]*\.json › /)
  }
})

test('el impacto en S/ es el de Lucas frente a no hacer nada, con su intervalo', () => {
  const colchon = impactoPorCliente().filas.find((f) => f.id === 'colchon')
  const esperado = impacto.diferencias.lucas_vs_nada.colchon_adicional_soles
  assert.equal(colchon.valor.valor, esperado.media)
  assert.deepEqual(colchon.intervalo.map((c) => c.valor), esperado.ic95)
})

test('una clave que no existe rompe en vez de mostrar un número inventado', () => {
  assert.throws(() => cifra('impacto', 'diferencias', 'no_existe'), /No hay número/)
  assert.throws(() => cifra('otro', 'x'), /desconocido/)
})

test('el veredicto se calcula según qué dirección es mejor', () => {
  assert.equal(veredicto(884, 1726, 'menor'), 'mejor')
  assert.equal(veredicto(0.73, 0.92, 'mayor'), 'peor')
  assert.equal(veredicto(1, 1, 'mayor'), 'parecido')
  assert.equal(veredicto(0.81, 0.72, { objetivo: 0.8 }), 'mejor')
})

test('las perturbaciones muestran también lo que empeora', () => {
  const { pruebas } = perturbaciones()
  assert.ok(pruebas.some((p) => p.veredicto === 'peor'))
})
