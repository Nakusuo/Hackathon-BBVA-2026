import { BookOpen, Calculator, CaretRight, CheckCircle, ListBullets, PaperPlaneRight, Target, WarningCircle } from '@phosphor-icons/react'
import { motion, useReducedMotion } from 'motion/react'
import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import MarcaLucas from '../componentes/MarcaLucas.jsx'
import { enSoles, fechaCorta } from '../formato.js'
import { SUAVE } from '../movimiento.js'
import { LARGO_MAXIMO, preguntarALucas } from './clienteChat.js'
import { metaDesdePropuesta } from './metas.js'
import { PREGUNTAS_SUGERIDAS } from './respuestas.js'
import { burbujasDe } from './textoChat.js'

// Apagado hasta que exista POST /api/v1/chat en FastAPI; las demás lecturas no dependen de esto.
const AGENTE = import.meta.env.VITE_CHAT_AGENTE === 'si'

// Lucas «escribe» al menos este tiempo: una plantilla responde al instante y el salto de golpe no deja ver quién habla.
const ESCRIBIENDO_MINIMO_MS = 700
// Cada bloque de la respuesta entra un poco después del anterior, como si se fuera escribiendo.
const PASO_ENTRE_BLOQUES_S = 0.22

// Cada mensaje nuevo sube un poco al entrar; con «reducir movimiento» aparece quieto.
function entradaDe(reducido, bloquesAntes = 0) {
  if (reducido) return { initial: false }
  return {
    initial: { opacity: 0, y: 8 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.25, ease: SUAVE, delay: bloquesAntes * PASO_ENTRE_BLOQUES_S },
  }
}

function Partes({ partes }) {
  return partes.map((p, i) => (p.fuerte ? <strong key={i}>{p.texto}</strong> : p.texto))
}

// Una burbuja: título, párrafos y listas, con las cifras resaltadas. `desde` es cuántos bloques ya se mostraron antes.
function Bloques({ bloques, desde }) {
  const reducido = useReducedMotion()
  const entrada = (i) =>
    reducido
      ? { initial: false }
      : {
          initial: { opacity: 0, y: 6 },
          animate: { opacity: 1, y: 0 },
          transition: { duration: 0.3, ease: SUAVE, delay: (desde + i) * PASO_ENTRE_BLOQUES_S },
        }
  return bloques.map((bloque, i) => {
    if (bloque.tipo === 'titulo') {
      return (
        <motion.p key={i} className="mensaje-titulo" {...entrada(i)}>
          {bloque.texto}
        </motion.p>
      )
    }
    if (bloque.tipo === 'lista') {
      return (
        <motion.ul key={i} className="mensaje-lista" {...entrada(i)}>
          {bloque.items.map((item, j) => (
            <li key={j}>
              <Partes partes={item} />
            </li>
          ))}
        </motion.ul>
      )
    }
    return (
      <motion.p key={i} {...entrada(i)}>
        <Partes partes={bloque.partes} />
      </motion.p>
    )
  })
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

// El plan que se acordó en el chat pasa a Metas solo si la persona lo pide. Desde ahí se edita y Lucas avisa al cobrar.
function GuardarMeta({ propuesta, cliente, metas, alCrearMeta, alEditarMeta }) {
  const revision = metaDesdePropuesta(propuesta, { hoy: cliente.hoy, primerApartado: cliente.proximoIngreso.fecha })
  if (!revision.datos) return null
  const { nombre, objetivo, fecha } = revision.datos
  const existente = metas.find((m) => m.nombre.toLowerCase() === nombre.toLowerCase())
  // Un plan nuevo para la misma meta (otro plazo u otro precio) la actualiza; lo ya ahorrado se conserva.
  const cambio = existente && (existente.objetivo !== objetivo || existente.fecha !== fecha)
  const conAnio = (f) => `${fechaCorta(f)}${f.slice(0, 4) === cliente.hoy.slice(0, 4) ? '' : ` de ${f.slice(0, 4)}`}`
  return (
    <div className="guardar-meta">
      <p className="guardar-meta-titulo">
        <Target size={18} aria-hidden="true" />
        {nombre}
      </p>
      <p>
        <b>{enSoles(objetivo)}</b> para el {conAnio(fecha)}
      </p>
      {cambio ? (
        <>
          <p className="suave">
            Hoy la tienes en {enSoles(existente.objetivo)} para el {conAnio(existente.fecha)}.
          </p>
          <button type="button" className="boton boton-chico" onClick={() => alEditarMeta(existente.id, { objetivo, fecha })}>
            Actualizar meta
          </button>
        </>
      ) : existente ? (
        <p className="guardar-meta-hecho" role="status">
          <CheckCircle size={18} weight="fill" aria-hidden="true" />
          <span>
            Está en tus metas.{' '}
            <Link className="enlace" to="/lucas/metas">
              Ver o editar
            </Link>
          </span>
        </p>
      ) : (
        <button type="button" className="boton boton-chico" onClick={() => alCrearMeta(revision.datos)}>
          Crear meta
        </button>
      )}
    </div>
  )
}

function Mensaje({ mensaje, cliente, metas, alCrearMeta, alEditarMeta }) {
  const reducido = useReducedMotion()
  const entra = entradaDe(reducido)
  if (mensaje.autor === 'tu') {
    return (
      <motion.li {...entra} className="mensaje mensaje-tu">
        <span className="solo-lector">Tú: </span>
        {mensaje.texto}
      </motion.li>
    )
  }
  // Una respuesta con varios bloques se reparte en burbujas; cada una entra cuando termina de «escribirse» la anterior.
  const burbujas = burbujasDe(mensaje.texto)
  const inicioDe = burbujas.reduce((inicios, b) => [...inicios, inicios.at(-1) + b.length], [0])
  return (
    <motion.li {...entra} className="mensaje mensaje-lucas">
      {/* Con un aviso de falla Lucas no puede salir celebrando ni ahorrando. */}
      <MarcaLucas tamano={40} pose={mensaje.aviso ? 'alerta' : mensaje.pose} />
      <div className="mensaje-burbujas">
        <span className="solo-lector">Lucas: </span>
        {burbujas.map((bloques, i) => (
          <motion.div key={i} className="mensaje-cuerpo" {...(i ? entradaDe(reducido, inicioDe[i]) : { initial: false })}>
            {i === 0 && mensaje.aviso && (
              <p className="aviso-chat">
                <WarningCircle size={18} aria-hidden="true" />
                <span>{mensaje.aviso}</span>
              </p>
            )}
            <Bloques bloques={bloques} desde={inicioDe[i]} />
            {i === burbujas.length - 1 && mensaje.cifras?.length > 0 && <Cifras mensaje={mensaje} />}
            {i === burbujas.length - 1 && mensaje.fuentes?.length > 0 && <Fuentes fuentes={mensaje.fuentes} />}
            {i === burbujas.length - 1 && mensaje.propuesta && alCrearMeta && (
              <GuardarMeta
                propuesta={mensaje.propuesta}
                cliente={cliente}
                metas={metas}
                alCrearMeta={alCrearMeta}
                alEditarMeta={alEditarMeta}
              />
            )}
          </motion.div>
        ))}
      </div>
    </motion.li>
  )
}

function Pensando() {
  return (
    <li className="mensaje mensaje-lucas" aria-busy="true">
      <MarcaLucas tamano={40} pose="pensando" />
      <div className="mensaje-cuerpo pensando">
        <span className="solo-lector">Lucas está escribiendo</span>
        <span className="puntos" aria-hidden="true">
          <span />
          <span />
          <span />
        </span>
      </div>
    </li>
  )
}

export default function Chat({ cliente, persona, metas = [], alCrearMeta, alEditarMeta }) {
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
  // Las preguntas frecuentes se ven abiertas al empezar; después de preguntar se pliegan en un botón.
  const [faqAbierto, setFaqAbierto] = useState(true)

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
    // Lo que la persona escribió antes: así una meta dada en dos mensajes se sigue entendiendo.
    const previas = mensajes.filter((m) => m.autor === 'tu').map((m) => m.texto)
    agregar({ autor: 'tu', texto: limpio })
    setBorrador('')
    setFaqAbierto(false)
    setPensando(true)
    try {
      const [respuesta] = await Promise.all([
        preguntarALucas(limpio, { cliente, persona, activo: AGENTE, previas, conversacion: conversacion.current }),
        new Promise((listo) => setTimeout(listo, ESCRIBIENDO_MINIMO_MS)),
      ])
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
          <p>¿En qué te ayudo hoy?</p>
        </div>
      </div>

      <ol className="lista-limpia mensajes" aria-live="polite">
        {mensajes.map((m) => (
          <Mensaje
            key={m.id}
            mensaje={m}
            cliente={cliente}
            metas={metas}
            alCrearMeta={alCrearMeta}
            alEditarMeta={alEditarMeta}
          />
        ))}
        {pensando && <Pensando />}
      </ol>
      <div ref={final} className="chat-final" />

      <div className="chat-pie">
        {faqAbierto && (
          <div
            id="faq"
            className="faq"
            role="group"
            aria-labelledby="faq-titulo"
            onKeyDown={(e) => e.key === 'Escape' && mensajes.length > 0 && setFaqAbierto(false)}
          >
            <p id="faq-titulo" className="faq-titulo">
              Preguntas frecuentes
            </p>
            <ul className="lista-limpia faq-lista">
              {visibles.map((p) => (
                <li key={p}>
                  <button type="button" className="faq-opcion" disabled={pensando} onClick={() => preguntar(p)}>
                    <span>{p}</span>
                    <CaretRight size={18} aria-hidden="true" />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        <form
          className="chat-entrada"
          onSubmit={(e) => {
            e.preventDefault()
            preguntar(borrador)
          }}
        >
          {mensajes.length > 0 && (
            <button
              type="button"
              className="icono-boton icono-boton-suave"
              aria-label="Preguntas frecuentes"
              aria-expanded={faqAbierto}
              aria-controls="faq"
              onClick={() => setFaqAbierto(!faqAbierto)}
            >
              <ListBullets size={22} aria-hidden="true" />
            </button>
          )}
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
        <p className="decision">Orientación, no asesoría. Tú decides.</p>
      </div>
    </section>
  )
}
