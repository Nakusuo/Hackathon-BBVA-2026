import AnilloSalud from '../componentes/AnilloSalud.jsx'
import AvisoRiesgo from '../componentes/AvisoRiesgo.jsx'
import { diasEntre, enSoles, fechaLarga, iniciales } from '../formato.js'

function nivel(puntaje) {
  if (puntaje >= 70) return 'Vas bien'
  if (puntaje >= 45) return 'Vas regular'
  return 'Estás en riesgo'
}

export default function ComoEstas({ cliente }) {
  const { salud, segmento, gastoHormiga, suscripciones, proximoIngreso } = cliente
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
            <p className="etiqueta-principal">Puedes gastar hasta</p>
            <p className="principal-cifra">
              {enSoles(cliente.disponibleDiario)} <small>al día</small>
            </p>
            <p>Así llegas a tu próximo ingreso con tus pagos fijos cubiertos.</p>
            <div className="principal-pie">
              <div>
                <span>Saldo hoy</span>
                <strong>{enSoles(cliente.saldoHoy)}</strong>
              </div>
              <div>
                <span>Próximo ingreso</span>
                <strong>
                  {enSoles(proximoIngreso.monto)} en {diasEntre(cliente.hoy, proximoIngreso.fecha)} días
                </strong>
              </div>
            </div>
          </section>

          <AvisoRiesgo riesgo={cliente.diaRiesgo} />

          <section className="tarjeta" aria-labelledby="hormiga-titulo">
            <div className="tarjeta-titulo">
              <h2 id="hormiga-titulo">Gasto hormiga este mes</h2>
              <span className="cifra">{enSoles(gastoHormiga.mes)}</span>
            </div>
            <ul className="lista-limpia">
              {gastoHormiga.detalle.map((g) => (
                <li key={g.comercio} className="fila">
                  <span className="circulo" aria-hidden="true">
                    {iniciales(g.comercio)}
                  </span>
                  <span className="fila-texto">
                    <span>{g.comercio}</span>
                    <span className="suave">{g.veces} veces este mes</span>
                  </span>
                  <span className="fila-monto">{enSoles(g.total)}</span>
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
                    <span className="suave chico">{c.explicacion}</span>
                  </li>
                ))}
              </ul>
            </div>
            <p className="suave chico">
              Tu perfil: <strong>{segmento.nombre}</strong>. {segmento.descripcion}
            </p>
          </section>

          <section className="tarjeta" aria-labelledby="suscripciones-titulo">
            <div className="tarjeta-titulo">
              <h2 id="suscripciones-titulo">Suscripciones</h2>
              <span className="cifra">{enSoles(totalSuscripciones)} al mes</span>
            </div>
            <ul className="lista-limpia">
              {suscripciones.map((s) => (
                <li key={s.comercio} className="fila">
                  <span className="circulo" aria-hidden="true">
                    {iniciales(s.comercio)}
                  </span>
                  <span className="fila-texto">
                    <span>{s.comercio}</span>
                    <span className="suave">
                      Día {s.dia}. {s.usoUltimoMes}
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
