// Toda cifra del panel Evidencia se lee aquí, con su archivo y su ruta de claves.
// Si `make eval` cambia el nombre de una clave, la build y las pruebas fallan en vez de mostrar un número viejo.
import agentePlantillas from '../../../models/metricas_agente_plantillas.json' with { type: 'json' }
import qaAgente from '../../../models/metricas_qa_agente.json' with { type: 'json' }
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
  qaAgente: { ruta: 'models/metricas_qa_agente.json', datos: qaAgente },
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

// La corrida de QA guarda una lista de casos con sus `checks`; estas cifras se cuentan sobre esa lista.
function lista(archivo, nombre) {
  const { valor, fuente } = buscar(archivo, [nombre])
  if (!Array.isArray(valor) || valor.length === 0) throw new Error(`No hay lista en ${fuente}`)
  return { casos: valor, fuente }
}

export function cuenta(archivo, nombre) {
  const { casos, fuente } = lista(archivo, nombre)
  return { valor: casos.length, fuente: `${fuente} › cantidad` }
}

// Parte de los casos que pasan un check. Si algún caso no lo trae, rompe en vez de contarlo como fallo.
export function proporcion(archivo, nombre, check) {
  const { casos, fuente } = lista(archivo, nombre)
  const marcas = casos.map((caso) => caso?.checks?.[check])
  if (marcas.some((m) => typeof m !== 'boolean')) throw new Error(`No hay sí/no en ${fuente} › checks › ${check}`)
  return { valor: marcas.filter(Boolean).length / casos.length, fuente: `${fuente} › checks › ${check}` }
}

// Parte de los casos que pasan todos sus checks.
export function proporcionCompleta(archivo, nombre) {
  const { casos, fuente } = lista(archivo, nombre)
  const marcas = casos.map((caso) => Object.values(caso?.checks ?? {}))
  if (marcas.some((m) => m.length === 0 || m.some((v) => typeof v !== 'boolean'))) {
    throw new Error(`No hay sí/no en ${fuente} › checks`)
  }
  return { valor: marcas.filter((m) => m.every(Boolean)).length / casos.length, fuente: `${fuente} › checks (todos)` }
}

export function media(archivo, nombre, campo) {
  const { casos, fuente } = lista(archivo, nombre)
  const valores = casos.map((caso) => caso?.[campo])
  if (valores.some((v) => typeof v !== 'number' || !Number.isFinite(v))) throw new Error(`No hay número en ${fuente} › ${campo}`)
  return { valor: valores.reduce((a, b) => a + b, 0) / valores.length, fuente: `${fuente} › ${campo} (media)` }
}

export function claves(archivo, ...ruta) {
  const { valor, fuente } = buscar(archivo, ruta)
  if (!valor || typeof valor !== 'object') throw new Error(`No hay tabla en ${fuente}`)
  return Object.keys(valor)
}
