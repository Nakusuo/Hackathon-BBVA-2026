import { Link } from 'react-router-dom'
import AnilloSalud from '../componentes/AnilloSalud.jsx'
import { nivelDeSalud } from '../formato.js'

// Cada parte del puntaje lleva a la pantalla donde se puede mejorar: así la salud no es solo una nota.
const ACCIONES = {
  Colchón: { texto: 'Ver cuánto apartar al cobrar', a: '/lucas/resumen#tips' },
  Deudas: { texto: 'Ver tus próximos pagos', a: '/lucas/que-viene' },
  'Regularidad del ingreso': { texto: 'Ver tus próximos cobros', a: '/lucas/que-viene' },
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
      <p className="suave">Es el promedio de las 4 partes. Sube cuando eliges tips que te sacan del rojo.</p>
    </section>
  )
}
