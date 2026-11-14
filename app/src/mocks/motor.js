// Sustituto del pronóstico (DI-06) y del recomendador (MG-04) mientras no exista la API (MG-01).
// Todas las cifras de las pantallas salen de aquí para que nunca se contradigan entre sí.

export function sumarDias(fechaIso, dias) {
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

// La banda se abre con los días porque el ingreso de un independiente es incierto.
export function anchoBanda(persona, dia) {
  return persona.banda.inicial + dia * persona.banda.porDia
}

export function simular(persona, { pagosOmitidos = [], frecuencias = {}, gastoDiario } = {}) {
  const diario = gastoDiario ?? gastoVariableDiario(persona, frecuencias)
  const puntos = []
  let saldo = persona.saldoHoy
  for (let i = 0; i <= persona.horizonteDias; i++) {
    const fecha = sumarDias(persona.hoy, i)
    if (i > 0) {
      const pagos = persona.pagos
        .filter((p) => p.fecha === fecha && !pagosOmitidos.includes(p.id))
        .reduce((s, p) => s + p.monto, 0)
      saldo -= diario + pagos
    }
    if (fecha === persona.ingreso.fecha) saldo += persona.ingreso.monto
    const ancho = anchoBanda(persona, i)
    puntos.push({
      fecha,
      esperado: Math.round(saldo),
      banda: [Math.round(saldo - ancho), Math.round(saldo + ancho)],
    })
  }
  return puntos
}

// Solo importa el tramo hasta el ingreso: después del cobro el riesgo cambia de mes.
export function peorDia(persona, puntos) {
  const antesDelIngreso = puntos.filter((p) => p.fecha < persona.ingreso.fecha)
  return antesDelIngreso.reduce((peor, p) => (p.banda[0] < peor.banda[0] ? p : peor))
}

export function diasEnRojo(persona, puntos) {
  return puntos.filter((p) => p.fecha < persona.ingreso.fecha && p.banda[0] < 0).map((p) => p.fecha)
}

// El mayor gasto diario con el que ni el peor caso queda bajo cero antes del ingreso.
export function gastoDiarioSeguro(persona) {
  let bajo = 0
  let alto = gastoVariableDiario(persona) * 3
  for (let i = 0; i < 40; i++) {
    const medio = (bajo + alto) / 2
    const puntos = simular(persona, { gastoDiario: medio })
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

export function evaluarTodos(persona, cambios) {
  const ajusteConjunto = cambios.reduce(
    (acum, c) => ({
      pagosOmitidos: [...acum.pagosOmitidos, ...(c.ajuste.pagosOmitidos ?? [])],
      frecuencias: { ...acum.frecuencias, ...(c.ajuste.frecuencias ?? {}) },
    }),
    { pagosOmitidos: [], frecuencias: {} },
  )
  const puntos = simular(persona, ajusteConjunto)
  return { peor: peorDia(persona, puntos), diasEnRojo: diasEnRojo(persona, puntos) }
}
