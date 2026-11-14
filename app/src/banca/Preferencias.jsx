import { CaretLeft, Moon, ShieldCheck } from '@phosphor-icons/react'
import { motion } from 'motion/react'
import { useState } from 'react'
import { Link, useOutletContext } from 'react-router-dom'
import SelectorPersona from '../componentes/SelectorPersona.jsx'
import { fechaCorta } from '../formato.js'
import { borrarAvisosGuardados } from '../lucas/avisosGuardados.js'
import { aplicarTema, temaGuardado } from '../tema.js'

function Privacidad() {
  const { permiso, retirarPermisoActual } = useOutletContext()
  const [confirmando, setConfirmando] = useState(false)
  const [retirado, setRetirado] = useState(false)

  function retirar() {
    retirarPermisoActual()
    setConfirmando(false)
    setRetirado(true)
  }

  return (
    <section className="tarjeta" aria-labelledby="privacidad-titulo">
      <h2 id="privacidad-titulo">Privacidad</h2>
      <div className="ajuste ajuste-permiso">
        <ShieldCheck size={24} aria-hidden="true" />
        <span className="ajuste-lineas">
          <span className="ajuste-nombre">Permiso para Lucas</span>
          <span className="suave" role="status">
            {permiso
              ? `Activo desde el ${fechaCorta(permiso)}.`
              : `${retirado ? 'Retirado. ' : ''}Lucas está apagado y no usa tus datos.`}
          </span>
        </span>
      </div>
      <p className="suave">
        Lucas usa tus movimientos, pagos, cobros y un perfil resumido solo para calcular tu pronóstico y sus tips. En esta demo los datos son
        sintéticos.
      </p>
      {permiso && !confirmando && (
        <button type="button" className="boton boton-borde" onClick={() => setConfirmando(true)}>
          Retirar permiso
        </button>
      )}
      {permiso && confirmando && (
        <div className="confirmar-retiro" role="group" aria-labelledby="retiro-pregunta">
          <p id="retiro-pregunta">Lucas se apaga y borra los tips que elegiste. ¿Retiras el permiso?</p>
          <div className="confirmar-retiro-botones">
            <button type="button" className="boton boton-riesgo" onClick={retirar}>
              Sí, retirar
            </button>
            <button type="button" className="boton-texto" onClick={() => setConfirmando(false)}>
              Cancelar
            </button>
          </div>
        </div>
      )}
      {!permiso && (
        <Link to="/consentimiento" state={{ volver: '/lucas/resumen' }} className="boton">
          Activar Lucas
        </Link>
      )}
    </section>
  )
}

export default function Preferencias() {
  const { personaId, elegirPersona } = useOutletContext()
  const [tema, setTema] = useState(temaGuardado)
  const [avisosBorrados, setAvisosBorrados] = useState(false)

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

      <section className="tarjeta" aria-labelledby="persona-titulo">
        <h2 id="persona-titulo">Demo</h2>
        <SelectorPersona valor={personaId} alCambiar={elegirPersona} />
        <p className="suave">Cambia todas las cifras de la banca y de Lucas. Cada persona da su propio permiso.</p>
      </section>

      <Privacidad />

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

      <section className="tarjeta" aria-labelledby="guardado-titulo">
        <h2 id="guardado-titulo">Tus avisos guardados en este navegador</h2>
        <p className="suave">Qué avisos viste esta semana y si te sirvieron. No guarda montos ni lo que escribes.</p>
        <button
          type="button"
          className="boton boton-secundario"
          onClick={() => {
            borrarAvisosGuardados()
            setAvisosBorrados(true)
          }}
        >
          Borrar mis avisos y opiniones
        </button>
        <p className="suave" role="status">
          {avisosBorrados && 'Listo, se borró.'}
        </p>
      </section>

      <section className="tarjeta" aria-labelledby="evidencia-titulo">
        <h2 id="evidencia-titulo">Para el jurado</h2>
        <p className="suave">Cada modelo de Lucas frente a su baseline, con la fuente de cada cifra.</p>
        <Link to="/evidencia" className="enlace">
          Ver la evidencia
        </Link>
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
