import { Bell, CalendarBlank, Money, ThumbsDown, ThumbsUp, Warning } from '@phosphor-icons/react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { enSoles, fechaCorta, fechaDia } from '../formato.js'
import { vistaCon } from '../motor/cliente.js'
import { armarBandeja, candidatos, MAXIMO_POR_SEMANA } from './avisos.js'
import { guardarOpiniones, guardarRegistro, leerOpiniones, leerRegistro } from './avisosGuardados.js'

const GASTO_DE_PRUEBA = 300

function sumarDias(fechaIso, dias) {
  const d = new Date(`${fechaIso}T12:00:00`)
  d.setDate(d.getDate() + dias)
  return d.toISOString().slice(0, 10)
}

function cuando(aviso) {
  if (aviso.dias === 0) return 'hoy'
  if (aviso.dias === 1) return 'mañana'
  return `el ${fechaDia(aviso.fecha)}`
}

function Etiqueta({ aviso }) {
  if (aviso.urgencia === 'urgente') {
    return (
      <span className="aviso-marca aviso-marca-urgente">
        <Warning size={20} weight="fill" aria-hidden="true" />
        Urgente
      </span>
    )
  }
  const Icono = aviso.tipo === 'ingreso' ? Money : aviso.tipo === 'pago' ? CalendarBlank : Bell
  return (
    <span className="aviso-marca">
      <Icono size={20} aria-hidden="true" />
      Aviso
    </span>
  )
}

function textos(aviso) {
  if (aviso.tipo === 'riesgo') {
    return {
      titulo: aviso.dias === 0 ? 'Hoy podrías quedar en rojo' : `Podrías quedar en rojo ${cuando(aviso)}`,
      detalle: `En el peor caso tu saldo baja a ${enSoles(aviso.impacto)} antes de tu cobro del ${fechaCorta(aviso.cobro.fecha)}. Lo más probable es que el ${fechaCorta(aviso.peorFecha)} tengas ${enSoles(aviso.esperado)}.`,
      impacto: `${enSoles(aviso.impacto)} en el peor caso`,
      porque:
        'Sale de tu pronóstico a 30 días: tus pagos programados, tu gasto diario y el rango de lo que sueles cobrar. Lucas avisa cuando faltan 7 días o menos, para que tengas tiempo de ajustar.',
    }
  }
  if (aviso.tipo === 'pago') {
    return {
      titulo: `${aviso.concepto}: ${enSoles(-aviso.impacto)} ${cuando(aviso)}`,
      detalle: aviso.tip
        ? `${aviso.uso}. Si la pausas, tu día más justo mejora ${enSoles(aviso.tip.mejora)}.`
        : 'Es un pago programado: tenlo en cuenta en lo que gastes hasta entonces.',
      impacto: `${enSoles(aviso.impacto)} de tu saldo`,
      porque: 'Es un pago programado de tu cuenta y cae en los próximos 7 días.',
    }
  }
  return {
    titulo: `Cobras ${enSoles(aviso.impacto)} ${cuando(aviso)}`,
    detalle: aviso.apartado
      ? `Ese día podrías apartar ${enSoles(aviso.apartado.monto)} sin quedar en rojo después.`
      : 'Ese margen lo necesitas para tus próximos pagos.',
    impacto: `+${enSoles(aviso.impacto)} esperados`,
    porque: 'Sale de tus cobros de los últimos 6 meses.',
  }
}

function Opinion({ id, opinion, alOpinar }) {
  return (
    <div className="aviso-opinion">
      <div role="group" aria-label="¿Te sirvió este aviso?" className="aviso-opinion-botones">
        <button type="button" aria-pressed={opinion === 'util'} onClick={() => alOpinar(id, 'util')}>
          <ThumbsUp size={20} aria-hidden="true" weight={opinion === 'util' ? 'fill' : 'regular'} />
          Útil
        </button>
        <button type="button" aria-pressed={opinion === 'no-sirve'} onClick={() => alOpinar(id, 'no-sirve')}>
          <ThumbsDown size={20} aria-hidden="true" weight={opinion === 'no-sirve' ? 'fill' : 'regular'} />
          No me sirve
        </button>
      </div>
      <p className="suave" role="status">
        {opinion && 'Anotado. Por ahora se guarda solo en este navegador.'}
      </p>
    </div>
  )
}

function Aviso({ aviso, opinion, alOpinar }) {
  const t = textos(aviso)
  return (
    <li className={`aviso-item ${aviso.urgencia === 'urgente' ? 'aviso-item-urgente' : ''}`} data-tipo={aviso.tipo}>
      <div className="reco-cabecera">
        <Etiqueta aviso={aviso} />
        <span className="suave">{fechaCorta(aviso.fecha)}</span>
      </div>
      <h3>{t.titulo}</h3>
      <p>{t.detalle}</p>
      <p>
        Impacto: <span className="cifra">{t.impacto}</span>
      </p>
      <Link to={aviso.accion.ruta} className="boton boton-chico">
        {aviso.accion.texto}
      </Link>
      <details>
        <summary>¿Por qué?</summary>
        <p className="suave">{t.porque}</p>
      </details>
      <Opinion id={aviso.id} opinion={opinion} alOpinar={alOpinar} />
    </li>
  )
}

function Demo({ dias, diaDemo, setDiaDemo, conGasto, setConGasto }) {
  return (
    <details className="tarjeta aviso-demo">
      <summary>Probar la regla en la demo</summary>
      <p className="suave">Mismo pronóstico, visto en otro día o con un gasto de prueba.</p>
      <div className="selector" role="group" aria-label="Día de la demo">
        {dias.map((d) => (
          <button key={d.fecha} type="button" aria-pressed={diaDemo === d.fecha} onClick={() => setDiaDemo(d.fecha)}>
            {d.nombre}
          </button>
        ))}
      </div>
      <div className="selector" role="group" aria-label="Gasto de prueba">
        <button type="button" aria-pressed={!conGasto} onClick={() => setConGasto(false)}>
          Sin gasto
        </button>
        <button type="button" aria-pressed={conGasto} onClick={() => setConGasto(true)}>
          {enSoles(GASTO_DE_PRUEBA)} mañana
        </button>
      </div>
    </details>
  )
}

export default function Avisos({ cliente }) {
  const [diaDemo, setDiaDemo] = useState(cliente.hoy)
  const [conGasto, setConGasto] = useState(false)
  const [registro, setRegistro] = useState(leerRegistro)
  const [opiniones, setOpiniones] = useState(leerOpiniones)

  const vista = useMemo(
    () => (conGasto ? vistaCon(cliente.elegidos, cliente.personaId, [{ id: 'prueba', fecha: sumarDias(diaDemo, 1), monto: GASTO_DE_PRUEBA }]) : cliente),
    [cliente, conGasto, diaDemo],
  )
  const { avisos: lista, riesgoLejano } = candidatos(vista, diaDemo)
  const bandeja = armarBandeja(lista, registro, diaDemo)
  const idsSemana = bandeja.registro[bandeja.semana]

  // Lo que se muestra pasa a contar en el tope de la semana; se ajusta en el mismo render, sin esperar a un efecto.
  if (JSON.stringify(registro[bandeja.semana] ?? []) !== JSON.stringify(idsSemana)) {
    setRegistro({ ...registro, [bandeja.semana]: idsSemana })
  }
  useEffect(() => guardarRegistro(registro), [registro])

  function opinar(id, valor) {
    const nuevas = { ...opiniones, [id]: opiniones[id] === valor ? undefined : valor }
    setOpiniones(nuevas)
    guardarOpiniones(nuevas)
  }

  // Los días de la demo salen del propio riesgo: a 7 días (normal) y a 2 días (urgente).
  const riesgoBase = cliente.riesgo
  const diasDemo = riesgoBase
    ? [
        { fecha: cliente.hoy, nombre: 'Hoy' },
        { fecha: sumarDias(riesgoBase.desde, -7), nombre: fechaCorta(sumarDias(riesgoBase.desde, -7)) },
        { fecha: sumarDias(riesgoBase.desde, -2), nombre: fechaCorta(sumarDias(riesgoBase.desde, -2)) },
      ]
    : [{ fecha: cliente.hoy, nombre: 'Hoy' }]
  const enDemo = diaDemo !== cliente.hoy || conGasto

  return (
    <>
      <section className="seccion" aria-labelledby="avisos-titulo">
        <h2 id="avisos-titulo">Tus avisos</h2>
        <p className="suave">
          Lucas te escribe como máximo {MAXIMO_POR_SEMANA} veces por semana, de lunes a domingo. Esta semana{' '}
          {bandeja.restantes === 1 ? 'queda 1 aviso' : `quedan ${bandeja.restantes} avisos`}.
        </p>
        {enDemo && (
          <p className="aviso-nota" role="status">
            Vista de prueba: así se vería el {fechaDia(diaDemo)}
            {conGasto && ` con un gasto de ${enSoles(GASTO_DE_PRUEBA)} al día siguiente`}.
          </p>
        )}

        {bandeja.avisos.length ? (
          <ul className="lista-limpia avisos-lista">
            {bandeja.avisos.map((a) => (
              <Aviso key={a.id} aviso={a} opinion={opiniones[a.id]} alOpinar={opinar} />
            ))}
          </ul>
        ) : (
          <p className="tarjeta">No tienes avisos esta semana.</p>
        )}

        {riesgoLejano && (
          <p className="tarjeta">
            Tu riesgo de quedar en rojo empieza el {fechaDia(riesgoLejano.fecha)}, en {riesgoLejano.dias} días. Ya lo
            ves en tu Resumen; Lucas te escribirá un aviso cuando falten 7 días o menos.{' '}
            <Link className="enlace" to="/lucas/que-viene">
              Verlo en Qué viene
            </Link>
          </p>
        )}
        {bandeja.fueraDelTope > 0 && (
          <p className="suave">
            {bandeja.fueraDelTope === 1 ? 'Otro aviso quedó' : `Otros ${bandeja.fueraDelTope} avisos quedaron`} fuera
            por el tope semanal; lo ves en{' '}
            <Link className="enlace" to="/lucas/que-viene">
              Qué viene
            </Link>
            .
          </p>
        )}
      </section>

      <Demo dias={diasDemo} diaDemo={diaDemo} setDiaDemo={setDiaDemo} conGasto={conGasto} setConGasto={setConGasto} />

      <p className="decision">Lucas te avisa, no mueve tu plata ni es asesoría: tú decides.</p>
    </>
  )
}
