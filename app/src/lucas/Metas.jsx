import { CheckCircle, Lightbulb, PencilSimple, PiggyBank, Target, Trash } from '@phosphor-icons/react'
import { useCallback, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import AvisoBreve from '../componentes/AvisoBreve.jsx'
import Campo from '../componentes/Campo.jsx'
import { enSoles, fechaCorta } from '../formato.js'
import { estadoDe, finDeAnio, planDeMeta, repartoDelApartado, validarMeta } from './metas.js'

const VACIA = { nombre: '', objetivo: '', ahorrado: '', fecha: '' }
const IDEAS = ['Colchón', 'Viaje', 'Regalos']
const NOMBRE_ESTADO = { creada: 'Creada', 'en curso': 'En curso', cumplida: 'Cumplida' }

function fechaMeta(fechaIso, hoyIso) {
  const corta = fechaCorta(fechaIso)
  return fechaIso.slice(0, 4) === hoyIso.slice(0, 4) ? corta : `${corta} de ${fechaIso.slice(0, 4)}`
}

function TextoPlan({ meta, plan, conTips, totalCambios, espera, hoy, diaCobro }) {
  const fecha = fechaMeta(meta.fecha, hoy)
  if (plan.sinCobros) {
    return (
      <p>
        Ya no quedan cobros antes del {fecha}.
        {plan.llegaEl && ` Al ritmo de hoy llegarías el ${fechaMeta(plan.llegaEl, hoy)}.`} Puedes quitarla y crearla con
        otra fecha.
      </p>
    )
  }
  if (plan.alcanza) {
    return (
      <p>
        Aparta <b>{enSoles(plan.aporte)}</b> al mes, al cobrar el {Number(diaCobro.slice(8))} ({plan.veces}{' '}
        {plan.veces === 1 ? 'vez' : 'veces'} hasta el {fecha}), y llegas.
      </p>
    )
  }
  // Si con los tips llega antes, ese es el camino que Lucas propone: une la meta con «Lo hago».
  const tipsAyudan = conTips && conTips.aporte > plan.aporte && conTips.llegaEl
  return (
    <>
      {plan.aporte ? (
        <p>
          Con <b>{enSoles(plan.aporte)}</b> al mes llegas el {fechaMeta(plan.llegaEl, hoy)}.
        </p>
      ) : espera ? (
        <p>Lo que puedes apartar ya va a tus metas anteriores; esta espera su turno.</p>
      ) : (
        <p>Hoy no te conviene apartar para esta meta: ese margen lo necesitas para tus pagos.</p>
      )}
      {tipsAyudan && (
        <p className="nota-plan">
          <Lightbulb size={20} aria-hidden="true" />
          <span>
            Con los {totalCambios} tips apartas <b>{enSoles(conTips.aporte)}</b> al mes y llegas el{' '}
            {fechaMeta(conTips.llegaEl, hoy)}.{' '}
            <Link className="enlace" to="/lucas/resumen#tips">
              Ver tips
            </Link>
          </span>
        </p>
      )}
    </>
  )
}

function EditarMeta({ meta, contexto, alGuardar, alCancelar }) {
  const [borrador, setBorrador] = useState({
    nombre: meta.nombre,
    objetivo: String(meta.objetivo),
    ahorrado: meta.ahorrado ? String(meta.ahorrado) : '',
    fecha: meta.fecha,
  })
  const [intentado, setIntentado] = useState(false)
  const revision = validarMeta(borrador, contexto)
  const errores = revision.errores ?? {}
  const cambiar = (campo, valor) => setBorrador((previo) => ({ ...previo, [campo]: valor }))

  function guardar(evento) {
    evento.preventDefault()
    if (revision.datos) alGuardar(revision.datos)
    else setIntentado(true)
  }

  return (
    <form className="formulario-plan editar-meta" noValidate onSubmit={guardar} aria-label={`Editar ${meta.nombre}`}>
      <Campo etiqueta="Nombre" error={errores.nombre} mostrarError={intentado}>
        {(props) => (
          <input {...props} maxLength={40} autoComplete="off" value={borrador.nombre} onChange={(e) => cambiar('nombre', e.target.value)} />
        )}
      </Campo>
      <div className="campos-fila campos-montos">
        <Campo etiqueta="Meta en S/" error={errores.objetivo} mostrarError={intentado}>
          {(props) => (
            <input {...props} inputMode="decimal" autoComplete="off" value={borrador.objetivo} onChange={(e) => cambiar('objetivo', e.target.value)} />
          )}
        </Campo>
        <Campo etiqueta="Ya ahorré" error={errores.ahorrado} mostrarError={intentado}>
          {(props) => (
            <input {...props} inputMode="decimal" autoComplete="off" placeholder="0" value={borrador.ahorrado} onChange={(e) => cambiar('ahorrado', e.target.value)} />
          )}
        </Campo>
      </div>
      <Campo etiqueta="¿Para cuándo?" error={errores.fecha} mostrarError={intentado}>
        {(props) => (
          <input {...props} type="date" min={contexto.primerApartado} value={borrador.fecha} onChange={(e) => cambiar('fecha', e.target.value)} />
        )}
      </Campo>
      <div className="tip-acciones">
        <button type="submit" className="boton boton-chico">
          Guardar cambios
        </button>
        <button type="button" className="boton-texto" onClick={alCancelar}>
          Cancelar
        </button>
      </div>
    </form>
  )
}

function TarjetaMeta({ meta, plan, conTips, totalCambios, espera, hoy, diaCobro, contexto, alAportar, alQuitar, alEditar }) {
  const [editando, setEditando] = useState(false)
  const estado = estadoDe(meta)
  const anioTermina = meta.fecha > finDeAnio(hoy)
  return (
    <li className="tarjeta meta" aria-label={`Meta ${meta.nombre}`}>
      <div className="reco-cabecera">
        <span className="circulo" aria-hidden="true">
          {estado === 'cumplida' ? <CheckCircle size={22} /> : <Target size={22} />}
        </span>
        <span className="pildora">{NOMBRE_ESTADO[estado]}</span>
      </div>
      <h3>{meta.nombre}</h3>
      <p className="meta-avance">
        <span>
          <b>{enSoles(meta.ahorrado)}</b> de {enSoles(meta.objetivo)}
        </span>
        <span>{plan.avance} %</span>
      </p>
      <span className="medidor" aria-hidden="true">
        <span style={{ width: `${plan.avance}%` }} />
      </span>

      {editando ? (
        <EditarMeta
          meta={meta}
          contexto={contexto}
          alCancelar={() => setEditando(false)}
          alGuardar={(datos) => {
            alEditar(meta, datos)
            setEditando(false)
          }}
        />
      ) : estado === 'cumplida' ? (
        <p>Cumpliste tu meta. Lo que apartes desde ahora puede ir a otra.</p>
      ) : (
        <>
          <TextoPlan
            meta={meta}
            plan={plan}
            conTips={conTips}
            totalCambios={totalCambios}
            espera={espera}
            hoy={hoy}
            diaCobro={diaCobro}
          />
          {anioTermina && plan.aporte > 0 && <p className="suave">Al 31 dic tendrías {enSoles(plan.alFinDeAnio)}.</p>}
          <details>
            <summary>¿Cómo lo calculo? · Confianza {plan.confianza}</summary>
            <p className="suave">
              Uso lo que puedes apartar el día de tu cobro sin quedar en rojo, ni en el peor caso de tus próximos 30
              días.
              {plan.confianza !== 'alta' && ' Para los meses siguientes supongo que tus cobros y pagos se repiten.'}
              {plan.confianza === 'baja' && ' Como pasa de 3 meses, tómalo como una guía y no como una fecha segura.'}
            </p>
          </details>
        </>
      )}

      <div className="tip-acciones" hidden={editando}>
        {estado !== 'cumplida' && plan.aporte > 0 && (
          <button type="button" className="boton-lo-hago" onClick={() => alAportar(meta, plan.aporte)}>
            <PiggyBank size={20} aria-hidden="true" />
            Ya aparté {enSoles(plan.aporte)}
          </button>
        )}
        <button type="button" className="boton-texto" onClick={() => setEditando(true)}>
          <PencilSimple size={20} aria-hidden="true" />
          Editar
        </button>
        <button type="button" className="boton-texto" onClick={() => alQuitar(meta)}>
          <Trash size={20} aria-hidden="true" />
          Quitar
        </button>
      </div>
    </li>
  )
}

export default function Metas({ cliente, metas, alCrear, alAportar, alQuitar, alRestaurar, alEditar }) {
  const { apartado, apartadoConTodos, proximoIngreso, finPronostico, hoy } = cliente
  const [borrador, setBorrador] = useState({ ...VACIA, fecha: finDeAnio(hoy) })
  const [intentado, setIntentado] = useState(false)
  const [aviso, setAviso] = useState(null)
  // El error aparece al salir del campo, no mientras escribes.
  const [tocados, setTocados] = useState({})
  const cerrarAviso = useCallback(() => setAviso(null), [])
  const formulario = useRef(null)

  const puedes = apartado?.monto ?? 0
  const conTips = apartadoConTodos?.monto ?? 0
  const reparto = repartoDelApartado(puedes, metas)
  const repartoConTips = repartoDelApartado(conTips, metas)
  const contexto = { primerApartado: proximoIngreso.fecha, finPronostico, hoy }
  const revision = validarMeta(borrador, contexto)
  const errores = revision.errores ?? {}

  function cambiar(campo, valor) {
    setBorrador((previo) => ({ ...previo, [campo]: valor }))
  }

  function tocar(campo) {
    if (borrador[campo] !== '') setTocados((previos) => ({ ...previos, [campo]: true }))
  }

  function crear(evento) {
    evento.preventDefault()
    if (!revision.datos) {
      setIntentado(true)
      // Quien usa lector de pantalla oye el primer error al llegar el foco a su campo.
      window.requestAnimationFrame(() => formulario.current?.querySelector('[aria-invalid="true"]')?.focus())
      return
    }
    alCrear(revision.datos)
    setBorrador({ ...VACIA, fecha: finDeAnio(hoy) })
    setIntentado(false)
    setTocados({})
    setAviso({ texto: `Creé tu meta ${revision.datos.nombre}.` })
  }

  function aportarA(meta, monto) {
    alAportar(meta.id, monto)
    setAviso({ texto: `Registré ${enSoles(monto)} en ${meta.nombre}.` })
  }

  function editarMeta(meta, datos) {
    alEditar(meta.id, datos)
    setAviso({ texto: `Guardé los cambios de ${datos.nombre}.` })
  }

  function quitar(meta) {
    const lugar = metas.findIndex((m) => m.id === meta.id)
    alQuitar(meta.id)
    setAviso({
      texto: `Quité la meta ${meta.nombre}.`,
      deshacer: () => {
        alRestaurar(meta, lugar)
        setAviso({ texto: `Recuperé tu meta ${meta.nombre}.` })
      },
    })
  }

  return (
    <>
      <section className="panel-azul panel-metas" aria-labelledby="metas-titulo">
        <h2 id="metas-titulo">Tus metas</h2>
        {puedes > 0 ? (
          <>
            <p>
              El {fechaCorta(proximoIngreso.fecha)}, al cobrar, puedes apartar{' '}
              <span className="panel-cifra">{enSoles(puedes)}</span>
            </p>
            <p>Sin quedar en rojo, ni en el peor caso previsto.</p>
          </>
        ) : (
          <p>Al cobrar todavía no te conviene apartar: ese margen lo necesitas para tus próximos pagos.</p>
        )}
        {conTips > puedes && (
          <p className="metas-tips">
            <Lightbulb size={20} aria-hidden="true" />
            <span>
              Con los {cliente.totalCambios} tips serían <b>{enSoles(conTips)}</b>.{' '}
              <Link className="enlace" to="/lucas/resumen#tips">
                Ver tips
              </Link>
            </span>
          </p>
        )}
        {reparto.abiertas > 1 && reparto.conAporte > 0 && (
          <p>
            {reparto.conAporte === reparto.abiertas
              ? `Lo reparto entre tus ${reparto.abiertas} metas: ${enSoles(reparto.parte)} para cada una.`
              : `Alcanza para ${reparto.conAporte} de tus ${reparto.abiertas} metas: ${enSoles(reparto.parte)} para cada una, en el orden en que las creaste.`}
          </p>
        )}
      </section>

      {metas.length > 0 && (
        <ul className="lista-limpia lista-metas">
          {metas.map((m) => (
            <TarjetaMeta
              key={m.id}
              meta={m}
              plan={planDeMeta(m, { ...contexto, apartado: reparto.porMeta[m.id] ?? 0 })}
              conTips={
                conTips > puedes ? planDeMeta(m, { ...contexto, apartado: repartoConTips.porMeta[m.id] ?? 0 }) : null
              }
              totalCambios={cliente.totalCambios}
              espera={puedes > 0 && !reparto.porMeta[m.id]}
              diaCobro={proximoIngreso.fecha}
              hoy={hoy}
              contexto={contexto}
              alAportar={aportarA}
              alQuitar={quitar}
              alEditar={editarMeta}
            />
          ))}
        </ul>
      )}

      <section className="tarjeta" aria-labelledby="nueva-meta-titulo">
        <h2 id="nueva-meta-titulo">{metas.length ? 'Otra meta' : 'Crea tu primera meta'}</h2>
        <form ref={formulario} className="formulario-plan" noValidate onSubmit={crear}>
          <Campo etiqueta="¿Para qué ahorras?" error={errores.nombre} mostrarError={intentado}>
            {(props) => (
              <input
                {...props}
                maxLength={40}
                autoComplete="off"
                placeholder="Colchón para enero"
                value={borrador.nombre}
                onChange={(e) => cambiar('nombre', e.target.value)}
              />
            )}
          </Campo>
          <div className="atajos-meta" role="group" aria-label="Ideas de meta">
            {IDEAS.map((idea) => (
              <button
                key={idea}
                type="button"
                className="atajo-meta"
                aria-pressed={borrador.nombre === idea}
                onClick={() => cambiar('nombre', idea)}
              >
                {idea}
              </button>
            ))}
          </div>
          <div className="campos-fila campos-montos">
            <Campo etiqueta="Meta en S/" error={errores.objetivo} mostrarError={intentado || tocados.objetivo}>
              {(props) => (
                <input
                  {...props}
                  inputMode="decimal"
                  autoComplete="off"
                  placeholder="300"
                  onBlur={() => tocar('objetivo')}
                  value={borrador.objetivo}
                  onChange={(e) => cambiar('objetivo', e.target.value)}
                />
              )}
            </Campo>
            <Campo etiqueta="Ya ahorré" error={errores.ahorrado} mostrarError={intentado || tocados.ahorrado}>
              {(props) => (
                <input
                  {...props}
                  inputMode="decimal"
                  autoComplete="off"
                  placeholder="0"
                  onBlur={() => tocar('ahorrado')}
                  value={borrador.ahorrado}
                  onChange={(e) => cambiar('ahorrado', e.target.value)}
                />
              )}
            </Campo>
          </div>
          <Campo etiqueta="¿Para cuándo?" error={errores.fecha} mostrarError={intentado || tocados.fecha}>
            {(props) => (
              <input
                {...props}
                type="date"
                min={proximoIngreso.fecha}
                onBlur={() => tocar('fecha')}
                value={borrador.fecha}
                onChange={(e) => cambiar('fecha', e.target.value)}
              />
            )}
          </Campo>
          <button type="submit" className="boton boton-ancho">
            Crear meta
          </button>
        </form>
      </section>

      <AvisoBreve aviso={aviso} alCerrar={cerrarAviso} />
      <p className="decision">Son simulaciones. Tú decides.</p>
    </>
  )
}
