// Sustituto del pronóstico (DI-06) y del recomendador (MG-04) hasta que la API devuelva cifras de la misma persona.
// Todas las cifras de las pantallas salen de aquí para que nunca se contradigan entre sí.

function sumarDias(fechaIso, dias) {
  const d = new Date(`${fechaIso}T12:00:00`)
  d.setDate(d.getDate() + dias)
  return d.toISOString().slice(0, 10)
}

function redondear(monto) {
  return Math.round(monto * 100) / 100
}

export function gastoVariableDiario(persona, frecuencias = {}) {
  const frecuentes = persona.gastosFrecuentes.reduce((total, g) => {
    const vecesMes = frecuencias[g.id] ?? g.vecesMes
    return total + (vecesMes * g.ticket) / 30
  }, 0)
  return persona.gastoBaseDiario + frecuentes
}

// La banda se abre con los días porque el gasto diario varía, y se ensancha más en cada cobro
// porque un independiente no sabe cuánto le pagarán sus clientes.
export function anchoBanda(persona, dia, fecha) {
  const porCobros = persona.ingresos.filter((i) => i.fecha <= fecha).reduce((s, i) => s + i.variacion, 0)
  return persona.banda.inicial + dia * persona.banda.porDia + porCobros
}

export function primerCobro(persona) {
  return persona.ingresos.reduce((a, b) => (a.fecha <= b.fecha ? a : b))
}

// Una meta mensual («4 veces al mes») llevada al tramo que falta hasta el cobro, que es lo que el tip pide.
export function vecesHastaCobro(persona, vecesMes) {
  const dias = (new Date(`${primerCobro(persona).fecha}T12:00:00`) - new Date(`${persona.hoy}T12:00:00`)) / 86400000
  return Math.round((vecesMes * dias) / 30)
}

export function simular(persona, { pagosOmitidos = [], frecuencias = {}, gastoDiario, pagosExtra = [] } = {}) {
  const diario = gastoDiario ?? gastoVariableDiario(persona, frecuencias)
  const puntos = []
  let saldo = persona.saldoHoy
  for (let i = 0; i <= persona.horizonteDias; i++) {
    const fecha = sumarDias(persona.hoy, i)
    if (i > 0) {
      const pagos = [...persona.pagos, ...pagosExtra]
        .filter((p) => p.fecha === fecha && !pagosOmitidos.includes(p.id))
        .reduce((s, p) => s + p.monto, 0)
      saldo -= diario + pagos
    }
    for (const cobro of persona.ingresos) if (cobro.fecha === fecha) saldo += cobro.monto
    const ancho = anchoBanda(persona, i, fecha)
    puntos.push({
      fecha,
      esperado: Math.round(saldo),
      banda: [Math.round(saldo - ancho), Math.round(saldo + ancho)],
    })
  }
  return puntos
}

// Solo importa el tramo hasta el primer cobro: después el riesgo cambia de mes.
export function peorDia(persona, puntos) {
  const antesDelIngreso = puntos.filter((p) => p.fecha < primerCobro(persona).fecha)
  return antesDelIngreso.reduce((peor, p) => (p.banda[0] < peor.banda[0] ? p : peor))
}

export function diasEnRojo(persona, puntos) {
  return puntos.filter((p) => p.fecha < primerCobro(persona).fecha && p.banda[0] < 0).map((p) => p.fecha)
}

// El mayor gasto diario con el que ni el peor caso queda bajo cero antes del ingreso.
export function gastoDiarioSeguro(persona, ajuste = {}) {
  let bajo = 0
  let alto = Math.max(gastoVariableDiario(persona) * 3, persona.saldoHoy)
  for (let i = 0; i < 40; i++) {
    const medio = (bajo + alto) / 2
    const puntos = simular(persona, { ...ajuste, gastoDiario: medio })
    if (peorDia(persona, puntos).banda[0] >= 0) bajo = medio
    else alto = medio
  }
  return Math.floor(bajo)
}

export function evaluarCambio(persona, cambio) {
  const antes = peorDia(persona, simular(persona))
  const despues = simular(persona, cambio.ajuste)
  const peorDespues = despues.find((p) => p.fecha === antes.fecha)
  return {
    ...cambio,
    fechaPeorDia: antes.fecha,
    peorAntes: antes.banda[0],
    peorDespues: peorDespues.banda[0],
    mejora: redondear(peorDespues.banda[0] - antes.banda[0]),
  }
}

export function ajusteDe(cambios) {
  return cambios.reduce(
    (acum, c) => ({
      pagosOmitidos: [...acum.pagosOmitidos, ...(c.ajuste.pagosOmitidos ?? [])],
      frecuencias: { ...acum.frecuencias, ...(c.ajuste.frecuencias ?? {}) },
    }),
    { pagosOmitidos: [], frecuencias: {} },
  )
}

// Un gasto puntual mañana: cómo cambia el peor día y cuánto conviene gastar al día después.
export function evaluarGastoExtra(persona, monto, ajuste = {}) {
  const extra = { ...ajuste, pagosExtra: [...(ajuste.pagosExtra ?? []), { id: 'extra', fecha: sumarDias(persona.hoy, 1), monto }] }
  const antes = peorDia(persona, simular(persona, ajuste))
  const despues = peorDia(persona, simular(persona, extra))
  return {
    monto,
    peorAntes: antes.banda[0],
    peorDespues: despues.banda[0],
    fechaPeorDia: despues.fecha,
    gastoDiarioSeguro: gastoDiarioSeguro(persona, extra),
  }
}

// Apartar el día del cobro solo se propone si el peor caso del resto del horizonte sigue sobre cero.
export function apartadoSinRojo(persona, monto, ajuste = {}) {
  const cobro = primerCobro(persona).fecha
  const extra = [...(ajuste.pagosExtra ?? []), { id: 'apartado', fecha: cobro, monto }]
  const puntos = simular(persona, { ...ajuste, pagosExtra: extra })
  const despuesDelCobro = puntos.filter((p) => p.fecha >= cobro)
  return Math.min(...despuesDelCobro.map((p) => p.banda[0])) >= 0
}

// El mayor apartado en múltiplos de S/ 10 que no deja en rojo ni en el peor caso; 0 si no hay margen.
export function apartadoMaximo(persona, ajuste = {}) {
  let monto = 0
  while (monto < persona.saldoHoy && apartadoSinRojo(persona, monto + 10, ajuste)) monto += 10
  return monto
}
