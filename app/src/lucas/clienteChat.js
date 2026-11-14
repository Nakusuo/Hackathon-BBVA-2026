// Cliente de POST /api/v1/chat (propuesta MC-06). Sin VITE_LUCAS_API el chat responde solo con plantillas.
import { enSoles } from '../formato.js'
import { esPedidoDeOperacion, responder as responderConPlantilla } from './respuestas.js'

export const CLIENTE_ID = 'demo-001'
export const LARGO_MAXIMO = 500
// La meta del agente es p95 < 8 s con LLM local; pasado esto ya no vale la pena esperar.
const ESPERA_MS = 12000

export const AVISOS = {
  sinConexion: 'No pude hablar con el agente de Lucas. Te respondo con mis cálculos de siempre.',
  demora: 'El agente de Lucas tardó demasiado. Te respondo con mis cálculos de siempre.',
  sinVerificar: 'No pude comprobar estas cifras con tus datos. Tómalas con cuidado.',
}

function formatoCifra(c) {
  if (typeof c.value !== 'number') return String(c.text ?? '')
  if (c.unit === 'PEN') return enSoles(c.value)
  if (c.unit === 'percent') return `${c.value} %`
  if (c.unit === 'rate') return `S/ ${c.value} por US$`
  if (c.unit === 'months') return `${c.value} meses`
  if (c.unit === 'days') return `${c.value} días`
  return c.text ? String(c.text) : String(c.value)
}

// Solo se enlaza lo que es http(s): una fuente nunca debe poder inyectar `javascript:`.
function enlaceSeguro(url) {
  return typeof url === 'string' && /^https?:\/\//i.test(url) ? url : null
}

export function desdeAgente(cuerpo) {
  if (!cuerpo || typeof cuerpo.answer !== 'string' || !cuerpo.answer.trim()) {
    throw new Error('respuesta sin answer')
  }
  const verificado = cuerpo.verified === true
  const cifras = verificado && Array.isArray(cuerpo.figures) ? cuerpo.figures : []
  const fuentes = Array.isArray(cuerpo.sources) ? cuerpo.sources : []
  return {
    origen: 'agente',
    texto: cuerpo.answer.trim(),
    verificado,
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
    aviso: verificado ? null : AVISOS.sinVerificar,
  }
}

function plantilla(texto, cliente, persona, aviso = null) {
  return { origen: 'plantilla', verificado: false, fuentes: [], aviso, ...responderConPlantilla(texto, cliente, persona) }
}

export async function preguntarALucas(texto, { cliente, persona, conversacion, base, fetchImpl = fetch, esperaMs = ESPERA_MS }) {
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
    return desdeAgente(await r.json())
  } catch (e) {
    return plantilla(texto, cliente, persona, e?.name === 'AbortError' ? AVISOS.demora : AVISOS.sinConexion)
  } finally {
    clearTimeout(reloj)
  }
}
