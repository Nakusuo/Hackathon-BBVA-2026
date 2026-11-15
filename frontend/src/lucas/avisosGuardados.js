// Hasta que exista la ruta de avisos en la API, lo que se mostró cada semana y la opinión
// «útil / no me sirve» se guardan solo en este navegador.
const CLAVE_REGISTRO = 'lucas-avisos-semana'
const CLAVE_OPINIONES = 'lucas-avisos-opinion'

function leer(clave) {
  try {
    const guardado = JSON.parse(window.localStorage.getItem(clave))
    return guardado && typeof guardado === 'object' && !Array.isArray(guardado) ? guardado : {}
  } catch {
    return {}
  }
}

function guardar(clave, valor) {
  try {
    window.localStorage.setItem(clave, JSON.stringify(valor))
  } catch {
    // Sin almacenamiento el tope semanal y las opiniones duran solo esta visita.
  }
}

export const leerRegistro = () => leer(CLAVE_REGISTRO)
export const guardarRegistro = (registro) => guardar(CLAVE_REGISTRO, registro)
export const leerOpiniones = () => leer(CLAVE_OPINIONES)
export const guardarOpiniones = (opiniones) => guardar(CLAVE_OPINIONES, opiniones)

export function borrarAvisosGuardados() {
  try {
    window.localStorage.removeItem(CLAVE_REGISTRO)
    window.localStorage.removeItem(CLAVE_OPINIONES)
  } catch {
    // Sin almacenamiento no hay nada guardado que borrar.
  }
}
