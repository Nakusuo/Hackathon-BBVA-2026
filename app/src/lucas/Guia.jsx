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

export default function Guia({ alCerrar }) {
  const [paso, setPaso] = useState(0)
  const [caja, setCaja] = useState(null)
  const siguiente = useRef(null)
  const actual = PASOS[paso]
  const esUltimo = paso === PASOS.length - 1

  function cerrar() {
    marcarGuiaVista()
    alCerrar()
  }

  useLayoutEffect(() => {
    const elemento = document.querySelector(`[data-guia="${actual.objetivo}"]`)
    if (!elemento) return undefined
    elemento.scrollIntoView({ block: 'center' })
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
    const alTeclear = (e) => e.key === 'Escape' && cerrar()
    window.addEventListener('keydown', alTeclear)
    return () => window.removeEventListener('keydown', alTeclear)
  })

  const margen = 8
  const abajo = caja && caja.bottom + 220 < window.innerHeight

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
        className="guia-tarjeta"
        style={caja ? (abajo ? { top: caja.bottom + 16 } : { bottom: window.innerHeight - caja.top + 16 }) : {}}
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
