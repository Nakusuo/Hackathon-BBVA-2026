import {
  ArrowsLeftRight,
  Bell,
  CreditCard,
  DeviceMobile,
  Eye,
  EyeSlash,
  QrCode,
  Receipt,
  UserCircle,
} from '@phosphor-icons/react'
import { useState } from 'react'
import { Link, useOutletContext } from 'react-router-dom'
import MarcaLucas from '../componentes/MarcaLucas.jsx'
import { enSoles, fechaCorta, fechaDia, textoDiasEnRojo } from '../formato.js'
import { cliente } from '../mocks/cliente.js'

const ACCESOS = [
  { nombre: 'Transferir', Icono: ArrowsLeftRight },
  { nombre: 'Pagar servicios', Icono: Receipt },
  { nombre: 'Recargar celular', Icono: DeviceMobile },
  { nombre: 'Pagar con QR', Icono: QrCode },
]

const OCULTO = 'S/ ••••'

export default function InicioBanca() {
  const { avisarSinDemo } = useOutletContext()
  const [montosVisibles, setMontosVisibles] = useState(true)
  const monto = (valor) => (montosVisibles ? enSoles(valor) : OCULTO)
  const { riesgo, cuenta, tarjeta } = cliente

  return (
    <>
      <header className="banca-cabecera">
        <div className="banca-barra">
          <span className="logotipo logotipo-claro">Mi Banca</span>
          <div className="banca-iconos">
            <button type="button" className="icono-boton" aria-label="Notificaciones" onClick={avisarSinDemo}>
              <Bell size={24} aria-hidden="true" />
            </button>
            <button type="button" className="icono-boton" aria-label="Mi perfil" onClick={avisarSinDemo}>
              <UserCircle size={24} aria-hidden="true" />
            </button>
          </div>
        </div>
        <h1 className="saludo">Hola</h1>
      </header>

      <main className="banca-contenido">
        <section className="tarjeta cuenta" aria-labelledby="cuenta-titulo">
          <div className="tarjeta-titulo">
            <h2 id="cuenta-titulo" className="titulo-chico">
              {cuenta.nombre} ••• {cuenta.terminacion}
            </h2>
            <button
              type="button"
              className="icono-boton icono-boton-suave"
              aria-pressed={!montosVisibles}
              aria-label={montosVisibles ? 'Ocultar montos' : 'Mostrar montos'}
              onClick={() => setMontosVisibles(!montosVisibles)}
            >
              {montosVisibles ? <EyeSlash size={22} aria-hidden="true" /> : <Eye size={22} aria-hidden="true" />}
            </button>
          </div>
          <p className="suave">Saldo disponible</p>
          <p className="saldo">{monto(cliente.saldoHoy)}</p>
          <div className="fila fila-tarjeta">
            <CreditCard size={24} aria-hidden="true" />
            <span className="fila-texto">
              <span>
                {tarjeta.nombre} ••• {tarjeta.terminacion}
              </span>
              <span className="suave">Pago del mes, vence el {fechaDia(tarjeta.vence)}</span>
            </span>
            <span className="fila-monto">{monto(tarjeta.pagoMes)}</span>
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
          <Link to="/lucas/resumen" className="tarjeta-lucas" aria-label="Lucas te avisa: ver tu plan">
            <MarcaLucas tamano={44} />
            <span className="tarjeta-lucas-texto">
              <strong>Lucas te avisa</strong>
              <span>
                {textoDiasEnRojo(riesgo)} podrías quedar en rojo. Mira cómo evitarlo.
              </span>
            </span>
          </Link>
        )}

        <section className="tarjeta" aria-labelledby="movimientos-titulo">
          <h2 id="movimientos-titulo" className="titulo-chico">
            Últimos movimientos
          </h2>
          <ul className="lista-limpia">
            {cliente.movimientosRecientes.map((m) => (
              <li key={m.id} className="fila">
                <span className="fila-texto">
                  <span>{m.concepto}</span>
                  <span className="suave">{fechaCorta(m.fecha)}</span>
                </span>
                <span className={`fila-monto ${m.monto > 0 ? 'entra' : ''}`}>
                  {montosVisibles ? `${m.monto > 0 ? '+' : ''}${enSoles(m.monto)}` : OCULTO}
                </span>
              </li>
            ))}
          </ul>
        </section>
      </main>
    </>
  )
}
