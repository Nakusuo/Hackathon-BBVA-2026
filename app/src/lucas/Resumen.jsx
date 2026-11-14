import { CheckCircle, Coffee, ForkKnife, PauseCircle, PiggyBank, Question, SealCheck, Warning } from '@phosphor-icons/react'
import { AnimatePresence, motion, useReducedMotion } from 'motion/react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import AnilloSalud from '../componentes/AnilloSalud.jsx'
import NumeroAnimado from '../componentes/NumeroAnimado.jsx'
import { conSigno, diasEntre, enSoles, fechaCorta, fechaDia, textoDiasEnRojo } from '../formato.js'
import { entrada } from '../movimiento.js'
import { PREGUNTAS_SUGERIDAS } from './respuestas.js'

const ICONOS = { musika: PauseCircle, delivery: ForkKnife, cafe: Coffee }
const CAMBIO = {
  initial: { opacity: 0, y: 4 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -4 },
  transition: { duration: 0.15 },
}

function nivel(puntaje) {
  if (puntaje >= 70) return 'vas bien'
  if (puntaje >= 45) return 'vas regular'
  return 'estás en riesgo'
}

function DatoAprendido({ dato }) {
  const [respuesta, setRespuesta] = useState(null)
  return (
    <li className={`aprendido ${respuesta === 'no' ? 'por-revisar' : ''}`}>
      <p>{dato.dato}</p>
      <p className="suave">Lo saqué de: {dato.fuente.toLowerCase()}</p>
      <AnimatePresence mode="wait" initial={false}>
        {respuesta === null ? (
          <motion.div key="pregunta" {...CAMBIO} className="confirmar" role="group" aria-label="¿Es correcto?">
            <span className="suave">¿Es correcto?</span>
            <button type="button" className="boton-texto" onClick={() => setRespuesta('si')}>
              Sí
            </button>
            <button type="button" className="boton-texto" onClick={() => setRespuesta('no')}>
              No
            </button>
          </motion.div>
        ) : (
          <motion.p key={respuesta} {...CAMBIO} className={respuesta === 'si' ? 'confirmado' : 'marcado'}>
            {respuesta === 'si' ? (
              <CheckCircle size={20} aria-hidden="true" />
            ) : (
              <Question size={20} aria-hidden="true" />
            )}
            {respuesta === 'si' ? 'Gracias, lo sigo usando.' : 'Marcado como por revisar.'}
            {respuesta === 'no' && (
              <button type="button" className="boton-texto" onClick={() => setRespuesta(null)}>
                Deshacer
              </button>
            )}
          </motion.p>
        )}
      </AnimatePresence>
    </li>
  )
}

function Tip({ tip, activo, alAlternar }) {
  const Icono = ICONOS[tip.id] ?? PiggyBank
  return (
    <li className={`tarjeta tip ${activo ? 'tip-activo' : ''}`}>
      <div className="reco-cabecera">
        <span className="circulo" aria-hidden="true">
          <Icono size={22} />
        </span>
        <span className="pildora">{tip.facilidad}</span>
      </div>
      <h3>{tip.titulo}</h3>
      <p>
        <span className="cifra cifra-azul">{enSoles(tip.mejora)} más</span> el {fechaDia(tip.fechaPeorDia)} en el peor
        caso.
      </p>
      <div className="tip-acciones">
        <button type="button" className="boton-lo-hago" aria-pressed={activo} onClick={() => alAlternar(tip.id)}>
          {activo && <CheckCircle size={20} weight="fill" aria-hidden="true" />}
          Lo hago
        </button>
        <details>
          <summary>¿Por qué?</summary>
          <p className="suave">{tip.porque}</p>
        </details>
      </div>
    </li>
  )
}

function textoDelPlan(cliente) {
  const { elegidos, totalCambios, conTodos, peorDia, riesgo } = cliente
  if (!elegidos.length) {
    const sinRojo = conTodos.peorMonto >= 0 ? ': ya no quedarías en rojo' : ''
    return `Si haces los ${totalCambios}, tu peor caso del ${fechaDia(conTodos.peorFecha)} pasa de ${enSoles(conTodos.peorAntes)} a ${conSigno(conTodos.peorMonto)}${sinRojo}.`
  }
  const cuantos = elegidos.length === 1 ? 'tu cambio' : `tus ${elegidos.length} cambios`
  const cierre = riesgo ? '' : ' Ya no quedas en rojo antes de cobrar.'
  return `Con ${cuantos}, tu peor caso del ${fechaDia(peorDia.fecha)} pasa de ${enSoles(conTodos.peorAntes)} a ${conSigno(peorDia.monto)}.${cierre}`
}

export default function Resumen({ cliente, alternarTip, animarEntrada = true }) {
  const { riesgo, proximoIngreso, recomendaciones, apartado, apartadoConTodos, salud, elegidos, peorDia } = cliente
  const exceso = cliente.gastoDiarioActual - cliente.gastoDiarioSeguro
  const [saludAbierta, setSaludAbierta] = useState(false)
  // MotionConfig frena los desplazamientos con movimiento reducido, pero no los desvanecidos: aquí se apagan también.
  const reducido = useReducedMotion()
  const entra = (orden) => entrada(orden, animarEntrada && !reducido)

  return (
    <>
      <motion.section {...entra(0)} className="recuadros" data-guia="cobro" aria-label="Cuánto puedes gastar">
        <div className="recuadro recuadro-azul">
          <span>Puedes gastar al día</span>
          <strong className="recuadro-cifra">
            <NumeroAnimado valor={cliente.gastoDiarioSeguro} formato={enSoles} />
          </strong>
          <span>sin quedar en rojo hasta el {fechaDia(proximoIngreso.fecha)}</span>
        </div>
        <div className="recuadro">
          <span className="suave">Ahora gastas al día</span>
          <strong className="recuadro-cifra">
            <NumeroAnimado valor={cliente.gastoDiarioActual} formato={enSoles} retraso={0.1} />
          </strong>
          <span className="suave">
            {exceso > 0 ? `${enSoles(exceso)} más de lo que te conviene` : 'Dentro de lo que te conviene'}
          </span>
        </div>
        <p className="recuadros-pie suave">
          Cobras {enSoles(proximoIngreso.monto)} en {diasEntre(cliente.hoy, proximoIngreso.fecha)} días.
        </p>
      </motion.section>

      <motion.div {...entra(1)}>
        {riesgo ? (
          <section className="aviso" role="status" aria-label="Aviso de Lucas">
            <p className="aviso-etiqueta">
              <Warning size={20} aria-hidden="true" />
              Lucas te avisa
            </p>
            <p>
              Si gastas un poco más de lo normal, {textoDiasEnRojo(riesgo).toLowerCase()} podrías quedar en rojo: el{' '}
              {fechaDia(riesgo.peorFecha)} tendrías <span className="cifra">{enSoles(riesgo.peorMonto)}</span>. Lo más
              probable es que ese día te queden {enSoles(riesgo.esperado)}.
            </p>
            <a className="boton" href="#tips">
              Ver cómo evitarlo
            </a>
          </section>
        ) : (
          <section className="aviso aviso-bien" role="status" aria-label="Aviso de Lucas">
            <p className="aviso-etiqueta">
              <SealCheck size={20} aria-hidden="true" />
              Vas bien
            </p>
            <p>
              Con tus cambios llegas a tu cobro del {fechaDia(proximoIngreso.fecha)} sin quedar en rojo, incluso si gastas
              un poco más de lo normal. Lo más probable es que el {fechaDia(peorDia.fecha)} te queden{' '}
              {enSoles(peorDia.esperado)}.
            </p>
          </section>
        )}
      </motion.div>

      <motion.section {...entra(2)} id="tips" className="seccion" aria-labelledby="tips-titulo">
        <h2 id="tips-titulo">Tips para tu día más justo</h2>
        <p className="sugerencia" aria-live="polite">
          {textoDelPlan(cliente)}
        </p>
        <ul className="lista-limpia lista-tips">
          {recomendaciones.map((t) => (
            <Tip key={t.id} tip={t} activo={elegidos.includes(t.id)} alAlternar={alternarTip} />
          ))}
        </ul>

        <div className="tarjeta tip">
          <div className="reco-cabecera">
            <span className="circulo" aria-hidden="true">
              <PiggyBank size={22} />
            </span>
            <span className="pildora">Después de cobrar</span>
          </div>
          {apartado ? (
            <>
              <h3>
                Cuando cobres el {fechaDia(proximoIngreso.fecha)}, podrías apartar {enSoles(apartado.monto)}
              </h3>
              <p className="suave">
                Lo comprobé con tus pagos hasta el {fechaCorta(apartado.hasta)} y no te deja en rojo. Si lo repites{' '}
                {apartado.repeticiones} meses, juntarías {enSoles(apartado.total)}.
              </p>
            </>
          ) : (
            <>
              <h3>Cuando cobres, todavía no te conviene apartar</h3>
              <p className="suave">Ese margen lo necesitas para tus pagos de diciembre.</p>
            </>
          )}
          {apartadoConTodos && (!apartado || apartadoConTodos.monto > apartado.monto) && (
            <p className="cifra-azul">
              Con los {cliente.totalCambios} cambios podrías apartar {enSoles(apartadoConTodos.monto)}.
            </p>
          )}
        </div>
      </motion.section>

      <motion.section {...entra(3)} className="tarjeta" data-guia="aprendido" aria-labelledby="aprendido-titulo">
        <h2 id="aprendido-titulo">Lo que aprendí de ti</h2>
        <ul className="lista-limpia lista-aprendido">
          {cliente.aprendido.map((d) => (
            <DatoAprendido key={d.id} dato={d} />
          ))}
        </ul>
      </motion.section>

      <motion.section {...entra(4)} className="tarjeta" aria-labelledby="salud-titulo">
        <details onToggle={(e) => setSaludAbierta(e.currentTarget.open)}>
          <summary>
            <span id="salud-titulo">
              Tu salud financiera: {salud.puntaje} de 100, {nivel(salud.puntaje)}
            </span>
          </summary>
          <div className="salud">
            {saludAbierta ? (
              <AnilloSalud puntaje={salud.puntaje} componentes={salud.componentes} />
            ) : (
              <div className="anillo" />
            )}
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
      </motion.section>

      <motion.section {...entra(5)} className="tarjeta" aria-labelledby="pregunta-titulo">
        <h2 id="pregunta-titulo">Pregúntale a Lucas</h2>
        <div className="chips">
          {PREGUNTAS_SUGERIDAS.slice(0, 2).map((p) => (
            <Link key={p} className="chip" to={`/lucas/chat?q=${encodeURIComponent(p)}`}>
              {p}
            </Link>
          ))}
        </div>
      </motion.section>

      <motion.p {...entra(6)} className="decision">
        Lucas te muestra simulaciones con tus datos. No mueve tu plata ni es asesoría: tú decides.
      </motion.p>
    </>
  )
}
