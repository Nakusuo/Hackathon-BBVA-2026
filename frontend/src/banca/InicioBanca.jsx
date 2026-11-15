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
  const { avisarSinDemo, vista: cliente, permiso, metas = [] } = useOutletContext()
  const [montosVisibles, setMontosVisibles] = useState(true)
  const monto = (valor) => (montosVisibles ? enSoles(valor) : OCULTO)
  const { riesgo, cuenta, tarjeta, hoy } = cliente
  const { avisos: candidatosHoy, riesgoLejano } = candidatos(cliente, hoy, metas)
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
            <h1>Hola</h1>
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
      </header>

      <main className="banca-contenido">
        <div className="billetera">
          <section className="tarjeta-credito" aria-label={`${tarjeta.nombre} terminada en ${tarjeta.terminacion}`}>
            <div className="tarjeta-credito-fila">
              <span className="logotipo logotipo-claro">Vértice</span>
              <span className="tarjeta-credito-tipo">Crédito</span>
            </div>
            <span className="tarjeta-credito-numero" aria-hidden="true">
              •••• •••• •••• {tarjeta.terminacion}
            </span>
          </section>

          <div className="bolsillo">
            {/* Forma y costura son dos capas: el contenido lleva su propio fondo del mismo color (así el contraste se mide contra
                lo que de verdad hay detrás) y la costura se dibuja encima. Estirado a propósito (preserveAspectRatio none):
                el corte y la costura siguen al bolsillo sea cual sea su ancho. */}
            <svg className="bolsillo-forma" viewBox="0 0 360 200" preserveAspectRatio="none" aria-hidden="true">
              <path
                className="bolsillo-cuerpo"
                d="M0,28 Q0,0 28,0 H118 C146,0 150,24 180,24 C210,24 214,0 242,0 H332 Q360,0 360,28 V172 Q360,200 332,200 H28 Q0,200 0,172 Z"
              />
            </svg>
            <div className="bolsillo-contenido">
              <p className="bolsillo-cuenta">
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
              <p className="bolsillo-cuenta">Saldo disponible</p>
              <div className="bolsillo-pago">
                <div>
                  <span>Pago del mes</span>
                  <strong>{monto(tarjeta.pagoMes)}</strong>
                </div>
                <div>
                  <span>Vence</span>
                  <strong>{fechaDia(tarjeta.vence)}</strong>
                </div>
              </div>
            </div>
            <svg className="bolsillo-forma" viewBox="0 0 360 200" preserveAspectRatio="none" aria-hidden="true">
              <path
                className="bolsillo-costura"
                d="M9,30 Q9,9 30,9 H121 C148,9 152,33 180,33 C208,33 212,9 239,9 H330 Q351,9 351,30 V170 Q351,191 330,191 H30 Q9,191 9,170 Z"
              />
            </svg>
          </div>
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
