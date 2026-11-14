const solesEnteros = new Intl.NumberFormat('es-PE', { maximumFractionDigits: 0 })
const solesConCentimos = new Intl.NumberFormat('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export function enSoles(monto) {
  const signo = monto < 0 ? '−' : ''
  const absoluto = Math.abs(monto)
  const formato = Number.isInteger(absoluto) ? solesEnteros : solesConCentimos
  return `${signo}S/\u00a0${formato.format(absoluto)}`
}

const diaLargo = new Intl.DateTimeFormat('es-PE', { weekday: 'long', day: 'numeric', month: 'long' })
const diaCorto = new Intl.DateTimeFormat('es-PE', { day: 'numeric', month: 'short' })

function aFecha(fechaIso) {
  return new Date(`${fechaIso}T12:00:00`)
}

export function fechaLarga(fechaIso) {
  return diaLargo.format(aFecha(fechaIso))
}

export function fechaCorta(fechaIso) {
  return diaCorto.format(aFecha(fechaIso)).replace('.', '')
}

export function iniciales(nombre) {
  return nombre
    .split(/\s+/)
    .slice(0, 2)
    .map((palabra) => palabra[0].toUpperCase())
    .join('')
}

export function diasEntre(desdeIso, hastaIso) {
  return Math.round((aFecha(hastaIso) - aFecha(desdeIso)) / 86400000)
}
