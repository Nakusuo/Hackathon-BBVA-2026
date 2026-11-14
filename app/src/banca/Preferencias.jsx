import { CaretLeft, Moon, Sun } from '@phosphor-icons/react'
import { motion } from 'motion/react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { aplicarTema, temaGuardado } from '../tema.js'

const TEMAS = [
  { id: 'claro', nombre: 'Claro', Icono: Sun },
  { id: 'oscuro', nombre: 'Oscuro', Icono: Moon },
]

export default function Preferencias() {
  const [tema, setTema] = useState(temaGuardado)

  function elegir(id) {
    setTema(id)
    aplicarTema(id)
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
        <div className="selector-tema" role="group" aria-label="Tema de la app">
          {TEMAS.map(({ id, nombre, Icono }) => (
            <button key={id} type="button" aria-pressed={tema === id} onClick={() => elegir(id)}>
              {tema === id && <motion.span layoutId="tema-activo" className="selector-tema-fondo" />}
              <Icono size={20} aria-hidden="true" />
              {nombre}
            </button>
          ))}
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
