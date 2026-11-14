// Única puerta del front hacia la API de Lucas (src/api/ en FastAPI). Ninguna pantalla llama a fetch por su cuenta.
import {
  leerEventos,
  leerPronostico,
  leerRecomendaciones,
  leerSalud,
  leerSimulacion,
  leerTipoCambio,
  pedidoSimulacion,
} from './contrato.js'
import { ErrorApi, pedirJson } from './http.js'
import { RESPALDO } from './respaldo.js'

// Rutas relativas: en desarrollo las pasa el proxy de Vite al puerto 8000, porque la API no tiene CORS.
const BASE = '/api/v1'
export const CLIENTE_DEMO = 'demo-001'

const FUENTES = {
  salud: { ruta: (id) => `${BASE}/customers/${id}/health`, leer: leerSalud },
  pronostico: { ruta: (id) => `${BASE}/customers/${id}/forecast`, leer: leerPronostico },
  recomendaciones: { ruta: (id) => `${BASE}/customers/${id}/recommendations`, leer: leerRecomendaciones },
  eventos: { ruta: (id) => `${BASE}/customers/${id}/events`, leer: leerEventos },
  tipoCambio: { ruta: () => `${BASE}/fx?base=USD&quote=PEN`, leer: leerTipoCambio },
}

/**
 * Devuelve { datos, origen: 'api' | 'respaldo', motivo? }. Solo un ErrorApi pasa al respaldo:
 * cualquier otro error es un fallo del front y debe verse, no esconderse.
 */
async function conRespaldo(nombre, leer, respaldo, pedirApi) {
  try {
    return { datos: leer(await pedirApi()), origen: 'api' }
  } catch (error) {
    if (!(error instanceof ErrorApi)) throw error
    console.warn(`API: «${nombre}» pasa al respaldo (${error.tipo})`, error.message)
    return { datos: leer(respaldo), origen: 'respaldo', motivo: error.tipo }
  }
}

function leerFuente(nombre, id, opciones) {
  const fuente = FUENTES[nombre]
  return conRespaldo(nombre, fuente.leer, RESPALDO[nombre], () => pedirJson(fuente.ruta(id), opciones))
}

/** Pide las cinco lecturas a la vez; una que falle no frena a las demás. */
export async function cargarCliente(id = CLIENTE_DEMO, opciones = {}) {
  const nombres = Object.keys(FUENTES)
  const resultados = await Promise.all(nombres.map((n) => leerFuente(n, id, opciones)))
  return Object.fromEntries(nombres.map((n, i) => [n, resultados[i]]))
}

// Un 4xx aquí es un pedido mal armado por el front: se lanza en vez de tapar el error con el mock.
export function simularCambios(cambios, { id = CLIENTE_DEMO, horizonteDias = 30, ...opciones } = {}) {
  const cuerpo = pedidoSimulacion(id, cambios, horizonteDias)
  return conRespaldo('simulacion', leerSimulacion, RESPALDO.simulacion, async () => {
    try {
      return await pedirJson(`${BASE}/simulations`, { ...opciones, metodo: 'POST', cuerpo })
    } catch (error) {
      if (error.tipo === 'http' && error.estado < 500) throw new Error(error.message, { cause: error })
      throw error
    }
  })
}

// El agente redacta con un LLM: su meta es p95 < 8 s, más lenta que una lectura.
const ESPERA_CHAT_MS = 12000

/** Devuelve el cuerpo crudo de /chat; quien llama decide qué se muestra según `verified`. */
export function preguntarAgente(mensaje, { id = CLIENTE_DEMO, conversacion, ...opciones } = {}) {
  const cuerpo = { customer_id: id, message: mensaje, ...(conversacion ? { conversation_id: conversacion } : {}) }
  return pedirJson(`${BASE}/chat`, { esperaMs: ESPERA_CHAT_MS, ...opciones, metodo: 'POST', cuerpo })
}

/** 'api' si todo vino del servidor, 'respaldo' si nada, 'parcial' si hubo de los dos. */
export function origenGeneral(fuentes) {
  const origenes = new Set(Object.values(fuentes).map((f) => f.origen))
  if (origenes.size > 1) return 'parcial'
  return origenes.has('api') ? 'api' : 'respaldo'
}
