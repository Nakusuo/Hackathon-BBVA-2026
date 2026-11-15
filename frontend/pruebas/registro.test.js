import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { enviarGasto } from '../src/api/lucas.js'
import { ErrorApi } from '../src/api/http.js'
import { agregarRegistro, esRegistroValido, sinRepetidos, validarRegistro } from '../src/lucas/registro.js'
import { cliente, cuantoCabe, vistaCon } from '../src/motor/cliente.js'
import { personaPorId } from '../src/motor/personas.js'
import { CLAVE_REGISTRADOS, CLAVE_TIPS, darPermiso, guardarPersona, retirarPermiso } from '../src/sesion.js'

// P5: lo que la persona registra mueve el saldo de partida y todo el pronóstico, una sola vez.

const gasto = (monto, extra = {}) => ({ id: 'mov-1', tipo: 'gasto', monto, fecha: cliente.hoy, concepto: 'Almuerzo', categoria: 'comida', ...extra })
const ingreso = (monto, extra = {}) => ({ id: 'mov-2', tipo: 'ingreso', monto, fecha: cliente.hoy, concepto: 'Cliente', ...extra })
const con = (...registrados) => vistaCon([], 'independiente', [], [], registrados)
const borrador = (extra = {}) => ({ id: 'mov-1', tipo: 'gasto', monto: '45', fecha: cliente.hoy, concepto: '', categoria: 'comida', ...extra })
const dia = (vista, fecha) => vista.pronostico.find((p) => p.fecha === fecha)

test('un gasto de hoy baja el saldo y cada día del pronóstico por el monto exacto', () => {
  const vista = con(gasto(120))
  assert.equal(vista.saldoHoy, cliente.saldoHoy - 120)
  for (const p of cliente.pronostico) {
    assert.equal(p.esperado - dia(vista, p.fecha).esperado, 120)
  }
})

test('un gasto lleva el peor caso y los días en rojo en la misma dirección', () => {
  const vista = con(gasto(300))
  assert.equal(vista.peorDia.monto, cliente.peorDia.monto - 300)
  assert.ok(vista.diasEnRojo >= cliente.diasEnRojo)
  assert.ok(vista.salud.puntaje <= cliente.salud.puntaje)
})

test('un ingreso sube el saldo, puede quitar el rojo y lo recuerda cuantoCabe', () => {
  const vista = con(ingreso(500))
  assert.equal(vista.saldoHoy, cliente.saldoHoy + 500)
  assert.ok(vista.peorDia.monto > cliente.peorDia.monto)
  assert.equal(vista.diasEnRojo, 0)
  assert.ok(cuantoCabe(vista, '2026-11-20').ese >= cuantoCabe(cliente, '2026-11-20').ese)
})

test('el mismo id no se suma dos veces, ni al agregar ni al leer lo guardado', () => {
  const una = agregarRegistro([], gasto(120))
  const dos = agregarRegistro(una, gasto(120))
  assert.equal(dos.length, 1)
  assert.deepEqual(sinRepetidos([gasto(120), gasto(120), ingreso(50)]).map((m) => m.id), ['mov-1', 'mov-2'])
  assert.equal(con(...dos).saldoHoy, cliente.saldoHoy - 120)
})

test('el gasto aparece entre los movimientos recientes con signo y categoría, y suma a su categoría', () => {
  const vista = con(gasto(120, { concepto: 'Cena' }))
  assert.deepEqual(vista.movimientosRecientes[0], { id: 'mov-1', fecha: cliente.hoy, concepto: 'Cena', monto: -120, categoria: 'comida' })
  const total = (v) => v.categorias.find((c) => c.id === 'comida').total
  assert.equal(Math.round((total(vista) - total(cliente)) * 100) / 100, 120)
})

test('registrar no cambia a la otra persona ni el guion de la persona inicial sin registros', () => {
  assert.deepEqual(vistaCon([], 'independiente', [], [], []).pronostico, cliente.pronostico)
  assert.equal(vistaCon([], 'formal', [], [], []).saldoHoy, personaPorId('formal').persona.saldoHoy)
})

test('validaciones: monto, fecha futura, fecha vieja y categoría', () => {
  assert.ok(validarRegistro(cliente, borrador()).movimiento)
  assert.ok(validarRegistro(cliente, borrador({ monto: '0' })).errores.monto)
  assert.ok(validarRegistro(cliente, borrador({ monto: '' })).errores.monto)
  assert.ok(validarRegistro(cliente, borrador({ monto: 'abc' })).errores.monto)
  assert.ok(validarRegistro(cliente, borrador({ monto: '50001' })).errores.monto)
  assert.ok(validarRegistro(cliente, borrador({ fecha: '2026-11-15' })).errores.fecha)
  assert.ok(validarRegistro(cliente, borrador({ fecha: '2026-10-01' })).errores.fecha)
  assert.ok(validarRegistro(cliente, borrador({ fecha: '' })).errores.fecha)
  assert.ok(validarRegistro(cliente, borrador({ categoria: 'inventada' })).errores.categoria)
  const ing = validarRegistro(cliente, borrador({ tipo: 'ingreso', categoria: '' }))
  assert.equal(ing.movimiento.categoria, undefined)
  assert.equal(ing.movimiento.concepto, 'Ingreso registrado')
})

test('lo guardado roto o inventado se descarta', () => {
  assert.ok(esRegistroValido(gasto(10)))
  assert.equal(esRegistroValido({ ...gasto(10), monto: '10' }), false)
  assert.equal(esRegistroValido({ ...gasto(10), id: 'con espacio' }), false)
  assert.equal(esRegistroValido({ ...gasto(10), categoria: undefined }), false)
  assert.equal(esRegistroValido(null), false)
})

test('retirar el permiso o cambiar de persona olvida lo registrado', () => {
  const datos = new Map()
  globalThis.window = {
    localStorage: { getItem: (k) => datos.get(k) ?? null, setItem: (k, v) => datos.set(k, String(v)), removeItem: (k) => datos.delete(k) },
  }
  darPermiso('independiente', '2026-11-14')
  datos.set(CLAVE_REGISTRADOS, '[]')
  datos.set(CLAVE_TIPS, '[]')
  retirarPermiso('independiente')
  assert.equal(datos.has(CLAVE_REGISTRADOS), false)
  datos.set(CLAVE_REGISTRADOS, '[]')
  guardarPersona('formal')
  assert.equal(datos.has(CLAVE_REGISTRADOS), false)
})

test('el gasto viaja a POST /expenses con su id y se valida la respuesta', async () => {
  let visto
  const pedir = async (ruta, opciones) => {
    visto = { ruta, cuerpo: JSON.parse(opciones.body), metodo: opciones.method }
    return { ok: true, status: 201, json: async () => ({ id: 'mov-1', amount: '120.00', date: cliente.hoy, duplicate: false }) }
  }
  const respuesta = await enviarGasto(gasto(120), { pedir })
  assert.deepEqual(visto, {
    ruta: '/api/v1/customers/demo-001/expenses',
    metodo: 'POST',
    cuerpo: { id: 'mov-1', amount: 120, currency: 'PEN', category: 'comida', date: cliente.hoy },
  })
  assert.deepEqual(respuesta, { id: 'mov-1', duplicado: false })
})

test('si el servidor cae o contesta algo roto, enviarGasto lanza ErrorApi para dejarlo en local', async () => {
  const caida = async () => {
    throw new TypeError('fetch failed')
  }
  await assert.rejects(enviarGasto(gasto(120), { pedir: caida }), ErrorApi)
  const rota = async () => ({ ok: true, status: 201, json: async () => ({ nada: 1 }) })
  await assert.rejects(enviarGasto(gasto(120), { pedir: rota }), (e) => e instanceof ErrorApi && e.tipo === 'formato')
})

test('el formato del gasto coincide con el esquema del backend', () => {
  const esquema = readFileSync(new URL('../../backend/src/api/schemas/expenses.py', import.meta.url), 'utf-8')
  for (const campo of ['id', 'amount', 'currency', 'category', 'date']) assert.match(esquema, new RegExp(`\n    ${campo}:`))
})
