import { ArrowDown, ArrowUp, CheckCircle, DotsThree } from '@phosphor-icons/react'
import { enSoles, enSolesRedondo, fechaCorta, iniciales } from '../formato.js'
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

// Una suscripción que Lucas propone pausar se puede elegir desde aquí: es el mismo tip del Resumen.
function PausarSuscripcion({ tip, activo, alAlternar }) {
  return (
    <span className="suscripcion-accion">
      <button type="button" className="boton-lo-hago" aria-pressed={activo} onClick={() => alAlternar(tip.id)}>
        {activo && <CheckCircle size={20} weight="fill" aria-hidden="true" />}
        Pausar hasta tu cobro
      </button>
      <span className="cifra cifra-azul">
        +{enSoles(tip.mejora)} el {fechaCorta(tip.fechaPeorDia)}
      </span>
    </span>
  )
}

export default function GastosDetalle({ cliente, alternarTip }) {
  const { categorias, suscripciones, recomendaciones, elegidos } = cliente
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
          {suscripciones.map((s) => {
            const tip = recomendaciones.find((r) => r.id === s.id)
            return (
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
                {tip && <PausarSuscripcion tip={tip} activo={elegidos.includes(tip.id)} alAlternar={alternarTip} />}
              </li>
            )
          })}
        </ul>
      </section>
    </>
  )
}
