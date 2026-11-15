import { useEffect, useRef, useState } from 'react'

// Confirmación visible después de una acción: se va sola y, si la acción se puede deshacer, lo ofrece.
export default function AvisoBreve({ aviso, alCerrar }) {
  // Con el puntero o el foco encima no se cierra: da tiempo a quien navega con teclado.
  const [enPausa, setEnPausa] = useState(false)
  const deshacer = useRef(null)

  useEffect(() => {
    if (!aviso || enPausa) return undefined
    const reloj = window.setTimeout(alCerrar, aviso.deshacer ? 7000 : 4000)
    return () => window.clearTimeout(reloj)
  }, [aviso, enPausa, alCerrar])

  // El botón que se tocó ya no existe: el foco pasa a «Deshacer» en vez de perderse.
  useEffect(() => {
    if (aviso?.deshacer) deshacer.current?.focus()
  }, [aviso])

  return (
    <>
      {/* Siempre montado: algunos lectores no anuncian un role="status" que aparece junto con su texto. */}
      <p className="solo-lector" role="status">
        {aviso?.texto}
      </p>
      {aviso && (
        <div
          className="aviso-flotante aviso-breve"
          onPointerEnter={() => setEnPausa(true)}
          onPointerLeave={() => setEnPausa(false)}
          onFocus={() => setEnPausa(true)}
          onBlur={() => setEnPausa(false)}
        >
          <span aria-hidden="true">{aviso.texto}</span>
          {aviso.deshacer && (
            <button
              ref={deshacer}
              type="button"
              className="aviso-deshacer"
              onClick={() => {
                // El botón desaparece sin avisar que perdió el foco: la pausa se suelta aquí.
                setEnPausa(false)
                aviso.deshacer()
              }}
            >
              Deshacer
            </button>
          )}
        </div>
      )}
    </>
  )
}
