// Regla de avisos acordada en estado.md (revisión A1), mientras el motor de eventos (MG-05) no tenga ruta en la API:
// riesgo a 3–7 días normal, a 1–2 urgente, a más de 7 sin aviso; máximo 3 por semana de lunes a domingo,
// con un lugar reservado para el de riesgo; un solo aviso por hueco (`riesgo-` + fecha del próximo ingreso).
import { diasEntre } from '../formato.js'

export const MAXIMO_POR_SEMANA = 3
export const DIAS_PARA_AVISAR = 7
const DIAS_URGENTE = 2
const PREFIJO_RIESGO = 'riesgo-'

// El día 0 (el rojo es hoy) también es urgente: el caso CP-SIS-28 lo prueba y no avisar sería peor.
export function urgenciaDeRiesgo(dias) {
  if (dias > DIAS_PARA_AVISAR) return null
  return dias <= DIAS_URGENTE ? 'urgente' : 'normal'
}

export function inicioDeSemana(fechaIso) {
  const d = new Date(`${fechaIso}T12:00:00`)
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7))
  return d.toISOString().slice(0, 10)
}

function avisoDeRiesgo(cliente, hoy) {
  const { riesgo, proximoIngreso } = cliente
  if (!riesgo || riesgo.hasta < hoy) return { aviso: null, lejano: null }
  const fecha = riesgo.desde < hoy ? hoy : riesgo.desde
  const dias = diasEntre(hoy, fecha)
  const urgencia = urgenciaDeRiesgo(dias)
  if (!urgencia) return { aviso: null, lejano: { fecha, dias } }
  return {
    lejano: null,
    aviso: {
      id: `${PREFIJO_RIESGO}${proximoIngreso.fecha}`,
      tipo: 'riesgo',
      urgencia,
      fecha,
      dias,
      impacto: riesgo.peorMonto,
      esperado: riesgo.esperado,
      peorFecha: riesgo.peorFecha,
      cobro: proximoIngreso,
      // El primer tip que la persona todavía no eligió; y si con todos sale del rojo, también se dice.
      tip: cliente.recomendaciones.find((r) => !cliente.elegidos.includes(r.id)),
      conTodos: cliente.conTodos.peorMonto >= 0 ? { ...cliente.conTodos, total: cliente.totalCambios } : null,
      accion: { texto: 'Ver cómo evitarlo', ruta: '/lucas/resumen#tips' },
    },
  }
}

// Solo avisan los pagos con algo que hacer (un tip que los pausa); los demás se ven en Qué viene sin gastar el tope.
function avisosDePagos(cliente, hoy) {
  return cliente.proximosPagos.flatMap((pago) => {
    const dias = diasEntre(hoy, pago.fecha)
    const tip = cliente.recomendaciones.find((r) => r.ajuste.pagosOmitidos?.includes(pago.id))
    if (!tip || dias < 0 || dias > DIAS_PARA_AVISAR) return []
    const suscripcion = cliente.suscripciones.find((s) => s.id === pago.id)
    return [
      {
        id: `pago-${pago.id}`,
        tipo: 'pago',
        urgencia: 'normal',
        fecha: pago.fecha,
        dias,
        impacto: -pago.monto,
        concepto: pago.concepto,
        uso: suscripcion?.uso,
        tip,
        accion: { texto: 'Ver el tip para pausarla', ruta: '/lucas/resumen#tips' },
      },
    ]
  })
}

function avisoDeIngreso(cliente, hoy) {
  const cobro = cliente.proximoIngreso
  const dias = diasEntre(hoy, cobro.fecha)
  if (dias < 0 || dias > DIAS_PARA_AVISAR) return []
  return [
    {
      id: `ingreso-${cobro.fecha}`,
      tipo: 'ingreso',
      urgencia: 'normal',
      fecha: cobro.fecha,
      dias,
      impacto: cobro.monto,
      concepto: cobro.concepto,
      apartado: cliente.apartado,
      accion: { texto: 'Ver cuánto puedes apartar', ruta: '/lucas/resumen#tips' },
    },
  ]
}

export function candidatos(cliente, hoy = cliente.hoy) {
  const { aviso, lejano } = avisoDeRiesgo(cliente, hoy)
  return {
    avisos: [...(aviso ? [aviso] : []), ...avisosDePagos(cliente, hoy), ...avisoDeIngreso(cliente, hoy)],
    riesgoLejano: lejano,
  }
}

const esRiesgo = (id) => id.startsWith(PREFIJO_RIESGO)

// `registro` guarda por semana los ids que ya se mostraron: un aviso ya mostrado sigue y no gasta otro lugar
// (el de riesgo, aunque cambien su fecha o su monto). Los demás entran por impacto en S/ mientras quede lugar,
// sin tocar nunca el lugar de un riesgo que todavía no se mostró.
export function armarBandeja(lista, registro = {}, hoy) {
  const semana = inicioDeSemana(hoy)
  const previos = registro[semana] ?? []
  const riesgo = lista.find((a) => a.tipo === 'riesgo')
  const otros = lista.filter((a) => a.tipo !== 'riesgo')

  const otrosPrevios = otros.filter((a) => previos.includes(a.id))
  const riesgoNuevo = riesgo && !previos.includes(riesgo.id) ? 1 : 0
  const lugaresOtros = Math.min(
    MAXIMO_POR_SEMANA - 1 - previos.filter((id) => !esRiesgo(id)).length,
    MAXIMO_POR_SEMANA - previos.length - riesgoNuevo,
  )
  const otrosNuevos = otros
    .filter((a) => !previos.includes(a.id))
    .sort((a, b) => Math.abs(b.impacto) - Math.abs(a.impacto))
    .slice(0, Math.max(0, lugaresOtros))

  const usados = previos.length + otrosNuevos.length
  const entraRiesgo = riesgo && (previos.includes(riesgo.id) || usados < MAXIMO_POR_SEMANA)
  const avisos = [...(entraRiesgo ? [riesgo] : []), ...[...otrosPrevios, ...otrosNuevos].sort((a, b) => a.dias - b.dias)]

  const ids = [...new Set([...previos, ...avisos.map((a) => a.id)])]
  return {
    avisos,
    semana,
    registro: { [semana]: ids },
    restantes: MAXIMO_POR_SEMANA - ids.length,
    fueraDelTope: lista.length - avisos.length,
  }
}
