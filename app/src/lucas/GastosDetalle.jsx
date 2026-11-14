import { ArrowDown, ArrowUp, DotsThree } from '@phosphor-icons/react'
import { enSoles, enSolesRedondo, iniciales } from '../formato.js'
import { diferenciaConPromedio, ICONOS_CATEGORIA } from './categorias.js'

function Comparacion({ categoria }) {
  const diferencia = diferenciaConPromedio(categoria)
  if (!diferencia) return <span className="suave">Como siempre</span>
  const Flecha = diferencia > 0 ? ArrowUp : ArrowDown
  return (
    <span className={diferencia > 0 ? 'sube' : 'baja'}>
      <Flecha size={16} aria-hidden="true" />
      {enSoles(Math.abs(diferencia))} {diferencia > 0 ? 'más' : 'menos'} que tu promedio
    </span>
  )
}

export default function GastosDetalle({ cliente }) {
  const { categorias, suscripciones } = cliente
  const mayor = Math.max(...categorias.map((c) => c.total))

  return (
    <>
      <section className="tarjeta" aria-labelledby="categorias-titulo">
        <h2 id="categorias-titulo">Tus gastos por categoría</h2>
        <ul className="lista-limpia">
          {categorias.map((c) => {
            const Icono = ICONOS_CATEGORIA[c.id] ?? DotsThree
            return (
              <li key={c.id} className="categoria">
                <span className="circulo" aria-hidden="true">
                  <Icono size={22} />
                </span>
                <span className="categoria-texto">
                  <span className="categoria-cabecera">
                    <span>{c.nombre}</span>
                    <span className="cifra">{enSolesRedondo(c.total)}</span>
                  </span>
                  <span className="medidor" aria-hidden="true">
                    <span style={{ width: `${(c.total / mayor) * 100}%` }} />
                  </span>
                  <span className="categoria-pie">
                    <span className="suave">{c.ejemplo}</span>
                    <Comparacion categoria={c} />
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
