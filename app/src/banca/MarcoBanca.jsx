import { ArrowsLeftRight, CreditCard, DotsThreeOutline, House } from '@phosphor-icons/react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import MarcaLucas from '../componentes/MarcaLucas.jsx'
import { vistaCon } from '../mocks/cliente.js'
import { personaPorId } from '../mocks/personas.js'
import { CLAVE_TIPS, guardarPersona, permisoDe, personaGuardada, retirarPermiso } from '../sesion.js'

const SIN_DEMO = 'En esta demo solo está activo Lucas.'

function leerElegidos() {
  try {
    const guardado = JSON.parse(window.localStorage.getItem(CLAVE_TIPS))
    return Array.isArray(guardado) ? guardado : []
  } catch {
    return []
  }
}

export default function MarcoBanca() {
  const [aviso, setAviso] = useState('')
  const temporizador = useRef(null)
  const [personaId, setPersonaId] = useState(personaGuardada)
  const [permiso, setPermiso] = useState(() => permisoDe(personaGuardada()))
  const [elegidos, setElegidos] = useState(leerElegidos)
  const vista = useMemo(() => vistaCon(elegidos, personaId), [elegidos, personaId])
  const persona = personaPorId(personaId).persona

  function elegirPersona(id) {
    if (id === personaId) return
    guardarPersona(id)
    setPersonaId(id)
    setPermiso(permisoDe(id))
    setElegidos([])
  }

  function retirarPermisoActual() {
    retirarPermiso(personaId)
    setPermiso(null)
    setElegidos([])
  }

  // Cada clic reinicia el tiempo; si no, el temporizador de un clic anterior borraba el aviso nuevo antes de leerlo.
  // Se vacía un instante antes para que el lector de pantalla vuelva a anunciar el mismo texto.
  function avisarSinDemo() {
    setAviso('')
    window.clearTimeout(temporizador.current)
    window.requestAnimationFrame(() => setAviso(SIN_DEMO))
    temporizador.current = window.setTimeout(() => setAviso(''), 2500)
  }

  function alternarTip(id) {
    setElegidos((previos) => (previos.includes(id) ? previos.filter((e) => e !== id) : [...previos, id]))
  }

  useEffect(() => {
    try {
      window.localStorage.setItem(CLAVE_TIPS, JSON.stringify(elegidos))
    } catch {
      // Sin almacenamiento los tips elegidos duran solo esta visita; la app sigue funcionando.
    }
  }, [elegidos])

  useEffect(() => () => window.clearTimeout(temporizador.current), [])

  return (
    <div className="exterior">
      <div className="marco">
        <Outlet
          context={{ avisarSinDemo, vista, persona, alternarTip, personaId, elegirPersona, permiso, retirarPermisoActual }}
        />

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
          <NavLink to="/preferencias" className="barra-item">
            <DotsThreeOutline size={24} aria-hidden="true" />
            <span>Más</span>
          </NavLink>
        </nav>

        <p className="aviso-flotante" role="status">
          {aviso}
        </p>
      </div>
      <p className="nota-demo">
        Banco Vértice es un banco ficticio con datos sintéticos. Lucas podría integrarse en cualquier banca.
      </p>
    </div>
  )
}
