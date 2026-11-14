// Monograma propio de Lucas: no usa iconos de terceros para que la marca sea reconocible dentro de cualquier banca.
export default function MarcaLucas({ tamano = 40 }) {
  return (
    <span className="marca-lucas" style={{ '--tamano': `${tamano}px` }} aria-hidden="true">
      L
    </span>
  )
}
