import assert from 'node:assert/strict'
import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'

// Límite de marca (juez-cumplimiento): ningún color a menos de 20 puntos por canal de los azules de BBVA.
const AZULES_BBVA = ['#004481', '#072146', '#1464A5', '#1973B8', '#5BBEFF', '#2DCCCD']
const CARPETA = fileURLToPath(new URL('../src/', import.meta.url))

function archivos(carpeta) {
  return readdirSync(carpeta, { withFileTypes: true }).flatMap((e) =>
    e.isDirectory() ? archivos(join(carpeta, e.name)) : /\.(css|jsx?)$/.test(e.name) ? [join(carpeta, e.name)] : [],
  )
}

const fuentes = archivos(CARPETA).map((ruta) => ({ ruta, texto: readFileSync(ruta, 'utf8') }))

const aCanales = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16))

function coloresDe(texto) {
  const hex = [...texto.matchAll(/#[0-9a-fA-F]{6}\b/g)].map((m) => aCanales(m[0]))
  const rgb = [...texto.matchAll(/rgba?\(\s*(\d+)[\s,]+(\d+)[\s,]+(\d+)/g)].map((m) => m.slice(1, 4).map(Number))
  return [...hex, ...rgb]
}

test('se leyeron los estilos y componentes', () => {
  assert.ok(fuentes.length > 20)
})

test('ningún color del front queda a menos de 20 puntos por canal de un azul de BBVA', () => {
  const cercanos = []
  for (const { ruta, texto } of fuentes) {
    for (const color of coloresDe(texto)) {
      for (const azul of AZULES_BBVA) {
        if (aCanales(azul).every((c, i) => Math.abs(c - color[i]) < 20)) cercanos.push(`${ruta}: rgb(${color}) ≈ ${azul}`)
      }
    }
  }
  assert.deepEqual(cercanos, [])
})

test('sin degradados en estilos ni en SVG', () => {
  const conDegradado = fuentes.filter(({ texto }) => /gradient/i.test(texto)).map((f) => f.ruta)
  assert.deepEqual(conDegradado, [])
})
