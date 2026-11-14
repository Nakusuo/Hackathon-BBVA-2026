import { Bell, CalendarBlank, Money, ThumbsDown, ThumbsUp, Warning } from '@phosphor-icons/react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import LucasPose from '../componentes/LucasPose.jsx'
import { enSoles, fechaCorta, fechaDia } from '../formato.js'
import { vistaCon } from '../motor/cliente.js'
import { armarBandeja, candidatos, inicioDeSemana, MAXIMO_POR_SEMANA } from './avisos.js'
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

// Regla 3 de historias.md: cada aviso dice acción, impacto en S/, por qué, datos usados, supuesto y qué tan seguro es.
function textos(aviso) {
  if (aviso.tipo === 'riesgo') {
    const masProbable = aviso.esperado < 0
    return {
      titulo: aviso.dias === 0 ? 'Hoy podrías quedar en rojo' : `Podrías quedar en rojo ${cuando(aviso)}`,
      detalle: `En el peor caso tu saldo baja a ${enSoles(aviso.impacto)} antes de tu cobro del ${fechaCorta(aviso.cobro.fecha)}.${
        aviso.tip ? ` Con «${aviso.tip.titulo}», ese día mejora ${enSoles(aviso.tip.mejora)}.` : ''
      }${
        aviso.conTodos
          ? ` Con los ${aviso.conTodos.total} tips de tu Resumen, tu peor caso pasa a +${enSoles(aviso.conTodos.peorMonto)}.`
          : ''
      }`,
      impacto: `${enSoles(aviso.impacto)} en el peor caso`,
      porque: 'Lucas avisa cuando faltan 7 días o menos, para que tengas tiempo de ajustar.',
      datos: 'Tu pronóstico a 30 días: pagos programados, gasto diario y el rango de lo que sueles cobrar.',
      supuesto: 'El peor caso es el borde bajo de la banda del pronóstico, no lo más probable.',
      seguridad: masProbable
        ? `Alta: incluso lo más probable es que ese día tengas ${enSoles(aviso.esperado)}.`
        : `Baja: es poco probable, porque lo más probable es que el ${fechaCorta(aviso.peorFecha)} tengas ${enSoles(aviso.esperado)}. Te avisamos igual porque, si pasa, pagarías intereses por cubrir el hueco.`,
    }
  }
  if (aviso.tipo === 'pago') {
    return {
      titulo: `${aviso.concepto}: ${enSoles(-aviso.impacto)} ${cuando(aviso)}`,
      detalle: `${aviso.uso}. Si la pausas, tu día más justo mejora ${enSoles(aviso.tip.mejora)}.`,
      impacto: `+${enSoles(aviso.tip.mejora)} en tu día más justo si la pausas`,
      porque: 'Se cobra en los próximos 7 días y casi no la usas.',
      datos: 'Tus pagos programados y cuántas veces usaste el servicio.',
      supuesto: 'Que la pausas antes del cobro y la retomas cuando quieras.',
      seguridad: 'Alta: el monto y la fecha son los de tu pago programado.',
    }
  }
  return {
    titulo: `Cobras ${enSoles(aviso.impacto)} ${cuando(aviso)}`,
    detalle: aviso.apartado
      ? `Ese día podrías apartar ${enSoles(aviso.apartado.monto)} sin quedar en rojo después.`
      : 'Ese margen lo necesitas para tus próximos pagos.',
    impacto: `+${enSoles(aviso.impacto)} esperados`,
    porque: 'Apartar el día del cobro es más fácil que al final del mes.',
    datos: 'Tus cobros de los últimos 6 meses.',
    supuesto: 'Que el cobro llegue en la fecha de siempre.',
    seguridad: 'Media: el monto de tus cobros cambia de un mes a otro.',
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
        <ul className="lista-limpia aviso-porque">
          <li>{t.porque}</li>
          <li>Datos usados: {t.datos}</li>
          <li>Supuesto: {t.supuesto}</li>
          <li>Qué tan seguro: {t.seguridad}</li>
          <li>Tú decides: Lucas no mueve tu plata.</li>
        </ul>
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
  const [diaDemo, setDiaDia] = useState(cliente.hoy)
  const [conGasto, setConGastoDemo] = useState(false)
  const [registro, setRegistro] = useState(leerRegistro)
  // La demo usa una copia en memoria: probar otros días no gasta el tope de la semana real.
  const [registroDemo, setRegistroDemo] = useState(leerRegistro)
  const [opiniones, setOpiniones] = useState(leerOpiniones)

  const vista = useMemo(
    () => (conGasto ? vistaCon(cliente.elegidos, cliente.personaId, [{ id: 'prueba', fecha: sumarDias(diaDemo, 1), monto: GASTO_DE_PRUEBA }]) : cliente),
    [cliente, conGasto, diaDemo],
  )
  const enDemo = diaDemo !== cliente.hoy || conGasto
  // Al entrar a la demo, su copia parte de lo que la semana real ya mostró.
  function entrarADemo(cambio) {
    if (!enDemo) setRegistroDemo(registro)
    cambio()
  }
  const setDiaDemo = (dia) => entrarADemo(() => setDiaDia(dia))
  const setConGasto = (valor) => entrarADemo(() => setConGastoDemo(valor))
  const actual = enDemo ? registroDemo : registro
  const { avisos: lista, riesgoLejano } = candidatos(vista, diaDemo)
  const bandeja = armarBandeja(lista, actual, diaDemo)
  const idsSemana = bandeja.registro[bandeja.semana]

  // Lo que se muestra pasa a contar en el tope de la semana; se ajusta en el mismo render, sin esperar a un efecto.
  if (JSON.stringify(actual[bandeja.semana] ?? []) !== JSON.stringify(idsSemana)) {
    const nuevo = { ...actual, [bandeja.semana]: idsSemana }
    if (enDemo) setRegistroDemo(nuevo)
    else setRegistro(nuevo)
  }
  // Solo se guarda la semana en curso: las pasadas ya no cuentan para el tope.
  const semanaReal = inicioDeSemana(cliente.hoy)
  const idsReales = registro[semanaReal]
  useEffect(() => {
    if (idsReales) guardarRegistro({ [semanaReal]: idsReales })
  }, [semanaReal, idsReales])

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
  return (
    <>
      <section className="seccion" aria-labelledby="avisos-titulo">
        <h2 id="avisos-titulo">Tus avisos</h2>
        <p className="suave">
          Lucas te escribe como máximo {MAXIMO_POR_SEMANA} veces por semana, de lunes a domingo. Esta semana van{' '}
          {MAXIMO_POR_SEMANA - bandeja.restantes} de {MAXIMO_POR_SEMANA}.
        </p>
        <Demo dias={diasDemo} diaDemo={diaDemo} setDiaDemo={setDiaDemo} conGasto={conGasto} setConGasto={setConGasto} />
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
          <div className="tarjeta avisos-vacio">
            <LucasPose pose="descansa" tamano={72} />
            <p>No tienes avisos esta semana.</p>
          </div>
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


      <p className="decision">Lucas te avisa, no mueve tu plata ni es asesoría: tú decides.</p>
    </>
  )
}
