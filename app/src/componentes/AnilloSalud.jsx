import { motion, useReducedMotion } from 'motion/react'
import { SUAVE } from '../movimiento.js'
import NumeroAnimado from './NumeroAnimado.jsx'

const RADIO = 54
const GROSOR = 12
const CIRCUNFERENCIA = 2 * Math.PI * RADIO
const SEPARACION = 9

// Un tramo por componente: así se ve qué parte baja el puntaje, no solo el total.
// Los tramos se llenan uno tras otro para que se note cuál se queda corto.
export default function AnilloSalud({ puntaje, componentes }) {
  const reducido = useReducedMotion()
  const tramo = CIRCUNFERENCIA / componentes.length
  const largo = tramo - SEPARACION

  return (
    <div className="anillo">
      <svg viewBox="0 0 132 132" aria-hidden="true">
        {componentes.map((c, i) => (
          <g key={c.nombre}>
            <circle
              cx="66"
              cy="66"
              r={RADIO}
              fill="none"
              stroke="var(--superficie-suave)"
              strokeWidth={GROSOR}
              strokeLinecap="round"
              strokeDasharray={`${largo} ${CIRCUNFERENCIA - largo}`}
              strokeDashoffset={-i * tramo}
            />
            <motion.circle
              cx="66"
              cy="66"
              r={RADIO}
              fill="none"
              stroke="var(--azul)"
              strokeWidth={GROSOR}
              strokeLinecap="round"
              strokeDashoffset={-i * tramo}
              initial={reducido ? false : { strokeDasharray: `0 ${CIRCUNFERENCIA}` }}
              animate={{ strokeDasharray: `${(largo * c.valor) / 100} ${CIRCUNFERENCIA}` }}
              transition={{ duration: 0.6, ease: SUAVE, delay: i * 0.12 }}
            />
          </g>
        ))}
      </svg>
      <div className="anillo-centro">
        <span className="anillo-valor">
          <NumeroAnimado valor={puntaje} />
        </span>
        <span className="suave chico">de 100</span>
      </div>
    </div>
  )
}
