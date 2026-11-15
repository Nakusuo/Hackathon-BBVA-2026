import { motion } from 'motion/react'
import ahorra from '../assets/lucas/lucas-ahorra.webp'
import alerta from '../assets/lucas/lucas-alerta.webp'
import celebra from '../assets/lucas/lucas-celebra.webp'
import descansa from '../assets/lucas/lucas-descansa.webp'
import neutral from '../assets/lucas/lucas-neutral.webp'
import pensando from '../assets/lucas/lucas-pensando.webp'
import saludo from '../assets/lucas/lucas-saludo.webp'
import senala from '../assets/lucas/lucas-senala.webp'

// Lucas es un personaje propio inspirado en las mascotas de @aokulova (créditos en Preferencias).
// El brote de la cabeza es el ahorro que crece. Cada pose acompaña un momento: avisar, celebrar, apartar…
const POSES = { ahorra, alerta, celebra, descansa, neutral, pensando, saludo, senala }

export default function LucasPose({ pose = 'neutral', tamano = 96, animada = false, className = '' }) {
  return (
    <motion.img
      className={`lucas-pose ${className}`}
      src={POSES[pose] ?? neutral}
      width={tamano}
      height={tamano}
      alt=""
      aria-hidden="true"
      draggable="false"
      animate={animada ? { y: [0, -4, 0] } : undefined}
      transition={{ duration: 3, ease: 'easeInOut', repeat: Infinity }}
    />
  )
}
