// Personas sintéticas de la demo. Comparten fecha y motor; solo cambian sus datos.
// El arquetipo sirve para elegir a quién mostrar, nunca entra al cálculo (reglas de negocio).

const miles = (n) => `S/ ${n.toLocaleString('es-PE')}`

const independiente = {
  id: 'independiente',
  nombre: 'Independiente',
  descripcion: 'Recibo por honorarios: cobra de dos clientes y ninguno paga siempre lo mismo.',
  persona: {
    hoy: '2026-11-14',
    horizonteDias: 30,
    saldoHoy: 1240,
    tipoIngreso: 'Recibo por honorarios',
    ingresoMensual: 2600,
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
  },
  tarjeta: { pagoMes: 950, vence: '2026-12-01' },
  categorias: [
    { id: 'comida', nombre: 'Comida y delivery', promedio3m: 380, ejemplo: 'Supermercado y RapiFood' },
    { id: 'transporte', nombre: 'Transporte', promedio3m: 175, ejemplo: 'Bus y taxi por aplicativo' },
    { id: 'salidas', nombre: 'Salidas', promedio3m: 90, ejemplo: 'Restaurantes y reuniones' },
    { id: 'hormiga', nombre: 'Gasto hormiga', promedio3m: 80, ejemplo: 'Café y snacks' },
    { id: 'suscripciones', nombre: 'Suscripciones', promedio3m: 61.8, ejemplo: 'StreamFlix y MusiKa Plus' },
    { id: 'entretenimiento', nombre: 'Entretenimiento', promedio3m: 55, ejemplo: 'Cine y juegos' },
    { id: 'otros', nombre: 'Otros', promedio3m: 45, ejemplo: 'Farmacia y regalos' },
  ],
  cambios: [
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
  ],
  movimientosRecientes: [
    { id: 'm1', fecha: '2026-11-13', concepto: 'RapiFood', monto: -12.4, categoria: 'comida' },
    { id: 'm2', fecha: '2026-11-13', concepto: 'Cafetería La Esquina', monto: -5.3, categoria: 'hormiga' },
    { id: 'm3', fecha: '2026-11-12', concepto: 'Supermercado El Ahorro', monto: -86.5, categoria: 'comida' },
    { id: 'm4', fecha: '2026-11-11', concepto: 'Taxi por aplicativo', monto: -14, categoria: 'transporte' },
    { id: 'm5', fecha: '2026-11-10', concepto: 'Cobro de un proyecto aparte', monto: 350, categoria: 'ingreso' },
  ],
  salud: [
    { nombre: 'Colchón', valor: 35, explicacion: 'Cubre 2 semanas de gastos; lo sano son 3 meses.' },
    { nombre: 'Regularidad del ingreso', valor: 48, explicacion: 'Tus cobros cambian mucho de un mes a otro.' },
    { nombre: 'Control del gasto', valor: 71, explicacion: 'Gastaste menos de lo que entró en 4 de 6 meses.' },
  ],
  aprendido: (p, veces) => ({
    cobro: `Cobras de ${p.ingresos.length} clientes por ${p.tipoIngreso.toLowerCase()}: el principal a fin de mes y otro a mitad de mes.`,
    cobroFuente: 'Tus últimos 6 meses de cobros',
    variacion: `En un mes cobras entre ${miles(p.rangoMensual6m.minimo)} y ${miles(p.rangoMensual6m.maximo)}.`,
    habitos: `Pides delivery ${veces.delivery} veces al mes y vas por café ${veces.cafe} veces.`,
  }),
}

// Nov 15 de 2026 cae domingo: la quincena se adelantó al viernes 13 y ya está en el saldo.
const formal = {
  id: 'formal',
  nombre: 'Formal con quincena',
  descripcion: 'Sueldo fijo el 15 y a fin de mes, con gratificación en julio y diciembre.',
  persona: {
    hoy: '2026-11-14',
    horizonteDias: 30,
    saldoHoy: 1610,
    tipoIngreso: 'Sueldo por quincena',
    // El horizonte de 30 días solo ve una quincena; el peso de las cuotas se mide contra el mes completo.
    ingresoMensual: 2600,
    ingresos: [
      { id: 'quincena-fin', fecha: '2026-11-30', monto: 1300, variacion: 0, concepto: 'Quincena de tu empleador' },
    ],
    gastoBaseDiario: 22,
    banda: { inicial: 10, porDia: 3 },
    pagos: [
      { id: 'alquiler', fecha: '2026-11-16', concepto: 'Alquiler de departamento', monto: 600 },
      { id: 'luz-agua', fecha: '2026-11-20', concepto: 'Luz y agua', monto: 95 },
      { id: 'fitzona', fecha: '2026-11-22', concepto: 'Gimnasio FitZona', monto: 89 },
      { id: 'streamflix', fecha: '2026-11-24', concepto: 'StreamFlix', monto: 39.9 },
      { id: 'tarjeta', fecha: '2026-11-28', concepto: 'Pago mínimo de tarjeta de crédito', monto: 260 },
      { id: 'prestamo', fecha: '2026-12-02', concepto: 'Cuota préstamo personal', monto: 180, cuota: true },
      { id: 'internet', fecha: '2026-12-05', concepto: 'Internet y celular', monto: 120 },
    ],
    gastosFrecuentes: [
      { id: 'delivery', comercio: 'RapiFood', vecesMes: 12, ticket: 15, categoria: 'comida' },
      { id: 'taxi', comercio: 'Taxi por aplicativo', vecesMes: 14, ticket: 11, categoria: 'transporte' },
    ],
    // Reparto de los S/ 22 diarios de gasto base en los últimos 30 días (22 × 30 = 660).
    gastoBasePorCategoria: { comida: 280, transporte: 120, salidas: 140, entretenimiento: 60, otros: 60 },
    suscripciones: [
      { id: 'fitzona', comercio: 'Gimnasio FitZona', monto: 89, dia: 22, uso: 'Fuiste 2 veces este mes' },
      { id: 'streamflix', comercio: 'StreamFlix', monto: 39.9, dia: 24, uso: 'La usaste 14 veces este mes' },
    ],
  },
  tarjeta: { pagoMes: 260, vence: '2026-11-28' },
  categorias: [
    { id: 'comida', nombre: 'Comida y delivery', promedio3m: 430, ejemplo: 'Supermercado y RapiFood' },
    { id: 'transporte', nombre: 'Transporte', promedio3m: 250, ejemplo: 'Bus y taxi por aplicativo' },
    { id: 'salidas', nombre: 'Salidas', promedio3m: 150, ejemplo: 'Restaurantes y reuniones' },
    { id: 'suscripciones', nombre: 'Suscripciones', promedio3m: 128.9, ejemplo: 'FitZona y StreamFlix' },
    { id: 'entretenimiento', nombre: 'Entretenimiento', promedio3m: 55, ejemplo: 'Cine y juegos' },
    { id: 'otros', nombre: 'Otros', promedio3m: 65, ejemplo: 'Farmacia y regalos' },
  ],
  cambios: [
    {
      id: 'fitzona',
      titulo: 'Pausa FitZona este mes',
      facilidad: 'Fácil',
      porque: 'Fuiste 2 veces este mes y se cobra el 22, una semana antes de tu quincena.',
      ajuste: { pagosOmitidos: ['fitzona'] },
    },
    {
      id: 'delivery',
      titulo: 'Pide RapiFood una vez por semana hasta el 30',
      facilidad: 'Esfuerzo medio',
      porque: 'Este mes pediste 12 veces, a unos S/ 15 por pedido. Bajar a 4 al mes deja más saldo antes de la quincena.',
      ajuste: { frecuencias: { delivery: 4 } },
    },
    {
      id: 'taxi',
      titulo: 'Cambia 6 taxis del mes por bus',
      facilidad: 'Esfuerzo medio',
      porque: 'Este mes tomaste 14 taxis por aplicativo, a unos S/ 11 cada uno.',
      ajuste: { frecuencias: { taxi: 8 } },
    },
  ],
  movimientosRecientes: [
    { id: 'm1', fecha: '2026-11-13', concepto: 'Quincena de tu empleador', monto: 1300, categoria: 'ingreso' },
    { id: 'm2', fecha: '2026-11-13', concepto: 'RapiFood', monto: -15, categoria: 'comida' },
    { id: 'm3', fecha: '2026-11-12', concepto: 'Taxi por aplicativo', monto: -11, categoria: 'transporte' },
    { id: 'm4', fecha: '2026-11-12', concepto: 'Supermercado El Ahorro', monto: -92.3, categoria: 'comida' },
    { id: 'm5', fecha: '2026-11-11', concepto: 'Menú del día', monto: -14, categoria: 'comida' },
  ],
  salud: [
    { nombre: 'Colchón', valor: 40, explicacion: 'Cubre 3 semanas de gastos; lo sano son 3 meses.' },
    { nombre: 'Regularidad del ingreso', valor: 92, explicacion: 'Cobras lo mismo cada quincena.' },
    { nombre: 'Control del gasto', valor: 52, explicacion: 'Gastaste menos de lo que entró en 3 de 6 meses.' },
  ],
  aprendido: (p, veces) => ({
    cobro: 'Cobras por quincena, el 15 y a fin de mes. Si cae en fin de semana, te pagan el viernes antes.',
    cobroFuente: 'Tus últimos 12 meses de sueldos',
    variacion: `Cada quincena cobras ${miles(p.ingresos[0].monto)}; en julio y diciembre se suma la gratificación.`,
    habitos: `Pides delivery ${veces.delivery} veces al mes y tomas ${veces.taxi} taxis por aplicativo.`,
  }),
}

export const PERSONAS = [independiente, formal]
export const PERSONA_INICIAL = independiente.id

export function personaPorId(id) {
  return PERSONAS.find((p) => p.id === id) ?? independiente
}
