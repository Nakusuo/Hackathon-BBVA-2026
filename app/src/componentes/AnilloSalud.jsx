const RADIO = 64
const GROSOR = 14
const CIRCUNFERENCIA = 2 * Math.PI * RADIO
const SEPARACION = 10

// Un tramo por componente: así se ve qué parte baja el puntaje, no solo el total.
export default function AnilloSalud({ puntaje, componentes }) {
  const tramo = CIRCUNFERENCIA / componentes.length
  const largo = tramo - SEPARACION

  return (
    <div className="anillo">
      <svg viewBox="0 0 156 156" aria-hidden="true">
        {componentes.map((c, i) => (
          <g key={c.nombre}>
            <circle
              cx="78"
              cy="78"
              r={RADIO}
              fill="none"
              stroke="var(--superficie-suave)"
              strokeWidth={GROSOR}
              strokeLinecap="round"
              strokeDasharray={`${largo} ${CIRCUNFERENCIA - largo}`}
              strokeDashoffset={-i * tramo}
            />
            <circle
              cx="78"
              cy="78"
              r={RADIO}
              fill="none"
              stroke="var(--acento)"
              strokeWidth={GROSOR}
              strokeLinecap="round"
              strokeDasharray={`${(largo * c.valor) / 100} ${CIRCUNFERENCIA}`}
              strokeDashoffset={-i * tramo}
            />
          </g>
        ))}
      </svg>
      <div className="anillo-centro">
        <span className="anillo-valor">{puntaje}</span>
        <span className="suave chico">de 100</span>
      </div>
    </div>
  )
}
