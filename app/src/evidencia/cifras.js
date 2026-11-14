// Toda cifra del panel Evidencia se lee aquí, con su archivo y su ruta de claves.
// Si `make eval` cambia el nombre de una clave, la build y las pruebas fallan en vez de mostrar un número viejo.
import agentePlantillas from '../../../models/metricas_agente_plantillas.json' with { type: 'json' }
import agenteGemini from '../../../models/metricas_agente_gemini.json' with { type: 'json' }
import clasificacion from '../../../models/metricas_clasificacion.json' with { type: 'json' }
import escala from '../../../models/metricas_escala.json' with { type: 'json' }
import impacto from '../../../models/metricas_impacto.json' with { type: 'json' }
import principal from '../../../models/metricas.json' with { type: 'json' }
import rag from '../../../models/metricas_rag.json' with { type: 'json' }
import valor from '../../../models/metricas_valor.json' with { type: 'json' }

export const ARCHIVOS = {
  impacto: { ruta: 'models/metricas_impacto.json', datos: impacto },
  valor: { ruta: 'models/metricas_valor.json', datos: valor },
  principal: { ruta: 'models/metricas.json', datos: principal },
  clasificacion: { ruta: 'models/metricas_clasificacion.json', datos: clasificacion },
  rag: { ruta: 'models/metricas_rag.json', datos: rag },
  agentePlantillas: { ruta: 'models/metricas_agente_plantillas.json', datos: agentePlantillas },
  agenteGemini: { ruta: 'models/metricas_agente_gemini.json', datos: agenteGemini },
  escala: { ruta: 'models/metricas_escala.json', datos: escala },
}

function buscar(archivo, claves) {
  const fuente = ARCHIVOS[archivo]
  if (!fuente) throw new Error(`Archivo de métricas desconocido: ${archivo}`)
  const valor = claves.reduce((nodo, clave) => (nodo == null ? undefined : nodo[clave]), fuente.datos)
  return { valor, fuente: `${fuente.ruta} › ${claves.join(' › ')}` }
}

export function cifra(archivo, ...claves) {
  const encontrada = buscar(archivo, claves)
  if (typeof encontrada.valor !== 'number' || !Number.isFinite(encontrada.valor)) {
    throw new Error(`No hay número en ${encontrada.fuente}`)
  }
  return encontrada
}

export function texto(archivo, ...claves) {
  const encontrada = buscar(archivo, claves)
  if (typeof encontrada.valor !== 'string') throw new Error(`No hay texto en ${encontrada.fuente}`)
  return encontrada
}

export function booleano(archivo, ...claves) {
  const encontrada = buscar(archivo, claves)
  if (typeof encontrada.valor !== 'boolean') throw new Error(`No hay sí/no en ${encontrada.fuente}`)
  return encontrada
}

export function claves(archivo, ...ruta) {
  const { valor, fuente } = buscar(archivo, ruta)
  if (!valor || typeof valor !== 'object') throw new Error(`No hay tabla en ${fuente}`)
  return Object.keys(valor)
}
