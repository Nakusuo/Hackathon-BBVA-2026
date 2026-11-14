// Cliente de POST /api/v1/chat (propuesta MC-06). Sin VITE_LUCAS_API el chat responde solo con plantillas.
import { enSoles } from '../formato.js'
import { esPedidoDeOperacion, responder as responderConPlantilla } from './respuestas.js'

// Es el mismo cliente sintético de las plantillas locales (src/mocks/cliente.js), así ambas respuestas hablan de la misma persona.
export const CLIENTE_ID = 'demo-001'
export const LARGO_MAXIMO = 500
// La meta del agente es p95 < 8 s con LLM local; pasado esto ya no vale la pena esperar.
const ESPERA_MS = 12000

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

class RespuestaIlegible extends Error {}

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

export async function preguntarALucas(
  texto,
  { cliente, persona, conversacion, base, fetchImpl = fetch, esperaMs = ESPERA_MS },
) {
  // Los pedidos de operación o inversión se cortan aquí: no hace falta mandarlos a ningún servidor.
  if (!base || esPedidoDeOperacion(texto)) return plantilla(texto, cliente, persona)

  const control = new AbortController()
  const reloj = setTimeout(() => control.abort(), esperaMs)
  try {
    const r = await fetchImpl(`${base.replace(/\/$/, '')}/api/v1/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_id: CLIENTE_ID,
        message: texto.slice(0, LARGO_MAXIMO),
        ...(conversacion ? { conversation_id: conversacion } : {}),
      }),
      signal: control.signal,
    })
    if (!r.ok) throw new Error(`HTTP ${r.status}`)
    const cuerpo = await r.json().catch(() => null)
    if (!esRespuestaValida(cuerpo)) throw new RespuestaIlegible()
    if (cuerpo.verified !== true) {
      return { ...plantilla(texto, cliente, persona, AVISOS.sinVerificar), conversacion: cuerpo.conversation_id ?? null }
    }
    return desdeAgente(cuerpo)
  } catch (e) {
    const aviso = e instanceof RespuestaIlegible ? AVISOS.ilegible : e?.name === 'AbortError' ? AVISOS.demora : AVISOS.sinConexion
    return plantilla(texto, cliente, persona, aviso)
  } finally {
    clearTimeout(reloj)
  }
}
