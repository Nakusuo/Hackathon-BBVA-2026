// Traduce cada respuesta del contrato (MG-01) a los nombres del front y rechaza la que no cumple,
// para que una respuesta rota pase al respaldo en vez de pintar «NaN» o «undefined» en pantalla.
import { ErrorApi } from './http.js'

function exigir(condicion, campo) {
  if (!condicion) throw new ErrorApi('formato', `La respuesta no trae un «${campo}» válido`)
}

const esObjeto = (o) => typeof o === 'object' && o !== null
const esNumero = (n) => typeof n === 'number' && Number.isFinite(n)
const esTexto = (s) => typeof s === 'string' && s.length > 0
const esFecha = (s) => typeof s === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(s)

export function leerSalud(json) {
  exigir(esNumero(json?.score) && json.score >= 0 && json.score <= 100, 'score')
  exigir(esNumero(json.emergency_fund_months), 'emergency_fund_months')
  return {
    puntaje: json.score,
    estado: json.status,
    cuadrante: json.quadrant,
    colchonMeses: json.emergency_fund_months,
  }
}

/** Mismos nombres que el motor (fecha, esperado, banda) para que el gráfico acepte cualquiera de los dos. */
export function leerPronostico(json) {
  exigir(esNumero(json?.confidence_level) && json.confidence_level > 0 && json.confidence_level <= 1, 'confidence_level')
  exigir(Array.isArray(json.forecast) && json.forecast.length > 0, 'forecast')
  const puntos = json.forecast.map((p) => {
    exigir(esObjeto(p) && esFecha(p.date), 'forecast.date')
    exigir([p.predicted_balance, p.lower_bound, p.upper_bound].every(esNumero), 'forecast.predicted_balance')
    return { fecha: p.date, esperado: p.predicted_balance, banda: [p.lower_bound, p.upper_bound] }
  })
  return { confianza: json.confidence_level, puntos }
}

export function leerRecomendaciones(json) {
  exigir(Array.isArray(json?.recommendations), 'recommendations')
  return json.recommendations.map((r) => {
    exigir(esObjeto(r) && esTexto(r.id) && esTexto(r.action), 'recommendations.action')
    exigir(esNumero(r.estimated_impact), 'recommendations.estimated_impact')
    return {
      id: r.id,
      accion: r.action,
      impacto: r.estimated_impact,
      periodo: r.impact_period,
      porque: r.reason,
      supuestos: r.assumptions ?? [],
      confianza: r.confidence,
      aviso: r.disclaimer,
    }
  })
}

export function leerEventos(json) {
  exigir(Array.isArray(json?.events), 'events')
  exigir(esNumero(json.weekly_notifications_remaining), 'weekly_notifications_remaining')
  return {
    eventos: json.events.map((e) => {
      exigir(esObjeto(e) && esTexto(e.id) && esFecha(e.event_date), 'events.event_date')
      exigir(esNumero(e.estimated_impact), 'events.estimated_impact')
      return {
        id: e.id,
        tipo: e.type,
        titulo: e.title,
        mensaje: e.message,
        fecha: e.event_date,
        prioridad: e.priority,
        impacto: e.estimated_impact,
        notificado: Boolean(e.notified),
      }
    }),
    avisosRestantesSemana: json.weekly_notifications_remaining,
  }
}

// La API manda `rate` como texto («3.75») porque es un Decimal de Pydantic; el mock lo trae como número.
export function leerTipoCambio(json) {
  const tasa = typeof json?.rate === 'string' ? Number(json.rate) : json?.rate
  exigir(esNumero(tasa) && tasa > 0, 'rate')
  exigir(esFecha(json.date), 'date')
  return {
    tasa,
    fecha: json.date,
    fuente: json.source,
    esRespaldo: Boolean(json.is_fallback),
    desactualizado: Boolean(json.is_stale),
  }
}

function leerEscenario(escenario, nombre) {
  exigir(esNumero(escenario?.final_balance), `${nombre}.final_balance`)
  exigir(esNumero(escenario.negative_balance_days), `${nombre}.negative_balance_days`)
  return { saldoFinal: escenario.final_balance, diasEnRojo: escenario.negative_balance_days }
}

export function leerSimulacion(json) {
  exigir(esNumero(json?.difference), 'difference')
  return {
    base: leerEscenario(json.baseline, 'baseline'),
    simulado: leerEscenario(json.simulated, 'simulated'),
    diferencia: json.difference,
    aviso: json.disclaimer,
  }
}

/** cambios: [{ tipo: 'income' | 'expense', monto (S/, positivo), frecuencia: 'once' | 'monthly', descripcion }]. */
export function pedidoSimulacion(idCliente, cambios, horizonteDias = 30) {
  return {
    customer_id: idCliente,
    horizon_days: horizonteDias,
    changes: cambios.map((c) => ({ type: c.tipo, amount: c.monto, frequency: c.frecuencia, description: c.descripcion })),
  }
}

/** El servidor identifica el gasto por `id`: reenviarlo no lo suma otra vez. */
export function pedidoGasto(gasto) {
  return {
    id: gasto.id,
    amount: gasto.monto,
    currency: 'PEN',
    category: gasto.categoria,
    date: gasto.fecha,
  }
}

export function leerGastoRegistrado(json) {
  exigir(esObjeto(json) && esTexto(json.id), 'id')
  exigir(esNumero(Number(json.amount)), 'amount')
  exigir(esFecha(json.date), 'date')
  return { id: json.id, duplicado: json.duplicate === true }
}
