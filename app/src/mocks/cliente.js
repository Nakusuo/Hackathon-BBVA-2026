// Persona sintética de la demo. Se reemplaza por la API cuando exista el contrato (MG-01).
import {
  diasEnRojo,
  evaluarCambio,
  evaluarTodos,
  gastoDiarioSeguro,
  gastoVariableDiario,
  peorDia,
  simular,
} from './motor.js'

const persona = {
  hoy: '2026-11-14',
  horizonteDias: 30,
  saldoHoy: 1240,
  ingreso: { fecha: '2026-11-30', monto: 2600, tipo: 'Recibo por honorarios' },
  gastoBaseDiario: 23,
  banda: { inicial: 25, porDia: 8.6 },
  pagos: [
    { id: 'streamflix', fecha: '2026-11-16', concepto: 'StreamFlix', monto: 39.9 },
    { id: 'prestamo', fecha: '2026-11-18', concepto: 'Cuota préstamo personal', monto: 210, deuda: true },
    { id: 'musika', fecha: '2026-11-20', concepto: 'MusiKa Plus', monto: 21.9 },
    { id: 'alquiler', fecha: '2026-11-25', concepto: 'Alquiler de cuarto', monto: 420 },
    { id: 'tarjeta', fecha: '2026-12-01', concepto: 'Tarjeta de crédito', monto: 950, deuda: true },
    { id: 'internet', fecha: '2026-12-05', concepto: 'Internet y celular', monto: 180 },
  ],
  gastosFrecuentes: [
    { id: 'delivery', comercio: 'RapiFood', vecesMes: 9, ticket: 12.44 },
    { id: 'cafe', comercio: 'Cafetería La Esquina', vecesMes: 20, ticket: 5.3 },
  ],
  suscripciones: [
    { id: 'streamflix', comercio: 'StreamFlix', monto: 39.9, dia: 16, uso: 'La usaste 11 veces este mes' },
    { id: 'musika', comercio: 'MusiKa Plus', monto: 21.9, dia: 20, uso: 'No la usas hace 5 semanas' },
  ],
}

const CAMBIOS = [
  {
    id: 'musika',
    titulo: 'Pausa MusiKa Plus hasta tu próximo cobro',
    facilidad: 'Fácil',
    ahorro: 21.9,
    porque: 'No la usas hace 5 semanas y se cobra el 20, justo antes de tus días más justos.',
    ajuste: { pagosOmitidos: ['musika'] },
  },
  {
    id: 'delivery',
    titulo: 'Pide RapiFood una vez por semana hasta el 30',
    facilidad: 'Esfuerzo medio',
    ahorro: null,
    porque: 'Este mes pediste 9 veces, a unos S/ 12.44 por pedido. Bajar a 4 al mes deja más saldo antes de cobrar.',
    ajuste: { frecuencias: { delivery: 4 } },
  },
  {
    id: 'cafe',
    titulo: 'Toma café fuera 3 veces por semana',
    facilidad: 'Esfuerzo medio',
    ahorro: null,
    porque: 'Este mes fuiste 20 veces a Cafetería La Esquina, a unos S/ 5.30 cada vez.',
    ajuste: { frecuencias: { cafe: 13 } },
  },
]

const APARTADO = { monto: 150, cobros: 3 }

const pronostico = simular(persona)
const peor = peorDia(persona, pronostico)
const rojo = diasEnRojo(persona, pronostico)
const recomendaciones = CAMBIOS.map((c) => evaluarCambio(persona, c)).sort((a, b) => b.mejora - a.mejora)
const conTodos = evaluarTodos(persona, CAMBIOS)

const cuotasMes = persona.pagos.filter((p) => p.deuda).reduce((s, p) => s + p.monto, 0)
const pesoDeudas = Math.round((cuotasMes / persona.ingreso.monto) * 100)

// Mientras no exista el modelo de salud (DI-07), el puntaje de deudas baja en línea recta con el peso de las cuotas.
const componentesSalud = [
  { nombre: 'Colchón', valor: 35, explicacion: 'Cubre 2 semanas de gastos; lo sano son 3 meses.' },
  {
    nombre: 'Deudas',
    valor: Math.max(0, 100 - pesoDeudas),
    explicacion: `Tus cuotas son el ${pesoDeudas}\u00a0% de lo que cobras.`,
  },
  { nombre: 'Regularidad del ingreso', valor: 48, explicacion: 'Cobraste entre S/ 1,900 y S/ 3,400 al mes.' },
  { nombre: 'Control del gasto', valor: 71, explicacion: 'Gastaste menos de lo que entró en 4 de 6 meses.' },
]

export const cliente = {
  hoy: persona.hoy,
  saldoHoy: persona.saldoHoy,
  proximoIngreso: persona.ingreso,
  gastoDiarioActual: Math.round(gastoVariableDiario(persona)),
  gastoDiarioSeguro: gastoDiarioSeguro(persona),
  proximosPagos: persona.pagos,
  pronostico,
  riesgo: rojo.length
    ? { desde: rojo[0], hasta: rojo.at(-1), peorFecha: peor.fecha, peorMonto: peor.banda[0], esperado: peor.esperado }
    : null,
  salud: {
    puntaje: Math.round(componentesSalud.reduce((s, c) => s + c.valor, 0) / componentesSalud.length),
    componentes: componentesSalud,
  },
  segmento: { nombre: 'Ingreso justo' },
  gastosFrecuentes: persona.gastosFrecuentes.map((g) => ({
    ...g,
    totalMes: Math.round(g.vecesMes * g.ticket),
  })),
  suscripciones: persona.suscripciones,
  recomendaciones,
  conTodos: { peorFecha: conTodos.peor.fecha, peorMonto: conTodos.peor.banda[0], diasEnRojo: conTodos.diasEnRojo.length },
  apartado: { ...APARTADO, total: APARTADO.monto * APARTADO.cobros },
}
