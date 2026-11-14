import { Calculator, PaperPlaneRight } from '@phosphor-icons/react'
import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import MarcaLucas from '../componentes/MarcaLucas.jsx'
import { PREGUNTAS_SUGERIDAS, responder } from './respuestas.js'

const BIENVENIDA = {
  autor: 'lucas',
  texto: 'Hola, soy Lucas. Respondo con lo que aprendí de tus movimientos y con mi pronóstico de tu saldo.',
  cifras: [],
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
        <p>{mensaje.texto}</p>
        {mensaje.cifras.length > 0 && (
          <ul className="lista-limpia cifras-verificadas" aria-label="Calculado con tus datos">
            {mensaje.cifras.map((c) => (
              <li key={c.etiqueta}>
                <Calculator size={18} aria-hidden="true" />
                <span>{c.etiqueta}</span>
                <strong>{c.valor}</strong>
              </li>
            ))}
          </ul>
        )}
      </div>
    </li>
  )
}

export default function Chat({ cliente, persona }) {
  const [parametros, setParametros] = useSearchParams()
  const [mensajes, setMensajes] = useState([BIENVENIDA])
  const [borrador, setBorrador] = useState('')
  const final = useRef(null)

  function preguntar(texto) {
    const limpio = texto.trim()
    if (!limpio) return
    const respuesta = responder(limpio, cliente, persona)
    setMensajes((previos) => [...previos, { autor: 'tu', texto: limpio }, { autor: 'lucas', ...respuesta }])
    setBorrador('')
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
  }, [mensajes])

  return (
    <section className="chat" aria-label="Chat con Lucas">
      <ol className="lista-limpia mensajes" aria-live="polite">
        {mensajes.map((m, i) => (
          <Mensaje key={i} mensaje={m} />
        ))}
      </ol>
      <div ref={final} />

      <div className="chips" role="group" aria-label="Preguntas sugeridas">
        {PREGUNTAS_SUGERIDAS.map((p) => (
          <button key={p} type="button" className="chip" onClick={() => preguntar(p)}>
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
        />
        <button type="submit" className="icono-boton icono-boton-azul" aria-label="Enviar">
          <PaperPlaneRight size={22} aria-hidden="true" />
        </button>
      </form>
      <p className="decision">No es asesoría y no muevo tu plata: tú decides.</p>
    </section>
  )
}
