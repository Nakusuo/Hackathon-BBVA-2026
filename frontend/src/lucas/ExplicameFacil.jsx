import { BookOpenText, X } from '@phosphor-icons/react'
import { AnimatePresence, motion } from 'motion/react'
import { useId, useRef, useState } from 'react'

export default function ExplicameFacil({ puntos }) {
  const [abierto, setAbierto] = useState(false)
  const id = useId()
  const boton = useRef(null)

  function cerrar() {
    setAbierto(false)
    boton.current?.focus()
  }

  return (
    <div className="facil">
      <button
        ref={boton}
        type="button"
        className="chip facil-boton"
        aria-expanded={abierto}
        aria-controls={id}
        onClick={() => setAbierto(!abierto)}
      >
        <BookOpenText size={20} aria-hidden="true" />
        Explícamelo fácil
      </button>
      <AnimatePresence initial={false}>
        {abierto && (
          <motion.section
            id={id}
            className="facil-panel"
            aria-label="Explicación fácil"
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.18 }}
          >
            <dl>
              {puntos.map((p) => (
                <div key={p.termino}>
                  <dt>{p.termino}</dt>
                  <dd>{p.texto}</dd>
                </div>
              ))}
            </dl>
            <button type="button" className="boton-texto facil-cerrar" onClick={cerrar}>
              <X size={18} aria-hidden="true" />
              Entendido
            </button>
          </motion.section>
        )}
      </AnimatePresence>
    </div>
  )
}
