import { Link } from 'react-router-dom'
import AnilloSalud from '../componentes/AnilloSalud.jsx'
import AvisoRiesgo from '../componentes/AvisoRiesgo.jsx'
import { diasEntre, enSoles, fechaLarga, iniciales } from '../formato.js'

function nivel(puntaje) {
  if (puntaje >= 70) return 'Vas bien'
  if (puntaje >= 45) return 'Vas regular'
  return 'Estás en riesgo'
}

export default function ComoEstas({ cliente }) {
  const { salud, segmento, gastosFrecuentes, suscripciones, proximoIngreso, riesgo } = cliente
  const totalSuscripciones = suscripciones.reduce((s, x) => s + x.monto, 0)

  return (
    <>
      <div className="encabezado-pantalla">
        <h1>Cómo estás</h1>
        <p>Hoy es {fechaLarga(cliente.hoy)}.</p>
      </div>

      <div className="dos-columnas">
        <div className="columna">
          <section className="principal" aria-label="Cuánto puedes gastar">
            <p className="principal-etiqueta">Para llegar a tu cobro sin quedar en rojo, gasta hasta</p>
            <p className="principal-cifra">
              {enSoles(cliente.gastoDiarioSeguro)} <small>al día</small>
            </p>
            <p>Hoy gastas unos {enSoles(cliente.gastoDiarioActual)} al día.</p>
            <div className="principal-pie">
              <div>
                <span>Saldo hoy</span>
                <strong>{enSoles(cliente.saldoHoy)}</strong>
              </div>
              <div>
                <span>Cobras</span>
                <strong>
                  {enSoles(proximoIngreso.monto)} en {diasEntre(cliente.hoy, proximoIngreso.fecha)} días
                </strong>
              </div>
            </div>
          </section>

          <AvisoRiesgo riesgo={riesgo} />

          <section className="tarjeta" aria-labelledby="frecuentes-titulo">
            <div className="tarjeta-titulo">
              <h2 id="frecuentes-titulo">Gastos que se repiten</h2>
              <Link className="enlace" to="/que-hacer">
                Ver cómo bajarlos
              </Link>
            </div>
            <ul className="lista-limpia">
              {gastosFrecuentes.map((g) => (
                <li key={g.id} className="fila">
                  <span className="circulo" aria-hidden="true">
                    {iniciales(g.comercio)}
                  </span>
                  <span className="fila-texto">
                    <span>{g.comercio}</span>
                    <span className="suave">{g.vecesMes} veces este mes</span>
                  </span>
                  <span className="fila-monto">{enSoles(g.totalMes)}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>

        <div className="columna">
          <section className="tarjeta" aria-labelledby="salud-titulo">
            <div className="tarjeta-titulo">
              <h2 id="salud-titulo">Tu salud financiera</h2>
              <span className="pildora">{nivel(salud.puntaje)}</span>
            </div>
            <div className="salud">
              <AnilloSalud puntaje={salud.puntaje} componentes={salud.componentes} />
              <ul className="lista-limpia componentes">
                {salud.componentes.map((c) => (
                  <li key={c.nombre} className="componente">
                    <span className="componente-cabecera">
                      <span>{c.nombre}</span>
                      <span>{c.valor}</span>
                    </span>
                    <span className="suave">{c.explicacion}</span>
                  </li>
                ))}
              </ul>
            </div>
            <p className="suave">
              Es el promedio de las 4 partes. Tu perfil: <strong>{segmento.nombre}</strong>.
            </p>
          </section>

          <section className="tarjeta" aria-labelledby="suscripciones-titulo">
            <div className="tarjeta-titulo">
              <h2 id="suscripciones-titulo">Suscripciones</h2>
              <span className="cifra">{enSoles(totalSuscripciones)} al mes</span>
            </div>
            <ul className="lista-limpia">
              {suscripciones.map((s) => (
                <li key={s.id} className="fila">
                  <span className="circulo" aria-hidden="true">
                    {iniciales(s.comercio)}
                  </span>
                  <span className="fila-texto">
                    <span>{s.comercio}</span>
                    <span className="suave">
                      Día {s.dia}. {s.uso}
                    </span>
                  </span>
                  <span className="fila-monto">{enSoles(s.monto)}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </>
  )
}
