import { CheckCircle, Coffee, ForkKnife, PauseCircle, PiggyBank, Warning } from '@phosphor-icons/react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import AnilloSalud from '../componentes/AnilloSalud.jsx'
import { conSigno, diasEntre, enSoles, fechaDia, textoDiasEnRojo } from '../formato.js'
import { PREGUNTAS_SUGERIDAS } from './respuestas.js'

const ICONOS = { musika: PauseCircle, delivery: ForkKnife, cafe: Coffee }
const TIPS_VISIBLES = 2

function nivel(puntaje) {
  if (puntaje >= 70) return 'vas bien'
  if (puntaje >= 45) return 'vas regular'
  return 'estás en riesgo'
}

function DatoAprendido({ dato }) {
  const [respuesta, setRespuesta] = useState(null)
  return (
    <li className="aprendido">
      <p>{dato.dato}</p>
      <p className="suave">Lo saqué de: {dato.fuente.toLowerCase()}</p>
      {respuesta === null ? (
        <div className="confirmar" role="group" aria-label="¿Es correcto?">
          <span className="suave">¿Es correcto?</span>
          <button type="button" className="boton-texto" onClick={() => setRespuesta('si')}>
            Sí
          </button>
          <button type="button" className="boton-texto" onClick={() => setRespuesta('no')}>
            No
          </button>
        </div>
      ) : (
        <p className="confirmado">
          <CheckCircle size={20} aria-hidden="true" />
          {respuesta === 'si' ? 'Gracias, lo sigo usando.' : 'Gracias, lo reviso y dejo de usarlo hasta confirmarlo.'}
        </p>
      )}
    </li>
  )
}

function Tip({ tip }) {
  const Icono = ICONOS[tip.id] ?? PiggyBank
  return (
    <li className="tarjeta tip">
      <div className="reco-cabecera">
        <span className="circulo" aria-hidden="true">
          <Icono size={22} />
        </span>
        <span className="pildora">{tip.facilidad}</span>
      </div>
      <h3>{tip.titulo}</h3>
      <p>
        <span className="cifra cifra-azul">{enSoles(tip.mejora)} más</span> el {fechaDia(tip.fechaPeorDia)}. Tu
        peor caso pasa de {enSoles(tip.peorAntes)} a {enSoles(tip.peorDespues)}.
      </p>
      <details>
        <summary>¿Por qué?</summary>
        <p className="suave">{tip.porque}</p>
      </details>
    </li>
  )
}

export default function Resumen({ cliente }) {
  const { riesgo, proximoIngreso, recomendaciones, conTodos, apartado, salud } = cliente
  const [todosLosTips, setTodosLosTips] = useState(false)
  const tips = todosLosTips ? recomendaciones : recomendaciones.slice(0, TIPS_VISIBLES)

  return (
    <>
      <section className="tarjeta-cobro" data-guia="cobro" aria-labelledby="cobro-titulo">
        <p id="cobro-titulo" className="cobro-etiqueta">
          Hasta tu cobro del {fechaDia(proximoIngreso.fecha)}
        </p>
        <p className="cobro-cifra">
          {enSoles(cliente.gastoDiarioSeguro)} <small>al día</small>
        </p>
        <p>
          Es lo que puedes gastar sin quedar en rojo. Hoy gastas unos {enSoles(cliente.gastoDiarioActual)} al día.
        </p>
        <p className="suave">
          Cobras {enSoles(proximoIngreso.monto)} en {diasEntre(cliente.hoy, proximoIngreso.fecha)} días.
        </p>
      </section>

      {riesgo && (
        <section className="aviso" role="status" aria-label="Aviso de Lucas">
          <p className="aviso-etiqueta">
            <Warning size={20} aria-hidden="true" />
            Lucas te avisa
          </p>
          <p>
            {textoDiasEnRojo(riesgo)} podrías quedar en rojo si sigues gastando igual. En el peor caso, es decir, si
            este mes cobras menos o gastas más de lo normal, el {fechaDia(riesgo.peorFecha)} tendrías{' '}
            <span className="cifra">{enSoles(riesgo.peorMonto)}</span>.
          </p>
          <a className="boton" href="#tips">
            Ver cómo evitarlo
          </a>
        </section>
      )}

      <section className="tarjeta" data-guia="aprendido" aria-labelledby="aprendido-titulo">
        <h2 id="aprendido-titulo">Lo que aprendí de ti</h2>
        <ul className="lista-limpia lista-aprendido">
          {cliente.aprendido.map((d) => (
            <DatoAprendido key={d.id} dato={d} />
          ))}
        </ul>
      </section>

      <section id="tips" className="seccion" aria-labelledby="tips-titulo">
        <h2 id="tips-titulo">Tips para tu día más justo</h2>
        {riesgo && (
          <p className="sugerencia">
            Si haces los {recomendaciones.length}, tu peor caso del {fechaDia(riesgo.peorFecha)} pasa de{' '}
            <span className="cifra">{enSoles(riesgo.peorMonto)}</span> a{' '}
            <span className="cifra">{conSigno(conTodos.peorMonto)}</span>
            {conTodos.diasEnRojo === 0 && `: evitas ${diasEntre(riesgo.desde, riesgo.hasta) + 1} días en rojo`}.
          </p>
        )}
        <ul className="lista-limpia lista-tips">
          {tips.map((t) => (
            <Tip key={t.id} tip={t} />
          ))}
        </ul>
        {recomendaciones.length > TIPS_VISIBLES && (
          <button type="button" className="boton-texto" onClick={() => setTodosLosTips(!todosLosTips)}>
            {todosLosTips ? 'Ver menos' : `Ver ${recomendaciones.length - TIPS_VISIBLES} más`}
          </button>
        )}
        {apartado && (
          <div className="tarjeta tip">
            <div className="reco-cabecera">
              <span className="circulo" aria-hidden="true">
                <PiggyBank size={22} />
              </span>
              <span className="pildora">Después de cobrar</span>
            </div>
            <h3>
              Cuando cobres el {fechaDia(proximoIngreso.fecha)}, aparta {enSoles(apartado.monto)}
            </h3>
            <p className="suave">
              Lo comprobé con tus pagos de diciembre y no te deja en rojo. En {apartado.cobros} cobros tendrías{' '}
              {enSoles(apartado.total)} de colchón.
            </p>
          </div>
        )}
      </section>

      <section className="tarjeta" aria-labelledby="salud-titulo">
        <details>
          <summary>
            <span id="salud-titulo">
              Tu salud financiera: {salud.puntaje} de 100, {nivel(salud.puntaje)}
            </span>
          </summary>
          <div className="salud">
            <AnilloSalud puntaje={salud.puntaje} componentes={salud.componentes} />
            <ul className="lista-limpia componentes">
              {salud.componentes.map((c) => (
                <li key={c.nombre} className="componente">
                  <span className="componente-cabecera">
                    <span>{c.nombre}</span>
                    <span>{c.valor}</span>
                  </span>
                  <span className="suave">{c.explicacion}</span>
                </li>
              ))}
            </ul>
          </div>
          <p className="suave">Es el promedio de las 4 partes.</p>
        </details>
      </section>

      <section className="tarjeta" aria-labelledby="pregunta-titulo">
        <h2 id="pregunta-titulo">Pregúntale a Lucas</h2>
        <div className="chips">
          {PREGUNTAS_SUGERIDAS.slice(0, 2).map((p) => (
            <Link key={p} className="chip" to={`/lucas/chat?q=${encodeURIComponent(p)}`}>
              {p}
            </Link>
          ))}
        </div>
      </section>

      <p className="decision">Lucas te muestra simulaciones con tus datos. No mueve tu plata ni es asesoría: tú decides.</p>
    </>
  )
}
