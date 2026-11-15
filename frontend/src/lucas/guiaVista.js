const CLAVE_GUIA = 'lucas-guia-vista'

export function guiaYaVista() {
  try {
    return window.localStorage.getItem(CLAVE_GUIA) === 'si'
  } catch {
    return false
  }
}

export function marcarGuiaVista() {
  try {
    window.localStorage.setItem(CLAVE_GUIA, 'si')
  } catch {
    // Sin almacenamiento la guía vuelve a salir la próxima vez; no impide usar la app.
  }
}
