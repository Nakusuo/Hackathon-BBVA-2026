import {
  ArrowDown,
  ArrowUp,
  Bus,
  Coffee,
  DotsThree,
  FilmSlate,
  ForkKnife,
  Martini,
  Repeat,
} from '@phosphor-icons/react'
import { enSoles, iniciales } from '../formato.js'

const ICONOS = {
  comida: ForkKnife,
  transporte: Bus,
  salidas: Martini,
  hormiga: Coffee,
  suscripciones: Repeat,
  entretenimiento: FilmSlate,
  otros: DotsThree,
}

// Diferencias de hasta S/ 5 no se señalan: con montos así cualquier mes varía un poco.
const UMBRAL = 5

function Comparacion({ total, promedio }) {
  const diferencia = Math.round(total - promedio)
  if (Math.abs(diferencia) <= UMBRAL) return <span className="suave">Como siempre</span>
  const Flecha = diferencia > 0 ? ArrowUp : ArrowDown
  return (
    <span className={diferencia > 0 ? 'sube' : 'baja'}>
      <Flecha size={16} aria-hidden="true" />
      {enSoles(Math.abs(diferencia))} {diferencia > 0 ? 'más' : 'menos'} que tu promedio
    </span>
  )
}

export default function Gastos({ cliente }) {
  const { categorias, suscripciones } = cliente
  const total = categorias.reduce((s, c) => s + c.total, 0)
  const mayor = Math.max(...categorias.map((c) => c.total))

  return (
    <>
      <section className="tarjeta" aria-labelledby="categorias-titulo">
        <div className="tarjeta-titulo">
          <h2 id="categorias-titulo">Tus gastos por categoría</h2>
          <span className="cifra">{enSoles(Math.round(total))}</span>
        </div>
        <p className="suave">Últimos 30 días, comparado con tu promedio de 3 meses.</p>
        <ul className="lista-limpia">
          {categorias.map((c) => {
            const Icono = ICONOS[c.id] ?? DotsThree
            return (
              <li key={c.id} className="categoria">
                <span className="circulo" aria-hidden="true">
                  <Icono size={22} />
                </span>
                <span className="categoria-texto">
                  <span className="categoria-cabecera">
                    <span>{c.nombre}</span>
                    <span className="cifra">{enSoles(Math.round(c.total))}</span>
                  </span>
                  <span className="medidor" aria-hidden="true">
                    <span style={{ width: `${(c.total / mayor) * 100}%` }} />
                  </span>
                  <span className="categoria-pie">
                    <span className="suave">{c.ejemplo}</span>
                    <Comparacion total={c.total} promedio={c.promedio3m} />
                  </span>
                </span>
              </li>
            )
          })}
        </ul>
      </section>

      <section className="tarjeta" aria-labelledby="suscripciones-titulo">
        <h2 id="suscripciones-titulo">Suscripciones</h2>
        <ul className="lista-limpia">
          {suscripciones.map((s) => (
            <li key={s.id} className="fila">
              <span className="circulo" aria-hidden="true">
                {iniciales(s.comercio)}
              </span>
              <span className="fila-texto">
                <span>{s.comercio}</span>
                <span className="suave">
                  Día {s.dia}. {s.uso}
                </span>
              </span>
              <span className="fila-monto">{enSoles(s.monto)}</span>
            </li>
          ))}
        </ul>
      </section>
    </>
  )
}
