import { useState } from 'react'
import { Link } from 'react-router-dom'
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
import { enSoles, fechaCorta, fechaDia, fechaLarga, textoDiasEnRojo } from '../formato.js'
import { marcasDelEje } from '../grafico.js'

const PERIODOS = [
  { id: 'ingreso', nombre: 'Hasta mi cobro' },
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

export default function QueViene({ cliente }) {
  const { pronostico, riesgo, proximoIngreso, proximosPagos, saldoHoy } = cliente
  const [periodo, setPeriodo] = useState('ingreso')

  const datos = periodo === 'ingreso' ? pronostico.filter((p) => p.fecha <= proximoIngreso.fecha) : pronostico
  const { dominio, marcas } = marcasDelEje(datos)
  const puntoRiesgo = riesgo && datos.find((p) => p.fecha === riesgo.peorFecha)
  const ultimoDia = datos.at(-1).fecha

  const movimientos = [
    ...proximosPagos.map((p) => ({ ...p, entra: false })),
    { id: 'ingreso', fecha: proximoIngreso.fecha, concepto: 'Tu cobro', monto: proximoIngreso.monto, entra: true },
  ]
    .filter((m) => m.fecha <= ultimoDia)
    .sort((a, b) => a.fecha.localeCompare(b.fecha))

  const resumen = riesgo
    ? `Saldo de hoy ${enSoles(saldoHoy)}. Baja hasta el ${fechaDia(riesgo.peorFecha)}, donde el peor caso es ${enSoles(riesgo.peorMonto)}, y sube el ${fechaDia(proximoIngreso.fecha)} con tu cobro.`
    : `Saldo de hoy ${enSoles(saldoHoy)}. No baja de cero antes de tu cobro.`

  return (
    <>
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

          {riesgo ? (
            <p>
              <strong className="texto-riesgo">{textoDiasEnRojo(riesgo)} podrías quedar en rojo.</strong> Peor caso:{' '}
              <span className="cifra">{enSoles(riesgo.peorMonto)}</span> el {fechaDia(riesgo.peorFecha)}.{' '}
              <Link className="enlace" to="/lucas/resumen">
                Ver tips
              </Link>
            </p>
          ) : (
            <p>Llegas a tu cobro sin quedar en rojo, incluso en el peor caso.</p>
          )}

          <p className="solo-lector">{resumen}</p>
          <div className="grafico" aria-hidden="true">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={datos} margin={{ top: 8, right: 24, bottom: 0, left: 4 }}>
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
                  width={88}
                />
                <Tooltip content={<Globo />} cursor={{ stroke: 'var(--tinta-suave)', strokeDasharray: '4 4' }} />
                <Area dataKey="banda" stroke="none" fill="var(--banda)" fillOpacity={0.7} isAnimationActive={false} />
                <Line
                  dataKey="esperado"
                  stroke="var(--azul)"
                  strokeWidth={3}
                  dot={false}
                  activeDot={{ r: 6, fill: 'var(--superficie)', stroke: 'var(--azul)', strokeWidth: 3 }}
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
            <span className="clave-esperado">Lo más probable</span>
            <span className="clave-banda">Rango posible</span>
            <span className="clave-cero">Saldo en cero</span>
          </div>
          <p className="suave">El rango se abre con los días porque tu ingreso varía de un mes a otro.</p>
        </section>

        <section className="tarjeta" aria-labelledby="movimientos-titulo">
          <h2 id="movimientos-titulo">Pagos y cobros</h2>
          <ul className="lista-limpia">
            {movimientos.map((m) => (
              <li key={m.id} className="fila">
                <span className="fila-texto">
                  <span>{m.concepto}</span>
                  <span className="suave">{fechaDia(m.fecha)}</span>
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
