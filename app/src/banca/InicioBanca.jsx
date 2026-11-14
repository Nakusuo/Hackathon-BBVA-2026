import { ArrowsLeftRight, Bell, DeviceMobile, Eye, EyeSlash, QrCode, Receipt, UserCircle } from '@phosphor-icons/react'
import { useState } from 'react'
import { Link, useOutletContext } from 'react-router-dom'
import MarcaLucas from '../componentes/MarcaLucas.jsx'
import { diasEntre, enSoles, fechaCorta, fechaDia, iniciales, textoDiasEnRojo } from '../formato.js'
import { cliente } from '../mocks/cliente.js'

const ACCESOS = [
  { nombre: 'Transferir', Icono: ArrowsLeftRight },
  { nombre: 'Pagar servicios', Icono: Receipt },
  { nombre: 'Recargar celular', Icono: DeviceMobile },
  { nombre: 'Pagar con QR', Icono: QrCode },
]

const OCULTO = 'S/ ••••'

function nombreDelDia(fecha, hoy) {
  const dias = diasEntre(fecha, hoy)
  if (dias === 0) return 'Hoy'
  if (dias === 1) return 'Ayer'
  return fechaCorta(fecha)
}

function agruparPorDia(movimientos, hoy) {
  const grupos = []
  for (const m of movimientos) {
    const nombre = nombreDelDia(m.fecha, hoy)
    const grupo = grupos.at(-1)
    if (grupo?.nombre === nombre) grupo.movimientos.push(m)
    else grupos.push({ nombre, movimientos: [m] })
  }
  return grupos
}

export default function InicioBanca() {
  const { avisarSinDemo } = useOutletContext()
  const [montosVisibles, setMontosVisibles] = useState(true)
  const monto = (valor) => (montosVisibles ? enSoles(valor) : OCULTO)
  const { riesgo, cuenta, tarjeta, hoy, proximoIngreso } = cliente
  const pagosAntesDelCobro = cliente.proximosPagos.filter((p) => p.fecha < proximoIngreso.fecha)

  return (
    <>
      <header className="banca-cabecera">
        <div className="banca-barra">
          <button type="button" className="icono-boton" aria-label="Mi perfil" onClick={avisarSinDemo}>
            <UserCircle size={26} aria-hidden="true" />
          </button>
          <div className="banca-saludo">
            <h1>Hola</h1>
            <p>Bienvenido a Banco Vértice</p>
          </div>
          <span className="etiqueta-demo">Banco ficticio</span>
          <button type="button" className="icono-boton" aria-label="Notificaciones" onClick={avisarSinDemo}>
            <Bell size={24} aria-hidden="true" />
          </button>
        </div>

        <div className="saldo-total">
          <p>
            {cuenta.nombre} ••• {cuenta.terminacion}
          </p>
          <div className="saldo-fila">
            <p className="saldo">{monto(cliente.saldoHoy)}</p>
            <button
              type="button"
              className="icono-boton"
              aria-pressed={!montosVisibles}
              aria-label={montosVisibles ? 'Ocultar montos' : 'Mostrar montos'}
              onClick={() => setMontosVisibles(!montosVisibles)}
            >
              {montosVisibles ? <EyeSlash size={22} aria-hidden="true" /> : <Eye size={22} aria-hidden="true" />}
            </button>
          </div>
          <p>Saldo disponible</p>
        </div>
      </header>

      <main className="banca-contenido">
        <section className="tarjeta-credito" aria-label={`${tarjeta.nombre} terminada en ${tarjeta.terminacion}`}>
          <div className="tarjeta-credito-frente">
            <span className="logotipo logotipo-claro">Vértice</span>
            <span className="tarjeta-credito-numero" aria-hidden="true">
              •••• •••• •••• {tarjeta.terminacion}
            </span>
          </div>
          <div className="tarjeta-credito-pie">
            <div>
              <span>Pago del mes</span>
              <strong>{monto(tarjeta.pagoMes)}</strong>
            </div>
            <div>
              <span>Vence</span>
              <strong>{fechaDia(tarjeta.vence)}</strong>
            </div>
          </div>
        </section>

        <ul className="accesos" aria-label="Operaciones frecuentes">
          {ACCESOS.map(({ nombre, Icono }) => (
            <li key={nombre}>
              <button type="button" className="acceso" onClick={avisarSinDemo}>
                <span className="circulo circulo-grande">
                  <Icono size={26} aria-hidden="true" />
                </span>
                {nombre}
              </button>
            </li>
          ))}
        </ul>

        {riesgo && (
          <Link to="/lucas/resumen" className="tarjeta-lucas">
            <MarcaLucas tamano={44} />
            <span className="tarjeta-lucas-texto">
              <strong>Lucas te avisa</strong>
              <span>{textoDiasEnRojo(riesgo)} podrías quedar en rojo. Mira cómo evitarlo.</span>
            </span>
          </Link>
        )}

        <section aria-labelledby="programados-titulo" className="seccion-banca">
          <div className="tarjeta-titulo">
            <h2 id="programados-titulo" className="titulo-chico">
              Pagos programados
            </h2>
            <Link className="enlace" to="/lucas/que-viene">
              Ver todos
            </Link>
          </div>
          <ul className="programados" aria-label="Pagos antes de tu cobro">
            {pagosAntesDelCobro.map((p) => (
              <li key={p.id} className="programado">
                <span className="circulo" aria-hidden="true">
                  {iniciales(p.concepto)}
                </span>
                <span className="programado-texto">
                  <span>{p.concepto}</span>
                  <strong>{monto(p.monto)}</strong>
                  <span className="suave">{fechaDia(p.fecha)}</span>
                </span>
              </li>
            ))}
          </ul>
        </section>

        <section className="tarjeta" aria-labelledby="movimientos-titulo">
          <h2 id="movimientos-titulo" className="titulo-chico">
            Últimos movimientos
          </h2>
          {agruparPorDia(cliente.movimientosRecientes, hoy).map((g) => (
            <div key={g.nombre} className="grupo-dia">
              <h3 className="grupo-nombre">{g.nombre}</h3>
              <ul className="lista-limpia">
                {g.movimientos.map((m) => (
                  <li key={m.id} className="fila">
                    <span className="circulo" aria-hidden="true">
                      {iniciales(m.concepto)}
                    </span>
                    <span className="fila-texto">{m.concepto}</span>
                    <span className={`fila-monto ${m.monto > 0 ? 'entra' : ''}`}>
                      {montosVisibles ? `${m.monto > 0 ? '+' : ''}${enSoles(m.monto)}` : OCULTO}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </section>
      </main>
    </>
  )
}
