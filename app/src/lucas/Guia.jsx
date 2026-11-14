import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { marcarGuiaVista } from './guiaVista.js'

// Tres marcas en contexto y siempre con «Saltar»: los tutoriales largos no mejoran el uso (NN/g, ver investigacion/ui-banca.md).
const PASOS = [
  {
    objetivo: 'cobro',
    titulo: 'Lo que puedes gastar',
    texto: 'Aquí ves cuánto puedes gastar cada día hasta tu cobro sin quedar en rojo.',
  },
  {
    objetivo: 'aprendido',
    titulo: 'Lo que aprendí de ti',
    texto: 'Uso tus movimientos para conocerte. Si algo no es correcto, dímelo y lo corrijo.',
  },
  {
    objetivo: 'pestana-chat',
    titulo: 'Pregúntame',
    texto: 'En el chat respondo con tus datos, por ejemplo si te alcanza para un gasto.',
  },
]

const ESPACIO_TARJETA = 230
// Alto de la barra inferior de la banca más un respiro, para no taparla.
const SOBRE_LA_BARRA = 84

// Debajo de lo señalado si cabe, si no encima, y si lo señalado ocupa casi toda la pantalla, pegada abajo.
// Siempre se fijan top y bottom: si queda uno del CSS, la tarjeta se aplasta entre los dos.
function posicionTarjeta(caja) {
  if (!caja) return {}
  if (window.innerHeight - caja.bottom >= ESPACIO_TARJETA) return { top: caja.bottom + 16, bottom: 'auto' }
  if (caja.top >= ESPACIO_TARJETA) return { top: 'auto', bottom: window.innerHeight - caja.top + 16 }
  return { top: 'auto', bottom: SOBRE_LA_BARRA }
}

export default function Guia({ alCerrar }) {
  const [paso, setPaso] = useState(0)
  const [caja, setCaja] = useState(null)
  const siguiente = useRef(null)
  const tarjeta = useRef(null)
  const actual = PASOS[paso]
  const esUltimo = paso === PASOS.length - 1

  function cerrar() {
    marcarGuiaVista()
    alCerrar()
  }

  useLayoutEffect(() => {
    const elemento = document.querySelector(`[data-guia="${actual.objetivo}"]`)
    if (!elemento) return undefined
    const esAlto = elemento.getBoundingClientRect().height > window.innerHeight / 2
    elemento.scrollIntoView({ block: esAlto ? 'start' : 'center' })
    const medir = () => setCaja(elemento.getBoundingClientRect())
    medir()
    window.addEventListener('resize', medir)
    window.addEventListener('scroll', medir, true)
    return () => {
      window.removeEventListener('resize', medir)
      window.removeEventListener('scroll', medir, true)
    }
  }, [actual.objetivo])

  useEffect(() => {
    siguiente.current?.focus()
  }, [paso])

  // Mientras la guía está abierta, Tab no sale de ella y Escape la cierra.
  useEffect(() => {
    const alTeclear = (e) => {
      if (e.key === 'Escape') cerrar()
      if (e.key !== 'Tab' || !tarjeta.current) return
      const enfocables = [...tarjeta.current.querySelectorAll('button')]
      const primero = enfocables[0]
      const ultimo = enfocables.at(-1)
      if (e.shiftKey && document.activeElement === primero) {
        e.preventDefault()
        ultimo.focus()
      } else if (!e.shiftKey && document.activeElement === ultimo) {
        e.preventDefault()
        primero.focus()
      } else if (!tarjeta.current.contains(document.activeElement)) {
        e.preventDefault()
        primero.focus()
      }
    }
    window.addEventListener('keydown', alTeclear)
    return () => window.removeEventListener('keydown', alTeclear)
  })

  const margen = 8

  return (
    <div className="guia" role="dialog" aria-modal="true" aria-labelledby="guia-titulo">
      {caja && (
        <div
          className="guia-foco"
          style={{
            top: caja.top - margen,
            left: caja.left - margen,
            width: caja.width + margen * 2,
            height: caja.height + margen * 2,
          }}
        />
      )}
      <div
        ref={tarjeta}
        className="guia-tarjeta"
        style={posicionTarjeta(caja)}
      >
        <p className="suave">
          Paso {paso + 1} de {PASOS.length}
        </p>
        <h2 id="guia-titulo">{actual.titulo}</h2>
        <p>{actual.texto}</p>
        <div className="guia-botones">
          <button type="button" className="boton-texto" onClick={cerrar}>
            Saltar
          </button>
          <button
            ref={siguiente}
            type="button"
            className="boton"
            onClick={() => (esUltimo ? cerrar() : setPaso(paso + 1))}
          >
            {esUltimo ? 'Listo' : 'Siguiente'}
          </button>
        </div>
      </div>
    </div>
  )
}
