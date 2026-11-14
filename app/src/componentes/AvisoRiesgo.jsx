import { TriangleAlert } from 'lucide-react'
import { Link } from 'react-router-dom'
import { enSoles, fechaDia, textoDiasEnRojo } from '../formato.js'

export default function AvisoRiesgo({ riesgo }) {
  if (!riesgo) return null
  return (
    <section className="aviso" role="status" aria-label="Aviso de Lucas">
      <p className="aviso-etiqueta">
        <TriangleAlert size={18} aria-hidden="true" />
        Lucas te avisa
      </p>
      <p>
        {textoDiasEnRojo(riesgo)} podrías quedar en rojo si sigues gastando igual. Peor caso:{' '}
        <span className="cifra">{enSoles(riesgo.peorMonto)}</span> el {fechaDia(riesgo.peorFecha)}.
      </p>
      <Link className="boton" to="/que-hacer">
        Ver qué puedo hacer
      </Link>
    </section>
  )
}
