import { CloudSlash } from '@phosphor-icons/react'

const TEXTOS = {
  cargando: 'Leyendo tus datos del servidor.',
  parcial: 'Parte de tus datos no llegó del servidor. Tus cifras siguen calculándose aquí con los datos de la demo.',
  respaldo: 'No pude conectar con el servidor. Tus cifras siguen calculándose aquí con los datos de la demo.',
  error: 'No pude conectar con el servidor. Tus cifras siguen calculándose aquí con los datos de la demo.',
}

// La carga dura milisegundos con la API local: se anuncia solo al lector de pantalla para no mover la página.
// Con todo llegado de la API no hay nada que avisar.
export default function EstadoDatos({ estado }) {
  const visible = estado === 'parcial' || estado === 'respaldo' || estado === 'error'
  return (
    <p className={visible ? 'estado-datos' : 'solo-lector'} role="status">
      {visible && <CloudSlash size={20} aria-hidden="true" />}
      {TEXTOS[estado]}
    </p>
  )
}
