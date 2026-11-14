import AnilloSalud from '../componentes/AnilloSalud.jsx'
import { nivelDeSalud } from '../formato.js'

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
    </section>
  )
}
