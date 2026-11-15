import assert from 'node:assert/strict'
import { test } from 'node:test'
import { bloquesDe, partesDe } from '../src/lucas/textoChat.js'

const textoDe = (partes) => partes.map((p) => p.texto).join('')
const fuertes = (partes) => partes.filter((p) => p.fuerte).map((p) => p.texto)

test('cada línea es un párrafo y las líneas con guion seguidas forman una sola lista', () => {
  const bloques = bloquesDe('Lo que hoy sí calza:\n- Abre un apartado.\n- Activa el redondeo.\n\nEs un catálogo de demostración.')
  assert.deepEqual(
    bloques.map((b) => b.tipo),
    ['parrafo', 'lista', 'parrafo'],
  )
  assert.deepEqual(bloques[1].items.map(textoDe), ['Abre un apartado.', 'Activa el redondeo.'])
})

test('un texto de una sola línea sigue siendo un párrafo y uno vacío no pinta nada', () => {
  assert.deepEqual(bloquesDe('Llegas a tu cobro.').map((b) => b.tipo), ['parrafo'])
  assert.deepEqual(bloquesDe(''), [])
  assert.deepEqual(bloquesDe(undefined), [])
})

test('resalta montos, porcentajes y plazos sin cambiar el texto', () => {
  const linea = 'Con ese gasto de S/ 450, en 30 dias tu saldo rondaria -S/ 290 en vez de S/ 1,661. Riesgo: 15%. Llegarias en 10 meses.'
  const partes = partesDe(linea)
  assert.equal(textoDe(partes), linea)
  assert.deepEqual(fuertes(partes), ['S/ 450', '30 dias', '-S/ 290', 'S/ 1,661', '15%', '10 meses'])
})

test('un número suelto o el punto final de la frase no se resaltan', () => {
  assert.deepEqual(fuertes(partesDe('Lo hiciste en 6 de esos 6 intentos.')), [])
  assert.deepEqual(fuertes(partesDe('Apartas S/ 1,950.')), ['S/ 1,950'])
  assert.deepEqual(fuertes(partesDe('S/ 6,000 al mes es mucho.')), ['S/ 6,000'])
})
