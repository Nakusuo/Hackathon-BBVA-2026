// Persona sintética de la demo. Se reemplaza por la API cuando exista el contrato (MG-01).
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

// Independiente con recibo por honorarios: cobra de dos clientes y ninguno paga siempre lo mismo.
export const persona = {
  hoy: '2026-11-14',
  horizonteDias: 30,
  saldoHoy: 1240,
  tipoIngreso: 'Recibo por honorarios',
  rangoMensual6m: { minimo: 1900, maximo: 3400 },
  ingresos: [
    { id: 'cobro-principal', fecha: '2026-11-30', monto: 2000, variacion: 300, concepto: 'Cobro de tu cliente principal' },
    { id: 'cobro-proyecto', fecha: '2026-12-12', monto: 600, variacion: 400, concepto: 'Cobro de un proyecto aparte' },
  ],
  gastoBaseDiario: 23,
  banda: { inicial: 25, porDia: 8.6 },
  pagos: [
    { id: 'streamflix', fecha: '2026-11-16', concepto: 'StreamFlix', monto: 39.9 },
    { id: 'prestamo', fecha: '2026-11-18', concepto: 'Cuota préstamo personal', monto: 210, cuota: true },
    { id: 'musika', fecha: '2026-11-20', concepto: 'MusiKa Plus', monto: 21.9 },
    { id: 'alquiler', fecha: '2026-11-25', concepto: 'Alquiler de cuarto', monto: 420 },
    { id: 'tarjeta', fecha: '2026-12-01', concepto: 'Pago total de tarjeta de crédito', monto: 950 },
    { id: 'internet', fecha: '2026-12-05', concepto: 'Internet y celular', monto: 180 },
  ],
  gastosFrecuentes: [
    { id: 'delivery', comercio: 'RapiFood', vecesMes: 9, ticket: 12.44, categoria: 'comida' },
    { id: 'cafe', comercio: 'Cafetería La Esquina', vecesMes: 20, ticket: 5.3, categoria: 'hormiga' },
  ],
  // Reparto de los S/ 23 diarios de gasto base en los últimos 30 días (23 × 30 = 690).
  gastoBasePorCategoria: { comida: 300, transporte: 180, salidas: 120, entretenimiento: 50, otros: 40 },
  suscripciones: [
    { id: 'streamflix', comercio: 'StreamFlix', monto: 39.9, dia: 16, uso: 'La usaste 11 veces este mes' },
    { id: 'musika', comercio: 'MusiKa Plus', monto: 21.9, dia: 20, uso: 'No la usas hace 5 semanas' },
  ],
}

const CATEGORIAS = [
  { id: 'comida', nombre: 'Comida y delivery', promedio3m: 380, ejemplo: 'Supermercado y RapiFood' },
  { id: 'transporte', nombre: 'Transporte', promedio3m: 175, ejemplo: 'Bus y taxi por aplicativo' },
  { id: 'salidas', nombre: 'Salidas', promedio3m: 90, ejemplo: 'Restaurantes y reuniones' },
  { id: 'hormiga', nombre: 'Gasto hormiga', promedio3m: 80, ejemplo: 'Café y snacks' },
  { id: 'suscripciones', nombre: 'Suscripciones', promedio3m: 61.8, ejemplo: 'StreamFlix y MusiKa Plus' },
  { id: 'entretenimiento', nombre: 'Entretenimiento', promedio3m: 55, ejemplo: 'Cine y juegos' },
  { id: 'otros', nombre: 'Otros', promedio3m: 45, ejemplo: 'Farmacia y regalos' },
]

export const CAMBIOS = [
  {
    id: 'musika',
    titulo: 'Pausa MusiKa Plus hasta tu próximo cobro',
    facilidad: 'Fácil',
    porque: 'No la usas hace 5 semanas y se cobra el 20, justo antes de tus días más justos.',
    ajuste: { pagosOmitidos: ['musika'] },
  },
  {
    id: 'delivery',
    titulo: 'Pide RapiFood una vez por semana hasta el 30',
    facilidad: 'Esfuerzo medio',
    porque: 'Este mes pediste 9 veces, a unos S/ 12.44 por pedido. Bajar a 4 al mes deja más saldo antes de cobrar.',
    ajuste: { frecuencias: { delivery: 4 } },
  },
  {
    id: 'cafe',
    titulo: 'Toma café fuera 3 veces por semana',
    facilidad: 'Esfuerzo medio',
    porque: 'Este mes fuiste 20 veces a Cafetería La Esquina, a unos S/ 5.30 cada vez.',
    ajuste: { frecuencias: { cafe: 13 } },
  },
]

const MOVIMIENTOS_RECIENTES = [
  { id: 'm1', fecha: '2026-11-13', concepto: 'RapiFood', monto: -12.4, categoria: 'comida' },
  { id: 'm2', fecha: '2026-11-13', concepto: 'Cafetería La Esquina', monto: -5.3, categoria: 'hormiga' },
  { id: 'm3', fecha: '2026-11-12', concepto: 'Supermercado El Ahorro', monto: -86.5, categoria: 'comida' },
  { id: 'm4', fecha: '2026-11-11', concepto: 'Taxi por aplicativo', monto: -14, categoria: 'transporte' },
  { id: 'm5', fecha: '2026-11-10', concepto: 'Cobro de un proyecto aparte', monto: 350, categoria: 'ingreso' },
]

const REPETICIONES_APARTADO = 3

const totalPorCategoria = { ...persona.gastoBasePorCategoria, suscripciones: 0 }
for (const g of persona.gastosFrecuentes) {
  totalPorCategoria[g.categoria] = (totalPorCategoria[g.categoria] ?? 0) + g.vecesMes * g.ticket
}
for (const s of persona.suscripciones) totalPorCategoria.suscripciones += s.monto

const ingresoMensual = persona.ingresos.reduce((s, i) => s + i.monto, 0)
const cuotasMes = persona.pagos.filter((p) => p.cuota).reduce((s, p) => s + p.monto, 0)
const pesoCuotas = Math.round((cuotasMes / ingresoMensual) * 100)

// Mientras no exista el modelo de salud (DI-07), el puntaje de deudas baja el doble de rápido que sube el peso de las cuotas.
const componentesSalud = [
  { nombre: 'Colchón', valor: 35, explicacion: 'Cubre 2 semanas de gastos; lo sano son 3 meses.' },
  {
    nombre: 'Deudas',
    valor: Math.max(0, 100 - pesoCuotas * 2),
    explicacion: `Tus cuotas son el ${pesoCuotas} % de lo que cobras.`,
  },
  { nombre: 'Regularidad del ingreso', valor: 48, explicacion: 'Tus cobros cambian mucho de un mes a otro.' },
  { nombre: 'Control del gasto', valor: 71, explicacion: 'Gastaste menos de lo que entró en 4 de 6 meses.' },
]

const delivery = persona.gastosFrecuentes.find((g) => g.id === 'delivery')
const cafe = persona.gastosFrecuentes.find((g) => g.id === 'cafe')
const cobro = primerCobro(persona)
const miles = (n) => `S/ ${n.toLocaleString('es-PE')}`

const recomendaciones = CAMBIOS.map((c) => evaluarCambio(persona, c)).sort((a, b) => b.mejora - a.mejora)
const peorSinCambios = peorDia(persona, simular(persona))
const conTodosLosCambios = peorDia(persona, simular(persona, ajusteDe(CAMBIOS)))

function riesgoDe(puntos) {
  const rojo = diasEnRojo(persona, puntos)
  if (!rojo.length) return null
  const peor = peorDia(persona, puntos)
  return { desde: rojo[0], hasta: rojo.at(-1), peorFecha: peor.fecha, peorMonto: peor.banda[0], esperado: peor.esperado }
}

function apartadoDe(ajuste) {
  const monto = apartadoMaximo(persona, ajuste)
  if (!monto) return null
  return { monto, repeticiones: REPETICIONES_APARTADO, total: monto * REPETICIONES_APARTADO, hasta: simular(persona).at(-1).fecha }
}

// Todo lo que cambia cuando la persona activa tips con «Lo hago» se recalcula aquí, con el mismo motor.
export function vistaCon(elegidos = []) {
  const activos = CAMBIOS.filter((c) => elegidos.includes(c.id))
  const ajuste = ajusteDe(activos)
  const pronostico = simular(persona, ajuste)
  const peor = peorDia(persona, pronostico)
  return {
    hoy: persona.hoy,
    saldoHoy: persona.saldoHoy,
    cuenta: { nombre: 'Cuenta de ahorros', terminacion: '0001' },
    tarjeta: { nombre: 'Tarjeta de crédito', terminacion: '0002', pagoMes: 950, vence: '2026-12-01' },
    movimientosRecientes: MOVIMIENTOS_RECIENTES,
    proximoIngreso: { ...cobro, tipo: persona.tipoIngreso },
    ingresos: persona.ingresos,
    gastoDiarioActual: Math.round(gastoVariableDiario(persona, ajuste.frecuencias)),
    gastoDiarioSeguro: gastoDiarioSeguro(persona, ajuste),
    proximosPagos: persona.pagos,
    pronostico,
    riesgo: riesgoDe(pronostico),
    riesgoSinCambios: riesgoDe(simular(persona)),
    peorDia: { fecha: peor.fecha, monto: peor.banda[0], esperado: peor.esperado },
    elegidos: activos.map((c) => c.id),
    salud: {
      puntaje: Math.round(componentesSalud.reduce((s, c) => s + c.valor, 0) / componentesSalud.length),
      componentes: componentesSalud,
    },
    aprendido: [
      {
        id: 'cobro',
        dato: `Cobras de 2 clientes por ${persona.tipoIngreso.toLowerCase()}: el principal a fin de mes y otro a mitad de mes.`,
        fuente: 'Tus últimos 6 meses de cobros',
      },
      {
        id: 'variacion',
        dato: `En un mes cobras entre ${miles(persona.rangoMensual6m.minimo)} y ${miles(persona.rangoMensual6m.maximo)}.`,
        fuente: 'Últimos 6 meses',
      },
      {
        id: 'ritmo',
        dato: `Fuera de tus pagos fijos gastas unos S/ ${Math.round(gastoVariableDiario(persona))} al día.`,
        fuente: 'Últimos 30 días',
      },
      {
        id: 'habitos',
        dato: `Pides delivery ${delivery.vecesMes} veces al mes y vas por café ${cafe.vecesMes} veces.`,
        fuente: 'Tus compras con tarjeta',
      },
    ],
    categorias: CATEGORIAS.map((c) => ({ ...c, total: Math.round(totalPorCategoria[c.id] * 100) / 100 })).sort(
      (a, b) => b.total - a.total,
    ),
    suscripciones: persona.suscripciones,
    recomendaciones,
    conTodos: {
      peorFecha: conTodosLosCambios.fecha,
      peorMonto: conTodosLosCambios.banda[0],
      peorAntes: peorSinCambios.banda[0],
    },
    apartado: apartadoDe(ajuste),
    apartadoConTodos: apartadoDe(ajusteDe(CAMBIOS)),
    totalCambios: CAMBIOS.length,
  }
}

export const cliente = vistaCon()
