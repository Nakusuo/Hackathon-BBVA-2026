import { CaretLeft, Question } from '@phosphor-icons/react'
import { useState } from 'react'
import { Link, Navigate, NavLink, useParams } from 'react-router-dom'
import MarcaLucas from '../componentes/MarcaLucas.jsx'
import { cliente, persona } from '../mocks/cliente.js'
import Chat from './Chat.jsx'
import Gastos from './Gastos.jsx'
import Guia from './Guia.jsx'
import { guiaYaVista } from './guiaVista.js'
import QueViene from './QueViene.jsx'
import Resumen from './Resumen.jsx'

const SECCIONES = [
  { id: 'resumen', nombre: 'Resumen' },
  { id: 'gastos', nombre: 'Gastos' },
  { id: 'que-viene', nombre: 'Qué viene' },
  { id: 'chat', nombre: 'Chat' },
]

export default function EspacioLucas() {
  const { seccion } = useParams()
  const [guiaAbierta, setGuiaAbierta] = useState(() => !guiaYaVista())

  if (!SECCIONES.some((s) => s.id === seccion)) return <Navigate to="/lucas/resumen" replace />

  return (
    <div className="lucas">
      <header className="lucas-cabecera">
        <div className="lucas-barra">
          <Link to="/banca" className="volver">
            <CaretLeft size={20} aria-hidden="true" />
            Mi Banca
          </Link>
          <button type="button" className="icono-boton icono-boton-suave" aria-label="Ver la guía" onClick={() => setGuiaAbierta(true)}>
            <Question size={24} aria-hidden="true" />
          </button>
        </div>
        <div className="lucas-titulo">
          <MarcaLucas tamano={44} />
          <div>
            <h1>Lucas</h1>
            <p className="suave">Tu copiloto de plata</p>
          </div>
        </div>
        <nav className="pestanas" aria-label="Secciones de Lucas">
          {SECCIONES.map((s) => (
            <NavLink key={s.id} to={`/lucas/${s.id}`} data-guia={s.id === 'chat' ? 'pestana-chat' : undefined}>
              {s.nombre}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="lucas-contenido">
        {seccion === 'resumen' && <Resumen cliente={cliente} />}
        {seccion === 'gastos' && <Gastos cliente={cliente} />}
        {seccion === 'que-viene' && <QueViene cliente={cliente} />}
        {seccion === 'chat' && <Chat cliente={cliente} persona={persona} />}
      </main>

      {guiaAbierta && seccion === 'resumen' && <Guia alCerrar={() => setGuiaAbierta(false)} />}
    </div>
  )
}
