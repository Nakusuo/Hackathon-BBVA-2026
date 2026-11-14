import { ArrowsLeftRight, Bell, CaretRight, DeviceMobile, Eye, EyeSlash, QrCode, Receipt, UserCircle } from '@phosphor-icons/react'
import { useState } from 'react'
import { Link, useOutletContext } from 'react-router-dom'
import MarcaLucas from '../componentes/MarcaLucas.jsx'
import { diasEntre, enSoles, fechaCorta, fechaDia, iniciales, textoDiasEnRojo } from '../formato.js'
import { armarBandeja, candidatos } from '../lucas/avisos.js'
import { leerRegistro } from '../lucas/avisosGuardados.js'

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

// En el inicio bastan los últimos 3; el resto se abre con «Ver todo» para no cargar la pantalla.
const MOVIMIENTOS_VISIBLES = 3

export default function InicioBanca() {
  const { avisarSinDemo, vista: cliente, permiso } = useOutletContext()
  const [montosVisibles, setMontosVisibles] = useState(true)
  const monto = (valor) => (montosVisibles ? enSoles(valor) : OCULTO)
  const { riesgo, cuenta, tarjeta, hoy } = cliente
  const { avisos: candidatosHoy, riesgoLejano } = candidatos(cliente)
  const totalAvisos = armarBandeja(candidatosHoy, leerRegistro(), hoy).avisos.length
  const [todos, setTodos] = useState(false)
  const movimientos = todos ? cliente.movimientosRecientes : cliente.movimientosRecientes.slice(0, MOVIMIENTOS_VISIBLES)

  return (
    <>
      <header className="banca-cabecera">
        <div className="banca-barra">
          <button type="button" className="icono-boton" aria-label="Mi perfil" onClick={avisarSinDemo}>
            <UserCircle size={26} aria-hidden="true" />
          </button>
          <div className="banca-saludo">
            <div className="banca-saludo-fila">
              <h1>Hola</h1>
              <span className="etiqueta-demo">Banco ficticio</span>
            </div>
            <p>Bienvenido a Banco Vértice</p>
          </div>
          <Link to="/lucas/avisos" className="icono-boton campana" aria-label={`Avisos de Lucas: ${totalAvisos}`}>
            <Bell size={24} aria-hidden="true" />
            {totalAvisos > 0 && (
              <span className="campana-numero" aria-hidden="true">
                {totalAvisos}
              </span>
            )}
          </Link>
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
              aria-label="Ocultar montos"
              onClick={() => setMontosVisibles(!montosVisibles)}
            >
              {montosVisibles ? <EyeSlash size={22} aria-hidden="true" /> : <Eye size={22} aria-hidden="true" />}
            </button>
          </div>
          <p>Saldo disponible</p>
        </div>
      </header>

      <main className="banca-contenido">
        <div className="tarjeta-pila">
          <section className="tarjeta-credito" aria-label={`${tarjeta.nombre} terminada en ${tarjeta.terminacion}`}>
            <div className="tarjeta-credito-frente">
              <svg className="tarjeta-credito-arcos" viewBox="0 0 200 200" aria-hidden="true">
                <circle cx="200" cy="0" r="96" />
              </svg>
              <div className="tarjeta-credito-fila">
                <span className="logotipo logotipo-claro">Vértice</span>
                <span className="tarjeta-credito-tipo">Crédito</span>
              </div>
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
        </div>

        {!permiso ? (
          <Link to="/consentimiento" state={{ volver: '/lucas/resumen' }} className="tarjeta-lucas">
            <MarcaLucas tamano={52} pose="saludo" />
            <span className="tarjeta-lucas-texto">
              <strong>Activa Lucas</strong>
              <span>Te avisa antes de quedar en rojo. Primero te cuento qué datos uso.</span>
            </span>
          </Link>
        ) : riesgo ? (
          <Link to="/lucas/resumen" className="tarjeta-lucas">
            <MarcaLucas tamano={52} pose={riesgoLejano ? 'pensando' : 'alerta'} />
            {/* Con el rojo a más de 7 días no hay aviso (regla de avisos): Lucas lo muestra como algo que viene. */}
            <span className="tarjeta-lucas-texto">
              <strong>{riesgoLejano ? 'Lucas lo ve venir' : 'Lucas te avisa'}</strong>
              <span>
                {riesgoLejano
                  ? `En ${riesgoLejano.dias} días, ${textoDiasEnRojo(riesgo).toLowerCase()}`
                  : textoDiasEnRojo(riesgo)}{' '}
                podrías quedar en rojo. Mira cómo evitarlo.
              </span>
            </span>
            <CaretRight size={20} aria-hidden="true" />
          </Link>
        ) : (
          <Link to="/lucas/resumen" className="tarjeta-lucas">
            <MarcaLucas tamano={52} pose="celebra" />
            <span className="tarjeta-lucas-texto">
              <strong>Lucas</strong>
              <span>Con tus cambios llegas a tu cobro sin quedar en rojo. Mira tu plan.</span>
            </span>
            <CaretRight size={20} aria-hidden="true" />
          </Link>
        )}

        <ul className="accesos" aria-label="Operaciones frecuentes">
          {ACCESOS.map(({ nombre, Icono }) => (
            <li key={nombre}>
              <button type="button" className="acceso" onClick={avisarSinDemo}>
                <span className="acceso-icono">
                  <Icono size={24} aria-hidden="true" />
                </span>
                {nombre}
              </button>
            </li>
          ))}
        </ul>

        <section className="tarjeta" aria-labelledby="movimientos-titulo">
          <div className="tarjeta-titulo">
            <h2 id="movimientos-titulo" className="titulo-chico">
              Últimos movimientos
            </h2>
            {cliente.movimientosRecientes.length > MOVIMIENTOS_VISIBLES && (
              <button
                type="button"
                className="boton-texto"
                aria-expanded={todos}
                aria-controls="lista-movimientos"
                onClick={() => setTodos(!todos)}
              >
                {todos ? 'Ver menos' : 'Ver todo'}
              </button>
            )}
          </div>
          <ul id="lista-movimientos" className="lista-limpia">
            {movimientos.map((m) => (
              <li key={m.id} className="fila">
                <span className="circulo" aria-hidden="true">
                  {iniciales(m.concepto)}
                </span>
                <span className="fila-texto">
                  <span>{m.concepto}</span>
                  <span className="suave">{nombreDelDia(m.fecha, hoy)}</span>
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
