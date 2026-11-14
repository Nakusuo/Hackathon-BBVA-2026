// Datos sintéticos de una persona de demo. Se reemplazan por la API cuando exista el contrato (MG-01).

const HOY = '2026-11-14'
const SALDO_HOY = 1240
const INGRESO = { fecha: '2026-11-30', monto: 2600, tipo: 'Recibo por honorarios' }

const PAGOS = {
  '2026-11-16': 39.9,
  '2026-11-18': 210,
  '2026-11-20': 21.9,
  '2026-11-25': 420,
  '2026-12-01': 950,
  '2026-12-05': 180,
}

const GASTO_DIARIO = 30

function sumarDias(fechaIso, dias) {
  const d = new Date(`${fechaIso}T12:00:00`)
  d.setDate(d.getDate() + dias)
  return d.toISOString().slice(0, 10)
}

// La banda se abre con los días porque el ingreso de un independiente es incierto.
function construirPronostico() {
  const puntos = []
  let saldo = SALDO_HOY
  for (let i = 0; i <= 30; i++) {
    const fecha = sumarDias(HOY, i)
    if (i > 0) saldo -= GASTO_DIARIO + (PAGOS[fecha] ?? 0)
    if (fecha === INGRESO.fecha) saldo += INGRESO.monto
    const ancho = 40 + i * 14
    puntos.push({
      fecha,
      esperado: Math.round(saldo),
      banda: [Math.round(saldo - ancho), Math.round(saldo + ancho)],
    })
  }
  return puntos
}

const pronostico = construirPronostico()
const diaRiesgo = pronostico.find((p) => p.banda[0] < 0)

export const cliente = {
  hoy: HOY,
  arquetipo: 'Independiente con recibo por honorarios',
  saldoHoy: SALDO_HOY,
  proximoIngreso: INGRESO,
  salud: {
    puntaje: 58,
    componentes: [
      { nombre: 'Colchón', valor: 35, explicacion: 'Tu ahorro cubre unas 2 semanas de gastos. Lo sano es 3 meses.' },
      { nombre: 'Deudas', valor: 62, explicacion: 'Tus cuotas se llevan el 24 % de lo que ganas.' },
      { nombre: 'Regularidad del ingreso', valor: 48, explicacion: 'En los últimos 6 meses cobraste entre S/ 1,900 y S/ 3,400.' },
      { nombre: 'Control del gasto', valor: 71, explicacion: 'Gastas menos de lo que entra en 4 de cada 6 meses.' },
    ],
  },
  segmento: {
    nombre: 'Ingreso justo',
    descripcion: 'Gastas con cuidado, pero casi no te queda para ahorrar. Un pequeño colchón te daría calma entre pago y pago.',
  },
  gastoHormiga: {
    mes: 186,
    detalle: [
      { comercio: 'RapiFood', veces: 9, total: 112 },
      { comercio: 'Cafetería La Esquina', veces: 14, total: 74 },
    ],
  },
  suscripciones: [
    { comercio: 'StreamFlix', monto: 39.9, dia: 16, usoUltimoMes: 'La usaste 11 veces' },
    { comercio: 'MusiKa Plus', monto: 21.9, dia: 20, usoUltimoMes: 'No la usaste en 5 semanas' },
  ],
  pronostico,
  diaRiesgo: diaRiesgo
    ? { fecha: diaRiesgo.fecha, minimo: diaRiesgo.banda[0], maximo: diaRiesgo.banda[1], confianza: 'media' }
    : null,
  recomendaciones: [
    {
      id: 'reco-1',
      titulo: 'Pausa MusiKa Plus hasta tu próximo pago',
      monto: 21.9,
      efecto: 'Ahorras S/ 21.90 antes del 20 de noviembre.',
      porque: 'No la usaste en 5 semanas y se cobra 10 días antes de tu ingreso, justo cuando tu saldo está más bajo.',
      facilidad: 'Fácil',
    },
    {
      id: 'reco-2',
      titulo: 'Baja RapiFood a 2 pedidos por semana',
      monto: 60,
      efecto: 'Te quedan unos S/ 60 más al 26 de noviembre.',
      porque: 'Este mes pediste 9 veces, con un promedio de S/ 12.40. Con 2 por semana pasas tu día más justo sin quedar en rojo.',
      facilidad: 'Media',
    },
    {
      id: 'reco-3',
      titulo: 'Aparta S/ 80 cuando cobres el 30',
      monto: 80,
      efecto: 'En 3 meses tendrías S/ 240 de colchón.',
      porque: 'Diciembre trae la cuota del 1 y gastos de fin de año. Separar una parte el día que cobras evita usarla sin darte cuenta.',
      facilidad: 'Fácil',
    },
  ],
}
