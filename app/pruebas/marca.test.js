import assert from 'node:assert/strict'
import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'

// Límite de marca (juez-cumplimiento): ningún color a menos de 20 puntos por canal de los azules de BBVA.
const AZULES_BBVA = ['#004481', '#072146', '#1464A5', '#1973B8', '#5BBEFF', '#2DCCCD']
const APP = fileURLToPath(new URL('../', import.meta.url))

function archivos(carpeta) {
  return readdirSync(carpeta, { withFileTypes: true }).flatMap((e) =>
    e.isDirectory()
      ? archivos(join(carpeta, e.name))
      : /\.(css|jsx?|svg|html)$/.test(e.name)
        ? [join(carpeta, e.name)]
        : [],
  )
}

// El favicon y el index.html también se ven en la demo: entran a la revisión junto con src/.
const fuentes = [...archivos(join(APP, 'src')), ...archivos(join(APP, 'public')), join(APP, 'index.html')].map(
  (ruta) => ({ ruta, texto: readFileSync(ruta, 'utf8') }),
)

// Acepta #abc, #aabbcc y #aabbccdd (la transparencia no cambia el tono).
function aCanales(hex) {
  const cifras = hex.slice(1)
  if (cifras.length === 3) return [...cifras].map((c) => parseInt(c + c, 16))
  return [0, 2, 4].map((i) => parseInt(cifras.slice(i, i + 2), 16))
}

function coloresDe(texto) {
  const hex = [...texto.matchAll(/#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b/g)].map((m) => aCanales(m[0]))
  const rgb = [...texto.matchAll(/rgba?\(\s*(\d+)[\s,]+(\d+)[\s,]+(\d+)/g)].map((m) => m.slice(1, 4).map(Number))
  return [...hex, ...rgb]
}

test('se leyeron los estilos, componentes, favicon e index.html', () => {
  assert.ok(fuentes.length > 20)
  assert.ok(fuentes.some((f) => f.ruta.endsWith('favicon.svg')))
})

test('#abc se lee como #aabbcc', () => {
  assert.deepEqual(aCanales('#1e3'), [0x11, 0xee, 0x33])
  assert.deepEqual(aCanales('#1e3fb2cc'), [0x1e, 0x3f, 0xb2])
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
