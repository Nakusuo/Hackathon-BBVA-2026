import { CheckCircle, Question } from '@phosphor-icons/react'
import { AnimatePresence, motion } from 'motion/react'
import { useState } from 'react'

const CAMBIO = {
  initial: { opacity: 0, y: 4 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -4 },
  transition: { duration: 0.15 },
}

function DatoAprendido({ dato }) {
  const [respuesta, setRespuesta] = useState(null)
  return (
    <li className={`aprendido ${respuesta === 'no' ? 'por-revisar' : ''}`}>
      <p>{dato.dato}</p>
      <p className="suave">Lo saqué de: {dato.fuente.toLowerCase()}</p>
      <AnimatePresence mode="wait" initial={false}>
        {respuesta === null ? (
          <motion.div key="pregunta" {...CAMBIO} className="confirmar" role="group" aria-label="¿Es correcto?">
            <span className="suave">¿Es correcto?</span>
            <button type="button" className="boton-texto" onClick={() => setRespuesta('si')}>
              Sí
            </button>
            <button type="button" className="boton-texto" onClick={() => setRespuesta('no')}>
              No
            </button>
          </motion.div>
        ) : (
          <motion.p key={respuesta} {...CAMBIO} className={respuesta === 'si' ? 'confirmado' : 'marcado'}>
            {respuesta === 'si' ? (
              <CheckCircle size={20} aria-hidden="true" />
            ) : (
              <Question size={20} aria-hidden="true" />
            )}
            {respuesta === 'si' ? 'Gracias, lo sigo usando.' : 'Marcado como por revisar.'}
            {respuesta === 'no' && (
              <button type="button" className="boton-texto" onClick={() => setRespuesta(null)}>
                Deshacer
              </button>
            )}
          </motion.p>
        )}
      </AnimatePresence>
    </li>
  )
}

export default function Aprendido({ cliente }) {
  return (
    <section className="tarjeta" aria-labelledby="aprendido-titulo">
      <h2 id="aprendido-titulo">Lo que aprendí de ti</h2>
      <p className="suave">Si algo no es correcto, dímelo y dejo de usarlo.</p>
      <ul className="lista-limpia lista-aprendido">
        {cliente.aprendido.map((d) => (
          <DatoAprendido key={d.id} dato={d} />
        ))}
      </ul>
    </section>
  )
}
