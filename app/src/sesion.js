// Sesión de la demo en el navegador: qué persona eligió quien presenta y si esa persona dio su permiso a Lucas.
// Con la API, elegir persona pasa a ser `POST /sesion` y el token firmado reemplaza a la persona guardada aquí;
// el identificador nunca va en la dirección (ARCHITECTURE §5.2).
import { PERSONA_INICIAL, PERSONAS } from './mocks/personas.js'

const CLAVE_PERSONA = 'lucas-persona'
const CLAVE_PERMISOS = 'lucas-consentimiento'
export const CLAVE_TIPS = 'lucas-tips-elegidos'

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

// Los tips elegidos son de una persona: al cambiar de persona se descartan.
export function guardarPersona(id) {
  if (id !== personaGuardada()) escribir(CLAVE_TIPS, null)
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
  escribir(CLAVE_TIPS, null)
}
