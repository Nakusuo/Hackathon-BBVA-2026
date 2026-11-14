import { CheckCircle } from '@phosphor-icons/react'

// Sitio de la marca ✓ (HU del verificador de Jeffrey). Hasta que la API devuelva qué cifras pasaron el verificador,
// nadie pasa `verificada` y no se muestra: decir «verificada» sin verificador fue un hallazgo del juez.
export default function CifraVerificada({ verificada = false, children }) {
  return (
    <span className="cifra-verificada">
      {children}
      {verificada && <CheckCircle size={20} weight="fill" className="marca-verificada" aria-label="Cifra verificada" />}
    </span>
  )
}
