// Persona sintética de la demo. Se reemplaza por la API cuando exista el contrato (MG-01).
import {
  apartadoSinRojo,
  diasEnRojo,
  evaluarCambio,
  evaluarTodos,
  gastoDiarioSeguro,
  gastoVariableDiario,
  peorDia,
  simular,
} from './motor.js'

export const persona = {
  hoy: '2026-11-14',
  horizonteDias: 30,
  saldoHoy: 1240,
  ingreso: { fecha: '2026-11-30', monto: 2600, tipo: 'Recibo por honorarios', minimo6m: 1900, maximo6m: 3400 },
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

const CAMBIOS = [
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
  { id: 'm5', fecha: '2026-11-10', concepto: 'Transferencia recibida', monto: 350, categoria: 'ingreso' },
]

const APARTADO_PROPUESTO = 150

const pronostico = simular(persona)
const peor = peorDia(persona, pronostico)
const rojo = diasEnRojo(persona, pronostico)
const recomendaciones = CAMBIOS.map((c) => evaluarCambio(persona, c)).sort((a, b) => b.mejora - a.mejora)
const conTodos = evaluarTodos(persona, CAMBIOS)
const gastoDiarioActual = Math.round(gastoVariableDiario(persona))

const totalPorCategoria = { ...persona.gastoBasePorCategoria, suscripciones: 0 }
for (const g of persona.gastosFrecuentes) {
  totalPorCategoria[g.categoria] = (totalPorCategoria[g.categoria] ?? 0) + g.vecesMes * g.ticket
}
for (const s of persona.suscripciones) totalPorCategoria.suscripciones += s.monto

const cuotasMes = persona.pagos.filter((p) => p.deuda).reduce((s, p) => s + p.monto, 0)
const pesoDeudas = Math.round((cuotasMes / persona.ingreso.monto) * 100)

// Mientras no exista el modelo de salud (DI-07), el puntaje de deudas baja en línea recta con el peso de las cuotas.
const componentesSalud = [
  { nombre: 'Colchón', valor: 35, explicacion: 'Cubre 2 semanas de gastos; lo sano son 3 meses.' },
  {
    nombre: 'Deudas',
    valor: Math.max(0, 100 - pesoDeudas),
    explicacion: `Tus cuotas son el ${pesoDeudas} % de lo que cobras.`,
  },
  { nombre: 'Regularidad del ingreso', valor: 48, explicacion: 'Tu cobro cambia mucho de un mes a otro.' },
  { nombre: 'Control del gasto', valor: 71, explicacion: 'Gastaste menos de lo que entró en 4 de 6 meses.' },
]

const delivery = persona.gastosFrecuentes.find((g) => g.id === 'delivery')
const cafe = persona.gastosFrecuentes.find((g) => g.id === 'cafe')

export const cliente = {
  hoy: persona.hoy,
  saldoHoy: persona.saldoHoy,
  cuenta: { nombre: 'Cuenta sueldo', terminacion: '0001' },
  tarjeta: { nombre: 'Tarjeta de crédito', terminacion: '0002', pagoMes: 950, vence: '2026-12-01' },
  movimientosRecientes: MOVIMIENTOS_RECIENTES,
  proximoIngreso: persona.ingreso,
  gastoDiarioActual,
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
  aprendido: [
    {
      id: 'cobro',
      dato: `Cobras una vez al mes, a fin de mes, por ${persona.ingreso.tipo.toLowerCase()}.`,
      fuente: 'Tus últimos 6 cobros',
    },
    {
      id: 'variacion',
      dato: `Tu cobro va de S/ ${persona.ingreso.minimo6m.toLocaleString('es-PE')} a S/ ${persona.ingreso.maximo6m.toLocaleString('es-PE')}.`,
      fuente: 'Últimos 6 meses',
    },
    {
      id: 'ritmo',
      dato: `Fuera de tus pagos fijos gastas unos S/ ${gastoDiarioActual} al día.`,
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
  conTodos: { peorFecha: conTodos.peor.fecha, peorMonto: conTodos.peor.banda[0], diasEnRojo: conTodos.diasEnRojo.length },
  apartado: apartadoSinRojo(persona, APARTADO_PROPUESTO) ? { monto: APARTADO_PROPUESTO, cobros: 3 } : null,
}

if (cliente.apartado) cliente.apartado.total = cliente.apartado.monto * cliente.apartado.cobros
