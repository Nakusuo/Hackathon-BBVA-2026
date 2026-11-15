import { useId } from 'react'

// El error va fuera de la etiqueta para no sumarse al nombre del campo; se ata con aria-describedby.
export default function Campo({ etiqueta, error, mostrarError, children }) {
  const id = useId()
  const idError = `${id}-error`
  const conError = mostrarError && error
  return (
    <div className="campo campo-plan">
      <label htmlFor={id}>{etiqueta}</label>
      {children({ id, 'aria-invalid': conError ? 'true' : undefined, 'aria-describedby': conError ? idError : undefined })}
      {conError && (
        <span id={idError} className="campo-error">
          {error}
        </span>
      )}
    </div>
  )
}
