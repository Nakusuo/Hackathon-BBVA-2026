import { ArrowUp, CaretRight } from '@phosphor-icons/react'
import { motion, useReducedMotion } from 'motion/react'
import { Link } from 'react-router-dom'
import { Cell, Pie, PieChart } from 'recharts'
import { enSolesRedondo } from '../formato.js'
import { diferenciaConPromedio, partesDelGrafico, porcentajes, UMBRAL } from './categorias.js'

const SERIES = [
  'var(--serie-1)',
  'var(--serie-2)',
  'var(--serie-3)',
  'var(--serie-4)',
  'var(--serie-5)',
  'var(--serie-6)',
]

export default function Gastos({ cliente }) {
  const { categorias, suscripciones } = cliente
  const reducido = useReducedMotion()
  const total = categorias.reduce((s, c) => s + c.total, 0)
  const promedio = categorias.reduce((s, c) => s + c.promedio3m, 0)
  const diferencia = Math.round(total - promedio)
  const partes = partesDelGrafico(categorias)
  const porcentaje = porcentajes(partes)
  const enSuscripciones = suscripciones.reduce((s, x) => s + x.monto, 0)

  return (
    <section className="tarjeta gastos-resumen" aria-labelledby="gastos-titulo">
      <h2 id="gastos-titulo">Gastaste en los últimos 30 días</h2>
      <div className="dona">
        <PieChart width={168} height={168} aria-hidden="true">
          <Pie
            data={partes}
            dataKey="total"
            nameKey="nombre"
            innerRadius={56}
            outerRadius={80}
            startAngle={90}
            endAngle={-270}
            paddingAngle={2}
            stroke="none"
            isAnimationActive={!reducido}
          >
            {partes.map((p, i) => (
              <Cell key={p.id} fill={SERIES[i]} />
            ))}
          </Pie>
        </PieChart>
        <div className="dona-centro">
          <strong>{enSolesRedondo(total)}</strong>
          <span className="suave">
            {Math.abs(diferencia) <= UMBRAL
              ? 'como siempre'
              : `${enSolesRedondo(Math.abs(diferencia))} ${diferencia > 0 ? 'más' : 'menos'}`}
          </span>
        </div>
      </div>
      <ul className="lista-limpia leyenda-gastos">
        {partes.map((p, i) => (
          <motion.li
            key={p.id}
            initial={reducido ? false : { opacity: 0, x: 8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 + i * 0.05 }}
          >
            <span className="leyenda-punto" style={{ background: SERIES[i] }} aria-hidden="true" />
            <span className="leyenda-nombre">{p.nombre}</span>
            <span className="suave">{porcentaje[i]} %</span>
            <span className="cifra">{enSolesRedondo(p.total)}</span>
            {diferenciaConPromedio(p) > 0 && (
              <span className="sube" title="Más que tu promedio">
                <ArrowUp size={16} aria-label="Más que tu promedio" />
              </span>
            )}
          </motion.li>
        ))}
      </ul>
      <p className="suave">Comparado con tu promedio de 3 meses. Suscripciones: {enSolesRedondo(enSuscripciones)} al mes.</p>
      <Link to="/lucas/gastos-detalle" className="boton boton-chico boton-secundario">
        Ver detalle
        <CaretRight size={18} aria-hidden="true" />
      </Link>
    </section>
  )
}
