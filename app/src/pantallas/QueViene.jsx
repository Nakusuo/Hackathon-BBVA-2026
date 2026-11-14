import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { diasEntre, enSoles, fechaCorta, fechaLarga } from '../formato.js'

function DetalleDia({ active, payload }) {
  if (!active || !payload?.length) return null
  const punto = payload[0].payload
  return (
    <div className="tooltip">
      <strong>{fechaLarga(punto.fecha)}</strong>
      <p>Lo más probable: {enSoles(punto.esperado)}</p>
      <p className="suave">
        Entre {enSoles(punto.banda[0])} y {enSoles(punto.banda[1])}
      </p>
    </div>
  )
}

export default function QueViene({ cliente }) {
  const { pronostico, diaRiesgo, proximoIngreso, hoy } = cliente
  const puntoRiesgo = diaRiesgo && pronostico.find((p) => p.fecha === diaRiesgo.fecha)
  // Recharts redondea el eje a -1000 por un rojo pequeño y el cero queda perdido; las marcas van a mano.
  const piso = Math.floor(Math.min(0, ...pronostico.map((p) => p.banda[0])) / 250) * 250
  const techo = Math.ceil(Math.max(...pronostico.map((p) => p.banda[1])) / 1000) * 1000
  const marcas = [piso, ...Array.from({ length: techo / 1000 + 1 }, (_, i) => i * 1000)].filter(
    (v, i, todas) => todas.indexOf(v) === i,
  )

  return (
    <>
      <div className="encabezado-pantalla">
        <h1>Qué viene</h1>
        <p>Tu saldo de los próximos 30 días, día por día.</p>
      </div>

      <section className="tarjeta" aria-labelledby="pronostico-titulo">
        <h2 id="pronostico-titulo">
          {diaRiesgo
            ? `Tu día más justo es el ${fechaLarga(diaRiesgo.fecha)}`
            : 'Llegas a tu próximo ingreso sin quedar en rojo'}
        </h2>
        {diaRiesgo && (
          <p>
            Faltan {diasEntre(hoy, diaRiesgo.fecha)} días. Ese día tu saldo estaría entre{' '}
            <span className="cifra">{enSoles(diaRiesgo.minimo)}</span> y{' '}
            <span className="cifra">{enSoles(diaRiesgo.maximo)}</span>. Cobras{' '}
            <span className="cifra">{enSoles(proximoIngreso.monto)}</span> el {fechaLarga(proximoIngreso.fecha)}.
          </p>
        )}

        <div className="grafico">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={pronostico} margin={{ top: 12, right: 28, bottom: 0, left: 8 }}>
              <CartesianGrid stroke="var(--borde)" vertical={false} />
              <XAxis
                dataKey="fecha"
                tickFormatter={fechaCorta}
                interval="preserveStartEnd"
                minTickGap={28}
                tick={{ fill: 'var(--tinta-suave)', fontSize: 14 }}
                axisLine={{ stroke: 'var(--borde)' }}
                tickLine={false}
              />
              <YAxis
                tickFormatter={enSoles}
                domain={[piso, techo]}
                ticks={marcas}
                tick={{ fill: 'var(--tinta-suave)', fontSize: 14 }}
                axisLine={false}
                tickLine={false}
                width={84}
              />
              <Tooltip content={<DetalleDia />} />
              <Area
                dataKey="banda"
                stroke="none"
                fill="var(--banda)"
                fillOpacity={0.6}
                isAnimationActive={false}
              />
              <Line
                dataKey="esperado"
                stroke="var(--acento)"
                strokeWidth={3}
                dot={false}
                isAnimationActive={false}
              />
              <ReferenceLine y={0} stroke="var(--riesgo)" strokeDasharray="6 4" strokeWidth={2} />
              {puntoRiesgo && (
                <ReferenceDot
                  x={puntoRiesgo.fecha}
                  y={puntoRiesgo.banda[0]}
                  r={6}
                  fill="var(--riesgo)"
                  stroke="var(--superficie)"
                  strokeWidth={2}
                />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        <div className="leyenda" aria-hidden="true">
          <span className="clave-esperado">Saldo más probable</span>
          <span className="clave-banda">Rango posible</span>
          <span className="clave-cero">Saldo en cero</span>
        </div>
        <p className="suave">
          El rango se ensancha con los días porque tus ingresos como independiente varían de un mes a otro.
        </p>
      </section>
    </>
  )
}
