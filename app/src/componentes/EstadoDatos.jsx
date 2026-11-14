import { CloudSlash } from '@phosphor-icons/react'

const TEXTOS = {
  cargando: 'Leyendo tus datos del servidor.',
  parcial: 'Parte de tus datos no llegó del servidor; sigo con los datos de la demo.',
  respaldo: 'No llegaron tus datos del servidor; sigo con los datos de la demo.',
  error: 'No pude leer los datos del servidor; sigo con los datos de la demo.',
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
