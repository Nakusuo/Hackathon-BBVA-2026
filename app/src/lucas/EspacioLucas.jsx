import { Bell, CaretLeft, Question } from '@phosphor-icons/react'
import { motion } from 'motion/react'
import { useEffect, useRef, useState } from 'react'
import { Link, Navigate, NavLink, useLocation, useNavigate, useOutletContext, useParams } from 'react-router-dom'
import EstadoDatos from '../componentes/EstadoDatos.jsx'
import MarcaLucas from '../componentes/MarcaLucas.jsx'
import Aprendido from './Aprendido.jsx'
import Avisos from './Avisos.jsx'
import Chat from './Chat.jsx'
import Gastos from './Gastos.jsx'
import GastosDetalle from './GastosDetalle.jsx'
import Guia from './Guia.jsx'
import { guiaYaVista } from './guiaVista.js'
import QueViene from './QueViene.jsx'
import Resumen from './Resumen.jsx'
import Salud from './Salud.jsx'

const SECCIONES = [
  { id: 'resumen', nombre: 'Resumen' },
  { id: 'gastos', nombre: 'Gastos' },
  { id: 'que-viene', nombre: 'Qué viene' },
  { id: 'chat', nombre: 'Chat' },
]
// Pantallas de detalle: se abren desde los bloques del Resumen y no tienen pestaña propia.
const DETALLES = { aprendido: 'resumen', salud: 'resumen', 'gastos-detalle': 'gastos', avisos: 'resumen' }

export default function EspacioLucas() {
  const { seccion } = useParams()
  const { vista, persona, alternarTip, permiso, datosApi } = useOutletContext()
  const navegar = useNavigate()
  const { hash, pathname } = useLocation()
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

  // Sin permiso no se muestra nada de Lucas: primero se pide, y luego se vuelve aquí. Con la API, el servidor también
  // tendrá que negar `/yo/...` sin permiso; hoy el cálculo local sigue corriendo aunque no se muestre.
  if (!permiso) return <Navigate to="/consentimiento" replace state={{ volver: pathname }} />
  if (!SECCIONES.some((s) => s.id === seccion) && !DETALLES[seccion]) return <Navigate to="/lucas/resumen" replace />

  return (
    <div className="lucas">
      <header className="lucas-cabecera">
        <div className="lucas-barra">
          <Link to="/banca" className="volver">
            <CaretLeft size={20} aria-hidden="true" />
            Inicio
          </Link>
          <div className="lucas-titulo">
            <MarcaLucas tamano={36} />
            <h1>Lucas</h1>
          </div>
          <div className="lucas-iconos">
            <Link to="/lucas/avisos" className="icono-boton icono-boton-suave" aria-label="Avisos">
              <Bell size={24} aria-hidden="true" />
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
        </div>
        <nav className="pestanas" aria-label="Secciones de Lucas">
          {SECCIONES.map((s) => (
            <NavLink key={s.id} to={`/lucas/${s.id}`} data-guia={s.id === 'chat' ? 'pestana-chat' : undefined}>
              {({ isActive }) => (
                <>
                  {s.nombre}
                  {(isActive || DETALLES[seccion] === s.id) && (
                    <motion.span layoutId="pestana-activa" className="pestana-barra" />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="lucas-contenido">
        {seccion === 'resumen' && <Resumen cliente={vista} alternarTip={alternarTip} animarEntrada={!guiaAbierta} />}
        {seccion === 'gastos' && <Gastos cliente={vista} />}
        {seccion === 'que-viene' && <QueViene cliente={vista} />}
        {seccion === 'chat' && <Chat cliente={vista} persona={persona} />}
        {DETALLES[seccion] && (
          <Link to={`/lucas/${DETALLES[seccion]}`} className="volver">
            <CaretLeft size={20} aria-hidden="true" />
            {SECCIONES.find((s) => s.id === DETALLES[seccion]).nombre}
          </Link>
        )}
        {seccion === 'aprendido' && <Aprendido cliente={vista} />}
        {seccion === 'salud' && <Salud cliente={vista} />}
        {seccion === 'gastos-detalle' && <GastosDetalle cliente={vista} alternarTip={alternarTip} />}
        {seccion === 'avisos' && <Avisos cliente={vista} />}
        {/* Al final: las cifras de arriba no dependen del servidor, así que el aviso no les quita el primer plano. */}
        <EstadoDatos estado={datosApi.estado} />
      </main>

      {guiaAbierta && seccion === 'resumen' && <Guia alCerrar={cerrarGuia} />}
    </div>
  )
}
