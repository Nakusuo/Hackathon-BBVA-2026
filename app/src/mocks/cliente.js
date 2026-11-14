// Vista de la persona elegida. Se reemplaza por la API cuando exista el contrato (MG-01).
// Todas las personas pasan por el mismo motor: solo cambian sus datos, nunca las fórmulas.
import {
  ajusteDe,
  apartadoMaximo,
  diasEnRojo,
  evaluarCambio,
  gastoDiarioSeguro,
  gastoVariableDiario,
  peorDia,
  primerCobro,
  simular,
} from './motor.js'
import { PERSONA_INICIAL, personaPorId } from './personas.js'

const REPETICIONES_APARTADO = 3

function totalesPorCategoria(p) {
  const totales = { ...p.gastoBasePorCategoria, suscripciones: 0 }
  for (const g of p.gastosFrecuentes) totales[g.categoria] = (totales[g.categoria] ?? 0) + g.vecesMes * g.ticket
  for (const s of p.suscripciones) totales.suscripciones += s.monto
  return totales
}

// Mientras no exista el modelo de salud (DI-07), el puntaje de deudas baja el doble de rápido que sube el peso de las cuotas.
function componentesSalud(definicion) {
  const p = definicion.persona
  const ingresoMensual = p.ingresos.reduce((s, i) => s + i.monto, 0)
  const cuotas = p.pagos.filter((pago) => pago.cuota).reduce((s, pago) => s + pago.monto, 0)
  const peso = Math.round((cuotas / ingresoMensual) * 100)
  const [colchon, ...resto] = definicion.salud
  return [
    colchon,
    { nombre: 'Deudas', valor: Math.max(0, 100 - peso * 2), explicacion: `Tus cuotas son el ${peso} % de lo que cobras.` },
    ...resto,
  ]
}

function riesgoDe(p, puntos) {
  const rojo = diasEnRojo(p, puntos)
  if (!rojo.length) return null
  const peor = peorDia(p, puntos)
  return { desde: rojo[0], hasta: rojo.at(-1), peorFecha: peor.fecha, peorMonto: peor.banda[0], esperado: peor.esperado }
}

function apartadoDe(p, ajuste) {
  const monto = apartadoMaximo(p, ajuste)
  if (!monto) return null
  return { monto, repeticiones: REPETICIONES_APARTADO, total: monto * REPETICIONES_APARTADO, hasta: simular(p).at(-1).fecha }
}

// Todo lo que cambia con la persona elegida o con los tips activados con «Lo hago» se recalcula aquí.
export function vistaCon(elegidos = [], personaId = PERSONA_INICIAL) {
  const definicion = personaPorId(personaId)
  const p = definicion.persona
  const cambios = definicion.cambios
  const activos = cambios.filter((c) => elegidos.includes(c.id))
  const ajuste = ajusteDe(activos)
  const pronostico = simular(p, ajuste)
  const peor = peorDia(p, pronostico)
  const pronosticoConTodos = simular(p, ajusteDe(cambios))
  const peorConTodos = peorDia(p, pronosticoConTodos)
  const salud = componentesSalud(definicion)
  const totales = totalesPorCategoria(p)
  const veces = Object.fromEntries(p.gastosFrecuentes.map((g) => [g.id, g.vecesMes]))
  const aprendido = definicion.aprendido(p, veces)

  return {
    personaId: definicion.id,
    ingresoVariable: p.ingresos.some((i) => i.variacion > 0),
    hoy: p.hoy,
    saldoHoy: p.saldoHoy,
    cuenta: { nombre: 'Cuenta de ahorros', terminacion: '0001' },
    tarjeta: { nombre: 'Tarjeta de crédito', terminacion: '0002', ...definicion.tarjeta },
    movimientosRecientes: definicion.movimientosRecientes,
    proximoIngreso: { ...primerCobro(p), tipo: p.tipoIngreso },
    ingresos: p.ingresos,
    gastoDiarioActual: Math.round(gastoVariableDiario(p, ajuste.frecuencias)),
    gastoDiarioSeguro: gastoDiarioSeguro(p, ajuste),
    proximosPagos: p.pagos,
    pronostico,
    riesgo: riesgoDe(p, pronostico),
    diasEnRojo: diasEnRojo(p, pronostico).length,
    peorDia: { fecha: peor.fecha, monto: peor.banda[0], esperado: peor.esperado },
    elegidos: activos.map((c) => c.id),
    ajuste,
    salud: { puntaje: Math.round(salud.reduce((s, c) => s + c.valor, 0) / salud.length), componentes: salud },
    aprendido: [
      { id: 'cobro', dato: aprendido.cobro, fuente: aprendido.cobroFuente },
      { id: 'variacion', dato: aprendido.variacion, fuente: 'Últimos 6 meses' },
      {
        id: 'ritmo',
        dato: `Fuera de tus pagos fijos gastas unos S/ ${Math.round(gastoVariableDiario(p))} al día.`,
        fuente: 'Últimos 30 días',
      },
      { id: 'habitos', dato: aprendido.habitos, fuente: 'Tus compras con tarjeta' },
    ],
    categorias: definicion.categorias
      .map((c) => ({ ...c, total: Math.round((totales[c.id] ?? 0) * 100) / 100 }))
      .sort((a, b) => b.total - a.total),
    suscripciones: p.suscripciones,
    recomendaciones: cambios.map((c) => evaluarCambio(p, c)).sort((a, b) => b.mejora - a.mejora),
    conTodos: {
      peorFecha: peorConTodos.fecha,
      peorMonto: peorConTodos.banda[0],
      peorAntes: peorDia(p, simular(p)).banda[0],
      diasEnRojo: diasEnRojo(p, pronosticoConTodos).length,
    },
    apartado: apartadoDe(p, ajuste),
    apartadoConTodos: apartadoDe(p, ajusteDe(cambios)),
    totalCambios: cambios.length,
  }
}

// La persona de la demo por defecto, para quien todavía no eligió otra.
const inicial = personaPorId(PERSONA_INICIAL)
export const persona = inicial.persona
export const CAMBIOS = inicial.cambios
export const cliente = vistaCon()
