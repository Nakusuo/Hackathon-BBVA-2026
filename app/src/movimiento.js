// Frena al final: el movimiento acompaña la lectura en vez de llamar la atención sobre sí mismo.
export const SUAVE = [0.22, 1, 0.36, 1]

// Las secciones entran en el orden en que conviene leerlas: primero la cifra, luego el aviso, luego qué hacer.
export function entrada(orden, activa = true) {
  if (!activa) return { initial: false }
  return {
    initial: { opacity: 0, y: 12 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.4, ease: SUAVE, delay: orden * 0.06 },
  }
}
