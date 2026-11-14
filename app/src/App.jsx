import { Link, NavLink, Navigate, Route, Routes } from 'react-router-dom'
import { cliente } from './mocks/cliente.js'
import { enSoles, fechaLarga } from './formato.js'
import ComoEstas from './pantallas/ComoEstas.jsx'
import QueViene from './pantallas/QueViene.jsx'
import QueHacer from './pantallas/QueHacer.jsx'

const PANTALLAS = [
  { ruta: '/como-estas', nombre: 'Cómo estás' },
  { ruta: '/que-viene', nombre: 'Qué viene' },
  { ruta: '/que-hacer', nombre: 'Qué hacer' },
]

function AvisoRiesgo({ riesgo }) {
  if (!riesgo) return null
  return (
    <div className="aviso" role="status">
      <div className="aviso-interior">
        <p className="aviso-texto">
          <span className="aviso-etiqueta">Aviso</span>
          El {fechaLarga(riesgo.fecha)} podrías quedar en rojo. Ese día tu saldo estaría entre{' '}
          <span className="cifra">{enSoles(riesgo.minimo)}</span> y{' '}
          <span className="cifra">{enSoles(riesgo.maximo)}</span> (confianza {riesgo.confianza}).
        </p>
        <Link className="boton" to="/que-hacer">
          Ver qué puedo hacer
        </Link>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <div className="app">
      <header className="cabecera">
        <div className="cabecera-interior">
          <Link className="marca" to="/como-estas">
            Lucas
          </Link>
          <nav className="navegacion" aria-label="Pantallas">
            {PANTALLAS.map((p) => (
              <NavLink key={p.ruta} to={p.ruta}>
                {p.nombre}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <AvisoRiesgo riesgo={cliente.diaRiesgo} />

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
