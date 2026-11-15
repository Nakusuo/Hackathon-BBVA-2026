import assert from 'node:assert/strict'
import { test } from 'node:test'
import { PREGUNTAS_SUGERIDAS, responder } from '../src/lucas/respuestas.js'
import { cliente, persona } from '../src/motor/cliente.js'
import { evaluarGastoExtra } from '../src/motor/motor.js'

const NBSP = ' '
const preguntar = (texto) => responder(texto, cliente, persona)

test('cada pregunta sugerida tiene una respuesta propia, no la de «no entiendo»', () => {
  for (const p of PREGUNTAS_SUGERIDAS) {
    assert.doesNotMatch(preguntar(p).texto, /No te entendí/, p)
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
  const r = preguntar('¿cuál es la capital de Francia?')
  assert.match(r.texto, /No te entendí/)
  assert.deepEqual(r.cifras, [])
})

test('un saludo recibe un saludo, sin cifras', () => {
  for (const p of ['hola', 'Hola!', 'buenas tardes']) {
    const r = preguntar(p)
    assert.match(r.texto, /^Hola\. ¿En qué te ayudo\?/, p)
    assert.deepEqual(r.cifras, [])
  }
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

test('la charla del concierto: «en 3 meses» es plazo, «explícame más» da la cuenta y el carro no hereda el precio', () => {
  const [saludo, meta, detalle, carro, precio] = charla([
    'hola',
    'hola quiero ir a un concierto que es en 3 meses, la entrada esta 450 puedes darme un plan de metas para ahorro o que evitar',
    'puedes explicarme mas sobre eso?',
    'quiero hacer una compra de carro a fin de año, cuanto deberia ir ahorrando',
    'pero el carro esta alrededor de 12000 soles',
  ])
  assert.match(saludo.texto, /^Hola/)
  assert.match(meta.texto, /^Tu entrada cuesta S\/.450\./)
  assert.match(meta.texto, /Lo que más te ayuda/)
  assert.match(detalle.texto, /3 × S\/.40 = S\/.120/)
  assert.match(carro.texto, /¿Cuánto cuesta\?/)
  assert.match(precio.texto, /^Tu carro cuesta S\/.12,000\./)
  assert.doesNotMatch(precio.texto, /cr[eé]dito|pr[eé]stamo/i)
})

test('«¿por qué?» después de «¿Llego a mi cobro?» explica el cálculo; sin tema, no inventa', () => {
  const [, porque] = charla(['¿Llego a mi cobro?', '¿por qué?'])
  assert.match(porque.texto, /mes malo/)
  assert.match(preguntar('¿puedes explicarme más sobre eso?').texto, /No te entendí/)
})

test('un monto suelto pregunta si es compra o meta', () => {
  assert.match(preguntar('12000').texto, /¿S\/.12,000 es algo que quieres comprar ahora o una meta para juntar\?/)
})

test('una meta con campaña suma el ahorro y ofrece más info solo la primera vez', () => {
  const [entrada, detalle] = charla(['quiero ir al concierto, la entrada está 200', 'sí, más info'])
  assert.match(entrada.texto, /^Tu entrada cuesta S\/.200\..*Ticketera Sol: pagarías S\/.40 menos\. Con la campaña.*juntas tu entrada de S\/.160.*Campaña de ejemplo, tú decides\. ¿Quieres más info\?$/)
  assert.ok(entrada.cifras.some((c) => c.etiqueta === 'Pagarías' && c.valor === `S/${NBSP}160`))
  assert.match(detalle.texto, /^Ticketera Sol: .*Tú decides\.$/)
})

test('si pide una marca sin campaña, Lucas cuenta la que sí hay', () => {
  const r = charla(['quiero comprarme un carro', 'ya pero que sea toyota', 'cuesta 60 mil'])
  assert.match(r[1].texto, /^Para eso no hay campaña\. La que hay es con Autos Andinos/)
  assert.doesNotMatch(r[1].texto, /toyota|salirte mejor/i, 'no repite marcas reales ni empuja la compra')
  assert.doesNotMatch(r[2].texto, /Ojo/, 'la campaña ya se contó')
  assert.ok(!r[2].cifras.some((c) => c.etiqueta === 'Pagarías'), 'a ese ritmo el carro llega después de la campaña')
})

test('preguntar por campañas sin decir para qué lista los rubros, sin cifras', () => {
  const r = preguntar('¿hay ofertas con el banco?')
  assert.match(r.texto, /entradas, autos, viajes y tecnología/)
  assert.deepEqual(r.cifras, [])
})

test('un «sí» sin campaña ofrecida no inventa una', () => {
  assert.match(preguntar('sí').texto, /No te entendí/)
})

test('un plazo en semanas o días es la fecha, no el precio de la meta', () => {
  const r = charla(['quiero ir al concierto, la entrada está 450', 'quiero juntarlo a futuro, la venta es en 4 semanas'])
  assert.match(r[1].texto, /^Tu entrada cuesta S\/.450\. Para el 12 dic de 2026/)
})

test('«¿y si gano 6000 al mes?» es un ingreso supuesto: no cambia el precio de la meta', () => {
  const r = charla(['quiero comprarme un carro de 12000 dolares', 'y si obtengo un ingreso de 6000 mensual ?', 'y para fin de 2028?'])
  assert.match(r[1].texto, /^Si te llegan S\/.6,000 al mes a la cuenta y gastas lo mismo que hoy/)
  assert.match(r[1].texto, /tu carro de S\/.45,000/)
  assert.match(r[2].texto, /^Tu carro cuesta US\$ 12,000.*Para fin de 2028/)
})

test('un ingreso menor al de hoy no promete más margen', () => {
  assert.match(preguntar('¿y si gano 1000 al mes?').texto, /no tendrías más margen/)
})

// Cada número tiene un papel: precio, plazo, fecha, edad, lo ya ahorrado, la inicial, un ritmo o un ingreso.
const CASOS_DE_NUMEROS = [
  [['quiero un carro de 45000', 'tengo 25 años, me alcanza?'], /^Tu carro cuesta S\/.45,000\./],
  [['quiero un carro de 45000', 'ya tengo 5000 ahorrados'], /Ya tienes S\/.5,000: te faltan S\/.40,000/],
  [['quiero un carro de 45000', 'la inicial es de 9000'], /cuesta S\/.45,000 y la inicial es de S\/.9,000/],
  [['quiero un carro de 45000', 'la inicial es el 20%'], /la inicial es de S\/.9,000/],
  [['quiero un carro de 45000', 'y si aparto 500 al mes?'], /^Apartando S\/.500 al mes, juntas tu carro de S\/.45,000/],
  [['quiero una laptop de 3000', 'y si aparto 100 por quincena?'], /^Apartando S\/.200 al mes/],
  [['quiero un carro de 45000', 'y si consigo un trabajo extra de 800 al mes?'], /^Si te entran S\/.800 más al mes/],
  [
    ['quiero un carro de 45000', 'y si me dan la gratificacion de 2600 en diciembre?'],
    /^Con recibo por honorarios no te toca gratificación\. .*Si apartas tu ingreso extra de S\/.2,600, te faltarían S\/.42,400/,
  ],
  [['quiero un carro de 45000', 'para marzo'], /Para el 31 mar de 2027/],
  [['quiero un carro de 45000', 'para el 15 de marzo de 2027'], /^Tu carro cuesta S\/.45,000\. Para el 15 mar de 2027/],
  [['quiero un carro de 45000', 'en año y medio?'], /Para el 14 may de 2028/],
  [['quiero una laptop de S/3500 en 2 quincenas'], /^Tu laptop cuesta S\/.3,500\. Para el 14 dic de 2026/],
  [['quiero un celular de 1.5k'], /^Tu celular cuesta S\/.1,500\./],
  [['quiero un celular de mil quinientos'], /^Tu celular cuesta S\/.1,500\./],
  [['quiero unas zapatillas de 400'], /^Tus zapatillas cuestan S\/.400\./],
  [['quiero un depa de 300 mil para 2035'], /en más de 20 años/],
  [['tengo 2 hijos, cuanto puedo ahorrar?'], /podrías apartar S\/.40\./],
  [['cuánto gasto en taxis?'], /^En los últimos 30 días gastaste S\/.180 en transporte/],
  [['hola'], /^Hola/],
  [['puedo gastar S/150 en un regalo?', 'gracias lucas'], /^¡De nada!/],
]

test('cada número se lee con su papel y no como el precio de la meta', () => {
  for (const [mensajes, esperado] of CASOS_DE_NUMEROS) {
    assert.match(charla(mensajes).at(-1).texto, esperado, mensajes.join(' → '))
  }
})

test('un aporte que hoy deja en rojo se avisa; uno que cabe, no', () => {
  assert.match(charla(['quiero una laptop de 3000', 'y si aparto 500 al mes?'])[1].texto, /te dejaría en rojo/)
  assert.match(charla(['quiero una laptop de 3000', 'y si aparto 20 al mes?'])[1].texto, /no te deja en rojo/)
})

test('una campaña que vence antes de juntar la plata no se ofrece', () => {
  // Con los tips la entrada de S/ 450 se junta en enero de 2027 y la campaña vale hasta el 31 dic de 2026.
  const r = preguntar('quiero ir al concierto, la entrada está 450')
  assert.doesNotMatch(r.texto, /Ticketera Sol|más info/)
  assert.ok(!r.cifras.some((c) => c.etiqueta === 'Pagarías'))
})

test('después de ofrecer la campaña solo un «sí» a secas pide el detalle; lo demás sigue la meta', () => {
  const inicio = 'quiero ir al concierto, la entrada está 200'
  for (const sigue of ['ok, ¿cuánto me falta?', 'ya, ¿llego?', 'bueno, ¿y con los tips?']) {
    assert.doesNotMatch(charla([inicio, sigue])[1].texto, /^Ticketera Sol/, sigue)
  }
  assert.match(charla([inicio, 'cuéntame más'])[1].texto, /^Cada vez que cobras/)
  assert.match(charla([inicio, 'no me interesa'])[1].texto, /^Listo, seguimos con tu plan\.$/)
  assert.match(charla([inicio, 'no, gracias'])[1].texto, /^Listo/)
  assert.match(charla([inicio, 'sí quiero'])[1].texto, /^Ticketera Sol/)
  assert.match(charla([inicio, 'no, pero ¿llego a mi cobro?'])[1].texto, /^Lo más probable/, 'el «no» con otra pregunta no se la come')
  assert.match(charla([inicio, 'no entiendo'])[1].texto, /^Cada vez que cobras/)
  assert.doesNotMatch(charla([inicio, 'otra cosa', 'sí'])[2].texto, /^Ticketera Sol/, 'el «sí» vale solo en el turno siguiente')
})

test('«que sea nuevo» o «barato» describen el carro, no una marca', () => {
  for (const frase of ['que sea nuevo', 'que sea barato', 'que sea usado', 'que sea automatico']) {
    const r = charla(['quiero un carro', frase])[1]
    assert.doesNotMatch(r.texto, /marca|No te entendí/, frase)
  }
})

test('después de un monto suelto, «una meta» lo toma como precio y «comprar ahora» como gasto', () => {
  assert.match(charla(['12000', 'una meta'])[1].texto, /^Tu meta es de S\/.12,000\./)
  assert.match(charla(['12000', 'es para un carro'])[1].texto, /^Tu carro cuesta S\/.12,000\./)
  assert.match(charla(['12000', 'comprar ahora'])[1].texto, /^No te alcanza: hoy tienes/)
})

test('«explícame más» explica el gasto consultado con sus mismas cifras y la campaña consultada', () => {
  const [, gasto, detalle] = charla(['quiero ir al concierto, la entrada está 450', '¿puedo gastar 150 en un regalo?', 'explícame más'])
  const peor = gasto.texto.match(/−S\/.\d+/)[0]
  assert.ok(detalle.texto.includes(peor), 'mismo peor caso que la respuesta anterior')
  assert.match(charla(['¿hay ofertas para viajes?', '¿por qué?'])[1].texto, /^Viajes Horizonte: .*Tú decides\.$/)
})

test('«perfecto, ¿y para fin de año?» sigue la meta y no se toma como un gracias', () => {
  assert.match(charla(['quiero una laptop de 3000', 'perfecto, ¿y para fin de año?'])[1].texto, /^Tu laptop cuesta S\/.3,000\. Para fin de año/)
})

test('las metas de develop siguen teniendo nombre: vacaciones, ropa, negocio', () => {
  assert.match(preguntar('quiero juntar para unas vacaciones de 3000').texto, /^Tus vacaciones cuestan S\/.3,000\./)
})

test('«me suben el sueldo 500» suma al ingreso de hoy', () => {
  assert.match(preguntar('¿y si me suben el sueldo 500?').texto, /^Si te entran S\/.500 más al mes/)
})

test('una fecha que no existe se dice y no rompe la meta', () => {
  for (const fecha of ['45 de marzo', '32 de enero', '0 de mayo', '30 de febrero']) {
    const r = charla([`quiero un carro de 45000 para el ${fecha}`, 'y si aparto 500 al mes?'])
    assert.match(r[0].texto, /no existe en el calendario/, fecha)
    assert.match(r[1].texto, /^Apartando S\/.500 al mes, juntas tu carro de S\/.45,000/, fecha)
  }
})

test('una deuda o «tengo 2 trabajos» no cuentan como plata ahorrada', () => {
  assert.match(charla(['quiero juntar para pagar mi deuda', 'tengo una deuda de 3000'])[1].texto, /^Tu deuda es de S\/.3,000\./)
  assert.doesNotMatch(charla(['quiero un carro de 45000', 'tengo 2 trabajos, me alcanza?'])[1].texto, /Ya tienes/)
})

test('«mi sueldo es 2600» es un dato, no un supuesto ni el precio de la meta', () => {
  assert.match(charla(['quiero un carro de 45000', 'mi sueldo es 2600, cuanto me falta?'])[1].texto, /^Tu carro cuesta S\/.45,000\./)
})

test('el ingreso supuesto lo mide el motor: más ingreso nunca da menos apartado', () => {
  const apartado = (n) => {
    const r = charla(['quiero un carro de 45000', `y si gano ${n} al mes?`])[1]
    return Number(r.cifras.find((c) => c.etiqueta === 'Podrías apartar al mes').valor.replace(/[^\d]/g, ''))
  }
  assert.ok(apartado(3000) <= apartado(6000))
  assert.ok(apartado(6000) <= apartado(20000))
})

test('montos con palabras: «2 mil quinientos» sí, «mil razones» no', () => {
  assert.match(preguntar('quiero un celular de 2 mil quinientos').texto, /^Tu celular cuesta S\/.2,500\./)
  assert.doesNotMatch(preguntar('dame mil razones para ahorrar').texto, /1,000/)
})

test('lo que ya tiene se dice igual en el texto y en las cifras', () => {
  const r = charla(['quiero una laptop de 3000', 'ya tengo 5000'])[1]
  assert.match(r.texto, /Ya tienes S\/.5,000: te alcanza\./)
  assert.ok(r.cifras.some((c) => c.etiqueta === 'Ya tienes' && c.valor === `S/${NBSP}5,000`))
})

test('«¿puedo gastar 450 en un concierto?» se responde con el rojo, no con una campaña', () => {
  const r = preguntar('¿puedo gastar 450 en una entrada para un concierto?')
  assert.match(r.texto, /rojo/)
  assert.doesNotMatch(r.texto, /campaña|Ticketera/i)
})

test('un «sí» solo va a la campaña si la oferta salió de las plantillas', async () => {
  const { esPreguntaDeCampana } = await import('../src/lucas/respuestas.js')
  const pidioCampana = ['quiero ir al concierto, la entrada está 200', '¿hay alguna promo?']
  assert.equal(esPreguntaDeCampana('sí', pidioCampana, cliente), true)
  // La meta la contestó el agente: la persona no vio ninguna campaña.
  assert.equal(esPreguntaDeCampana('sí', ['quiero ir al concierto, la entrada está 200'], cliente), false)
})

test('un «sí» o «no» después de una campaña descartada no la trae de vuelta', () => {
  for (const inicio of ['quiero ir al concierto, la entrada está 450', 'quiero juntar para un carro de 40 mil a fin de 2027', 'quiero un celular de 1200']) {
    for (const r of ['sí', 'dale', 'más info', 'no']) {
      const respuesta = charla([inicio, r])[1]
      assert.doesNotMatch(respuesta.texto, /Ticketera|Autos Andinos|TecnoPunto|Listo, seguimos/, `${inicio} → ${r}`)
      assert.ok(!respuesta.cifras.some((c) => c.etiqueta === 'Pagarías'), `${inicio} → ${r}`)
    }
  }
  assert.match(charla(['quiero ir al concierto, la entrada está 450', 'sí'])[1].texto, /^Dime para cuándo lo quieres/)
})

test('si el precio baja y la campaña ya sirve, se ofrece y el «sí» trae su detalle', () => {
  const r = charla(['quiero ir al concierto, la entrada está 450', 'mejor cuesta 200', 'sí'])
  assert.match(r[1].texto, /Ticketera Sol: pagarías S\/.40 menos\..*Campaña de ejemplo, tú decides\. ¿Quieres más info\?$/)
  assert.match(r[2].texto, /^Ticketera Sol: /)
})

test('pedir la campaña directo cuando vence antes de la meta: sin «Pagarías» y con la fecha', () => {
  const r = charla(['quiero ir al concierto, la entrada está 450', '¿hay descuentos?'])[1]
  assert.match(r.texto, /Vale hasta el 31 dic de 2026, antes de que juntes la plata/)
  assert.deepEqual(r.cifras, [])
})

test('«quiero comprarlo ahora» tras un monto suelto es un gasto; un saludo cierra la pregunta', () => {
  assert.match(charla(['500', 'quiero comprarlo ahora'])[1].texto, /quedar en rojo/)
  assert.match(charla(['12000', 'lo quiero comprar hoy'])[1].texto, /^No te alcanza/)
  assert.doesNotMatch(charla(['12000', 'hola', '¿cuánto puedo gastar hoy?'])[2].texto, /12,000/)
  assert.match(charla(['12000', 'explícame más'])[1].texto, /^Para calcularlo necesito saber si S\/.12,000/)
})

test('«4x4» describe el carro, no su precio', () => {
  assert.match(charla(['quiero un carro de 40 mil a fin de 2027', 'que sea 4x4'])[1].texto, /^Tu carro cuesta S\/.40,000\./)
})

test('tras un monto suelto, «desde hoy» con «meta» o «juntar» sigue siendo meta', () => {
  assert.match(charla(['500', 'es una meta para juntar desde hoy'])[1].texto, /^Tu meta es de S\/.500\./)
  assert.match(charla(['12000', 'es una meta, empiezo a juntar desde hoy'])[1].texto, /^Tu meta es de S\/.12,000\./)
})

test('«no quiero» y «no, no me interesa» cierran la oferta', () => {
  for (const no of ['no quiero', 'no, no me interesa']) {
    assert.match(charla(['quiero ir al concierto, la entrada está 200', no])[1].texto, /^Listo, seguimos con tu plan\.$/, no)
  }
})

test('un ritmo propuesto no guarda una campaña que no sirve: si luego sirve, se avisa', () => {
  const r = charla(['quiero ir al concierto, la entrada está 450', 'si aparto 20 al mes', 'mejor cuesta 200'])
  assert.match(r[2].texto, /Ticketera Sol: pagarías S\/.40 menos\..*Campaña de ejemplo, tú decides\. ¿Quieres más info\?$/)
})
