export default function QueHacer({ cliente }) {
  return (
    <>
      <div className="encabezado-pantalla">
        <h1>Qué hacer</h1>
        <p>Cambios ordenados por lo que más te ayudan a pasar tu día más justo.</p>
      </div>

      <ul className="rejilla lista-limpia">
        {cliente.recomendaciones.map((r) => (
          <li key={r.id} className="tarjeta">
            <div className="reco-cabecera">
              <h2>{r.titulo}</h2>
              <span className="etiqueta">{r.facilidad}</span>
            </div>
            <p>{r.efecto}</p>
            <details>
              <summary>¿Por qué?</summary>
              <p className="suave">{r.porque}</p>
            </details>
          </li>
        ))}
      </ul>

      <p className="decision">
        Lucas te muestra simulaciones con tus datos. No mueve tu plata ni es asesoría: tú decides.
      </p>
    </>
  )
}
