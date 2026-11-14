import { CalendarRange, Gauge, ListChecks } from 'lucide-react'
import { Link, NavLink, Navigate, Route, Routes } from 'react-router-dom'
import { cliente } from './mocks/cliente.js'
import ComoEstas from './pantallas/ComoEstas.jsx'
import QueViene from './pantallas/QueViene.jsx'
import QueHacer from './pantallas/QueHacer.jsx'

const PANTALLAS = [
  { ruta: '/como-estas', nombre: 'Cómo estás', Icono: Gauge },
  { ruta: '/que-viene', nombre: 'Qué viene', Icono: CalendarRange },
  { ruta: '/que-hacer', nombre: 'Qué hacer', Icono: ListChecks },
]

export default function App() {
  return (
    <div className="app">
      <header className="lateral">
        <Link className="marca" to="/como-estas">
          Lucas
        </Link>
        <nav className="navegacion" aria-label="Pantallas">
          {PANTALLAS.map(({ ruta, nombre, Icono }) => (
            <NavLink key={ruta} to={ruta}>
              <Icono size={20} aria-hidden="true" />
              <span>{nombre}</span>
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="contenido">
        <Routes>
          <Route path="/" element={<Navigate to="/como-estas" replace />} />
          <Route path="/como-estas" element={<ComoEstas cliente={cliente} />} />
          <Route path="/que-viene" element={<QueViene cliente={cliente} />} />
          <Route path="/que-hacer" element={<QueHacer cliente={cliente} />} />
          <Route path="*" element={<Navigate to="/como-estas" replace />} />
        </Routes>
      </main>
    </div>
  )
}
