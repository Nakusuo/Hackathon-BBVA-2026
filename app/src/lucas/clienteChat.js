// Chat contra POST /api/v1/chat (propuesta MC-06). Sin VITE_CHAT_AGENTE=si responde solo con plantillas.
import { ErrorApi } from '../api/http.js'
import { preguntarAgente } from '../api/lucas.js'
import { enSoles } from '../formato.js'
import { esPedidoDeOperacion, responder as responderConPlantilla } from './respuestas.js'

export const LARGO_MAXIMO = 500

export const AVISOS = {
  sinConexion: 'No pude hablar con el agente de Lucas. Te respondo con mis cálculos de siempre.',
  demora: 'El agente de Lucas tardó demasiado. Te respondo con mis cálculos de siempre.',
  ilegible: 'El agente de Lucas respondió algo que no pude leer. Te respondo con mis cálculos de siempre.',
  sinVerificar: 'El agente de Lucas no pudo comprobar sus cifras. Te respondo con mis cálculos de siempre.',
}

function formatoCifra(c) {
  if (typeof c.value !== 'number') return String(c.text ?? '')
  if (c.unit === 'PEN') return enSoles(c.value)
  if (c.unit === 'percent') return `${c.value} %`
  if (c.unit === 'months') return `${c.value} meses`
  if (c.unit === 'days') return `${c.value} días`
  // Sin `unit`, un texto con «S/» se rehace con enSoles para que el signo sea el mismo «−» de la app.
  if (typeof c.text === 'string' && c.text.includes('S/')) return enSoles(c.value)
  return c.text ? String(c.text) : String(c.value)
}

// Solo se enlaza lo que es http(s): una fuente nunca debe poder inyectar `javascript:`.
function enlaceSeguro(url) {
  return typeof url === 'string' && /^https?:\/\//i.test(url) ? url : null
}

export function esRespuestaValida(cuerpo) {
  return Boolean(cuerpo) && typeof cuerpo.answer === 'string' && cuerpo.answer.trim() !== ''
}

// Solo se llama con verified === true: un texto del LLM sin verificar nunca llega al usuario.
export function desdeAgente(cuerpo) {
  const cifras = Array.isArray(cuerpo.figures) ? cuerpo.figures : []
  const fuentes = Array.isArray(cuerpo.sources) ? cuerpo.sources : []
  return {
    origen: 'agente',
    texto: cuerpo.answer.trim(),
    verificado: true,
    conversacion: typeof cuerpo.conversation_id === 'string' ? cuerpo.conversation_id : null,
    cifras: cifras
      .filter((c) => c && (c.label || c.etiqueta))
      .map((c) => ({ etiqueta: String(c.label ?? c.etiqueta), valor: formatoCifra(c) })),
    fuentes: fuentes
      .filter((f) => f && (f.title || f.titulo))
      .map((f, i) => ({
        id: String(f.id ?? i),
        titulo: String(f.title ?? f.titulo),
        enlace: enlaceSeguro(f.url ?? f.enlace),
      })),
    aviso: null,
  }
}

function plantilla(texto, cliente, persona, aviso = null) {
  return { origen: 'plantilla', verificado: false, fuentes: [], aviso, ...responderConPlantilla(texto, cliente, persona) }
}

export async function preguntarALucas(texto, { cliente, persona, conversacion, activo, ...opcionesApi }) {
  // Los pedidos de operación o inversión se cortan aquí: no hace falta mandarlos a ningún servidor.
  if (!activo || esPedidoDeOperacion(texto)) return plantilla(texto, cliente, persona)

  let cuerpo
  try {
    cuerpo = await preguntarAgente(texto.slice(0, LARGO_MAXIMO), { conversacion, ...opcionesApi })
  } catch (error) {
    if (!(error instanceof ErrorApi)) throw error
    const aviso = { tiempo: AVISOS.demora, formato: AVISOS.ilegible }[error.tipo] ?? AVISOS.sinConexion
    return plantilla(texto, cliente, persona, aviso)
  }
  if (!esRespuestaValida(cuerpo)) return plantilla(texto, cliente, persona, AVISOS.ilegible)
  if (cuerpo.verified !== true) {
    return { ...plantilla(texto, cliente, persona, AVISOS.sinVerificar), conversacion: cuerpo.conversation_id ?? null }
  }
  return desdeAgente(cuerpo)
}
