import { Warning, X } from '@phosphor-icons/react'
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
import { vistaCon } from '../motor/cliente.js'
import ExplicameFacil from './ExplicameFacil.jsx'
import { explicarQueViene } from './explicaciones.js'
import Planificar from './Planificar.jsx'
import { validarPlanificado } from './planificar.js'

const VACIO = { tipo: 'gasto', monto: '', fecha: '', concepto: '' }

const PERIODOS = [
  { id: 'ingreso', nombre: 'Hasta mi cobro' },
  { id: 'mes', nombre: '30 días' },
]

// El gráfico va sobre azul profundo: colores claros para la línea y el texto, y el rojo claro para el cero.
const COLOR = {
  linea: 'var(--grafico-linea)',
  banda: 'var(--grafico-banda)',
  rejilla: 'rgb(255 255 255 / 0.12)',
  texto: 'var(--sobre-azul-suave)',
  riesgo: 'var(--riesgo-claro)',
  fondo: 'var(--azul-profundo)',
  fuerte: 'var(--sobre-azul)',
}

// Etiquetas directas sobre el gráfico: quien mira no tiene que cruzar colores con la leyenda.
const ETIQUETA = { fontSize: 16, fontWeight: 700 }

// El rótulo del peor caso lleva fondo propio: así no se cruza con la línea del cero y conserva contraste.
// Va a la izquierda del punto, salvo que el peor día caiga al inicio y no quepa; entonces va a la derecha.
function RotuloPeorCaso({ viewBox, texto }) {
  if (!viewBox) return null
  const ancho = texto.length * 9 + 20
  const izquierda = viewBox.x - ancho - 6
  const x = izquierda >= 0 ? izquierda : viewBox.x + 6
  const y = viewBox.y - 40
  return (
    <g>
      <rect x={x} y={y} width={ancho} height={26} rx={13} fill={COLOR.fondo} stroke={COLOR.riesgo} strokeWidth={1.5} />
      <text x={x + ancho / 2} y={y + 18} textAnchor="middle" fill={COLOR.fuerte} {...ETIQUETA}>
        {texto}
      </text>
    </g>
  )
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

function ListaMovimientos({ titulo, movimientos, alQuitar }) {
  if (!movimientos.length) return null
  return (
    <div className="grupo-dia">
      <h3 className="grupo-nombre">{titulo}</h3>
      <ul className="lista-limpia">
        {movimientos.map((m) => (
          <li key={m.id} className="fila">
            <span className="fila-texto">
              <span>{m.concepto}</span>
              <span className="suave">
                {fechaDia(m.fecha)}
                {m.planificado && ' · lo agregaste tú'}
              </span>
            </span>
            <span className={`fila-monto ${m.entra ? 'entra' : ''}`}>
              {m.entra ? '+' : '−'}
              {enSoles(m.monto)}
            </span>
            {m.planificado && (
              <button
                type="button"
                className="icono-boton icono-boton-suave"
                aria-label={`Quitar ${m.concepto} del ${fechaDia(m.fecha)}`}
                onClick={() => alQuitar(m.id)}
              >
                <X size={20} aria-hidden="true" />
              </button>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

// «Hasta mi cobro» cuenta el rojo antes del cobro, como el Resumen; «30 días» mira todo el pronóstico,
// donde también cae lo que se planifica para diciembre.
function estadoDelPanel(vista, periodo) {
  if (periodo === 'ingreso') {
    const { riesgo, peorDia } = vista
    return riesgo
      ? { peorFecha: riesgo.peorFecha, peorMonto: riesgo.peorMonto, rojo: `${textoDiasEnRojo(riesgo)} podrías quedar en rojo.` }
      : { peorFecha: peorDia.fecha, peorMonto: peorDia.monto, bien: 'Con tus cambios llegas a tu cobro sin quedar en rojo.' }
  }
  const { mes } = vista
  const base = { peorFecha: mes.peorFecha, peorMonto: mes.peorMonto }
  if (!mes.diasEnRojo) return { ...base, bien: 'En estos 30 días no quedas en rojo.' }
  const rojo =
    mes.diasEnRojo === 1
      ? `El ${fechaDia(mes.primerRojo)} podrías quedar en rojo.`
      : `${mes.diasEnRojo} días podrías quedar en rojo, desde el ${fechaDia(mes.primerRojo)}.`
  return { ...base, rojo }
}

export default function QueViene({ cliente, alAgregar, alQuitar }) {
  const [periodo, setPeriodo] = useState('ingreso')
  const [borrador, setBorrador] = useState(VACIO)
  const [agregado, setAgregado] = useState('')

  const revision = validarPlanificado(cliente, borrador)
  const { movimiento } = revision
  // Mientras el borrador es válido, todo el panel muestra cómo quedaría; nada se guarda hasta «Agregar».
  const prueba = movimiento
    ? vistaCon(cliente.elegidos, cliente.personaId, [], [...cliente.planificados, { ...movimiento, id: 'borrador' }])
    : null
  const vista = prueba ?? cliente
  const { pronostico, proximoIngreso, proximosPagos, saldoHoy, ingresos } = vista

  const datos = periodo === 'ingreso' ? pronostico.filter((p) => p.fecha <= proximoIngreso.fecha) : pronostico
  const { dominio, marcas } = marcasDelEje(datos)
  const panel = estadoDelPanel(vista, periodo)
  const puntoRiesgo = panel.rojo && datos.find((p) => p.fecha === panel.peorFecha)
  const ultimoDia = datos.at(-1).fecha
  const primero = datos[0]

  const movimientos = [
    ...proximosPagos.map((p) => ({ ...p, entra: false })),
    ...ingresos.map((i) => ({ ...i, entra: true })),
    ...cliente.planificados.map((m) => ({ ...m, entra: m.tipo === 'ingreso', planificado: true })),
  ]
    .filter((m) => m.fecha <= ultimoDia)
    .sort((a, b) => a.fecha.localeCompare(b.fecha))
  const antes = movimientos.filter((m) => m.fecha < proximoIngreso.fecha)
  const desde = movimientos.filter((m) => m.fecha >= proximoIngreso.fecha)

  const resumen = `Saldo de hoy ${enSoles(saldoHoy)}. El peor caso es ${enSoles(panel.peorMonto)} el ${fechaDia(panel.peorFecha)}. ${panel.rojo ?? panel.bien}`

  function cambiar(campo, valor) {
    setAgregado('')
    setBorrador((previo) => ({ ...previo, [campo]: valor }))
    // La vista sigue a la fecha: lo que cae después del cobro no se ve en «Hasta mi cobro».
    if (campo === 'fecha' && valor) setPeriodo(valor >= proximoIngreso.fecha ? 'mes' : 'ingreso')
  }

  function agregar(nuevo) {
    alAgregar(nuevo)
    setBorrador(VACIO)
    setAgregado(`Agregué ${nuevo.concepto} (${enSoles(nuevo.monto)}) el ${fechaDia(nuevo.fecha)}. Ya está en tu pronóstico.`)
  }

  return (
    <>
      <section className="panel-azul panel-grafico" aria-labelledby="pronostico-titulo">
        <div className="tarjeta-titulo">
          <h2 id="pronostico-titulo">{prueba ? 'Así quedaría tu saldo' : 'Tu saldo proyectado'}</h2>
          <div className="selector selector-oscuro" role="group" aria-label="Periodo">
            {PERIODOS.map((p) => (
              <button key={p.id} type="button" aria-pressed={periodo === p.id} onClick={() => setPeriodo(p.id)}>
                {p.nombre}
              </button>
            ))}
          </div>
        </div>

        <div className="panel-riesgo">
          <p className="panel-etiqueta">Peor caso el {fechaDia(panel.peorFecha)}</p>
          <p className="panel-cifra">{panel.rojo ? enSoles(panel.peorMonto) : conSigno(panel.peorMonto)}</p>
          {panel.rojo ? (
            <p className="panel-aviso">
              <Warning size={20} weight="fill" aria-hidden="true" />
              <span>
                {panel.rojo}{' '}
                <Link className="enlace enlace-claro" to="/lucas/resumen#tips">
                  Ver tips
                </Link>
              </span>
            </p>
          ) : (
            <p className="panel-aviso">{panel.bien}</p>
          )}
        </div>

        <p className="solo-lector">{resumen}</p>
        <div className="grafico" aria-hidden="true">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={datos} margin={{ top: 28, right: 16, bottom: 0, left: 0 }}>
              <CartesianGrid stroke={COLOR.rejilla} vertical={false} />
              <ReferenceLine
                x={proximoIngreso.fecha}
                stroke={COLOR.texto}
                strokeDasharray="2 4"
                label={{ ...ETIQUETA, value: 'Cobro', position: 'insideTopRight', fill: COLOR.fuerte }}
              />
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
              <Area dataKey="banda" stroke="none" fill={COLOR.banda} isAnimationActive={false} />
              {/* Halo del color del fondo bajo la línea: la separa de la banda, que solo llega a 2.4:1 con la crema. */}
              <Line
                dataKey="esperado"
                stroke={COLOR.fondo}
                strokeWidth={7}
                dot={false}
                activeDot={false}
                tooltipType="none"
                legendType="none"
                isAnimationActive={false}
              />
              <Line
                dataKey="esperado"
                stroke={COLOR.linea}
                strokeWidth={3}
                strokeDasharray="8 5"
                dot={false}
                activeDot={{ r: 6, fill: COLOR.fondo, stroke: COLOR.linea, strokeWidth: 3 }}
                isAnimationActive={false}
              />
              <ReferenceLine y={0} stroke={COLOR.riesgo} strokeDasharray="6 4" strokeWidth={2} />
              <ReferenceDot
                x={primero.fecha}
                y={primero.esperado}
                r={6}
                fill={COLOR.linea}
                stroke={COLOR.fondo}
                strokeWidth={2}
                label={{ ...ETIQUETA, value: 'Hoy', position: 'top', fill: COLOR.fuerte }}
              />
              {puntoRiesgo && (
                <ReferenceDot
                  x={puntoRiesgo.fecha}
                  y={puntoRiesgo.banda[0]}
                  r={6}
                  fill={COLOR.riesgo}
                  stroke={COLOR.fondo}
                  strokeWidth={2}
                  label={<RotuloPeorCaso texto={`Peor caso ${enSoles(riesgo.peorMonto)}`} />}
                />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        <div className="leyenda" aria-hidden="true">
          <span className="clave-esperado">Lo más probable</span>
          <span className="clave-banda">Rango posible</span>
        </div>
      </section>

      <Planificar
        cliente={cliente}
        prueba={prueba}
        borrador={borrador}
        revision={revision}
        alCambiar={cambiar}
        alAgregar={agregar}
      />
      <p className="solo-lector" role="status">
        {agregado}
      </p>


      <section className="tarjeta" aria-labelledby="movimientos-titulo">
        <h2 id="movimientos-titulo">Pagos y cobros</h2>
        <ListaMovimientos titulo="Antes de tu cobro" movimientos={antes} alQuitar={alQuitar} />
        <ListaMovimientos titulo="Desde tu cobro" movimientos={desde} alQuitar={alQuitar} />
        <ExplicameFacil puntos={explicarQueViene(cliente)} />
      </section>
    </>
  )
}
