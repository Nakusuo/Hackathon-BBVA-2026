import LucasPose from './LucasPose.jsx'

// En tamaños de ícono Lucas va quieto: moverse en cada esquina de la app distrae.
export default function MarcaLucas({ tamano = 40, pose = 'neutral' }) {
  return (
    <span className="marca-lucas" style={{ '--tamano': `${tamano}px` }} aria-hidden="true">
      <LucasPose pose={pose} tamano={tamano * 0.92} />
    </span>
  )
}
