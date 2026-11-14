import { CaretLeft, Moon } from '@phosphor-icons/react'
import { motion } from 'motion/react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { aplicarTema, temaGuardado } from '../tema.js'

export default function Preferencias() {
  const [tema, setTema] = useState(temaGuardado)

  const oscuro = tema === 'oscuro'

  function alternar() {
    const nuevo = oscuro ? 'claro' : 'oscuro'
    setTema(nuevo)
    aplicarTema(nuevo)
  }

  return (
    <main className="preferencias">
      <Link to="/banca" className="volver">
        <CaretLeft size={20} aria-hidden="true" />
        Inicio
      </Link>
      <h1>Preferencias</h1>

      <section className="tarjeta" aria-labelledby="apariencia-titulo">
        <h2 id="apariencia-titulo">Apariencia</h2>
        <div className="ajuste">
          <Moon size={24} aria-hidden="true" />
          <span id="oscuro-etiqueta" className="ajuste-nombre">
            Modo oscuro
          </span>
          <button
            type="button"
            role="switch"
            aria-checked={oscuro}
            aria-labelledby="oscuro-etiqueta"
            className="interruptor"
            onClick={alternar}
          >
            <motion.span layout transition={{ type: 'spring', stiffness: 500, damping: 32 }} />
          </button>
        </div>
        <p className="suave">Se aplica a toda la app y se recuerda en este navegador.</p>
      </section>

      <section className="tarjeta" aria-labelledby="creditos-titulo">
        <h2 id="creditos-titulo">Créditos</h2>
        <ul className="lista-limpia creditos">
          <li>La mascota de Lucas está inspirada en el trabajo de mascotas de la ilustradora @aokulova.</li>
          <li>Tipografía Manrope, con licencia SIL Open Font.</li>
          <li>Íconos de Phosphor Icons, con licencia MIT.</li>
          <li>Banco Vértice es un banco ficticio con datos sintéticos.</li>
        </ul>
      </section>
    </main>
  )
}
