import { ArrowsLeftRight, CreditCard, DotsThreeOutline, House } from '@phosphor-icons/react'
import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import MarcaLucas from '../componentes/MarcaLucas.jsx'

const SIN_DEMO = 'En esta demo solo está activo Lucas.'

export default function MarcoBanca() {
  const [aviso, setAviso] = useState('')
  const temporizador = useRef(null)

  // Cada clic reinicia el tiempo; si no, el temporizador de un clic anterior borraba el aviso nuevo antes de leerlo.
  function avisarSinDemo() {
    setAviso(SIN_DEMO)
    window.clearTimeout(temporizador.current)
    temporizador.current = window.setTimeout(() => setAviso(''), 2500)
  }

  useEffect(() => () => window.clearTimeout(temporizador.current), [])

  return (
    <div className="exterior">
      <div className="marco">
        <Outlet context={{ avisarSinDemo }} />

        <nav className="barra-inferior" aria-label="Menú principal">
          <NavLink to="/banca" className="barra-item">
            <House size={24} aria-hidden="true" />
            <span>Inicio</span>
          </NavLink>
          <button type="button" className="barra-item" onClick={avisarSinDemo}>
            <ArrowsLeftRight size={24} aria-hidden="true" />
            <span>Pagos</span>
          </button>
          <NavLink to="/lucas" className="barra-item barra-lucas">
            <MarcaLucas tamano={48} />
            <span>Lucas</span>
          </NavLink>
          <button type="button" className="barra-item" onClick={avisarSinDemo}>
            <CreditCard size={24} aria-hidden="true" />
            <span>Tarjetas</span>
          </button>
          <button type="button" className="barra-item" onClick={avisarSinDemo}>
            <DotsThreeOutline size={24} aria-hidden="true" />
            <span>Más</span>
          </button>
        </nav>

        <p className="aviso-flotante" role="status">
          {aviso}
        </p>
      </div>
      <p className="nota-demo">Banca de ejemplo con datos sintéticos. Lucas podría integrarse en cualquier banca.</p>
    </div>
  )
}
