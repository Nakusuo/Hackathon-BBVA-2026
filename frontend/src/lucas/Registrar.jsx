import { Check } from '@phosphor-icons/react'
import { useRef, useState } from 'react'
import Campo from '../componentes/Campo.jsx'
import { enSoles } from '../formato.js'
import { categoriasDeGasto, rangoRegistrable } from './registro.js'

const TIPOS = [
  { id: 'gasto', nombre: 'Gasto' },
  { id: 'ingreso', nombre: 'Ingreso' },
]

function Cambio({ nombre, antes, despues }) {
  return (
    <span>
      {nombre} <b>{antes}</b>
      {antes !== despues && (
        <>
          {' '}
          → <b>{despues}</b>
        </>
      )}
    </span>
  )
}

// Solo describe el movimiento: QueViene lo guarda y el motor recalcula todas las pantallas.
export default function Registrar({ cliente, prueba, borrador, revision, alCambiar, alGuardar }) {
  const [intentado, setIntentado] = useState(false)
  const formulario = useRef(null)
  const { desde, hasta } = rangoRegistrable(cliente)
  const errores = revision.errores ?? {}
  const ver = (campo) => intentado || (campo === 'fecha' ? borrador.fecha !== hasta : borrador[campo] !== '')
  const gasto = borrador.tipo === 'gasto'

  function enviar(evento) {
    evento.preventDefault()
    if (!revision.movimiento) {
      setIntentado(true)
      window.requestAnimationFrame(() => formulario.current?.querySelector('[aria-invalid="true"]')?.focus())
      return
    }
    setIntentado(false)
    alGuardar(revision.movimiento)
  }

  return (
    <section className="tarjeta hoja" aria-labelledby="registrar-titulo">
      <h2 id="registrar-titulo">Registrar un movimiento</h2>
      <form ref={formulario} className="formulario-plan" noValidate onSubmit={enviar}>
        <div className="selector" role="group" aria-label="Tipo de movimiento">
          {TIPOS.map((t) => (
            <button key={t.id} type="button" aria-pressed={borrador.tipo === t.id} onClick={() => alCambiar('tipo', t.id)}>
              {t.nombre}
            </button>
          ))}
        </div>
        <div className="campos-fila">
          <Campo etiqueta="Monto en S/" error={errores.monto} mostrarError={ver('monto')}>
            {(props) => (
              <input
                {...props}
                inputMode="decimal"
                autoComplete="off"
                placeholder="45"
                value={borrador.monto}
                onChange={(e) => alCambiar('monto', e.target.value)}
              />
            )}
          </Campo>
          <Campo etiqueta="Fecha" error={errores.fecha} mostrarError={ver('fecha')}>
            {(props) => (
              <input
                {...props}
                type="date"
                min={desde}
                max={hasta}
                value={borrador.fecha}
                onChange={(e) => alCambiar('fecha', e.target.value)}
              />
            )}
          </Campo>
        </div>
        {gasto && (
          <Campo etiqueta="Categoría" error={errores.categoria} mostrarError={intentado}>
            {(props) => (
              <select {...props} value={borrador.categoria} onChange={(e) => alCambiar('categoria', e.target.value)}>
                {categoriasDeGasto(cliente).map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nombre}
                  </option>
                ))}
              </select>
            )}
          </Campo>
        )}
        <Campo etiqueta="¿Qué es? (opcional)">
          {(props) => (
            <input
              {...props}
              maxLength={40}
              autoComplete="off"
              placeholder={gasto ? 'Almuerzo' : 'Cobro de un cliente'}
              value={borrador.concepto}
              onChange={(e) => alCambiar('concepto', e.target.value)}
            />
          )}
        </Campo>

        <p className="impacto impacto-plan" aria-live="polite">
          {prueba && (
            <>
              <Cambio nombre="Saldo de hoy" antes={enSoles(cliente.saldoHoy)} despues={enSoles(prueba.saldoHoy)} />
              <Cambio nombre="Peor caso" antes={enSoles(cliente.mes.peorMonto)} despues={enSoles(prueba.mes.peorMonto)} />
              <Cambio nombre="Días en rojo" antes={cliente.mes.diasEnRojo} despues={prueba.mes.diasEnRojo} />
            </>
          )}
        </p>

        <button type="submit" className="boton boton-ancho">
          <Check size={20} aria-hidden="true" />
          Guardar movimiento
        </button>
      </form>
    </section>
  )
}
