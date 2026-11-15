import { ArrowCounterClockwise, Database, Flask, ShieldCheck, Target } from '@phosphor-icons/react'
import { motion } from 'motion/react'
import { useLocation, useNavigate } from 'react-router-dom'
import FondoIngreso from '../componentes/FondoIngreso.jsx'
import LucasPose from '../componentes/LucasPose.jsx'
import { personaPorId } from '../motor/personas.js'
import { SUAVE } from '../movimiento.js'
import { darPermiso, personaGuardada } from '../sesion.js'

const PUNTOS = [
  { Icono: Database, titulo: 'Qué uso', texto: 'Tus movimientos, pagos y cobros.' },
  { Icono: Target, titulo: 'Para qué', texto: 'Decirte cuánto puedes gastar y avisarte antes de quedar en rojo.' },
  { Icono: ShieldCheck, titulo: 'Lo que no hago', texto: 'No muevo tu plata. Tu nombre y tu DNI no salen de aquí.' },
  { Icono: ArrowCounterClockwise, titulo: 'Puedes retirarlo', texto: 'Cuando quieras, en Más → Preferencias → Privacidad.' },
]

// Segundo paso del ingreso: sin este permiso Lucas no se enciende, y la banca sigue funcionando igual.
export default function Consentimiento() {
  const navegar = useNavigate()
  const { state } = useLocation()
  const persona = personaPorId(personaGuardada())

  function aceptar() {
    darPermiso(persona.id, new Date().toISOString().slice(0, 10))
    navegar(state?.volver ?? '/banca', { replace: true })
  }

  return (
    <main className="ingreso">
      <FondoIngreso />
      <motion.section
        className="ingreso-tarjeta permiso"
        aria-labelledby="permiso-titulo"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: SUAVE }}
      >
        <div className="ingreso-saludo">
          <LucasPose pose="senala" tamano={72} />
          <p className="burbuja">Para avisarte a tiempo, necesito ver tus movimientos.</p>
        </div>
        <h1 id="permiso-titulo">Antes de activar Lucas</h1>

        <p className="permiso-sintetico">
          <Flask size={20} aria-hidden="true" />
          <span>
            <strong>Datos sintéticos.</strong> «{persona.nombre}» y sus montos son inventados.
          </span>
        </p>

        <ul className="lista-limpia permiso-puntos">
          {PUNTOS.map(({ Icono, titulo, texto }) => (
            <li key={titulo}>
              <span className="circulo" aria-hidden="true">
                <Icono size={20} />
              </span>
              <span>
                <strong>{titulo}</strong>
                <span className="suave">{texto}</span>
              </span>
            </li>
          ))}
        </ul>

        <div className="permiso-acciones">
          <motion.button type="button" className="boton boton-ancho" onClick={aceptar} whileTap={{ scale: 0.97 }}>
            Acepto, activar Lucas
          </motion.button>
          <button type="button" className="boton-texto" onClick={() => navegar('/banca', { replace: true })}>
            Ahora no
          </button>
        </div>
        <p className="suave permiso-pie">Orientación, no asesoría. Tus datos se cuidan según la Ley 29733.</p>
      </motion.section>
    </main>
  )
}
