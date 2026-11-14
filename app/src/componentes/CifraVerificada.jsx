import { CheckCircle } from '@phosphor-icons/react'

// Sitio de la marca ✓. Nadie pasa `verificada` hasta que la API diga qué cifras pasaron el verificador (Jeffrey):
// sin verificador, la marca no se muestra.
export default function CifraVerificada({ verificada = false, children }) {
  return (
    <span className="cifra-verificada">
      {children}
      {verificada && <CheckCircle size={20} weight="fill" className="marca-verificada" aria-label="Cifra verificada" />}
    </span>
  )
}
