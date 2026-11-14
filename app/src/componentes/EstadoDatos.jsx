import { CloudSlash } from '@phosphor-icons/react'

const TEXTOS = {
  cargando: 'Leyendo tus datos del servidor.',
  parcial: 'Parte de tus datos no se actualizó: te muestro los últimos.',
  respaldo: 'Sin conexión: te muestro tus últimos datos.',
  error: 'Sin conexión: te muestro tus últimos datos.',
}

// La carga dura milisegundos con la API local: se anuncia solo al lector de pantalla para no mover la página.
export default function EstadoDatos({ estado }) {
  const visible = estado === 'parcial' || estado === 'respaldo' || estado === 'error'
  return (
    <p className={visible ? 'estado-datos' : 'solo-lector'} role="status">
      {visible && <CloudSlash size={20} aria-hidden="true" />}
      {TEXTOS[estado]}
    </p>
  )
}
