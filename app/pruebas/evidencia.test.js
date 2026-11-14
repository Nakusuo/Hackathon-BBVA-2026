import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { cifra, cuenta, media, proporcion } from '../src/evidencia/cifras.js'
import { agente, estrategias, impactoPorCliente, perturbaciones, tecnicas, valorBanco, veredicto } from '../src/evidencia/secciones.js'

const impacto = JSON.parse(readFileSync(new URL('../../models/metricas_impacto.json', import.meta.url)))

test('cada cifra del panel existe en models/metricas*.json y es un número', () => {
  const todas = [
    ...impactoPorCliente().filas.flatMap((f) => [f.valor, ...f.intervalo]),
    ...estrategias().flatMap((e) => [e.diasRojo, e.colchon]),
    ...tecnicas().flatMap((f) => [f.lucas, f.base]),
    ...agente().filas.flatMap((f) => [f.lucas, f.base]),
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

test('el agente con Gemini sale de la corrida de QA, contado caso por caso', () => {
  const qa = JSON.parse(readFileSync(new URL('../../models/metricas_qa_agente.json', import.meta.url)))
  const { nPerfil, nAdversas, filas } = agente()
  assert.equal(nPerfil.valor, qa.perfil.length)
  assert.equal(nAdversas.valor, qa.adversas.length)
  const porId = Object.fromEntries(filas.map((f) => [f.id, f]))
  const pasan = (casos, check) => casos.filter((c) => c.checks[check]).length / casos.length
  assert.equal(porId['sin-inventar'].lucas.valor, pasan(qa.perfil, 'sin_cifras_inventadas'))
  assert.equal(porId['tu-decides'].lucas.valor, pasan(qa.perfil, 'cierra_con_tu_decides'))
  const latencia = qa.perfil.reduce((a, c) => a + c.segundos, 0) / qa.perfil.length
  assert.ok(Math.abs(porId.latencia.lucas.valor - latencia) < 1e-9)
  for (const f of filas) {
    assert.match(f.lucas.fuente, /^models\/metricas_qa_agente\.json › /)
    // Las muestras son distintas: cada fila lleva el n de los dos lados.
    assert.equal(f.n.valor, qa.perfil.length)
    assert.ok(Number.isFinite(f.nBase.valor), f.nBase.fuente)
  }
})

test('los pedidos prohibidos van aparte y sin veredicto: los corta el filtro previo, no Gemini', () => {
  const qa = JSON.parse(readFileSync(new URL('../../models/metricas_qa_agente.json', import.meta.url)))
  const { filas, prohibidos } = agente()
  assert.ok(!filas.some((f) => f.id === 'prohibidos'))
  assert.equal(prohibidos.qa.valor,
    qa.adversas.filter((c) => Object.values(c.checks).every(Boolean)).length / qa.adversas.length)
  assert.equal(prohibidos.nQa.valor, qa.adversas.length)
  assert.ok(qa.adversas.every((c) => 'rechazada_sin_llm' in c.checks))
})

test('proporcionCompleta rompe si un caso no trae checks', async () => {
  const { ARCHIVOS, proporcionCompleta } = await import('../src/evidencia/cifras.js')
  ARCHIVOS.prueba = { ruta: 'models/metricas_prueba.json', datos: { casos: [{ checks: { a: true } }, { checks: {} }] } }
  try {
    assert.throws(() => proporcionCompleta('prueba', 'casos'), /No hay sí\/no/)
    ARCHIVOS.prueba.datos.casos[1].checks = { a: true, b: false }
    assert.equal(proporcionCompleta('prueba', 'casos').valor, 0.5)
  } finally {
    delete ARCHIVOS.prueba
  }
})

test('un check o una lista que no existe en la corrida de QA rompe', () => {
  assert.throws(() => proporcion('qaAgente', 'perfil', 'no_existe'), /No hay sí\/no/)
  assert.throws(() => cuenta('qaAgente', 'no_existe'), /No hay lista/)
  assert.throws(() => media('qaAgente', 'adversas', 'segundos'), /No hay número/)
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
