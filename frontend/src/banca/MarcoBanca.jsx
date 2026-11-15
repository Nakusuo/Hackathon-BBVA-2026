import { ArrowsLeftRight, CreditCard, DotsThreeOutline, House } from '@phosphor-icons/react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { enviarGasto, CLIENTE_DEMO } from '../api/lucas.js'
import { useDatosApi } from '../api/useDatosApi.js'
import MarcaLucas from '../componentes/MarcaLucas.jsx'
import { aportar, crearMeta, editarMeta, esMetaValida } from '../lucas/metas.js'
import { agregarRegistro, esRegistroValido, sinRepetidos } from '../lucas/registro.js'
import { esPlanificadoValido } from '../lucas/planificar.js'
import { vistaCon } from '../motor/cliente.js'
import { PERSONA_INICIAL, personaPorId } from '../motor/personas.js'
import {
  CLAVE_METAS,
  CLAVE_PLANIFICADOS,
  CLAVE_REGISTRADOS,
  CLAVE_TIPS,
  guardarPersona,
  permisoDe,
  personaGuardada,
  retirarPermiso,
} from '../sesion.js'

const SIN_DEMO = 'En esta demo solo está activo Lucas.'

function leerLista(clave, esValido) {
  try {
    const guardado = JSON.parse(window.localStorage.getItem(clave))
    return Array.isArray(guardado) ? guardado.filter(esValido) : []
  } catch {
    return []
  }
}

function useListaGuardada(clave, esValido) {
  const [lista, setLista] = useState(() => leerLista(clave, esValido))
  useEffect(() => {
    try {
      window.localStorage.setItem(clave, JSON.stringify(lista))
    } catch {
      // Sin almacenamiento lo elegido dura solo esta visita; la app sigue funcionando.
    }
  }, [clave, lista])
  return [lista, setLista]
}

function nuevoId(prefijo) {
  return `${prefijo}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`
}

export default function MarcoBanca() {
  const [aviso, setAviso] = useState('')
  const temporizador = useRef(null)
  const [personaId, setPersonaId] = useState(personaGuardada)
  const [permiso, setPermiso] = useState(() => permisoDe(personaGuardada()))
  const [elegidos, setElegidos] = useListaGuardada(CLAVE_TIPS, (id) => typeof id === 'string')
  const [planificados, setPlanificados] = useListaGuardada(CLAVE_PLANIFICADOS, esPlanificadoValido)
  const [registrados, setRegistrados] = useListaGuardada(CLAVE_REGISTRADOS, esRegistroValido)
  const [metas, setMetas] = useListaGuardada(CLAVE_METAS, esMetaValida)
  const vista = useMemo(
    () => vistaCon(elegidos, personaId, [], planificados, sinRepetidos(registrados)),
    [elegidos, personaId, planificados, registrados],
  )
  const persona = personaPorId(personaId).persona
  const datosApi = useDatosApi()

  // Tips, lo planificado y las metas son de una persona: al cambiarla o al retirar el permiso se olvidan.
  function olvidarLoDeLaPersona() {
    setElegidos([])
    setPlanificados([])
    setRegistrados([])
    setMetas([])
  }

  function elegirPersona(id) {
    if (id === personaId) return
    guardarPersona(id)
    setPersonaId(id)
    setPermiso(permisoDe(id))
    olvidarLoDeLaPersona()
  }

  function retirarPermisoActual() {
    retirarPermiso(personaId)
    setPermiso(null)
    olvidarLoDeLaPersona()
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

  // Primero queda guardado aquí (manda el motor); el servidor es un aviso aparte y solo conoce a la persona de la API.
  // Devuelve 'enviado', 'solo-aqui' (no aplica o ya estaba) o 'sin-servidor' si falló, para que la pantalla lo diga.
  async function registrarMovimiento(movimiento) {
    if (registrados.some((m) => m.id === movimiento.id)) return 'solo-aqui'
    setRegistrados((previos) => agregarRegistro(previos, movimiento))
    if (movimiento.tipo !== 'gasto' || personaId !== PERSONA_INICIAL) return 'solo-aqui'
    try {
      await enviarGasto(movimiento, { id: CLIENTE_DEMO })
      return 'enviado'
    } catch (error) {
      console.warn('El gasto quedó solo en este navegador', error)
      return 'sin-servidor'
    }
  }

  const acciones = {
    registrarMovimiento,
    agregarPlanificado: (movimiento) => setPlanificados((previos) => [...previos, { ...movimiento, id: nuevoId('plan') }]),
    quitarPlanificado: (id) => setPlanificados((previos) => previos.filter((m) => m.id !== id)),
    crearMeta: (datos) => setMetas((previas) => [...previas, crearMeta(datos, nuevoId('meta'))]),
    aportarMeta: (id, monto) => setMetas((previas) => previas.map((m) => (m.id === id ? aportar(m, monto) : m))),
    quitarMeta: (id) => setMetas((previas) => previas.filter((m) => m.id !== id)),
    editarMeta: (id, datos) => setMetas((previas) => previas.map((m) => (m.id === id ? editarMeta(m, datos) : m))),
    // Deshacer «Quitar»: vuelve a su lugar, porque el apartado se reparte en el orden de creación.
    restaurarMeta: (meta, lugar) =>
      setMetas((previas) =>
        previas.some((m) => m.id === meta.id) ? previas : [...previas.slice(0, lugar), meta, ...previas.slice(lugar)],
      ),
  }

  useEffect(() => () => window.clearTimeout(temporizador.current), [])

  return (
    <div className="exterior">
      <div className="marco">
        <Outlet
          context={{
            avisarSinDemo,
            vista,
            persona,
            alternarTip,
            personaId,
            elegirPersona,
            permiso,
            retirarPermisoActual,
            datosApi,
            metas,
            ...acciones,
          }}
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
    </div>
  )
}
