import { useEffect } from 'react'

// Confirmación visible después de una acción: se va sola y, si la acción se puede deshacer, lo ofrece.
// Siempre montado: algunos lectores no anuncian un role="status" que aparece junto con su texto.
export default function AvisoBreve({ aviso, alCerrar }) {
  useEffect(() => {
    if (!aviso) return undefined
    const reloj = window.setTimeout(alCerrar, aviso.deshacer ? 7000 : 4000)
    return () => window.clearTimeout(reloj)
  }, [aviso, alCerrar])

  return (
    <div className="aviso-flotante aviso-breve" role="status">
      {aviso && (
        <>
          <span>{aviso.texto}</span>
          {aviso.deshacer && (
            <button type="button" className="aviso-deshacer" onClick={aviso.deshacer}>
              Deshacer
            </button>
          )}
        </>
      )}
    </div>
  )
}
