import Mascota from './Mascota.jsx'

// En tamaños de ícono la mascota va quieta: moverse en cada esquina de la app distrae.
export default function MarcaLucas({ tamano = 40 }) {
  return (
    <span className="marca-lucas" style={{ '--tamano': `${tamano}px` }} aria-hidden="true">
      <Mascota tamano={tamano * 0.92} animada={false} />
    </span>
  )
}
