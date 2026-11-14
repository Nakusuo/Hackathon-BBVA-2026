import assert from 'node:assert/strict'
import { test } from 'node:test'
import { PREGUNTAS_SUGERIDAS, responder } from '../src/lucas/respuestas.js'
import { cliente, persona } from '../src/motor/cliente.js'
import { evaluarGastoExtra } from '../src/motor/motor.js'

const NBSP = ' '
const preguntar = (texto) => responder(texto, cliente, persona)

test('cada pregunta sugerida tiene una respuesta propia, no la de «no entiendo»', () => {
  for (const p of PREGUNTAS_SUGERIDAS) {
    assert.doesNotMatch(preguntar(p).texto, /Todavía no sé/, p)
  }
})

test('las cifras de un gasto extra salen del motor y no del texto de la pregunta', () => {
  const esperado = evaluarGastoExtra(persona, 40)
  const r = preguntar('¿puedo gastar 40 en cine?')
  assert.ok(r.cifras.some((c) => c.valor === `−S/${NBSP}${Math.abs(esperado.peorDespues)}`))
  assert.ok(r.cifras.some((c) => c.valor === `S/${NBSP}${esperado.gastoDiarioSeguro}`))
})

test('montos con separador de miles se leen bien', () => {
  const r = preguntar('¿Puedo comprar algo de S/ 1,200?')
  assert.equal(r.cifras[0].valor, `S/${NBSP}1,200`)
})

test('no da asesoría de inversión ni ofrece mover plata', () => {
  for (const p of ['¿compro dólares?', '¿en qué acciones invierto?', 'transfiere 100 a mi mamá']) {
    assert.match(preguntar(p).texto, /no lo hago/, p)
  }
})

test('lo que no entiende lo dice sin inventar cifras', () => {
  const r = preguntar('hola')
  assert.match(r.texto, /Todavía no sé/)
  assert.deepEqual(r.cifras, [])
})

test('lectura de montos: con «S/», con «soles», con punto de miles y sin confundir días', async () => {
  const { montoEn } = await import('../src/lucas/respuestas.js')
  assert.equal(montoEn('¿puedo gastar s/ 150?'), 150)
  assert.equal(montoEn('un regalo de 80 soles'), 80)
  assert.equal(montoEn('algo de s/ 1.500'), 1500)
  assert.equal(montoEn('algo de s/ 12.50'), 12.5)
  assert.equal(montoEn('pagar la tarjeta el 1'), null)
  assert.equal(montoEn('el 15 gasto 40'), 40)
})

test('un gasto mayor que el saldo dice que no alcanza, sin decir «Puedes»', () => {
  const r = preguntar('¿puedo gastar 100000?')
  assert.match(r.texto, /^No te alcanza/)
  assert.doesNotMatch(r.texto, /Puedes/)
})

test('un gasto igual al saldo no se rechaza por saldo; un sol más, sí', () => {
  const justo = preguntar(`¿puedo gastar ${cliente.saldoHoy}?`).texto
  const pasado = preguntar(`¿puedo gastar ${cliente.saldoHoy + 1}?`).texto
  assert.doesNotMatch(justo, /^No te alcanza/)
  assert.match(pasado, /^No te alcanza/)
})

test('si el peor caso ya está en rojo, nunca responde «Sí, te alcanza»', () => {
  assert.doesNotMatch(preguntar('¿puedo gastar 5 en un chocolate?').texto, /Sí, te alcanza/)
})

test('con los tips activos el chat usa ese plan', async () => {
  const { vistaCon, CAMBIOS } = await import('../src/motor/cliente.js')
  const conTips = vistaCon(CAMBIOS.map((c) => c.id))
  assert.match(responder('¿puedo gastar 5?', conTips, persona).texto, /Sí, te alcanza/)
  assert.match(responder('¿Llego a mi cobro?', conTips, persona).texto, /^Sí/)
})

test('preguntar por un ahorro concreto lo comprueba contra los pagos', () => {
  assert.match(preguntar('¿Puedo ahorrar 30?').texto, /^Sí/)
  assert.match(preguntar('¿Puedo ahorrar 900?').texto, /^Es mucho/)
})

test('el precio de una meta en dólares no se confunde con comprar dólares', () => {
  const r = preguntar('el carro está 14000 dólares')
  assert.doesNotMatch(r.texto, /no lo hago/)
  assert.ok(r.cifras.some((c) => c.etiqueta === 'Tu meta' && c.valor === `S/${NBSP}52,500`))
  assert.ok(r.cifras.some((c) => /Cambio referencial/.test(c.etiqueta)))
  for (const p of ['¿Me conviene comprar dólares?', 'cámbiame 100 dólares', '¿ahorro en dólares?']) {
    assert.match(preguntar(p).texto, /no lo hago/, p)
  }
})

test('una meta dicha en dos mensajes usa la fecha del primero', () => {
  const r = responder('el carro está 14000 dólares', cliente, persona, ['tengo una meta para fin de año'])
  assert.match(r.texto, /^Tu carro cuesta US\$ 14,000, unos S\/.52,500\. Para fin de año/)
  assert.ok(r.cifras.some((c) => c.etiqueta === 'Necesitas al mes'))
})

test('una meta sin monto pide el monto y la fecha, sin inventar cifras', () => {
  const r = preguntar('tengo una meta para fin de año')
  assert.match(r.texto, /¿Cuánto cuesta\?/)
  assert.deepEqual(r.cifras, [])
})

test('una meta que cabe sale con el aporte mensual del mismo plan que la pantalla Metas', async () => {
  const { planDeMeta, finDeAnio } = await import('../src/lucas/metas.js')
  const r = preguntar('quiero juntar S/ 60 para fin de año')
  const plan = planDeMeta(
    { objetivo: 60, ahorrado: 0, fecha: finDeAnio(cliente.hoy) },
    { apartado: cliente.apartado.monto, primerApartado: cliente.proximoIngreso.fecha, finPronostico: cliente.finPronostico, hoy: cliente.hoy },
  )
  assert.match(r.texto, /^Tu meta es de S\/.60\. Sí llegas para fin de año/)
  assert.ok(r.cifras.some((c) => c.etiqueta === 'Apartar al mes' && c.valor === `S/${NBSP}${plan.aporte}`))
})

test('lectura de metas: «14 mil», un monto que parece año y los plazos', async () => {
  const { montoDeMeta, fechaDeMeta } = await import('../src/lucas/respuestas.js')
  assert.equal(montoDeMeta('una moto de 14 mil'), 14000)
  assert.equal(montoDeMeta('meta de 2000 para fin de ano'), 2000)
  assert.equal(montoDeMeta('juntar 3000 en 6 meses'), 3000)
  assert.equal(fechaDeMeta('para 2027', '2026-11-14'), '2027-12-31')
  assert.equal(fechaDeMeta('en 6 meses', '2026-11-14'), '2027-05-14')
  assert.equal(fechaDeMeta('en un ano', '2026-11-14'), '2027-11-14')
  assert.equal(fechaDeMeta('una laptop', '2026-11-14'), null)
})

// Una charla entera: cada respuesta se calcula con todo lo dicho antes, como en un chat de verdad.
function charla(mensajes) {
  const previas = []
  return mensajes.map((m) => {
    const r = responder(m, cliente, persona, previas)
    previas.push(m)
    return r
  })
}

test('el contexto sigue la meta a lo largo de la charla, no solo el último mensaje', () => {
  const [, , precio, plazo, otroPrecio, seguimiento] = charla([
    'tengo una meta para fin de año',
    'es un carro',
    'el carro está 14000 dólares',
    '¿y si lo hago en 3 años?',
    'mejor uno de 8 mil soles',
    '¿cuánto me falta por mes?',
  ])
  assert.match(precio.texto, /Para fin de año/)
  assert.match(plazo.texto, /^Tu carro cuesta US\$ 14,000.*Para el 14 nov de 2029/)
  assert.match(otroPrecio.texto, /^Tu carro cuesta S\/.8,000\. Para el 14 nov de 2029/)
  assert.equal(seguimiento.texto, otroPrecio.texto)
})

test('cambiar de tema y volver: la meta sigue recordada', () => {
  const r = charla(['quiero juntar 3000 para un viaje en 2027', '¿puedo gastar S/ 150 en un regalo?', '¿y 50?', '¿y mi meta?'])
  assert.match(r[1].texto, /peor caso/)
  assert.ok(r[2].cifras.some((c) => c.valor === `S/${NBSP}50`), 'el «¿y 50?» repite el cálculo del gasto')
  assert.match(r[3].texto, /^Tu viaje cuesta S\/.3,000\. Para fin de 2027/)
})

test('nombrar otra cosa con su precio empieza una meta nueva', () => {
  const r = charla(['quiero un viaje de 3000 en un año', 'y una laptop de 2500 para fin de año?'])
  assert.match(r[1].texto, /^Tu laptop cuesta S\/.2,500\. Para fin de año/)
})

test('un pedido de operación en medio de la charla se corta sin borrar la meta', () => {
  const r = charla(['meta: carro de 8 mil para 2029', '¿me conviene comprar dólares?', '¿y para 2030?'])
  assert.match(r[1].texto, /no lo hago/)
  assert.match(r[2].texto, /^Tu carro cuesta S\/.8,000\. Para fin de 2030/)
})

test('una meta con campaña suma el ahorro y ofrece más info solo la primera vez', () => {
  const [entrada, detalle] = charla(['quiero ir al concierto, la entrada está 450', 'sí, más info'])
  assert.match(entrada.texto, /^Tu entrada cuesta S\/.450\..*Ticketera Sol\. Te ahorras S\/.90\. ¿Quieres más info\?$/)
  assert.ok(entrada.cifras.some((c) => c.etiqueta === 'Pagarías' && c.valor === `S/${NBSP}360`))
  assert.match(detalle.texto, /^Ticketera Sol: .*Tú decides\.$/)
})

test('si pide una marca sin campaña, Lucas cuenta la que sí hay', () => {
  const r = charla(['quiero comprarme un carro', 'ya pero que sea toyota', 'cuesta 60 mil'])
  assert.match(r[1].texto, /^Con Toyota no hay campaña, pero con Autos Andinos/)
  assert.doesNotMatch(r[2].texto, /Ojo/, 'la campaña ya se contó')
  assert.ok(r[2].cifras.some((c) => c.etiqueta === 'Pagarías' && c.valor === `S/${NBSP}58,000`))
})

test('preguntar por campañas sin decir para qué lista los rubros, sin cifras', () => {
  const r = preguntar('¿hay ofertas con el banco?')
  assert.match(r.texto, /entradas, autos, viajes y tecnología/)
  assert.deepEqual(r.cifras, [])
})

test('un «sí» sin campaña ofrecida no inventa una', () => {
  assert.match(preguntar('sí').texto, /Todavía no sé/)
})

test('un plazo en semanas o días es la fecha, no el precio de la meta', () => {
  const r = charla(['quiero ir al concierto, la entrada está 450', 'quiero juntarlo a futuro, la venta es en 4 semanas'])
  assert.match(r[1].texto, /^Tu entrada cuesta S\/.450\. Para el 12 dic de 2026/)
})
