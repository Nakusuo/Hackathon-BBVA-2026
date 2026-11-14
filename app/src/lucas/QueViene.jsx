import { Warning } from '@phosphor-icons/react'
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
import { conSigno, enSoles, fechaCorta, fechaDia, fechaLarga, textoDiasEnRojo } from '../formato.js'
import { marcasDelEje } from '../grafico.js'

const PERIODOS = [
  { id: 'ingreso', nombre: 'Hasta mi cobro' },
  { id: 'mes', nombre: '30 días' },
]

// El gráfico va sobre azul profundo: colores claros para la línea y el texto, y el rojo claro para el cero.
const COLOR = {
  linea: 'var(--crema)',
  banda: 'var(--azul-claro)',
  rejilla: 'rgb(255 255 255 / 0.15)',
  texto: 'var(--sobre-azul-suave)',
  riesgo: 'var(--riesgo-claro)',
  fondo: 'var(--azul-profundo)',
}

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

function ListaMovimientos({ titulo, movimientos }) {
  if (!movimientos.length) return null
  return (
    <div className="grupo-dia">
      <h3 className="grupo-nombre">{titulo}</h3>
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
    </div>
  )
}

export default function QueViene({ cliente }) {
  const { pronostico, riesgo, proximoIngreso, proximosPagos, saldoHoy, ingresos } = cliente
  const [periodo, setPeriodo] = useState('ingreso')

  const datos = periodo === 'ingreso' ? pronostico.filter((p) => p.fecha <= proximoIngreso.fecha) : pronostico
  const { dominio, marcas } = marcasDelEje(datos)
  const puntoRiesgo = riesgo && datos.find((p) => p.fecha === riesgo.peorFecha)
  const ultimoDia = datos.at(-1).fecha

  const movimientos = [
    ...proximosPagos.map((p) => ({ ...p, entra: false })),
    ...ingresos.map((i) => ({ ...i, entra: true })),
  ]
    .filter((m) => m.fecha <= ultimoDia)
    .sort((a, b) => a.fecha.localeCompare(b.fecha))
  const antes = movimientos.filter((m) => m.fecha < proximoIngreso.fecha)
  const desde = movimientos.filter((m) => m.fecha >= proximoIngreso.fecha)

  const resumen = riesgo
    ? `Saldo de hoy ${enSoles(saldoHoy)}. Baja hasta el ${fechaDia(riesgo.peorFecha)}, donde el peor caso es ${enSoles(riesgo.peorMonto)}, y sube el ${fechaDia(proximoIngreso.fecha)} con tu cobro.`
    : `Saldo de hoy ${enSoles(saldoHoy)}. No baja de cero antes de tu cobro.`

  return (
    <>
      <section className="panel-azul panel-grafico" aria-labelledby="pronostico-titulo">
        <div className="tarjeta-titulo">
          <h2 id="pronostico-titulo">Tu saldo proyectado</h2>
          <div className="selector selector-oscuro" role="group" aria-label="Periodo">
            {PERIODOS.map((p) => (
              <button key={p.id} type="button" aria-pressed={periodo === p.id} onClick={() => setPeriodo(p.id)}>
                {p.nombre}
              </button>
            ))}
          </div>
        </div>

        {riesgo ? (
          <div className="panel-riesgo">
            <p className="panel-etiqueta">Peor caso el {fechaDia(riesgo.peorFecha)}</p>
            <p className="panel-cifra">{enSoles(riesgo.peorMonto)}</p>
            <p className="panel-aviso">
              <Warning size={20} weight="fill" aria-hidden="true" />
              <span>
                {textoDiasEnRojo(riesgo)} podrías quedar en rojo.{' '}
                <Link className="enlace enlace-claro" to="/lucas/resumen#tips">
                  Ver tips
                </Link>
              </span>
            </p>
          </div>
        ) : (
          <div className="panel-riesgo">
            <p className="panel-etiqueta">Peor caso el {fechaDia(cliente.peorDia.fecha)}</p>
            <p className="panel-cifra">{conSigno(cliente.peorDia.monto)}</p>
            <p className="panel-aviso">Con tus cambios llegas a tu cobro sin quedar en rojo.</p>
          </div>
        )}

        <p className="solo-lector">{resumen}</p>
        <div className="grafico" aria-hidden="true">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={datos} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
              <CartesianGrid stroke={COLOR.rejilla} vertical={false} />
              <XAxis
                dataKey="fecha"
                tickFormatter={fechaCorta}
                interval="preserveStartEnd"
                minTickGap={28}
                tick={{ fill: COLOR.texto, fontSize: 16 }}
                axisLine={{ stroke: COLOR.rejilla }}
                tickLine={false}
              />
              <YAxis
                tickFormatter={enSoles}
                domain={dominio}
                ticks={marcas}
                tick={{ fill: COLOR.texto, fontSize: 16 }}
                axisLine={false}
                tickLine={false}
                width={84}
              />
              <Tooltip content={<Globo />} cursor={{ stroke: COLOR.texto, strokeDasharray: '4 4' }} />
              <Area dataKey="banda" stroke="none" fill={COLOR.banda} fillOpacity={0.35} isAnimationActive={false} />
              <Line
                dataKey="esperado"
                stroke={COLOR.linea}
                strokeWidth={3}
                dot={false}
                activeDot={{ r: 6, fill: COLOR.fondo, stroke: COLOR.linea, strokeWidth: 3 }}
                isAnimationActive={false}
              />
              <ReferenceLine y={0} stroke={COLOR.riesgo} strokeDasharray="6 4" strokeWidth={2} />
              {puntoRiesgo && (
                <ReferenceDot
                  x={puntoRiesgo.fecha}
                  y={puntoRiesgo.banda[0]}
                  r={6}
                  fill={COLOR.riesgo}
                  stroke={COLOR.fondo}
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
      </section>

      <section className="tarjeta hoja" aria-labelledby="movimientos-titulo">
        <h2 id="movimientos-titulo">Pagos y cobros</h2>
        <ListaMovimientos titulo="Antes de tu cobro" movimientos={antes} />
        <ListaMovimientos titulo="Desde tu cobro" movimientos={desde} />
        <p className="suave">
          El rango se abre con los días porque tu gasto varía, y se ensancha en cada cobro porque tus clientes no siempre
          te pagan lo mismo.
        </p>
      </section>
    </>
  )
}
