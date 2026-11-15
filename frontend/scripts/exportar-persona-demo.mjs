// Genera las respuestas de `demo-001` a partir del motor del front, que es la fuente de verdad de esa persona
// (estado.md, «motor manda, API detrás»). La API sirve estos JSON tal cual, así ninguna cifra queda escrita a mano
// en Python. Uso: `node scripts/exportar-persona-demo.mjs` desde frontend/. La prueba `demo001.test.js` falla
// si el motor cambia y no se regeneran.
import { mkdirSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { enSoles, fechaLarga, nivelDeSalud } from '../src/formato.js'
import { armarBandeja, candidatos } from '../src/lucas/avisos.js'
import { PERSONA_INICIAL, personaPorId } from '../src/motor/personas.js'
import { vistaCon } from '../src/motor/cliente.js'

export const CARPETA_SALIDA = new URL('../../data/sample/demo-001/', import.meta.url)
const ID = 'demo-001'
const AVISO_DE_SIMULACION = 'Esta es una simulación. Tú decides.'
// Nivel que declara el contrato para la banda del pronóstico (la prueba de cobertura del 80 % está en evidencia).
const NIVEL_BANDA = 0.8
const DIAS_POR_MES = 30

// Meses que alcanza el saldo de hoy con el gasto variable y los pagos fijos del horizonte; con la persona
// independiente da unas dos semanas, que es lo que dice su componente «Colchón».
function mesesDeColchon(p, gastoDiario) {
  const gastoDelHorizonte = gastoDiario * p.horizonteDias + p.pagos.reduce((s, pago) => s + pago.monto, 0)
  return Math.round((p.saldoHoy / gastoDelHorizonte) * (p.horizonteDias / DIAS_POR_MES) * 100) / 100
}

// Propuesta de cuadrantes de `analitica/eval/generar_docs.py`: salud >= 60 y colchón >= 2 meses es Q1.
function cuadrante(puntaje, colchonMeses) {
  const sana = puntaje >= 60
  const conColchon = colchonMeses >= 2
  if (sana) return conColchon ? 'Q1' : 'Q2'
  return conColchon ? 'Q3' : 'Q4'
}

function salud(vista, p) {
  const colchonMeses = mesesDeColchon(p, vista.gastoDiarioActual)
  return {
    customer_id: ID,
    score: vista.salud.puntaje,
    status: nivelDeSalud(vista.salud.puntaje),
    quadrant: cuadrante(vista.salud.puntaje, colchonMeses),
    emergency_fund_months: colchonMeses,
    currency: 'PEN',
  }
}

function supuestosDe(definicion, cambio) {
  const p = definicion.persona
  const frecuencia = Object.entries(cambio.ajuste.frecuencias ?? {})[0]
  if (frecuencia) {
    const gasto = p.gastosFrecuentes.find((g) => g.id === frecuencia[0])
    return [`${gasto.comercio}: de ${gasto.vecesMes} a ${frecuencia[1]} veces al mes, a ${enSoles(gasto.ticket)} cada una`]
  }
  const pago = p.pagos.find((x) => cambio.ajuste.pagosOmitidos?.includes(x.id))
  return [`Se pausa ${pago.concepto} (${enSoles(pago.monto)}) el ${fechaLarga(pago.fecha)}`]
}

function recomendaciones(vista, definicion) {
  return {
    customer_id: ID,
    currency: 'PEN',
    recommendations: vista.recomendaciones.map((r) => ({
      id: r.id,
      action: r.titulo,
      estimated_impact: r.mejora,
      impact_type: 'expense_reduction',
      impact_period: 'until_next_income',
      reason: r.porque,
      data_used: r.ajuste.pagosOmitidos ? ['recurring_expenses'] : ['transactions'],
      assumptions: [
        ...supuestosDe(definicion, r),
        `Mejora el peor caso del ${fechaLarga(r.fechaPeorDia)}: de ${enSoles(r.peorAntes)} a ${enSoles(r.peorDespues)}`,
      ],
      confidence: 'media',
      disclaimer: AVISO_DE_SIMULACION,
    })),
  }
}

const TIPO_DE_EVENTO = { riesgo: 'negative_balance_risk', pago: 'recurring_expense', ingreso: 'income' }
const PRIORIDAD = { urgente: 'high', normal: 'medium' }

function mensajeDe(aviso) {
  if (aviso.tipo === 'riesgo') {
    return `Tu peor caso del ${fechaLarga(aviso.peorFecha)} llega a ${enSoles(aviso.impacto)} antes de tu cobro del ${fechaLarga(aviso.cobro.fecha)}.`
  }
  if (aviso.tipo === 'pago') return `${aviso.concepto} se cobra el ${fechaLarga(aviso.fecha)} (${enSoles(-aviso.impacto)}) y un tip puede pausarlo.`
  return `${aviso.concepto}: ${enSoles(aviso.impacto)} el ${fechaLarga(aviso.fecha)}.`
}

const TITULO_DE_EVENTO = { riesgo: 'Posible saldo negativo', pago: 'Pago que puedes pausar', ingreso: 'Próximo ingreso' }

// Los mismos avisos que la bandeja del front, con su tope semanal.
function eventos(vista) {
  const { avisos, restantes } = armarBandeja(candidatos(vista).avisos, {}, vista.hoy)
  return {
    customer_id: ID,
    events: avisos.map((a, i) => ({
      id: `evt-${String(i + 1).padStart(3, '0')}`,
      type: TIPO_DE_EVENTO[a.tipo],
      title: TITULO_DE_EVENTO[a.tipo],
      message: mensajeDe(a),
      event_date: a.fecha,
      priority: PRIORIDAD[a.urgencia] ?? 'low',
      estimated_impact: a.impacto,
      notified: false,
    })),
    weekly_notifications_remaining: restantes,
  }
}

// Los días van de mañana a mañana + 29, como el resto de la API; la fecha de hoy es la de la persona, no el reloj.
function pronostico(vista, p) {
  const futuros = vista.pronostico.filter((punto) => punto.fecha > p.hoy)
  return {
    customer_id: ID,
    currency: 'PEN',
    horizon_days: futuros.length,
    confidence_level: NIVEL_BANDA,
    forecast: futuros.map((punto) => ({
      date: punto.fecha,
      predicted_balance: punto.esperado,
      lower_bound: punto.banda[0],
      upper_bound: punto.banda[1],
    })),
    first_risk_date: vista.riesgo?.desde ?? null,
    model: 'motor-de-reglas-del-front',
    data_as_of: p.hoy,
    risk_probability: null,
    synthetic_data: true,
    sample_only: true,
  }
}

export function generarDemo() {
  const definicion = personaPorId(PERSONA_INICIAL)
  const vista = vistaCon([], PERSONA_INICIAL)
  const p = definicion.persona
  return {
    'health.json': salud(vista, p),
    'recommendations.json': recomendaciones(vista, definicion),
    'events.json': eventos(vista),
    'forecast.json': pronostico(vista, p),
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  mkdirSync(CARPETA_SALIDA, { recursive: true })
  for (const [nombre, cuerpo] of Object.entries(generarDemo())) {
    writeFileSync(new URL(nombre, CARPETA_SALIDA), `${JSON.stringify(cuerpo, null, 2)}\n`)
  }
}
