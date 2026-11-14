import { useState } from 'react'
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
import AvisoRiesgo from '../componentes/AvisoRiesgo.jsx'
import { enSoles, fechaCorta, fechaLarga } from '../formato.js'

const PERIODOS = [
  { id: 'ingreso', nombre: 'Hasta mi ingreso' },
  { id: 'mes', nombre: '30 días' },
]

function Globo({ active, payload }) {
  if (!active || !payload?.length) return null
  const punto = payload[0].payload
  return (
    <div className="globo">
      <strong>{fechaLarga(punto.fecha)}</strong>
      <span>Lo más probable: {enSoles(punto.esperado)}</span>
      <span>
        Entre {enSoles(punto.banda[0])} y {enSoles(punto.banda[1])}
      </span>
    </div>
  )
}

// Recharts redondea el eje a -1000 por un rojo pequeño y el cero queda perdido; las marcas van a mano.
function marcasDelEje(datos) {
  const piso = Math.floor(Math.min(0, ...datos.map((p) => p.banda[0])) / 250) * 250
  const paso = Math.max(...datos.map((p) => p.banda[1])) > 1500 ? 1000 : 500
  const techo = Math.ceil(Math.max(...datos.map((p) => p.banda[1])) / paso) * paso
  const marcas = new Set([piso])
  for (let v = 0; v <= techo; v += paso) marcas.add(v)
  return { dominio: [piso, techo], marcas: [...marcas] }
}

function DiaEnCirculo({ fecha }) {
  return (
    <span className="circulo" aria-hidden="true">
      {Number(fecha.slice(8))}
    </span>
  )
}

export default function QueViene({ cliente }) {
  const { pronostico, diaRiesgo, proximoIngreso, proximosPagos } = cliente
  const [periodo, setPeriodo] = useState('ingreso')

  const datos =
    periodo === 'ingreso' ? pronostico.filter((p) => p.fecha <= proximoIngreso.fecha) : pronostico
  const { dominio, marcas } = marcasDelEje(datos)
  const puntoRiesgo = diaRiesgo && datos.find((p) => p.fecha === diaRiesgo.fecha)
  const ultimoDia = datos.at(-1).fecha

  const movimientos = [
    ...proximosPagos.map((p) => ({ ...p, entra: false })),
    { fecha: proximoIngreso.fecha, concepto: 'Tu ingreso', tipo: proximoIngreso.tipo, monto: proximoIngreso.monto, entra: true },
  ]
    .filter((m) => m.fecha <= ultimoDia)
    .sort((a, b) => a.fecha.localeCompare(b.fecha))

  return (
    <>
      <div className="encabezado-pantalla">
        <h1>Qué viene</h1>
        <p>Tu saldo día por día y lo que entra o sale de tu cuenta.</p>
      </div>

      <AvisoRiesgo riesgo={diaRiesgo} />

      <section className="tarjeta" aria-labelledby="pronostico-titulo">
        <div className="tarjeta-titulo">
          <h2 id="pronostico-titulo">Tu saldo proyectado</h2>
          <div className="selector" role="group" aria-label="Periodo">
            {PERIODOS.map((p) => (
              <button key={p.id} type="button" aria-pressed={periodo === p.id} onClick={() => setPeriodo(p.id)}>
                {p.nombre}
              </button>
            ))}
          </div>
        </div>

        <div className="grafico">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={datos} margin={{ top: 12, right: 28, bottom: 0, left: 8 }}>
              <CartesianGrid stroke="var(--borde)" vertical={false} />
              <XAxis
                dataKey="fecha"
                tickFormatter={fechaCorta}
                interval="preserveStartEnd"
                minTickGap={28}
                tick={{ fill: 'var(--tinta-suave)', fontSize: 16 }}
                axisLine={{ stroke: 'var(--borde)' }}
                tickLine={false}
              />
              <YAxis
                tickFormatter={enSoles}
                domain={dominio}
                ticks={marcas}
                tick={{ fill: 'var(--tinta-suave)', fontSize: 16 }}
                axisLine={false}
                tickLine={false}
                width={92}
              />
              <Tooltip content={<Globo />} cursor={{ stroke: 'var(--tinta-suave)', strokeDasharray: '4 4' }} />
              <Area dataKey="banda" stroke="none" fill="var(--banda)" fillOpacity={0.6} isAnimationActive={false} />
              <Line
                dataKey="esperado"
                stroke="var(--acento)"
                strokeWidth={3}
                dot={false}
                activeDot={{ r: 6, fill: 'var(--superficie)', stroke: 'var(--acento)', strokeWidth: 3 }}
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
        <p className="suave chico">
          El rango se ensancha con los días porque tus ingresos como independiente varían de un mes a otro.
        </p>
      </section>

      <section className="tarjeta" aria-labelledby="movimientos-titulo">
        <h2 id="movimientos-titulo">Pagos e ingresos que vienen</h2>
        <ul className="lista-limpia">
          {movimientos.map((m) => (
            <li key={`${m.fecha}-${m.concepto}`} className="fila">
              <DiaEnCirculo fecha={m.fecha} />
              <span className="fila-texto">
                <span>{m.concepto}</span>
                <span className="suave">{fechaLarga(m.fecha)}</span>
              </span>
              <span className={`fila-monto ${m.entra ? 'entra' : ''}`}>
                {m.entra ? '+' : '−'}
                {enSoles(m.monto)}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </>
  )
}
