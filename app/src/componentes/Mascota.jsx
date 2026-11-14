import { motion } from 'motion/react'
import { useId } from 'react'

// Lucas es un personaje propio inspirado en las mascotas de @aokulova (créditos en Preferencias).
// El brote de la cabeza es el ahorro que crece; sin orejas de gato para no copiar su diseño.
const OJOS = [
  { x: 44, y: 62 },
  { x: 76, y: 62 },
]

export default function Mascota({ tamano = 96, animada = true }) {
  const id = useId()
  const cuerpo = `${id}-cuerpo`

  return (
    <svg className="mascota" width={tamano} height={tamano} viewBox="0 0 120 120" aria-hidden="true">
      <defs>
        <radialGradient id={cuerpo} cx="38%" cy="30%" r="75%">
          <stop offset="0%" stopColor="#7fb0ff" />
          <stop offset="55%" stopColor="#2875fb" />
          <stop offset="100%" stopColor="#1e3fb2" />
        </radialGradient>
      </defs>
      <motion.g
        animate={animada ? { y: [0, -3, 0] } : undefined}
        transition={{ duration: 3, ease: 'easeInOut', repeat: Infinity }}
      >
        <path d="M60 30 C60 22 60 18 61 13" stroke="#1e3fb2" strokeWidth="3" strokeLinecap="round" fill="none" />
        <path d="M61 15 C66 6 76 7 78 10 C73 17 66 18 61 15 Z" fill="#c3d7fc" stroke="#1e3fb2" strokeWidth="2" />
        <path d="M60 18 C55 11 47 12 45 15 C50 20 56 20 60 18 Z" fill="#c3d7fc" stroke="#1e3fb2" strokeWidth="2" />
        <ellipse cx="18" cy="76" rx="9" ry="13" fill="#2160e0" transform="rotate(25 18 76)" />
        <ellipse cx="102" cy="76" rx="9" ry="13" fill="#2160e0" transform="rotate(-25 102 76)" />
        <rect x="40" y="98" width="14" height="14" rx="7" fill="#1e3fb2" />
        <rect x="66" y="98" width="14" height="14" rx="7" fill="#1e3fb2" />
        <ellipse cx="60" cy="66" rx="44" ry="40" fill={`url(#${cuerpo})`} />
        <ellipse cx="60" cy="84" rx="26" ry="16" fill="#c3d7fc" opacity="0.55" />
        <motion.g
          style={{ originY: '62px' }}
          animate={animada ? { scaleY: [1, 1, 0.1, 1] } : undefined}
          transition={{ duration: 4, times: [0, 0.9, 0.95, 1], repeat: Infinity }}
        >
          {OJOS.map((o) => (
            <g key={o.x}>
              <circle cx={o.x} cy={o.y} r="13" fill="#ffffff" />
              <circle cx={o.x + 2} cy={o.y + 2} r="8" fill="#10131c" />
              <circle cx={o.x + 5} cy={o.y - 2} r="3" fill="#ffffff" />
            </g>
          ))}
        </motion.g>
        <path d="M53 81 Q60 87 67 81" stroke="#10131c" strokeWidth="2.5" strokeLinecap="round" fill="none" />
      </motion.g>
    </svg>
  )
}
