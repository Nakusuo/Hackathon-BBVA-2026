// Si la API tarda más que esto, la pantalla pasa al respaldo en vez de quedarse esperando en la demo.
export const ESPERA_MS = 4000

export class ErrorApi extends Error {
  /** tipo: «red», «tiempo», «http» o «formato». */
  constructor(tipo, mensaje, estado) {
    super(mensaje)
    this.name = 'ErrorApi'
    this.tipo = tipo
    this.estado = estado
  }
}

export async function pedirJson(ruta, { metodo = 'GET', cuerpo, esperaMs = ESPERA_MS, pedir = globalThis.fetch } = {}) {
  const control = new AbortController()
  const reloj = setTimeout(() => control.abort(), esperaMs)
  try {
    let respuesta
    try {
      respuesta = await pedir(ruta, {
        method: metodo,
        headers: cuerpo ? { 'Content-Type': 'application/json' } : undefined,
        body: cuerpo ? JSON.stringify(cuerpo) : undefined,
        signal: control.signal,
      })
    } catch {
      throw control.signal.aborted
        ? new ErrorApi('tiempo', `La API no respondió en ${esperaMs} ms`)
        : new ErrorApi('red', 'No se pudo conectar con la API')
    }
    if (!respuesta.ok) throw new ErrorApi('http', `La API respondió ${respuesta.status}`, respuesta.status)
    try {
      return await respuesta.json()
    } catch {
      throw control.signal.aborted
        ? new ErrorApi('tiempo', `La API no terminó de responder en ${esperaMs} ms`)
        : new ErrorApi('formato', 'La API no devolvió JSON')
    }
  } finally {
    clearTimeout(reloj)
  }
}
