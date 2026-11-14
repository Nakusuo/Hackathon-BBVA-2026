import { CaretLeft, Question } from '@phosphor-icons/react'
import { useEffect, useRef, useState } from 'react'
import { Link, Navigate, NavLink, useLocation, useNavigate, useOutletContext, useParams } from 'react-router-dom'
import MarcaLucas from '../componentes/MarcaLucas.jsx'
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
  const { vista, persona, alternarTip } = useOutletContext()
  const navegar = useNavigate()
  const { hash } = useLocation()
  // Solo se abre sola si la primera entrada es al Resumen, que es donde están sus tres marcas.
  const [guiaAbierta, setGuiaAbierta] = useState(() => !guiaYaVista() && seccion === 'resumen')
  const botonGuia = useRef(null)

  function abrirGuia() {
    if (seccion !== 'resumen') navegar('/lucas/resumen')
    setGuiaAbierta(true)
  }

  function cerrarGuia() {
    setGuiaAbierta(false)
    botonGuia.current?.focus()
  }

  // React Router no baja solo hasta un ancla: los enlaces a #tips llegan aquí.
  useEffect(() => {
    if (hash) document.getElementById(hash.slice(1))?.scrollIntoView({ block: 'start' })
  }, [hash, seccion])

  if (!SECCIONES.some((s) => s.id === seccion)) return <Navigate to="/lucas/resumen" replace />

  return (
    <div className="lucas">
      <header className="lucas-cabecera">
        <div className="lucas-barra">
          <Link to="/banca" className="volver">
            <CaretLeft size={20} aria-hidden="true" />
            Inicio
          </Link>
          <button
            ref={botonGuia}
            type="button"
            className="icono-boton icono-boton-suave"
            aria-label="Ver la guía"
            onClick={abrirGuia}
          >
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
        {seccion === 'resumen' && <Resumen cliente={vista} alternarTip={alternarTip} animarEntrada={!guiaAbierta} />}
        {seccion === 'gastos' && <Gastos cliente={vista} />}
        {seccion === 'que-viene' && <QueViene cliente={vista} />}
        {seccion === 'chat' && <Chat cliente={vista} persona={persona} />}
      </main>

      {guiaAbierta && seccion === 'resumen' && <Guia alCerrar={cerrarGuia} />}
    </div>
  )
}
