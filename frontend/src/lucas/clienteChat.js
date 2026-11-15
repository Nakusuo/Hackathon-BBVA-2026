// Chat contra POST /api/v1/chat (propuesta MC-06). Sin VITE_CHAT_AGENTE=si responde solo con plantillas.
import { ErrorApi } from '../api/http.js'
import { preguntarAgente } from '../api/lucas.js'
import { enSoles } from '../formato.js'
import { contextoDe, esPedidoDeOperacion, interpretar, responder as responderConPlantilla } from './respuestas.js'

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

// Solo se ofrece guardar una meta con forma completa; si viene rota se ignora y el chat sigue igual.
function leerPropuesta(p) {
  const ok = p && typeof p.name === 'string' && p.name.trim() && Number.isFinite(p.target) && p.target > 0 && /^\d{4}-\d{2}-\d{2}$/.test(p.date ?? '')
  return ok ? { nombre: p.name.trim().slice(0, 40), objetivo: p.target, fecha: p.date } : null
}

const MAX_OPCIONES = 4

// Botones de respuesta rápida del agente: solo los que traen texto y pregunta; el resto se descarta.
function leerOpciones(opciones) {
  if (!Array.isArray(opciones)) return []
  return opciones
    .filter((o) => o && typeof o.label === 'string' && o.label.trim() && typeof o.question === 'string' && o.question.trim())
    .slice(0, MAX_OPCIONES)
    .map((o, i) => ({ id: String(o.id ?? i), texto: o.label.trim(), pregunta: o.question.trim().slice(0, LARGO_MAXIMO) }))
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
    propuesta: leerPropuesta(cuerpo.goal_proposal),
    opciones: leerOpciones(cuerpo.options),
  }
}

export async function preguntarALucas(texto, { cliente, persona, conversacion, activo, previas = [], ...opcionesApi }) {
  // `previas`: lo que la persona escribió antes, para seguir una meta que dio en dos mensajes.
  const plantilla = (aviso = null) => ({
    origen: 'plantilla',
    verificado: false,
    fuentes: [],
    aviso,
    ...responderConPlantilla(texto, cliente, persona, previas),
  })
  // Los pedidos de operación o inversión se cortan aquí: no hace falta mandarlos a ningún servidor.
  if (!activo || esPedidoDeOperacion(texto)) return plantilla()
  // Las metas las arma el motor de la pantalla (lo que apartas y con qué tips): el agente las calcularía con otra persona.
  if (['meta', 'aporte'].includes(interpretar(texto, contextoDe(previas, cliente), cliente).intencion)) return plantilla()

  let cuerpo
  try {
    // El agente responde por la persona elegida: la API traduce su id al cliente sintético de la base.
    cuerpo = await preguntarAgente(texto.slice(0, LARGO_MAXIMO), { id: cliente.personaId, conversacion, ...opcionesApi })
  } catch (error) {
    if (!(error instanceof ErrorApi)) throw error
    const aviso = { tiempo: AVISOS.demora, formato: AVISOS.ilegible }[error.tipo] ?? AVISOS.sinConexion
    return plantilla(aviso)
  }
  if (!esRespuestaValida(cuerpo)) return plantilla(AVISOS.ilegible)
  if (cuerpo.verified !== true) {
    return { ...plantilla(AVISOS.sinVerificar), conversacion: cuerpo.conversation_id ?? null }
  }
  return desdeAgente(cuerpo)
}
