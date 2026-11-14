import { enSoles, fechaCorta } from '../formato.js'
import { sumarDias } from '../motor/motor.js'

export const TOPE_MOVIMIENTO = 50000
const MONTO = /^\d+(\.\d{1,2})?$/
const FECHA = /^\d{4}-\d{2}-\d{2}$/
// Dos cobros del mismo comercio rara vez son idénticos: un 20 % de diferencia sigue siendo el mismo pago.
const PARECIDO = 0.2

export function fechaValida(texto) {
  if (typeof texto !== 'string' || !FECHA.test(texto)) return false
  const fecha = new Date(`${texto}T12:00:00`)
  return !Number.isNaN(fecha.getTime()) && fecha.toISOString().slice(0, 10) === texto
}

// Devuelve el monto como número o el mensaje que se muestra junto al campo.
export function leerMonto(texto, tope, { permiteCero = false } = {}) {
  const limpio = String(texto ?? '').trim()
  if (!limpio && permiteCero) return { monto: 0 }
  if (!limpio) return { error: 'Escribe un monto en soles, por ejemplo 450.' }
  if (!MONTO.test(limpio)) return { error: 'Usa solo números, con hasta dos decimales.' }
  const monto = Number(limpio)
  if (monto <= 0 && !permiteCero) return { error: 'El monto debe ser mayor que S/ 0.' }
  if (monto > tope) return { error: `Hasta ${enSoles(tope)}.` }
  return { monto }
}

// Planificar es hacia adelante: lo de hoy o antes ya es historia y se registra como movimiento.
export function rangoPlanificable(cliente) {
  return { desde: sumarDias(cliente.hoy, 1), hasta: cliente.finPronostico }
}

export function validarPlanificado(cliente, borrador) {
  const errores = {}
  const { monto, error } = leerMonto(borrador.monto, TOPE_MOVIMIENTO)
  if (error) errores.monto = error
  const { desde, hasta } = rangoPlanificable(cliente)
  if (!fechaValida(borrador.fecha) || borrador.fecha < desde || borrador.fecha > hasta) {
    errores.fecha = `Elige una fecha entre el ${fechaCorta(desde)} y el ${fechaCorta(hasta)}.`
  }
  if (Object.keys(errores).length) return { errores }
  const concepto = borrador.concepto.trim() || (borrador.tipo === 'ingreso' ? 'Ingreso planificado' : 'Gasto planificado')
  return { movimiento: { tipo: borrador.tipo, monto, fecha: borrador.fecha, concepto } }
}

function normalizar(texto) {
  return texto
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
}

// Un gasto que ya es un pago conocido no se cuenta dos veces: Lucas avisa antes de guardarlo.
export function yaContado(pagos, movimiento) {
  if (movimiento.tipo !== 'gasto') return null
  const concepto = normalizar(movimiento.concepto)
  if (concepto.length < 3) return null
  return (
    pagos.find((p) => {
      const nombre = normalizar(p.concepto)
      const mismoNombre = concepto.includes(nombre) || nombre.includes(concepto)
      return mismoNombre && Math.abs(movimiento.monto - p.monto) <= p.monto * PARECIDO
    }) ?? null
  )
}

// Lo guardado en el navegador puede venir de otra versión o estar roto: un monto en texto dejaría el pronóstico en NaN.
export function esPlanificadoValido(m) {
  return (
    m !== null &&
    typeof m === 'object' &&
    typeof m.id === 'string' &&
    (m.tipo === 'gasto' || m.tipo === 'ingreso') &&
    Number.isFinite(m.monto) &&
    m.monto > 0 &&
    m.monto <= TOPE_MOVIMIENTO &&
    fechaValida(m.fecha) &&
    typeof m.concepto === 'string'
  )
}
