import { enSoles, fechaCorta } from '../formato.js'
import { sumarDias } from '../motor/motor.js'
import { fechaValida, leerMonto } from './planificar.js'

export const TOPE_META = 1000000
const MAX_NOMBRE = 40
const MAX_ANIOS = 5
// Más allá de unos 3 meses el pronóstico de 30 días ya no sostiene una fecha: la confianza baja.
const DIAS_CONFIANZA_MEDIA = 90
export const ESTADOS = ['creada', 'en curso', 'cumplida']

function aDecenaAbajo(monto) {
  return Math.floor(monto / 10) * 10
}

function aDecenaArriba(monto) {
  return Math.ceil(monto / 10) * 10
}

function iso(anio, mes, dia) {
  return new Date(Date.UTC(anio, mes, dia)).toISOString().slice(0, 10)
}

// Se aparta el día del cobro principal, cada mes. Si el mes es más corto (febrero), el último día.
function apartadoNumero(primeraIso, n) {
  const [anio, mes, dia] = primeraIso.split('-').map(Number)
  const ultimoDelMes = new Date(Date.UTC(anio, mes + n, 0)).getUTCDate()
  return iso(anio, mes - 1 + n, Math.min(dia, ultimoDelMes))
}

export function fechasDeApartado(primeraIso, hastaIso) {
  const fechas = []
  for (let n = 0; apartadoNumero(primeraIso, n) <= hastaIso; n++) fechas.push(apartadoNumero(primeraIso, n))
  return fechas
}

export function finDeAnio(hoyIso) {
  return `${hoyIso.slice(0, 4)}-12-31`
}

// Lo que se puede apartar sin rojo se reparte entre las metas abiertas, en el orden en que se crearon. Si no
// alcanza para S/ 10 a cada una, reciben aporte solo las primeras y las demás esperan.
export function repartoDelApartado(apartado, metas) {
  const abiertas = metas.filter((m) => estadoDe(m) !== 'cumplida')
  const conAporte = Math.min(abiertas.length, Math.floor(apartado / 10))
  const parte = conAporte ? aDecenaAbajo(apartado / conAporte) : 0
  const porMeta = Object.fromEntries(abiertas.map((m, i) => [m.id, i < conAporte ? parte : 0]))
  return { porMeta, abiertas: abiertas.length, conAporte, parte }
}

// `apartado` sale del motor: es el mayor monto que no deja en rojo ni en el peor caso del pronóstico.
// Cada «Ya aparté» cuenta como el apartado de un cobro: el plan sigue con los cobros que faltan.
export function planDeMeta(meta, { apartado, primerApartado, finPronostico, hoy }) {
  const hechos = meta.aportes ?? 0
  const pendientes = (hasta) => fechasDeApartado(primerApartado, hasta).slice(hechos)
  const falta = Math.max(0, meta.objetivo - meta.ahorrado)
  const fechas = pendientes(meta.fecha)
  const veces = fechas.length
  const necesario = veces ? aDecenaArriba(falta / veces) : falta
  // Sin cobros antes de la fecha no hay nada que apartar para ella; el ritmo sirve para decir cuándo llegaría.
  const ritmo = Math.min(apartado, falta)
  const aporte = veces ? Math.min(necesario, ritmo) : 0
  const juntado = (n) => Math.min(meta.objetivo, meta.ahorrado + aporte * n)
  const alcanza = veces > 0 && falta > 0 && aporte * veces >= falta
  // Si alcanza, se llega al paso del aporte que se muestra; si no, al mayor ritmo posible.
  const paso = alcanza ? aporte : ritmo
  const llegaEl = paso > 0 ? apartadoNumero(primerApartado, hechos + Math.ceil(falta / paso) - 1) : null
  const ultima = alcanza ? fechas.at(-1) : (llegaEl ?? meta.fecha)
  let confianza = 'media'
  // Solo el primer apartado cae dentro del pronóstico de 30 días; los demás suponen que los meses se repiten.
  if (veces && fechas.every((f) => f <= finPronostico)) confianza = 'alta'
  else if (ultima > sumarDias(hoy, DIAS_CONFIANZA_MEDIA)) confianza = 'baja'
  return {
    falta,
    veces,
    necesario,
    aporte,
    alcanza,
    sinCobros: veces === 0 && falta > 0,
    proyectado: juntado(veces),
    alFinDeAnio: juntado(pendientes(finDeAnio(hoy)).length),
    llegaEl,
    confianza,
    // Hacia abajo: 996 de 1 000 no puede mostrarse como 100 % mientras la meta sigue en curso.
    avance: Math.min(100, Math.floor((meta.ahorrado / meta.objetivo) * 100)),
  }
}

// Lo guardado en el navegador puede venir de otra versión o estar roto: solo se usa si tiene la forma esperada.
export function esMetaValida(m) {
  return (
    m !== null &&
    typeof m === 'object' &&
    typeof m.id === 'string' &&
    typeof m.nombre === 'string' &&
    Number.isFinite(m.objetivo) &&
    m.objetivo > 0 &&
    Number.isFinite(m.ahorrado) &&
    m.ahorrado >= 0 &&
    fechaValida(m.fecha) &&
    Number.isInteger(m.aportes ?? 0) &&
    Array.isArray(m.historial) &&
    m.historial.length > 0 &&
    m.historial.every((e) => ESTADOS.includes(e))
  )
}

export function estadoDe(meta) {
  return meta.historial.at(-1)
}

// Los estados avanzan de uno en uno: una meta que se cumple de golpe pasa igual por «en curso».
function avanzar(historial, ahorrado, objetivo) {
  const meta = ahorrado >= objetivo ? 'cumplida' : ahorrado > 0 ? 'en curso' : 'creada'
  const siguiente = [...historial]
  while (ESTADOS.indexOf(siguiente.at(-1)) < ESTADOS.indexOf(meta)) {
    siguiente.push(ESTADOS[ESTADOS.indexOf(siguiente.at(-1)) + 1])
  }
  return siguiente
}

export function crearMeta(datos, id) {
  return { id, ...datos, aportes: 0, historial: avanzar(['creada'], datos.ahorrado, datos.objetivo) }
}

export function aportar(meta, monto) {
  const ahorrado = Math.round((meta.ahorrado + monto) * 100) / 100
  return {
    ...meta,
    ahorrado,
    aportes: (meta.aportes ?? 0) + 1,
    historial: avanzar(meta.historial, ahorrado, meta.objetivo),
  }
}

export function validarMeta(borrador, { hoy, primerApartado }) {
  const errores = {}
  const nombre = borrador.nombre.trim()
  if (!nombre) errores.nombre = 'Ponle un nombre corto, por ejemplo «Colchón para enero».'
  else if (nombre.length > MAX_NOMBRE) errores.nombre = `Usa hasta ${MAX_NOMBRE} letras.`

  const objetivo = leerMonto(borrador.objetivo, TOPE_META)
  if (objetivo.error) errores.objetivo = objetivo.error

  const ahorrado = leerMonto(borrador.ahorrado, TOPE_META, { permiteCero: true })
  if (ahorrado.error) errores.ahorrado = ahorrado.error
  if (!errores.ahorrado && !errores.objetivo && ahorrado.monto >= objetivo.monto) {
    errores.ahorrado = `Debe ser menor que la meta de ${enSoles(objetivo.monto)}.`
  }

  const tope = `${Number(hoy.slice(0, 4)) + MAX_ANIOS}-12-31`
  if (!fechaValida(borrador.fecha)) errores.fecha = 'Elige una fecha.'
  else if (borrador.fecha < primerApartado) {
    errores.fecha = `Tu próximo cobro es el ${fechaCorta(primerApartado)}: elige desde ese día.`
  } else if (borrador.fecha > tope) errores.fecha = `Elige una fecha hasta el ${fechaCorta(tope)} de ${tope.slice(0, 4)}.`

  if (Object.keys(errores).length) return { errores }
  return { datos: { nombre, objetivo: objetivo.monto, ahorrado: ahorrado.monto, fecha: borrador.fecha } }
}
