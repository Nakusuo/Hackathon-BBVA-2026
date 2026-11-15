import { Info, Plus } from '@phosphor-icons/react'
import { useRef, useState } from 'react'
import Campo from '../componentes/Campo.jsx'
import { enSoles, fechaCorta, fechaDia } from '../formato.js'
import { cuantoCabe } from '../motor/cliente.js'
import { rangoPlanificable, yaContado } from './planificar.js'

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

// El formulario solo describe el movimiento; QueViene recalcula la banda con él mientras se escribe.
export default function Planificar({ cliente, prueba, borrador, revision, alCambiar, alAgregar }) {
  const [intentado, setIntentado] = useState(false)
  const formulario = useRef(null)
  const { desde, hasta } = rangoPlanificable(cliente)
  const errores = revision.errores ?? {}
  const repetido = revision.movimiento && yaContado(cliente.proximosPagos, revision.movimiento)
  const ver = (campo) => intentado || borrador[campo] !== ''
  const { movimiento } = revision
  const sumaRojo = prueba && movimiento.tipo === 'gasto' && prueba.mes.diasEnRojo > cliente.mes.diasEnRojo
  const cabe = sumaRojo && cuantoCabe(cliente, movimiento.fecha)
  const cambiaAlDia = prueba && prueba.gastoDiarioSeguro !== cliente.gastoDiarioSeguro

  function enviar(evento) {
    evento.preventDefault()
    if (!revision.movimiento) {
      setIntentado(true)
      // Quien usa lector de pantalla oye el primer error al llegar el foco a su campo.
      window.requestAnimationFrame(() => formulario.current?.querySelector('[aria-invalid="true"]')?.focus())
      return
    }
    setIntentado(false)
    alAgregar(revision.movimiento)
  }

  return (
    <section className="tarjeta hoja" aria-labelledby="planificar-titulo">
      <h2 id="planificar-titulo">¿Y si viene un gasto o un ingreso?</h2>
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
                placeholder="450"
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
        <Campo etiqueta="¿Qué es? (opcional)">
          {(props) => (
            <input
              {...props}
              maxLength={40}
              autoComplete="off"
              placeholder={borrador.tipo === 'ingreso' ? 'Un trabajo extra' : 'Regalo de cumpleaños'}
              value={borrador.concepto}
              onChange={(e) => alCambiar('concepto', e.target.value)}
            />
          )}
        </Campo>

        <p className="impacto impacto-plan" aria-live="polite">
          {prueba ? (
            <>
              <Cambio
                nombre="Peor caso"
                antes={enSoles(cliente.mes.peorMonto)}
                despues={enSoles(prueba.mes.peorMonto)}
              />
              <Cambio nombre="Días en rojo" antes={cliente.mes.diasEnRojo} despues={prueba.mes.diasEnRojo} />
              {cambiaAlDia && (
                <Cambio
                  nombre="Al día hasta tu cobro"
                  antes={enSoles(cliente.gastoDiarioSeguro)}
                  despues={enSoles(prueba.gastoDiarioSeguro)}
                />
              )}
              <span className="impacto-nota">en los próximos 30 días</span>
            </>
          ) : (
            <span className="impacto-nota">
              Entre el {fechaCorta(desde)} y el {fechaCorta(hasta)}
            </span>
          )}
        </p>

        {cabe && (
          <p className="nota-plan">
            <Info size={20} aria-hidden="true" />
            <span>
              {cabe.ese > 0
                ? `Hasta ${enSoles(cabe.ese)} el ${fechaDia(movimiento.fecha)} ${
                    cliente.mes.diasEnRojo ? 'no te suma días en rojo' : 'no te deja en rojo'
                  }, ni en el peor caso.`
                : `Ese día no te alcanza sin quedar en rojo.`}
              {cabe.ese === 0 &&
                cabe.despues?.monto > 0 &&
                ` Después de tu cobro del ${fechaDia(cabe.despues.fecha)} sí caben ${enSoles(cabe.despues.monto)}.`}
              {/* El simulador y Metas miran el mismo margen después del cobro: gastarlo es no apartarlo. */}
              {cliente.apartado && (cabe.ese > 0 ? movimiento.fecha : cabe.despues?.fecha) >= cliente.proximoIngreso.fecha &&
                ' Es el mismo margen que tienes para apartar: si lo gastas, ese mes no apartas para tus metas.'}
            </span>
          </p>
        )}
        {prueba && <p className="suave">Es una simulación con tus datos: tú decides.</p>}

        {/* Siempre montado: algunos lectores no anuncian un role="status" que aparece junto con su texto. */}
        <div role="status">
          {repetido && (
            <p className="nota-plan">
              <Info size={20} aria-hidden="true" />
              <span>
                Ya tengo contado «{repetido.concepto}» ({enSoles(repetido.monto)} el {fechaCorta(repetido.fecha)}). Si
                es otro gasto, agrégalo igual.
              </span>
            </p>
          )}
        </div>

        <button type="submit" className="boton boton-ancho">
          <Plus size={20} aria-hidden="true" />
          Agregar a mi pronóstico
        </button>
      </form>
    </section>
  )
}
