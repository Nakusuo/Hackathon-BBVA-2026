import { CirclePause, PiggyBank, UtensilsCrossed } from 'lucide-react'
import { enSoles } from '../formato.js'

const ICONOS = {
  'reco-1': CirclePause,
  'reco-2': UtensilsCrossed,
  'reco-3': PiggyBank,
}

export default function QueHacer({ cliente }) {
  return (
    <>
      <div className="encabezado-pantalla">
        <h1>Qué hacer</h1>
        <p>Cambios ordenados por lo que más te ayudan a pasar tu día más justo.</p>
      </div>

      <ul className="recos">
        {cliente.recomendaciones.map((r) => {
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
                <span className="cifra">+{enSoles(r.monto)}</span>
                <span className="suave">{r.efecto}</span>
              </p>
              <details>
                <summary>¿Por qué?</summary>
                <p className="suave">{r.porque}</p>
              </details>
            </li>
          )
        })}
      </ul>

      <p className="decision">
        Lucas te muestra simulaciones con tus datos. No mueve tu plata ni es asesoría: tú decides.
      </p>
    </>
  )
}
