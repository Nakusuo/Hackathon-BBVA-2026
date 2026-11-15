import {
  CalendarBlank,
  CheckCircle,
  Barbell,
  Coffee,
  ForkKnife,
  Heartbeat,
  Hourglass,
  Lightbulb,
  PauseCircle,
  PiggyBank,
  Target,
  Taxi,
  Wallet,
} from '@phosphor-icons/react'
import { motion, useReducedMotion } from 'motion/react'
import { Link } from 'react-router-dom'
import CifraVerificada from '../componentes/CifraVerificada.jsx'
import LucasPose from '../componentes/LucasPose.jsx'
import NumeroAnimado from '../componentes/NumeroAnimado.jsx'
import { diasEntre, enSoles, fechaCorta, fechaDia, llenadoDelGasto, nivelDeSalud } from '../formato.js'
import { entrada } from '../movimiento.js'
import ExplicameFacil from './ExplicameFacil.jsx'
import { explicarResumen } from './explicaciones.js'

// El arco va de izquierda a derecha en SEGMENTOS rayas, de 180° a 0°; solo se dibujan las rayas, sin degradados.
const SEGMENTOS = 21
const CENTRO = 120
const RADIO_INTERIOR = 78
const RADIO_EXTERIOR = 110

const RAYAS = Array.from({ length: SEGMENTOS }, (_, i) => {
  const angulo = Math.PI - (i / (SEGMENTOS - 1)) * Math.PI
  const punto = (radio) => [CENTRO + radio * Math.cos(angulo), CENTRO - radio * Math.sin(angulo)]
  const [x1, y1] = punto(RADIO_INTERIOR)
  const [x2, y2] = punto(RADIO_EXTERIOR)
  return { x1, y1, x2, y2 }
})

// Al pasarte, el arco queda lleno: en verde lo que alcanza y, al final, en color de riesgo lo que sobra.
// aria-hidden: lo que dice el medidor ya está en el texto (la cifra, lo que gastas y el «de más»).
function Medidor({ gastoActual, gastoSeguro, animar }) {
  const pasado = gastoActual > gastoSeguro
  const llenado = llenadoDelGasto(gastoActual, gastoSeguro)
  const alcanzan = pasado ? Math.round((gastoSeguro / gastoActual) * SEGMENTOS) : Math.round(llenado * SEGMENTOS)
  const verdes = pasado ? Math.min(alcanzan, SEGMENTOS - 1) : Math.max(alcanzan, llenado > 0 ? 1 : 0)
  return (
    <svg className="medidor-arco" viewBox="0 0 240 124" aria-hidden="true">
      {RAYAS.map((raya, i) => (
        <line
          key={i}
          {...raya}
          className={i < verdes ? 'raya raya-llena' : pasado ? 'raya raya-pasada' : 'raya'}
          style={animar ? { animationName: 'encender', animationDelay: `${i * 35}ms` } : undefined}
        />
      ))}
    </svg>
  )
}

const ICONOS = { musika: PauseCircle, delivery: ForkKnife, cafe: Coffee, fitzona: Barbell, taxi: Taxi }

// Al elegir un tip, la tarjeta pasa a mostrar cómo va: es la razón para volver mañana.
function Seguimiento({ seguimiento }) {
  if (seguimiento.tipo === 'pausa') {
    return (
      <p className="seguimiento">
        Pausa {seguimiento.comercio} antes del {fechaCorta(seguimiento.fecha)}, que es cuando se cobra.
      </p>
    )
  }
  const { usadas, limite, comercio, hasta } = seguimiento
  return (
    <div className="seguimiento">
      <p>
        Llevas <b>{usadas} de {limite}</b> veces en {comercio} hasta el {fechaCorta(hasta)}. Lucas lo cuenta con tus
        compras con tarjeta.
      </p>
      <span className="medidor" aria-hidden="true">
        <span style={{ width: `${Math.min(1, usadas / limite) * 100}%` }} />
      </span>
    </div>
  )
}

function Tip({ tip, activo, alAlternar }) {
  const Icono = ICONOS[tip.id] ?? PiggyBank
  return (
    <li className={`tip ${activo ? 'tip-activo' : ''}`}>
      <div className="reco-cabecera">
        <span className="circulo" aria-hidden="true">
          <Icono size={22} />
        </span>
        <span className="pildora">{tip.facilidad}</span>
      </div>
      <h3>{tip.titulo}</h3>
      <p className="cifra cifra-azul">
        +{enSoles(tip.mejora)} el {fechaCorta(tip.fechaPeorDia)}
      </p>
      {/* Solo en los tips por elegir: medido sobre lo ya elegido, cada «Evitas» se cumple al tocar «Lo hago». */}
      {!activo && tip.diasEvitados > 0 && (
        <p className="tip-evita">
          Evitas {tip.diasEvitados === 1 ? '1 día' : `${tip.diasEvitados} días`} en rojo
        </p>
      )}
      <div aria-live="polite">{activo && tip.seguimiento && <Seguimiento seguimiento={tip.seguimiento} />}</div>
      <div className="tip-acciones">
        <motion.button
          type="button"
          className="boton-lo-hago"
          aria-pressed={activo}
          onClick={() => alAlternar(tip.id)}
          whileTap={{ scale: 0.95 }}
        >
          {activo && <CheckCircle size={20} weight="fill" aria-hidden="true" />}
          Lo hago
        </motion.button>
        <details>
          <summary>¿Por qué?</summary>
          <p className="suave">{tip.porque}</p>
        </details>
      </div>
    </li>
  )
}

function Apartado({ cliente }) {
  const { apartado, proximoIngreso } = cliente
  return (
    <li className="tip" id="apartado">
      <div className="reco-cabecera">
        <LucasPose pose={apartado ? 'ahorra' : 'pensando'} tamano={56} />
        <span className="pildora">Después de cobrar</span>
      </div>
      {apartado ? (
        <>
          <h3>
            El {fechaCorta(proximoIngreso.fecha)} podrías apartar {enSoles(apartado.monto)}
          </h3>
          <p className="suave">
            No te deja en rojo hasta el {fechaCorta(apartado.hasta)}. Si lo repites en tus próximos {apartado.repeticiones} cobros, juntarías{' '}
            {enSoles(apartado.total)}.
          </p>
          <Link className="enlace" to="/lucas/metas">
            Llévalo a una meta
          </Link>
        </>
      ) : (
        <>
          <h3>Al cobrar, todavía no te conviene apartar</h3>
          <p className="suave">Ese margen lo necesitas para tus próximos pagos.</p>
        </>
      )}
    </li>
  )
}

export default function Resumen({ cliente, metas, alternarTip, animarEntrada = true }) {
  const { riesgo, mes, proximoIngreso, recomendaciones, apartado, apartadoConTodos, salud, elegidos, conTodos } = cliente
  const faltanCambios = elegidos.length < cliente.totalCambios
  const exceso = cliente.gastoDiarioActual - cliente.gastoDiarioSeguro
  const faltan = diasEntre(cliente.hoy, proximoIngreso.fecha)
  // MotionConfig frena los desplazamientos con movimiento reducido, pero no los desvanecidos: aquí se apagan también.
  const reducido = useReducedMotion()
  const entra = (orden) => entrada(orden, animarEntrada && !reducido)

  return (
    <>
      <motion.section {...entra(0)} className="hero" data-guia="cobro" aria-label="Cuánto puedes gastar">
        <div className="hero-datos">
          <span className="hero-dato">
            <Wallet size={20} aria-hidden="true" />
            <span className="hero-actual">
              Gastas <NumeroAnimado valor={cliente.gastoDiarioActual} formato={enSoles} retraso={0.1} /> al día
            </span>
          </span>
          <span className="hero-dato">
            <CalendarBlank size={20} aria-hidden="true" />
            Cobras {enSoles(proximoIngreso.monto)} · {fechaCorta(proximoIngreso.fecha)}
          </span>
          <span className="hero-dato">
            <Hourglass size={20} aria-hidden="true" />
            {faltan} días
          </span>
        </div>
        <div className="hero-medidor">
          <Medidor
            gastoActual={cliente.gastoDiarioActual}
            gastoSeguro={cliente.gastoDiarioSeguro}
            animar={animarEntrada && !reducido}
          />
          <strong className="hero-cifra">
            <CifraVerificada>
              <NumeroAnimado valor={cliente.gastoDiarioSeguro} formato={enSoles} />
            </CifraVerificada>
          </strong>
        </div>
        <div className="hero-pie">
          <span className="hero-etiqueta">Puedes gastar al día</span>
          {exceso > 0 && <span className="hero-exceso">{enSoles(exceso)} de más</span>}
        </div>
      </motion.section>

      <motion.div {...entra(1)}>
        {riesgo ? (
          <section className="aviso aviso-corto" role="status" aria-label="Aviso de Lucas">
            <div className="aviso-texto">
              <p>
                <strong>Lucas te avisa:</strong> en el peor caso, el {fechaDia(riesgo.desde)}
                {riesgo.hasta !== riesgo.desde && ` y el ${fechaDia(riesgo.hasta)}`} quedarías en rojo (
                <span className="cifra">{enSoles(riesgo.peorMonto)}</span>).
              </p>
              <a className="boton boton-chico" href="#tips">
                Cómo evitarlo
              </a>
            </div>
            <LucasPose pose="alerta" tamano={88} />
          </section>
        ) : mes.diasEnRojo ? (
          <section className="aviso aviso-corto" role="status" aria-label="Aviso de Lucas">
            <div className="aviso-texto">
              <p>
                <strong>Lucas te avisa:</strong> llegas a tu cobro, pero con lo que planificaste el{' '}
                {fechaDia(mes.primerRojo)} quedarías en rojo (<span className="cifra">{enSoles(mes.peorMonto)}</span>).
              </p>
              <Link className="boton boton-chico" to="/lucas/que-viene">
                Ver en Qué viene
              </Link>
            </div>
            <LucasPose pose="alerta" tamano={88} />
          </section>
        ) : (
          <section className="aviso aviso-corto aviso-bien" role="status" aria-label="Aviso de Lucas">
            <div className="aviso-texto">
              <p>
                <strong>Vas bien:</strong> llegas a tu cobro sin quedar en rojo, incluso si gastas un poco más.
              </p>
            </div>
            <LucasPose pose="celebra" tamano={88} />
          </section>
        )}
        <ExplicameFacil puntos={explicarResumen(cliente)} />
      </motion.div>

      <motion.section {...entra(2)} id="tips" className="seccion" aria-labelledby="tips-titulo">
        <h2 id="tips-titulo">Tips para tu día más justo</h2>
        <p className="impacto" aria-live="polite">
          {/* «0 → 0» no dice nada: sin rojo que evitar, solo se muestra cuánto apartas. */}
          {!(faltanCambios && cliente.diasEnRojo === 0 && conTodos.diasEnRojo === 0) && (
          <span>
            Días en rojo <b>{cliente.diasEnRojo}</b>
            {faltanCambios && (
              <>
                {' '}
                → <b>{conTodos.diasEnRojo}</b>
              </>
            )}
          </span>
          )}
          <span>
            Apartas <b>{enSoles(apartado?.monto ?? 0)}</b>
            {faltanCambios && apartadoConTodos && (
              <>
                {' '}
                → <b>{enSoles(apartadoConTodos.monto)}</b>
              </>
            )}
          </span>
          <span className="impacto-nota">
            {faltanCambios ? `con los ${cliente.totalCambios} tips` : 'con tus cambios'}
          </span>
        </p>
        <ul className="lista-limpia carrusel">
          {recomendaciones.map((t) => (
            <Tip key={t.id} tip={t} activo={elegidos.includes(t.id)} alAlternar={alternarTip} />
          ))}
          <Apartado cliente={cliente} />
        </ul>
      </motion.section>

      <motion.nav {...entra(3)} className="bento" aria-label="Más de Lucas">
        <Link to="/lucas/aprendido" className="bento-bloque" data-guia="aprendido">
          <Lightbulb size={24} aria-hidden="true" />
          <span className="bento-titulo">Lo que aprendí</span>
          <span className="suave">{cliente.aprendido.length} datos</span>
        </Link>
        <Link to="/lucas/salud" className="bento-bloque">
          <Heartbeat size={24} aria-hidden="true" />
          <span className="bento-titulo">Tu salud</span>
          {/* Corto para que el bloque no estire la fila: la meta con tips se lee en dos líneas en celular. */}
          <span className="suave">
            {faltanCambios && salud.puntaje !== conTodos.salud
              ? `${salud.puntaje} hoy, ${conTodos.salud} con tips`
              : `${salud.puntaje}, ${nivelDeSalud(salud.puntaje)}`}
          </span>
        </Link>
        <Link to="/lucas/metas" className="bento-bloque">
          <Target size={24} aria-hidden="true" />
          <span className="bento-titulo">Tus metas</span>
          <span className="suave">{metas.length ? `${metas.length} ${metas.length === 1 ? 'meta' : 'metas'}` : 'Crea la primera'}</span>
        </Link>
      </motion.nav>

      <p className="decision">Son simulaciones. Tú decides.</p>
    </>
  )
}
