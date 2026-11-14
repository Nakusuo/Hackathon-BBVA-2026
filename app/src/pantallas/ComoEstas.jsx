import { enSoles, fechaLarga } from '../formato.js'

function nivel(puntaje) {
  if (puntaje >= 70) return 'bien'
  if (puntaje >= 45) return 'regular'
  return 'en riesgo'
}

export default function ComoEstas({ cliente }) {
  const { salud, segmento, gastoHormiga, suscripciones } = cliente
  const totalSuscripciones = suscripciones.reduce((s, x) => s + x.monto, 0)

  return (
    <>
      <div className="encabezado-pantalla">
        <h1>Cómo estás</h1>
        <p>
          Tienes <span className="cifra">{enSoles(cliente.saldoHoy)}</span> hoy. Tu próximo ingreso llega el{' '}
          {fechaLarga(cliente.proximoIngreso.fecha)}.
        </p>
      </div>

      <div className="rejilla">
        <section className="tarjeta" aria-labelledby="salud-titulo">
          <h2 id="salud-titulo">Tu salud financiera</h2>
          <div className="puntaje">
            <span className="puntaje-valor">{salud.puntaje}</span>
            <span className="suave">de 100, {nivel(salud.puntaje)}</span>
          </div>
          <ul className="lista-limpia">
            {salud.componentes.map((c) => (
              <li key={c.nombre}>
                <div className="fila">
                  <h3>{c.nombre}</h3>
                  <span className="cifra">{c.valor} / 100</span>
                </div>
                <div
                  className="medidor"
                  role="meter"
                  aria-label={c.nombre}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={c.valor}
                >
                  <span style={{ width: `${c.valor}%` }} />
                </div>
                <p className="suave">{c.explicacion}</p>
              </li>
            ))}
          </ul>
        </section>

        <div className="columna">
          <section className="tarjeta" aria-labelledby="segmento-titulo">
            <h2 id="segmento-titulo">Cómo manejas tu plata</h2>
            <h3>{segmento.nombre}</h3>
            <p className="suave">{segmento.descripcion}</p>
          </section>

          <section className="tarjeta" aria-labelledby="hormiga-titulo">
            <div className="fila">
              <h2 id="hormiga-titulo">Gasto hormiga este mes</h2>
              <span className="cifra">{enSoles(gastoHormiga.mes)}</span>
            </div>
            <ul className="lista-limpia">
              {gastoHormiga.detalle.map((g) => (
                <li key={g.comercio} className="fila">
                  <span>
                    {g.comercio} <span className="suave">({g.veces} veces)</span>
                  </span>
                  <span className="cifra">{enSoles(g.total)}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="tarjeta" aria-labelledby="suscripciones-titulo">
            <div className="fila">
              <h2 id="suscripciones-titulo">Suscripciones</h2>
              <span className="cifra">{enSoles(totalSuscripciones)} al mes</span>
            </div>
            <ul className="lista-limpia">
              {suscripciones.map((s) => (
                <li key={s.comercio}>
                  <div className="fila">
                    <span>{s.comercio}</span>
                    <span className="cifra">{enSoles(s.monto)}</span>
                  </div>
                  <p className="suave">
                    Se cobra el día {s.dia}. {s.usoUltimoMes}.
                  </p>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </>
  )
}
