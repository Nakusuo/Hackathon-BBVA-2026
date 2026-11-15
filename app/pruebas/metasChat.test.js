import assert from 'node:assert/strict'
import { test } from 'node:test'
import { candidatos } from '../src/lucas/avisos.js'
import { desdeAgente } from '../src/lucas/clienteChat.js'
import { crearMeta, editarMeta, estadoDe, metaDesdePropuesta } from '../src/lucas/metas.js'
import { vistaCon } from '../src/motor/cliente.js'

const formal = vistaCon([], 'formal')
const contexto = { hoy: formal.hoy, primerApartado: formal.proximoIngreso.fecha }
const BASE = { conversation_id: 'c', answer: 'Plan listo.', verified: true }

test('la propuesta del agente llega al chat solo si tiene nombre, monto y fecha', () => {
  const ok = desdeAgente({ ...BASE, goal_proposal: { name: 'Viaje a Cusco', target: 2800, date: '2027-05-14' } })
  assert.deepEqual(ok.propuesta, { nombre: 'Viaje a Cusco', objetivo: 2800, fecha: '2027-05-14' })
  assert.equal(desdeAgente(BASE).propuesta, null)
  assert.equal(desdeAgente({ ...BASE, goal_proposal: { name: 'X', target: -5, date: '2027-05-14' } }).propuesta, null)
  assert.equal(desdeAgente({ ...BASE, goal_proposal: { name: 'X', target: 100, date: 'mayo' } }).propuesta, null)
})

test('la meta del chat se guarda con la forma de la pantalla Metas y una fecha anterior al cobro se corre al cobro', () => {
  const { datos } = metaDesdePropuesta({ nombre: 'Carro', objetivo: 10000, fecha: '2026-12-31' }, contexto)
  assert.deepEqual(datos, { nombre: 'Carro', objetivo: 10000, ahorrado: 0, fecha: '2026-12-31' })
  const temprana = metaDesdePropuesta({ nombre: 'Carro', objetivo: 10000, fecha: '2026-11-15' }, contexto)
  assert.equal(temprana.datos.fecha, formal.proximoIngreso.fecha)
})

test('editar una meta cambia sus datos y su estado avanza si ya se cumplió', () => {
  const meta = crearMeta({ nombre: 'Viaje', objetivo: 1000, ahorrado: 0, fecha: '2027-05-14' }, 'm1')
  const editada = editarMeta(meta, { nombre: 'Viaje a Brasil', objetivo: 1200, ahorrado: 300, fecha: '2027-06-30' })
  assert.equal(editada.nombre, 'Viaje a Brasil')
  assert.equal(editada.objetivo, 1200)
  assert.equal(estadoDe(editada), 'en curso')
  assert.equal(estadoDe(editarMeta(editada, { ahorrado: 1200 })), 'cumplida')
})

test('el día de cobro llega el recordatorio de cuánto apartar para cada meta; lejos del cobro no', () => {
  const meta = crearMeta({ nombre: 'Viaje a Brasil', objetivo: 3000, ahorrado: 0, fecha: '2027-06-30' }, 'm1')
  const delCobro = candidatos(formal, formal.proximoIngreso.fecha, [meta]).avisos.filter((a) => a.tipo === 'meta')
  assert.equal(delCobro.length, 1)
  assert.equal(delCobro[0].meta, 'Viaje a Brasil')
  assert.ok(delCobro[0].impacto > 0 && delCobro[0].impacto <= formal.apartado.monto)
  assert.equal(delCobro[0].accion.ruta, '/lucas/metas')
  assert.equal(candidatos(formal, formal.hoy, [meta]).avisos.filter((a) => a.tipo === 'meta').length, 0)
  assert.equal(candidatos(formal, formal.proximoIngreso.fecha).avisos.filter((a) => a.tipo === 'meta').length, 0)
})
