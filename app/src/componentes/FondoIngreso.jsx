import { motion, useReducedMotion } from 'motion/react'
import { SUAVE } from '../movimiento.js'

const ARCOS = [
  { lado: 'arriba', retraso: 0 },
  { lado: 'abajo', retraso: 0.25 },
]

export default function FondoIngreso() {
  const reducido = useReducedMotion()
  return (
    <>
      {ARCOS.map((a) => (
        <motion.svg
          key={a.lado}
          className={`ingreso-fondo ingreso-fondo-${a.lado}`}
          viewBox="0 0 200 200"
          aria-hidden="true"
        >
          <motion.circle
            className="ingreso-arco"
            cx="100"
            cy="100"
            r="94"
            initial={reducido ? false : { pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{ duration: 1.4, ease: SUAVE, delay: a.retraso }}
          />
        </motion.svg>
      ))}
    </>
  )
}
