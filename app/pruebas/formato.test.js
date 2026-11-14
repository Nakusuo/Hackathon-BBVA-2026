import assert from 'node:assert/strict'
import { test } from 'node:test'
import { avanceDelCiclo, conSigno, diasEntre, enSoles, enSolesRedondo, fechaDia, iniciales } from '../src/formato.js'

const NBSP = ' '

test('enSoles: enteros sin decimales, céntimos con dos, negativos con signo menos', () => {
  assert.equal(enSoles(0), `S/${NBSP}0`)
  assert.equal(enSoles(1240), `S/${NBSP}1,240`)
  assert.equal(enSoles(21.9), `S/${NBSP}21.90`)
  assert.equal(enSoles(-20), `−S/${NBSP}20`)
})

test('enSolesRedondo: los totales siempre al sol, también los negativos', () => {
  assert.equal(enSolesRedondo(61.8), `S/${NBSP}62`)
  assert.equal(enSolesRedondo(1240.4), `S/${NBSP}1,240`)
  assert.equal(enSolesRedondo(-20.6), `−S/${NBSP}21`)
})

test('conSigno: solo los positivos llevan +', () => {
  assert.equal(conSigno(12), `+S/${NBSP}12`)
  assert.equal(conSigno(0), `S/${NBSP}0`)
  assert.equal(conSigno(-60), `−S/${NBSP}60`)
})

test('fechas en español de Perú', () => {
  assert.equal(fechaDia('2026-11-29'), 'domingo 29')
  assert.equal(diasEntre('2026-11-14', '2026-11-30'), 16)
  assert.equal(diasEntre('2026-11-30', '2026-11-30'), 0)
})

test('iniciales: dos palabras como máximo y texto vacío sin error', () => {
  assert.equal(iniciales('Cafetería La Esquina'), 'CL')
  assert.equal(iniciales('RapiFood'), 'R')
  assert.equal(iniciales('  '), '')
})

test('avanceDelCiclo: la barra de días se queda entre 0 y 1', () => {
  assert.equal(avanceDelCiclo(15), 0.5)
  assert.equal(avanceDelCiclo(0), 1)
  assert.equal(avanceDelCiclo(45), 0)
  assert.equal(avanceDelCiclo(-3), 1)
})
