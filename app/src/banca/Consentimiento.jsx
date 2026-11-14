import { ArrowCounterClockwise, Database, Flask, ShieldCheck, Target } from '@phosphor-icons/react'
import { motion } from 'motion/react'
import { useLocation, useNavigate } from 'react-router-dom'
import FondoIngreso from '../componentes/FondoIngreso.jsx'
import Mascota from '../componentes/Mascota.jsx'
import { personaPorId } from '../mocks/personas.js'
import { SUAVE } from '../movimiento.js'
import { darPermiso, personaGuardada } from '../sesion.js'

const PUNTOS = [
  {
    Icono: Database,
    titulo: 'Qué uso',
    texto: 'Tus movimientos de cuenta y tarjeta de los últimos 12 meses, tus pagos programados, tus cobros y un perfil resumido: tipo de ingreso y nivel de deuda.',
  },
  {
    Icono: Target,
    titulo: 'Para qué',
    texto: 'Para calcular cuánto puedes gastar al día, avisarte antes de quedar en rojo y proponerte cambios con monto.',
  },
  {
    Icono: ShieldCheck,
    titulo: 'Lo que no hago',
    texto:
      'No muevo tu plata ni hago operaciones. Si se activa Gemini de Google para el chat (viene apagado), solo recibe resultados de cálculos: nunca tu nombre, tu DNI ni lo que escribes.',
  },
  {
    Icono: ArrowCounterClockwise,
    titulo: 'Puedes retirarlo',
    texto: 'Cuando quieras, en Más → Preferencias → Privacidad. Lucas se apaga y borra los tips que elegiste.',
  },
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
          <Mascota tamano={64} />
          <p className="burbuja">Para avisarte a tiempo necesito mirar tus movimientos. Te cuento qué uso.</p>
        </div>
        <h1 id="permiso-titulo">Antes de activar Lucas</h1>

        <p className="permiso-sintetico">
          <Flask size={20} aria-hidden="true" />
          <span>
            <strong>Datos sintéticos.</strong> Entras como «{persona.nombre}»: la persona, los montos y los comercios son
            inventados.
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
        <p className="suave permiso-pie">
          Lucas da orientación con simulaciones, no asesoría: tú decides. Alineado con la Ley 29733 de Protección de
          Datos Personales: el responsable de tus datos es el banco que integre a Lucas, y ante él pides acceso,
          rectificación, cancelación u oposición.
        </p>
      </motion.section>
    </main>
  )
}
