import { fechaCorta } from '../formato.js'
import { sumarDias } from '../motor/motor.js'
import { TOPE_MOVIMIENTO, fechaValida, leerMonto } from './planificar.js'

// Más atrás que esto ya no es «lo de estos días» y el saldo de hoy ya lo trae el banco.
export const DIAS_ATRAS = 30
// Mismo formato que acepta POST /expenses, para que el id viaje tal cual.
const ID = /^[A-Za-z0-9_-]{1,40}$/

export function rangoRegistrable(cliente) {
  return { desde: sumarDias(cliente.hoy, -DIAS_ATRAS), hasta: cliente.hoy }
}

export function categoriasDeGasto(cliente) {
  return cliente.categorias.map((c) => ({ id: c.id, nombre: c.nombre }))
}

export function validarRegistro(cliente, borrador) {
  const errores = {}
  const { monto, error } = leerMonto(borrador.monto, TOPE_MOVIMIENTO)
  if (error) errores.monto = error
  const { desde, hasta } = rangoRegistrable(cliente)
  if (!fechaValida(borrador.fecha) || borrador.fecha < desde || borrador.fecha > hasta) {
    errores.fecha = `Elige una fecha entre el ${fechaCorta(desde)} y hoy.`
  }
  const gasto = borrador.tipo === 'gasto'
  if (gasto && !categoriasDeGasto(cliente).some((c) => c.id === borrador.categoria)) errores.categoria = 'Elige una categoría.'
  if (Object.keys(errores).length) return { errores }
  const concepto = borrador.concepto.trim() || (gasto ? 'Gasto registrado' : 'Ingreso registrado')
  return {
    movimiento: {
      id: borrador.id,
      tipo: borrador.tipo,
      monto,
      fecha: borrador.fecha,
      concepto,
      ...(gasto ? { categoria: borrador.categoria } : {}),
    },
  }
}

// Reenviar el mismo movimiento (doble toque, recarga) no lo suma dos veces: el id manda.
export function agregarRegistro(lista, movimiento) {
  return lista.some((m) => m.id === movimiento.id) ? lista : [...lista, movimiento]
}

// Lo guardado en el navegador puede venir roto: un monto en texto dejaría el saldo en NaN.
export function esRegistroValido(m) {
  return (
    m !== null &&
    typeof m === 'object' &&
    typeof m.id === 'string' &&
    ID.test(m.id) &&
    (m.tipo === 'gasto' || m.tipo === 'ingreso') &&
    Number.isFinite(m.monto) &&
    m.monto > 0 &&
    m.monto <= TOPE_MOVIMIENTO &&
    fechaValida(m.fecha) &&
    typeof m.concepto === 'string' &&
    (m.tipo === 'ingreso' || typeof m.categoria === 'string')
  )
}

// Al cargar, un id repetido en lo guardado cuenta una sola vez.
export function sinRepetidos(lista) {
  return lista.reduce(agregarRegistro, [])
}
