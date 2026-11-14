import { LockSimple } from '@phosphor-icons/react'
import { motion, useReducedMotion } from 'motion/react'
import { useNavigate } from 'react-router-dom'
import { SUAVE } from '../movimiento.js'

const ARCOS = [
  { lado: 'arriba', retraso: 0 },
  { lado: 'abajo', retraso: 0.25 },
]

function Fondo() {
  const reducido = useReducedMotion()
  return (
    <>
      <div className="ingreso-halo" aria-hidden="true" />
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

// Formulario solo visual: los campos vienen llenos y bloqueados para que nadie escriba datos reales en la demo.
export default function Ingreso() {
  const navegar = useNavigate()

  function ingresar(evento) {
    evento.preventDefault()
    navegar('/banca')
  }

  return (
    <main className="ingreso">
      <Fondo />
      <motion.form
        className="ingreso-tarjeta"
        onSubmit={ingresar}
        aria-labelledby="ingreso-titulo"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: SUAVE, delay: 0.2 }}
      >
        <div className="ingreso-marca">
          <span className="logotipo">Banco Vértice</span>
          <span className="etiqueta-demo">Banco ficticio</span>
        </div>
        <h1 id="ingreso-titulo">Ingresa a tu banca</h1>
        <p className="ingreso-bajada">Con Lucas, tu copiloto de plata.</p>

        <label className="campo">
          <span>Número de DNI</span>
          <input value="00000000" readOnly inputMode="numeric" />
        </label>
        <label className="campo">
          <span>Clave de internet</span>
          <input type="password" value="clave-demo" readOnly autoComplete="off" />
        </label>

        <motion.button type="submit" className="boton boton-ancho" whileTap={{ scale: 0.97 }}>
          Ingresar
        </motion.button>
        <p className="nota-seguridad">
          <LockSimple size={18} aria-hidden="true" />
          Datos de prueba ya cargados. No escribas datos reales.
        </p>
      </motion.form>
    </main>
  )
}
