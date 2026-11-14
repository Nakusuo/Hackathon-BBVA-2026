import { TriangleAlert } from 'lucide-react'
import { Link } from 'react-router-dom'
import { enSoles, fechaLarga } from '../formato.js'

export default function AvisoRiesgo({ riesgo }) {
  if (!riesgo) return null
  return (
    <section className="aviso" role="status" aria-label="Aviso de Lucas">
      <p className="aviso-etiqueta">
        <TriangleAlert size={18} aria-hidden="true" />
        Lucas te avisa
      </p>
      <p>
        El {fechaLarga(riesgo.fecha)} podrías quedar en rojo. Ese día tu saldo estaría entre{' '}
        <span className="cifra">{enSoles(riesgo.minimo)}</span> y <span className="cifra">{enSoles(riesgo.maximo)}</span>{' '}
        (confianza {riesgo.confianza}).
      </p>
      <Link className="boton" to="/que-hacer">
        Ver qué puedo hacer
      </Link>
    </section>
  )
}
