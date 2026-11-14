import { useEffect, useState } from 'react'
import { CLIENTE_DEMO, cargarCliente, origenGeneral } from './lucas.js'

/** estado: 'cargando' | 'api' | 'parcial' | 'respaldo' | 'error'. Con 'error' fuentes queda en null y el motor sigue mostrando todo. */
export function useDatosApi(id = CLIENTE_DEMO) {
  const [datos, setDatos] = useState({ estado: 'cargando', fuentes: null })

  useEffect(() => {
    let vigente = true
    cargarCliente(id)
      .then((fuentes) => vigente && setDatos({ estado: origenGeneral(fuentes), fuentes }))
      .catch((error) => {
        console.warn('No se pudieron leer los datos de la API ni su respaldo', error)
        if (vigente) setDatos({ estado: 'error', fuentes: null })
      })
    return () => {
      vigente = false
    }
  }, [id])

  return datos
}
