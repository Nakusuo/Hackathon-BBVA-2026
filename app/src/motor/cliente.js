// Vista de la persona elegida. La API de hoy describe a otra persona (demo-001), así que las cifras que se recalculan salen de aquí.
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
  vecesHastaCobro,
} from './motor.js'
import { PERSONA_INICIAL, personaPorId } from './personas.js'

const REPETICIONES_APARTADO = 3

function totalesPorCategoria(p) {
  const totales = { ...p.gastoBasePorCategoria, suscripciones: 0 }
  for (const g of p.gastosFrecuentes) totales[g.categoria] = (totales[g.categoria] ?? 0) + g.vecesMes * g.ticket
  for (const s of p.suscripciones) totales.suscripciones += s.monto
  return totales
}

// Mientras no exista el modelo de salud (DI-07), el puntaje de deudas baja el doble de rápido que sube el peso de las cuotas,
// y el control del gasto promedia su historia con el plan de hoy: cada día en rojo proyectado antes del cobro le quita
// 30 puntos al plan. Así la salud se mueve cuando la persona elige tips.
const PUNTOS_POR_DIA_EN_ROJO = 30

function controlConPlan(control, diasRojo) {
  const plan = Math.max(0, 100 - diasRojo * PUNTOS_POR_DIA_EN_ROJO)
  const conPlan = diasRojo
    ? `Con tu plan de hoy quedarías ${diasRojo === 1 ? '1 día' : `${diasRojo} días`} en rojo antes de cobrar.`
    : 'Con tu plan de hoy llegas a tu cobro sin quedar en rojo.'
  return { ...control, valor: Math.round((control.valor + plan) / 2), explicacion: `${control.explicacion} ${conPlan}` }
}

function componentesSalud(definicion, diasRojo) {
  const p = definicion.persona
  const cuotas = p.pagos.filter((pago) => pago.cuota).reduce((s, pago) => s + pago.monto, 0)
  const peso = Math.round((cuotas / p.ingresoMensual) * 100)
  const [colchon, ...resto] = definicion.salud
  return [
    colchon,
    { nombre: 'Deudas', valor: Math.max(0, 100 - peso * 2), explicacion: `Tus cuotas son el ${peso} % de lo que cobras.` },
    ...resto.map((c) => (c.nombre === 'Control del gasto' ? controlConPlan(c, diasRojo) : c)),
  ]
}

function saludDe(definicion, diasRojo) {
  const componentes = componentesSalud(definicion, diasRojo)
  return { puntaje: Math.round(componentes.reduce((s, c) => s + c.valor, 0) / componentes.length), componentes }
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

// Lo que se sigue de cada tip desde que se elige: cuántas veces van del comercio frente a lo que el tip
// permite hasta el cobro, o la fecha del cargo que hay que pausar. Cuenta los movimientos desde hoy.
function seguimientoDe(definicion, cambio) {
  const p = definicion.persona
  const [idFrecuente, meta] = Object.entries(cambio.ajuste.frecuencias ?? {})[0] ?? []
  if (idFrecuente) {
    const gasto = p.gastosFrecuentes.find((g) => g.id === idFrecuente)
    const usadas = definicion.movimientosRecientes.filter((m) => m.concepto === gasto.comercio && m.fecha >= p.hoy).length
    return { tipo: 'veces', comercio: gasto.comercio, usadas, limite: vecesHastaCobro(p, meta), hasta: primerCobro(p).fecha }
  }
  const pago = p.pagos.find((pago) => cambio.ajuste.pagosOmitidos?.includes(pago.id))
  return { tipo: 'pausa', comercio: pago.concepto, fecha: pago.fecha }
}

// Todo lo que cambia con la persona elegida o con los tips activados con «Lo hago» se recalcula aquí.
// `pagosExtra` son gastos de prueba (la bandeja de avisos los usa para mostrar cómo se mueve el riesgo).
export function vistaCon(elegidos = [], personaId = PERSONA_INICIAL, pagosExtra = []) {
  const definicion = personaPorId(personaId)
  const p = definicion.persona
  const cambios = definicion.cambios
  const activos = cambios.filter((c) => elegidos.includes(c.id))
  const ajuste = { ...ajusteDe(activos), pagosExtra }
  const pronostico = simular(p, ajuste)
  const peor = peorDia(p, pronostico)
  const pronosticoConTodos = simular(p, ajusteDe(cambios))
  const peorConTodos = peorDia(p, pronosticoConTodos)
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
    salud: saludDe(definicion, diasEnRojo(p, pronostico).length),
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
    recomendaciones: cambios
      .map((c) => ({ ...evaluarCambio(p, c), seguimiento: seguimientoDe(definicion, c) }))
      .sort((a, b) => b.mejora - a.mejora),
    conTodos: {
      peorFecha: peorConTodos.fecha,
      peorMonto: peorConTodos.banda[0],
      peorAntes: peorDia(p, simular(p)).banda[0],
      diasEnRojo: diasEnRojo(p, pronosticoConTodos).length,
      salud: saludDe(definicion, diasEnRojo(p, pronosticoConTodos).length).puntaje,
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
