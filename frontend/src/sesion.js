// Sesión de la demo en el navegador: qué persona eligió quien presenta y si esa persona dio su permiso a Lucas.
// No hay sesión en el servidor: todo vive en este navegador (ARCHITECTURE.md, sección 4).
import { PERSONA_INICIAL, PERSONAS } from './motor/personas.js'

const CLAVE_PERSONA = 'lucas-persona'
const CLAVE_PERMISOS = 'lucas-consentimiento'
export const CLAVE_TIPS = 'lucas-tips-elegidos'
export const CLAVE_PLANIFICADOS = 'lucas-planificados'
export const CLAVE_METAS = 'lucas-metas'
export const CLAVE_REGISTRADOS = 'lucas-registrados'
// Lo que Lucas guarda de una persona en este navegador; se olvida al cambiar de persona o al retirar el permiso.
const DE_LA_PERSONA = [CLAVE_TIPS, CLAVE_PLANIFICADOS, CLAVE_METAS, CLAVE_REGISTRADOS]

function leer(clave) {
  try {
    return window.localStorage.getItem(clave)
  } catch {
    return null
  }
}

function escribir(clave, valor) {
  try {
    if (valor === null) window.localStorage.removeItem(clave)
    else window.localStorage.setItem(clave, valor)
  } catch {
    // Sin almacenamiento la elección dura solo esta visita; la app sigue funcionando.
  }
}

export function personaGuardada() {
  const id = leer(CLAVE_PERSONA)
  return PERSONAS.some((p) => p.id === id) ? id : PERSONA_INICIAL
}

// Los tips, lo planificado, lo registrado y las metas son de una persona: al cambiar de persona se descartan.
export function guardarPersona(id) {
  if (id !== personaGuardada()) for (const clave of DE_LA_PERSONA) escribir(clave, null)
  escribir(CLAVE_PERSONA, id)
}

function permisos() {
  try {
    const guardado = JSON.parse(leer(CLAVE_PERMISOS))
    return guardado && typeof guardado === 'object' ? guardado : {}
  } catch {
    return {}
  }
}

// El permiso es de cada persona, como lo sería de cada cliente: el de una no vale para otra.
export function permisoDe(personaId) {
  return permisos()[personaId] ?? null
}

export function darPermiso(personaId, fecha) {
  escribir(CLAVE_PERMISOS, JSON.stringify({ ...permisos(), [personaId]: fecha }))
}

// Retirar el permiso apaga Lucas para esa persona y borra lo que Lucas recordaba de ella en este navegador.
export function retirarPermiso(personaId) {
  const resto = { ...permisos() }
  delete resto[personaId]
  escribir(CLAVE_PERMISOS, JSON.stringify(resto))
  for (const clave of DE_LA_PERSONA) escribir(clave, null)
}
