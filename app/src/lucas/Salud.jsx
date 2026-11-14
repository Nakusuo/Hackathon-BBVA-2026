import { Link } from 'react-router-dom'
import AnilloSalud from '../componentes/AnilloSalud.jsx'
import { nivelDeSalud } from '../formato.js'
import { PREGUNTAS_SUGERIDAS } from './respuestas.js'

// Cada parte del puntaje lleva a la pantalla donde se puede mejorar: así la salud no es solo una nota.
const ACCIONES = {
  Colchón: { texto: 'Ver cuánto apartar al cobrar', a: '/lucas/resumen#apartado' },
  Deudas: { texto: 'Ver tus próximos pagos', a: '/lucas/que-viene' },
  // Con cobros irregulares, lo que ayuda es apartar al cobrar: se lo pregunta a Lucas.
  'Regularidad del ingreso': {
    texto: 'Pregúntale cuánto puedes ahorrar',
    a: `/lucas/chat?q=${encodeURIComponent(PREGUNTAS_SUGERIDAS[3])}`,
  },
  'Control del gasto': { texto: 'Ver tips para tu día más justo', a: '/lucas/resumen#tips' },
}

export default function Salud({ cliente }) {
  const { salud } = cliente
  return (
    <section className="tarjeta" aria-labelledby="salud-titulo">
      <h2 id="salud-titulo">
        Tu salud financiera: {salud.puntaje} de 100, {nivelDeSalud(salud.puntaje)}
      </h2>
      <div className="salud">
        <AnilloSalud puntaje={salud.puntaje} componentes={salud.componentes} />
        <ul className="lista-limpia componentes">
          {salud.componentes.map((c) => {
            const accion = ACCIONES[c.nombre]
            return (
              <li key={c.nombre} className="componente">
                <span className="componente-cabecera">
                  <span>{c.nombre}</span>
                  <span>{c.valor}</span>
                </span>
                <span className="suave">{c.explicacion}</span>
                {accion && (
                  <Link className="enlace" to={accion.a}>
                    {accion.texto}
                  </Link>
                )}
              </li>
            )
          })}
        </ul>
      </div>
      <p className="suave">
        Es el promedio de las 4 partes. Cálculo provisional mientras llega el modelo de salud: «Control del gasto» resta
        30 puntos por cada día en rojo que se proyecta antes de tu cobro.
      </p>
    </section>
  )
}
