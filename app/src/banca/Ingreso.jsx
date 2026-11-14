import { motion, useReducedMotion } from 'motion/react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import FondoIngreso from '../componentes/FondoIngreso.jsx'
import LucasPose from '../componentes/LucasPose.jsx'
import SelectorPersona from '../componentes/SelectorPersona.jsx'
import { SUAVE } from '../movimiento.js'
import { guardarPersona, permisoDe, personaGuardada } from '../sesion.js'

// Formulario solo visual: los campos vienen llenos y bloqueados para que nadie escriba datos reales en la demo.
// Elegir la persona es el inicio de sesión de la demo; el permiso a Lucas se pide después, una vez por persona.
export default function Ingreso() {
  const navegar = useNavigate()
  const reducido = useReducedMotion()
  const [personaId, setPersonaId] = useState(personaGuardada)

  function ingresar(evento) {
    evento.preventDefault()
    guardarPersona(personaId)
    navegar(permisoDe(personaId) ? '/banca' : '/consentimiento')
  }

  return (
    <main className="ingreso">
      <FondoIngreso />
      <motion.form
        className="ingreso-tarjeta"
        onSubmit={ingresar}
        aria-labelledby="ingreso-titulo"
        initial={reducido ? false : { opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: SUAVE, delay: 0.2 }}
      >
        <div className="ingreso-saludo">
          <LucasPose pose="saludo" tamano={92} animada />
          <p className="burbuja">¡Hola de nuevo! Soy Lucas, tu copiloto de plata.</p>
        </div>
        <span className="logotipo">Banco Vértice</span>
        <h1 id="ingreso-titulo">Ingresa a tu banca</h1>

        <SelectorPersona valor={personaId} alCambiar={setPersonaId} leyenda="Entra como" />

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
        <Link to="/evidencia" className="enlace">
          Ver la evidencia de los modelos
        </Link>
      </motion.form>
    </main>
  )
}
