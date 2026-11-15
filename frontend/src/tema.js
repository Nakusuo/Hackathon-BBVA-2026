const CLAVE_TEMA = 'lucas-tema'

export function temaGuardado() {
  try {
    return window.localStorage.getItem(CLAVE_TEMA) === 'oscuro' ? 'oscuro' : 'claro'
  } catch {
    return 'claro'
  }
}

export function aplicarTema(tema) {
  document.documentElement.dataset.tema = tema
  try {
    window.localStorage.setItem(CLAVE_TEMA, tema)
  } catch {
    // Sin almacenamiento el tema dura solo esta visita; la app sigue funcionando.
  }
}
