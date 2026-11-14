import { BookOpen, Calculator, CheckCircle, PaperPlaneRight, WarningCircle } from '@phosphor-icons/react'
import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import MarcaLucas from '../componentes/MarcaLucas.jsx'
import { LARGO_MAXIMO, preguntarALucas } from './clienteChat.js'
import { PREGUNTAS_SUGERIDAS } from './respuestas.js'

const API = import.meta.env.VITE_LUCAS_API ?? ''

const BIENVENIDA = {
  autor: 'lucas',
  texto: 'Hola, soy Lucas. Respondo con lo que aprendí de tus movimientos y con mi pronóstico de tu saldo.',
  cifras: [],
}

function Cifras({ mensaje }) {
  // ✓ solo cuando el verificador del agente aprobó; las plantillas locales siguen como «Calculado con tus datos».
  const verificadas = mensaje.origen === 'agente' && mensaje.verificado
  const Icono = verificadas ? CheckCircle : Calculator
  return (
    <ul
      className={`lista-limpia cifras-verificadas${verificadas ? ' con-verificador' : ''}`}
      aria-label={verificadas ? 'Cifras verificadas con tus datos' : 'Calculado con tus datos'}
    >
      {mensaje.cifras.map((c, i) => (
        <li key={`${i}-${c.etiqueta}`}>
          <Icono size={18} weight={verificadas ? 'fill' : 'regular'} aria-hidden="true" />
          <span>{c.etiqueta}</span>
          <strong>
            {c.valor}
            {verificadas && <span className="solo-lector"> (verificada)</span>}
          </strong>
        </li>
      ))}
    </ul>
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
  if (mensaje.autor === 'tu') {
    return (
      <li className="mensaje mensaje-tu">
        <span className="solo-lector">Tú: </span>
        {mensaje.texto}
      </li>
    )
  }
  return (
    <li className="mensaje mensaje-lucas">
      <MarcaLucas tamano={32} />
      <div className="mensaje-cuerpo">
        <span className="solo-lector">Lucas: </span>
        {mensaje.aviso && (
          <p className="aviso-chat">
            <WarningCircle size={18} aria-hidden="true" />
            <span>{mensaje.aviso}</span>
          </p>
        )}
        <p>{mensaje.texto}</p>
        {mensaje.cifras.length > 0 && <Cifras mensaje={mensaje} />}
        {mensaje.fuentes?.length > 0 && <Fuentes fuentes={mensaje.fuentes} />}
      </div>
    </li>
  )
}

function Pensando() {
  return (
    <li className="mensaje mensaje-lucas" aria-busy="true">
      <MarcaLucas tamano={32} />
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
  const [mensajes, setMensajes] = useState([BIENVENIDA])
  const [borrador, setBorrador] = useState('')
  const [pensando, setPensando] = useState(false)
  const conversacion = useRef(null)
  // Ref y no estado: dos clics en el mismo ciclo verían `pensando` aún en false.
  const ocupado = useRef(false)
  const montado = useRef(false)
  const final = useRef(null)

  // No se aborta el pedido al salir: en modo estricto React desmonta y vuelve a montar, y la
  // pregunta que llega desde el Resumen se perdería. La espera ya tiene tope en clienteChat.js.
  useEffect(() => {
    montado.current = true
    return () => {
      montado.current = false
    }
  }, [])

  async function preguntar(texto) {
    const limpio = texto.trim()
    if (!limpio || ocupado.current) return
    ocupado.current = true
    setMensajes((previos) => [...previos, { autor: 'tu', texto: limpio }])
    setBorrador('')
    setPensando(true)
    const respuesta = await preguntarALucas(limpio, {
      cliente,
      persona,
      base: API,
      conversacion: conversacion.current,
    })
    ocupado.current = false
    if (!montado.current) return
    if (respuesta.conversacion) conversacion.current = respuesta.conversacion
    setMensajes((previos) => [...previos, { autor: 'lucas', ...respuesta }])
    setPensando(false)
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
      <ol className="lista-limpia mensajes" aria-live="polite">
        {mensajes.map((m, i) => (
          <Mensaje key={i} mensaje={m} />
        ))}
        {pensando && <Pensando />}
      </ol>
      <div ref={final} />

      <div className="chips" role="group" aria-label="Preguntas sugeridas">
        {PREGUNTAS_SUGERIDAS.map((p) => (
          <button key={p} type="button" className="chip" disabled={pensando} onClick={() => preguntar(p)}>
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
    </section>
  )
}
