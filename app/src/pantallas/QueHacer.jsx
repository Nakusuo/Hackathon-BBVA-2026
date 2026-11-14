import { CirclePause, Coffee, PiggyBank, UtensilsCrossed } from 'lucide-react'
import { conSigno, enSoles, fechaDia } from '../formato.js'

const ICONOS = {
  musika: CirclePause,
  delivery: UtensilsCrossed,
  cafe: Coffee,
}

export default function QueHacer({ cliente }) {
  const { recomendaciones, conTodos, riesgo, apartado, proximoIngreso } = cliente
  const peorFecha = recomendaciones[0]?.fechaPeorDia

  return (
    <>
      <div className="encabezado-pantalla">
        <h1>Qué hacer</h1>
        <p>
          {peorFecha
            ? `Ordenados por cuánto mejoran tu día más justo, el ${fechaDia(peorFecha)}.`
            : 'Cambios que te dejan más margen hasta tu cobro.'}
        </p>
      </div>

      {riesgo && (
        <section className="sugerencia" aria-label="Efecto de los cambios juntos">
          <p className="sugerencia-etiqueta">Si haces los {recomendaciones.length} cambios</p>
          <p>
            Tu peor caso del {fechaDia(riesgo.peorFecha)} pasa de <span className="cifra">{enSoles(riesgo.peorMonto)}</span> a{' '}
            <span className="cifra">{conSigno(conTodos.peorMonto)}</span>
            {conTodos.diasEnRojo === 0 ? ': ya no quedas en rojo antes de cobrar.' : '.'}
          </p>
        </section>
      )}

      <ul className="recos">
        {recomendaciones.map((r) => {
          const Icono = ICONOS[r.id] ?? PiggyBank
          return (
            <li key={r.id} className="tarjeta">
              <div className="reco-cabecera">
                <span className="circulo" aria-hidden="true">
                  <Icono size={20} />
                </span>
                <span className="pildora">{r.facilidad}</span>
              </div>
              <h2>{r.titulo}</h2>
              <p className="reco-efecto">
                <span className="cifra">{conSigno(r.mejora)} en tu día más justo</span>
                <span className="suave">
                  Tu peor caso pasa de {enSoles(r.peorAntes)} a {enSoles(r.peorDespues)}.
                </span>
              </p>
              <details>
                <summary>¿Por qué?</summary>
                <p className="suave">{r.porque}</p>
              </details>
            </li>
          )
        })}
      </ul>

      <section className="tarjeta" aria-labelledby="despues-titulo">
        <div className="fila">
          <span className="circulo" aria-hidden="true">
            <PiggyBank size={20} />
          </span>
          <span className="fila-texto">
            <h2 id="despues-titulo">
              Cuando cobres el {fechaDia(proximoIngreso.fecha)}, aparta {enSoles(apartado.monto)}
            </h2>
            <span className="suave">
              Separarlo el mismo día evita gastarlo sin darte cuenta. En {apartado.cobros} cobros tendrías{' '}
              {enSoles(apartado.total)} de colchón.
            </span>
          </span>
        </div>
      </section>

      <p className="decision">Lucas te muestra simulaciones con tus datos. No mueve tu plata ni es asesoría: tú decides.</p>
    </>
  )
}
