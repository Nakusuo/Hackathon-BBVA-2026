import { animate, motion, useMotionValue, useReducedMotion, useTransform } from 'motion/react'
import { useEffect } from 'react'
import { SUAVE } from '../movimiento.js'

// El lector de pantalla recibe solo el valor final; los pasos intermedios del conteo serían ruido.
export default function NumeroAnimado({ valor, formato = String, duracion = 0.9, retraso = 0 }) {
  const reducido = useReducedMotion()
  const actual = useMotionValue(reducido ? valor : 0)
  const texto = useTransform(actual, (v) =>
    formato(Number.isInteger(valor) ? Math.round(v) : Math.round(v * 100) / 100),
  )

  useEffect(() => {
    if (reducido) {
      actual.set(valor)
      return
    }
    const control = animate(actual, valor, { duration: duracion, delay: retraso, ease: SUAVE })
    return () => control.stop()
  }, [actual, valor, reducido, duracion, retraso])

  return (
    <>
      <motion.span aria-hidden="true">{texto}</motion.span>
      <span className="solo-lector">{formato(valor)}</span>
    </>
  )
}
