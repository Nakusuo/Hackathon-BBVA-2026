import { BookOpen, Calculator, CheckCircle, PaperPlaneRight, WarningCircle } from '@phosphor-icons/react'
import { motion, useReducedMotion } from 'motion/react'
import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import MarcaLucas from '../componentes/MarcaLucas.jsx'
import { SUAVE } from '../movimiento.js'
import { LARGO_MAXIMO, preguntarALucas } from './clienteChat.js'
import { PREGUNTAS_SUGERIDAS } from './respuestas.js'

// Apagado hasta que exista POST /api/v1/chat en FastAPI; las demás lecturas no dependen de esto.
const AGENTE = import.meta.env.VITE_CHAT_AGENTE === 'si'

// Cada mensaje nuevo sube un poco al entrar; con «reducir movimiento» aparece quieto.
function entradaDe(reducido) {
  if (reducido) return { initial: false }
  return { initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.25, ease: SUAVE } }
}

// Las cifras van en un bloque aparte y con su rótulo visible: así se distinguen del texto del modelo.
function Cifras({ mensaje }) {
  // ✓ solo cuando el verificador del agente aprobó; las plantillas locales siguen como «Calculado con tus datos».
  const verificadas = mensaje.origen === 'agente' && mensaje.verificado
  const Icono = verificadas ? CheckCircle : Calculator
  const titulo = `cifras-${mensaje.id}`
  return (
    <div className={`cifras-verificadas${verificadas ? ' con-verificador' : ''}`}>
      <p className="cifras-titulo" id={titulo}>
        <Icono size={18} weight={verificadas ? 'fill' : 'regular'} aria-hidden="true" />
        {verificadas ? 'Cifras verificadas con tus datos' : 'Calculado con tus datos'}
      </p>
      <ul className="lista-limpia" aria-labelledby={titulo}>
        {mensaje.cifras.map((c, i) => (
          <li key={`${i}-${c.etiqueta}`}>
            <span>{c.etiqueta}</span>
            <strong>
              {c.valor}
              {verificadas && <span className="solo-lector"> (verificada)</span>}
            </strong>
          </li>
        ))}
      </ul>
    </div>
  )
}

function Fuentes({ fuentes }) {
  return (
    <div className="fuentes">
      <p className="fuentes-titulo">
        <BookOpen size={18} aria-hidden="true" /> Fuentes
      </p>
      <ul className="lista-limpia">
        {fuentes.map((f, i) => (
          <li key={`${i}-${f.id}`}>
            {f.enlace ? (
              <a href={f.enlace} target="_blank" rel="noopener noreferrer">
                {f.titulo}
              </a>
            ) : (
              f.titulo
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

function Mensaje({ mensaje }) {
  const entra = entradaDe(useReducedMotion())
  if (mensaje.autor === 'tu') {
    return (
      <motion.li {...entra} className="mensaje mensaje-tu">
        <span className="solo-lector">Tú: </span>
        {mensaje.texto}
      </motion.li>
    )
  }
  return (
    <motion.li {...entra} className="mensaje mensaje-lucas">
      {/* Con un aviso de falla Lucas no puede salir celebrando ni ahorrando. */}
      <MarcaLucas tamano={40} pose={mensaje.aviso ? 'alerta' : mensaje.pose} />
      <div className="mensaje-cuerpo">
        <span className="solo-lector">Lucas: </span>
        {mensaje.aviso && (
          <p className="aviso-chat">
            <WarningCircle size={18} aria-hidden="true" />
            <span>{mensaje.aviso}</span>
          </p>
        )}
        <p>{mensaje.texto}</p>
        {mensaje.cifras?.length > 0 && <Cifras mensaje={mensaje} />}
        {mensaje.fuentes?.length > 0 && <Fuentes fuentes={mensaje.fuentes} />}
      </div>
    </motion.li>
  )
}

function Pensando() {
  return (
    <li className="mensaje mensaje-lucas" aria-busy="true">
      <MarcaLucas tamano={40} pose="pensando" />
      <div className="mensaje-cuerpo pensando">
        <span>Lucas está pensando</span>
        <span className="puntos" aria-hidden="true">
          <span />
          <span />
          <span />
        </span>
      </div>
    </li>
  )
}

export default function Chat({ cliente, persona }) {
  const [parametros, setParametros] = useSearchParams()
  const [mensajes, setMensajes] = useState([])
  const [borrador, setBorrador] = useState('')
  const [pensando, setPensando] = useState(false)
  const conversacion = useRef(null)
  // Ref y no estado: dos clics en el mismo ciclo verían `pensando` aún en false.
  const ocupado = useRef(false)
  const montado = useRef(false)
  const siguienteId = useRef(0)
  const final = useRef(null)
  const sugerencias = useRef(null)

  // Lo ya preguntado sale de las sugerencias; si se usaron todas, vuelven a aparecer.
  const hechas = new Set(mensajes.filter((m) => m.autor === 'tu').map((m) => m.texto))
  const pendientes = PREGUNTAS_SUGERIDAS.filter((p) => !hechas.has(p))
  const visibles = pendientes.length ? pendientes : PREGUNTAS_SUGERIDAS

  // No se aborta el pedido al salir: en modo estricto React desmonta y vuelve a montar, y la
  // pregunta que llega desde el Resumen se perdería. La espera ya tiene tope en clienteChat.js.
  useEffect(() => {
    montado.current = true
    return () => {
      montado.current = false
    }
  }, [])

  function agregar(mensaje) {
    const id = siguienteId.current++
    setMensajes((previos) => [...previos, { id, ...mensaje }])
  }

  async function preguntar(texto) {
    const limpio = texto.trim()
    if (!limpio || ocupado.current) return
    ocupado.current = true
    const previas = mensajes.filter((m) => m.autor === 'tu').map((m) => m.texto)
    agregar({ autor: 'tu', texto: limpio })
    setBorrador('')
    sugerencias.current?.scrollTo?.({ left: 0 })
    setPensando(true)
    try {
      const respuesta = await preguntarALucas(limpio, {
        cliente,
        persona,
        previas,
        activo: AGENTE,
        conversacion: conversacion.current,
      })
      if (!montado.current) return
      if (respuesta.conversacion) conversacion.current = respuesta.conversacion
      agregar({ autor: 'lucas', ...respuesta })
    } finally {
      // Un fallo inesperado del front no debe dejar el chat bloqueado en «pensando».
      ocupado.current = false
      if (montado.current) setPensando(false)
    }
  }

  // Las preguntas que llegan desde el Resumen se envían solas una vez y se quitan de la dirección.
  // La referencia evita enviarla dos veces cuando React repite el efecto en modo estricto.
  const pendiente = parametros.get('q')
  const enviada = useRef(null)
  useEffect(() => {
    if (!pendiente || enviada.current === pendiente) return
    enviada.current = pendiente
    preguntar(pendiente)
    setParametros({}, { replace: true })
  })

  useEffect(() => {
    final.current?.scrollIntoView?.({ block: 'nearest' })
  }, [mensajes, pensando])

  return (
    <section className="chat" aria-label="Chat con Lucas">
      <div className="chat-bienvenida">
        <MarcaLucas tamano={56} pose="saludo" />
        <div>
          <h2>Pregúntale a Lucas</h2>
          <p>Respondo con lo que aprendí de tus movimientos y con mi pronóstico de tu saldo.</p>
        </div>
      </div>

      <ol className="lista-limpia mensajes" aria-live="polite">
        {mensajes.map((m) => (
          <Mensaje key={m.id} mensaje={m} />
        ))}
        {pensando && <Pensando />}
      </ol>
      <div ref={final} />

      <div className="chat-pie">
        <div ref={sugerencias} className="chips chips-fila" role="group" aria-label="Preguntas sugeridas">
          {visibles.map((p) => (
            <button key={p} type="button" className="chip chip-suave" disabled={pensando} onClick={() => preguntar(p)}>
              {p}
            </button>
          ))}
        </div>

        <form
          className="chat-entrada"
          onSubmit={(e) => {
            e.preventDefault()
            preguntar(borrador)
          }}
        >
          <label className="solo-lector" htmlFor="pregunta">
            Escribe tu pregunta
          </label>
          <input
            id="pregunta"
            value={borrador}
            onChange={(e) => setBorrador(e.target.value)}
            placeholder="Escribe tu pregunta"
            autoComplete="off"
            maxLength={LARGO_MAXIMO}
          />
          <button type="submit" className="icono-boton icono-boton-azul" aria-label="Enviar" disabled={pensando}>
            <PaperPlaneRight size={22} aria-hidden="true" />
          </button>
        </form>
        <p className="decision">
          No es asesoría: no recomiendo inversiones ni compra de dólares, y no muevo tu plata. Tú decides.
        </p>
      </div>
    </section>
  )
}
