import {
  ChatCircleDots,
  CheckCircle,
  Barbell,
  Coffee,
  ForkKnife,
  Heartbeat,
  Lightbulb,
  PauseCircle,
  PiggyBank,
  SealCheck,
  Taxi,
  Warning,
} from '@phosphor-icons/react'
import { motion, useReducedMotion } from 'motion/react'
import { Link } from 'react-router-dom'
import CifraVerificada from '../componentes/CifraVerificada.jsx'
import NumeroAnimado from '../componentes/NumeroAnimado.jsx'
import { avanceDelCiclo, diasEntre, enSoles, fechaCorta, fechaDia, nivelDeSalud } from '../formato.js'
import { entrada } from '../movimiento.js'
import ExplicameFacil from './ExplicameFacil.jsx'
import { explicarResumen } from './explicaciones.js'
import { PREGUNTAS_SUGERIDAS } from './respuestas.js'

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
        Llevas <b>{usadas} de {limite}</b> veces en {comercio} hasta el {fechaCorta(hasta)}. Vuelve mañana para ver
        cómo vas.
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
      {tip.diasEvitados > 0 && (
        <p className="tip-evita">
          Evitas {tip.diasEvitados === 1 ? '1 día' : `${tip.diasEvitados} días`} en rojo
        </p>
      )}
      <div aria-live="polite">{activo && <Seguimiento seguimiento={tip.seguimiento} />}</div>
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
    <li className="tip">
      <div className="reco-cabecera">
        <span className="circulo" aria-hidden="true">
          <PiggyBank size={22} />
        </span>
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

export default function Resumen({ cliente, alternarTip, animarEntrada = true }) {
  const { riesgo, proximoIngreso, recomendaciones, apartado, apartadoConTodos, salud, elegidos, conTodos } = cliente
  const faltanCambios = elegidos.length < cliente.totalCambios
  const exceso = cliente.gastoDiarioActual - cliente.gastoDiarioSeguro
  const faltan = diasEntre(cliente.hoy, proximoIngreso.fecha)
  // MotionConfig frena los desplazamientos con movimiento reducido, pero no los desvanecidos: aquí se apagan también.
  const reducido = useReducedMotion()
  const entra = (orden) => entrada(orden, animarEntrada && !reducido)

  return (
    <>
      <motion.section {...entra(0)} className="hero" data-guia="cobro" aria-label="Cuánto puedes gastar">
        <span className="hero-etiqueta">Puedes gastar al día</span>
        <strong className="hero-cifra">
          <CifraVerificada>
            <NumeroAnimado valor={cliente.gastoDiarioSeguro} formato={enSoles} />
          </CifraVerificada>
        </strong>
        <span className={`hero-actual ${exceso > 0 ? 'hero-actual-alto' : ''}`}>
          Hoy gastas <NumeroAnimado valor={cliente.gastoDiarioActual} formato={enSoles} retraso={0.1} />
          {exceso > 0 ? `, ${enSoles(exceso)} de más` : ''}
        </span>
        <div className="hero-cobro">
          <span>
            Cobras {enSoles(proximoIngreso.monto)} el {fechaCorta(proximoIngreso.fecha)}
          </span>
          <span>{faltan} días</span>
        </div>
        <span className="hero-barra" aria-hidden="true">
          <motion.span
            initial={reducido ? false : { scaleX: 0 }}
            animate={{ scaleX: avanceDelCiclo(faltan) }}
            transition={{ duration: 0.8, delay: 0.2 }}
          />
        </span>
      </motion.section>

      <motion.div {...entra(1)}>
        {riesgo ? (
          <section className="aviso aviso-corto" role="status" aria-label="Aviso de Lucas">
            <Warning size={24} aria-hidden="true" />
            <p>
              <strong>Lucas te avisa:</strong> en el peor caso, el {fechaDia(riesgo.desde)}
              {riesgo.hasta !== riesgo.desde && ` y el ${fechaDia(riesgo.hasta)}`} quedarías en rojo (
              <span className="cifra">{enSoles(riesgo.peorMonto)}</span>).
            </p>
            <a className="boton boton-chico" href="#tips">
              Cómo evitarlo
            </a>
          </section>
        ) : (
          <section className="aviso aviso-corto aviso-bien" role="status" aria-label="Aviso de Lucas">
            <SealCheck size={24} aria-hidden="true" />
            <p>
              <strong>Vas bien:</strong> llegas a tu cobro sin quedar en rojo, incluso si gastas un poco más.
            </p>
          </section>
        )}
        <ExplicameFacil puntos={explicarResumen(cliente)} />
      </motion.div>

      <motion.section {...entra(2)} id="tips" className="seccion" aria-labelledby="tips-titulo">
        <h2 id="tips-titulo">Tips para tu día más justo</h2>
        <p className="impacto" aria-live="polite">
          <span>
            Días en rojo <b>{cliente.diasEnRojo}</b>
            {faltanCambios && (
              <>
                {' '}
                → <b>{conTodos.diasEnRojo}</b>
              </>
            )}
          </span>
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
          <span className="suave">
            {salud.puntaje}, {nivelDeSalud(salud.puntaje)}
            {faltanCambios && salud.puntaje !== conTodos.salud && ` · ${conTodos.salud} con los tips`}
          </span>
        </Link>
        <Link to={`/lucas/chat?q=${encodeURIComponent(PREGUNTAS_SUGERIDAS[0])}`} className="bento-bloque">
          <ChatCircleDots size={24} aria-hidden="true" />
          <span className="bento-titulo">Pregúntale</span>
          <span className="suave">{PREGUNTAS_SUGERIDAS[0]}</span>
        </Link>
      </motion.nav>

      <p className="decision">Son simulaciones con tus datos. Lucas no mueve tu plata ni es asesoría: tú decides.</p>
    </>
  )
}
