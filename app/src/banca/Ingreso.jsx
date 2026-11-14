import { LockSimple } from '@phosphor-icons/react'
import { useNavigate } from 'react-router-dom'

// Formulario solo visual: los campos vienen llenos y bloqueados para que nadie escriba datos reales en la demo.
export default function Ingreso() {
  const navegar = useNavigate()

  function ingresar(evento) {
    evento.preventDefault()
    navegar('/banca')
  }

  return (
    <main className="ingreso">
      <form className="ingreso-tarjeta" onSubmit={ingresar} aria-labelledby="ingreso-titulo">
        <div className="ingreso-marca">
          <span className="logotipo">Banco Vértice</span>
          <span className="etiqueta-demo">Banco ficticio</span>
        </div>
        <h1 id="ingreso-titulo">Ingresa a tu banca</h1>

        <label className="campo">
          <span>Tipo de documento</span>
          <input value="DNI" readOnly />
        </label>
        <label className="campo">
          <span>Número de documento</span>
          <input value="00000000" readOnly inputMode="numeric" />
        </label>
        <label className="campo">
          <span>Clave de internet</span>
          <input type="password" value="clave-demo" readOnly autoComplete="off" />
        </label>

        <button type="submit" className="boton boton-ancho">
          Ingresar
        </button>
        <p className="nota-seguridad">
          <LockSimple size={18} aria-hidden="true" />
          Datos de prueba ya cargados. No escribas datos reales.
        </p>
      </form>
    </main>
  )
}
