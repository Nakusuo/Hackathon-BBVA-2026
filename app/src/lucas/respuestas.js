// Respuestas por plantilla: respaldo cuando el agente (JF-02) no está o no contesta. Toda cifra sale del motor, nunca del texto.
import { apartadoSinRojo, evaluarGastoExtra, sumarDias } from '../motor/motor.js'
import { conSigno, diasEntre, enSoles, enSolesRedondo, fechaCorta, fechaDia, textoDiasEnRojo } from '../formato.js'
import { leerTipoCambio } from '../api/contrato.js'
import { RESPALDO } from '../api/respaldo.js'
import { finDeAnio, planDeMeta } from './metas.js'
import { ahorroCon, avisoDeCampana, campanaPara, campanaPorId, cifrasDeCampana, detalleCampana, respuestaCampana } from './campanas.js'

export const PREGUNTAS_SUGERIDAS = [
  '¿Llego a mi cobro?',
  '¿Puedo gastar S/ 150 en un regalo?',
  '¿En qué gasto más?',
  '¿Cuánto puedo ahorrar?',
]

function normalizar(texto) {
  return texto
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
}

function aNumero(crudo) {
  const limpio = crudo.replace(/[.,]$/, '')
  // «1.500» y «1,500» son mil quinientos; «12.50» y «12,50» llevan céntimos.
  if (/^\d{1,3}([.,]\d{3})+$/.test(limpio)) return Number(limpio.replace(/[.,]/g, ''))
  return Number(limpio.replace(',', '.'))
}

// Primero el número que va con «S/» o «soles»; si no hay, el primero que no sea un día («el 1», «día 15»).
export function montoEn(texto) {
  const conMoneda = texto.match(/s\/\s*(\d[\d.,]*)/) ?? texto.match(/(\d[\d.,]*)\s*soles/)
  if (conMoneda) return aNumero(conMoneda[1])
  for (const hallado of texto.matchAll(/(?:(el|dia|del)\s+)?(\d[\d.,]*)/g)) {
    if (!hallado[1]) return aNumero(hallado[2])
  }
  return null
}

function ajusteActual(cliente) {
  return cliente.ajuste ?? {}
}

function llegarAlCobro(cliente) {
  const { riesgo, gastoDiarioActual, gastoDiarioSeguro, proximoIngreso, peorDia } = cliente
  if (!riesgo) {
    return {
      texto: `Sí. Llegas a tu cobro del ${fechaDia(proximoIngreso.fecha)} sin quedar en rojo, incluso si gastas un poco más de lo normal.`,
      cifras: [{ etiqueta: `Peor caso el ${fechaDia(peorDia.fecha)}`, valor: conSigno(peorDia.monto) }],
    }
  }
  return {
    texto: `Lo más probable es que sí, pero con poco margen. Si gastas un poco más de lo normal, ${textoDiasEnRojo(riesgo).toLowerCase()} podrías quedar en rojo. Si bajas a ${enSoles(gastoDiarioSeguro)} al día, llegas a tu cobro del ${fechaDia(proximoIngreso.fecha)} incluso en ese caso.`,
    cifras: [
      { etiqueta: 'Gasto actual por día', valor: enSoles(gastoDiarioActual) },
      { etiqueta: `Peor caso el ${fechaDia(riesgo.peorFecha)}`, valor: enSoles(riesgo.peorMonto) },
      { etiqueta: 'Gasto seguro por día', valor: enSoles(gastoDiarioSeguro) },
    ],
  }
}

// «¿Cuánto puedo gastar?» pide un monto, haya riesgo o no: el gasto seguro por día hasta el cobro.
function cuantoPuedoGastar(cliente) {
  const { gastoDiarioActual, gastoDiarioSeguro, proximoIngreso } = cliente
  const frente =
    gastoDiarioSeguro < gastoDiarioActual
      ? ` Hoy gastas ${enSoles(gastoDiarioActual)} al día: baja un poco para no quedar en rojo.`
      : ` Hoy gastas ${enSoles(gastoDiarioActual)} al día, así que vas bien.`
  return {
    texto: `Hasta tu cobro del ${fechaDia(proximoIngreso.fecha)} puedes gastar hasta ${enSoles(gastoDiarioSeguro)} al día sin quedar en rojo, aun en un mes malo.${frente}`,
    cifras: [
      { etiqueta: 'Gasto seguro por día', valor: enSoles(gastoDiarioSeguro) },
      { etiqueta: 'Gasto actual por día', valor: enSoles(gastoDiarioActual) },
    ],
    pose: 'pensando',
  }
}

function gastoExtra(cliente, persona, monto) {
  if (monto > cliente.saldoHoy) {
    return {
      texto: `No te alcanza: hoy tienes ${enSoles(cliente.saldoHoy)} y ese gasto es de ${enSoles(monto)}.`,
      cifras: [
        { etiqueta: 'Saldo de hoy', valor: enSoles(cliente.saldoHoy) },
        { etiqueta: 'Gasto que consultas', valor: enSoles(monto) },
      ],
    }
  }
  const r = evaluarGastoExtra(persona, monto, ajusteActual(cliente))
  const cifras = [
    { etiqueta: 'Gasto que consultas', valor: enSoles(monto) },
    { etiqueta: `Peor caso el ${fechaDia(r.fechaPeorDia)}`, valor: conSigno(r.peorDespues) },
  ]
  if (r.peorDespues >= 0) {
    return {
      texto: `Sí, te alcanza. Aun con ese gasto, tu día más justo, el ${fechaDia(r.fechaPeorDia)}, queda en ${conSigno(r.peorDespues)} si gastas un poco más de lo normal.`,
      cifras,
    }
  }
  if (r.gastoDiarioSeguro === 0) {
    return {
      texto: `Con ese gasto no llegarías a tu cobro sin quedar en rojo, aunque dejaras de gastar en todo lo demás. En el peor caso tendrías ${enSoles(r.peorDespues)} el ${fechaDia(r.fechaPeorDia)}.`,
      cifras,
    }
  }
  return {
    texto: `Si lo compras, en el peor caso quedas en ${enSoles(r.peorDespues)} el ${fechaDia(r.fechaPeorDia)}. Para evitarlo, gasta hasta ${enSoles(r.gastoDiarioSeguro)} al día hasta tu cobro.`,
    cifras: [...cifras, { etiqueta: 'Gasto seguro por día después', valor: enSoles(r.gastoDiarioSeguro) }],
  }
}

function dondeGastoMas(cliente) {
  const [mayor] = cliente.categorias
  const subeMas = [...cliente.categorias].sort((a, b) => b.total - b.promedio3m - (a.total - a.promedio3m))[0]
  const diferencia = Math.round(subeMas.total - subeMas.promedio3m)
  const subida =
    subeMas.id === mayor.id
      ? `Y es lo que más subió: ${enSoles(diferencia)} más que tu promedio.`
      : `Lo que más subió frente a tu promedio es ${subeMas.nombre.toLowerCase()}, ${enSoles(diferencia)} más de lo usual.`
  return {
    texto: `En los últimos 30 días gastaste más en ${mayor.nombre.toLowerCase()}: ${enSolesRedondo(mayor.total)}. ${subida}`,
    cifras: [
      { etiqueta: mayor.nombre, valor: enSolesRedondo(mayor.total) },
      { etiqueta: `${subeMas.nombre} sobre tu promedio`, valor: enSoles(diferencia) },
    ],
  }
}

function cuantoAhorrar(cliente, persona, monto) {
  const { apartado, proximoIngreso } = cliente
  const cobro = fechaDia(proximoIngreso.fecha)
  if (monto) {
    const seguro = apartadoSinRojo(persona, monto, ajusteActual(cliente))
    const alternativa = apartado ? ` Lo que sí puedes apartar sin riesgo es ${enSoles(apartado.monto)}.` : ''
    return {
      texto: seguro
        ? `Sí. Si apartas ${enSoles(monto)} cuando cobres el ${cobro}, no quedas en rojo con tus pagos de diciembre.`
        : `Es mucho para este mes: apartar ${enSoles(monto)} el ${cobro} te dejaría sin margen para tus pagos de diciembre.${alternativa}`,
      cifras: apartado ? [{ etiqueta: 'Apartado sin riesgo', valor: enSoles(apartado.monto) }] : [],
    }
  }
  if (!apartado) {
    return {
      texto: 'Este mes no te conviene apartar al cobrar: ese margen lo necesitas para tus pagos de diciembre.',
      cifras: [],
    }
  }
  return {
    texto: `Cuando cobres el ${cobro}, podrías apartar ${enSoles(apartado.monto)}. Lo comprobé con tus pagos hasta el ${fechaCorta(apartado.hasta)} y no te deja en rojo. Si lo repites en tus próximos ${apartado.repeticiones} cobros, juntarías ${enSoles(apartado.total)}.`,
    cifras: [
      { etiqueta: 'Apartado por cobro', valor: enSoles(apartado.monto) },
      { etiqueta: `En tus próximos ${apartado.repeticiones} cobros`, valor: enSoles(apartado.total) },
    ],
  }
}

const LIMITES = {
  texto:
    'Eso no lo hago: no recomiendo inversiones ni compra de dólares, y no muevo tu plata. Sí puedo decirte cuánto margen tienes hasta tu cobro.',
  cifras: [],
  pose: 'pensando',
}

const SALUDO = {
  texto: 'Hola. ¿En qué te ayudo? Puedo decirte si llegas a tu cobro, en qué gastas más o armarte un plan para una meta.',
  cifras: [],
  pose: 'saludo',
}

const NO_ENTIENDO = {
  texto: 'No te entendí. Prueba con una de las preguntas frecuentes.',
  cifras: [],
  pose: 'pensando',
}

// Las mismas reglas que src/agent/router.py: «el carro está 14 000 dólares» es un precio, no un pedido de comprar dólares.
const OPERACION = [
  /\b(invert|inviert|inversion|acciones?\b|cripto|transfer|transfier|paga por mi)/,
  /\bmueve\w*\s+(mi|mis|la|el|tu)?\s*(plata|dinero|ahorro|s\/|\d)/,
  /\b(compr|vend)\w*\s+(\w+\s+)?dolar/,
  /\bcambi\w*\s+(?!del?\b)(\w+\s+)?dolar/,
  /\b(ahorr|guard)\w*\s+(\w+\s+)?en\s+dolar/,
]

export function esPedidoDeOperacion(pregunta) {
  // Con límites de palabra: «transacción» no es «acción» y «¿qué mueve mi gasto?» no pide mover plata.
  const texto = normalizar(pregunta)
  return OPERACION.some((regla) => regla.test(texto))
}

// --- Metas: «quiero juntar para un carro a fin de año» se responde con el mismo plan de la pantalla Metas.

// Lo que la gente suele querer juntar. Nombrarlo ya abre una meta.
const OBJETOS =
  'carro|auto|moto|viaje|vacaciones|laptop|computadora|celular|depa|departamento|casa|terreno|matricula|boda|bicicleta|televisor|tele|consola|refri|refrigeradora|lavadora|muebles|ropa|zapatillas|mascota|negocio|curso|estudios|maestria|concierto|festival|evento|fiesta|entradas?|deudas?'
const OBJETO_META = new RegExp(`\\b(${OBJETOS})\\b`)
const PIDE_META = new RegExp(`\\b(metas?|plan de ahorro|juntar|junto|reunir|quiero comprar\\w*|comprarme|${OBJETOS})\\b`)
const EN_DOLARES = /(\bdolar|\busd\b|us\$|\$\s*\d)/
const MESES_LARGOS = new Intl.DateTimeFormat('es-PE', { month: 'long', year: 'numeric' })

function sumarMeses(fechaIso, meses) {
  const [anio, mes, dia] = fechaIso.split('-').map(Number)
  const ultimo = new Date(Date.UTC(anio, mes - 1 + meses + 1, 0)).getUTCDate()
  return new Date(Date.UTC(anio, mes - 1 + meses, Math.min(dia, ultimo))).toISOString().slice(0, 10)
}

// «para 2027» es un año; «una meta de 2000» es un monto.
const ANIO = /\b(?:para|en|hasta|del|fin de)\s+(?:el\s+)?(?:ano\s+)?(20\d\d)\b(?!\s*(soles|dolares|mil))/
const NUMERO_PALABRA = { un: 1, una: 1, dos: 2, tres: 3, cuatro: 4, cinco: 5, seis: 6, ocho: 8, diez: 10, doce: 12 }

// «en 4 semanas», «dentro de 10 días», «en 2 quincenas», «en 6 meses», «en 2 años».
const PLAZO =
  /\b(?:en|dentro de)\s+(\d+|un|una|dos|tres|cuatro|cinco|seis|ocho|diez|doce)\s+(dias?|semanas?|quincenas?|mes|meses|ano|anos)\b/
const PLAZOS = new RegExp(PLAZO.source, 'g')
const ANIO_Y_MEDIO = /\b(?:en|dentro de)\s+(?:un\s+)?ano y medio\b/
const MEDIO_ANIO = /\b(?:en|dentro de)\s+medio ano\b/

const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'setiembre', 'octubre', 'noviembre', 'diciembre']
const MES = '(enero|febrero|marzo|abril|mayo|junio|julio|agosto|setiembre|septiembre|octubre|noviembre|diciembre)'
const FECHA_CON_DIA = new RegExp(`\\b(\\d{1,2})\\s+de\\s+${MES}(?:\\s+(?:de|del)\\s+(20\\d\\d))?`)
const MES_CON_ANIO = new RegExp(`\\b${MES}\\s+(?:de\\s+|del\\s+)?(20\\d\\d)\\b`)
const SOLO_MES = new RegExp(`\\b${MES}\\b`)

function numeroDeMes(nombre) {
  return nombre === 'septiembre' ? 9 : MESES.indexOf(nombre) + 1
}

function ultimoDia(anio, mes) {
  return new Date(Date.UTC(anio, mes, 0)).toISOString().slice(0, 10)
}

// «marzo» sin año es el próximo marzo: si ya pasó este año, el del siguiente.
function anioDelMes(mes, hoy) {
  const [anio, mesHoy] = hoy.split('-').map(Number)
  return mes >= mesHoy ? anio : anio + 1
}

function diaConMes(texto, hoy) {
  const conDia = texto.match(FECHA_CON_DIA)
  if (!conDia) return null
  const mes = numeroDeMes(conDia[2])
  const anio = conDia[3] ? Number(conDia[3]) : anioDelMes(mes, hoy)
  const dia = Number(conDia[1])
  const fecha = new Date(Date.UTC(anio, mes - 1, dia))
  const existe = fecha.getUTCMonth() === mes - 1 && fecha.getUTCDate() === dia
  return { dicho: `${dia} de ${conDia[2]}`, fecha: existe ? fecha.toISOString().slice(0, 10) : null }
}

// «el 45 de marzo» o «el 30 de febrero»: hay que decirlo, no correr la fecha a otro día.
export function fechaImposible(texto, hoy) {
  const d = diaConMes(texto, hoy)
  return d && !d.fecha ? d.dicho : null
}

// «fin de año», «15 de marzo», «julio de 2027», «en 4 semanas», «en año y medio», «para 2027». Sin fecha, null.
export function fechaDeMeta(texto, hoy) {
  const conDia = diaConMes(texto, hoy)
  if (conDia) return conDia.fecha
  const mesAnio = texto.match(MES_CON_ANIO)
  if (mesAnio) return ultimoDia(Number(mesAnio[2]), numeroDeMes(mesAnio[1]))
  if (/\b(fin de (ano|anio)|fin del (ano|anio)|navidad)\b/.test(texto)) return finDeAnio(hoy)
  if (ANIO_Y_MEDIO.test(texto)) return sumarMeses(hoy, 18)
  if (MEDIO_ANIO.test(texto)) return sumarMeses(hoy, 6)
  const plazo = texto.match(PLAZO)
  if (plazo) {
    const n = NUMERO_PALABRA[plazo[1]] ?? Number(plazo[1])
    const unidad = plazo[2]
    if (unidad.startsWith('dia')) return sumarDias(hoy, n)
    if (unidad.startsWith('semana')) return sumarDias(hoy, n * 7)
    if (unidad.startsWith('quincena')) return sumarDias(hoy, n * 15)
    return sumarMeses(hoy, unidad.startsWith('mes') ? n : n * 12)
  }
  const anio = texto.match(ANIO)
  if (anio && anio[1] >= hoy.slice(0, 4)) return `${anio[1]}-12-31`
  const mes = texto.match(SOLO_MES)
  if (mes) {
    const n = numeroDeMes(mes[1])
    return ultimoDia(anioDelMes(n, hoy), n)
  }
  return null
}

const DECENAS = { un: 1, una: 1, dos: 2, tres: 3, cuatro: 4, cinco: 5, seis: 6, siete: 7, ocho: 8, nueve: 9, diez: 10, veinte: 20, treinta: 30, cuarenta: 40, cincuenta: 50 }
const CENTENAS = { cien: 100, ciento: 100, doscientos: 200, trescientos: 300, cuatrocientos: 400, quinientos: 500, seiscientos: 600, setecientos: 700, ochocientos: 800, novecientos: 900 }
const PALABRA_CENTENA = `(${Object.keys(CENTENAS).join('|')})`

// «mil» suelto es plata solo si va con soles, un número o el final de la idea: «mil razones» no es un monto.
const MIL_ES_PLATA = '(?=\\s*(?:soles|dolares|lucas|para|en|al|por|de|y|$|[,.?!]))'

// «1.5k», «2 mil quinientos», «mil quinientos», «dos mil», «quinientos soles» pasan a cifras.
export function numerosEnPalabras(texto) {
  return texto
    .replace(/(\d+(?:[.,]\d+)?)\s*k\b/g, (_, n) => String(Math.round(Number(n.replace(',', '.')) * 1000)))
    .replace(new RegExp(`\\b(\\d+)\\s+mil\\s+${PALABRA_CENTENA}\\b`, 'g'), (_, n, c) => String(Number(n) * 1000 + CENTENAS[c]))
    .replace(
      new RegExp(`(?<![\\d.,]\\s*)\\b(?:(${Object.keys(DECENAS).join('|')})\\s+)?mil\\s+${PALABRA_CENTENA}\\b`, 'g'),
      (_, d, c) => String((DECENAS[d] ?? 1) * 1000 + CENTENAS[c]),
    )
    .replace(
      new RegExp(`(?<![\\d.,]\\s*)\\b(?:(${Object.keys(DECENAS).join('|')})\\s+)?mil\\b${MIL_ES_PLATA}`, 'g'),
      (_, d) => String((DECENAS[d] ?? 1) * 1000),
    )
    .replace(new RegExp(`(?<!por\\s)\\b${PALABRA_CENTENA}\\b`, 'g'), (c) => String(CENTENAS[c]))
}

// Números que no son plata: plazos, fechas, años de edad, hijos, trabajos, cuotas, porcentajes, medidas («2x1»).
const NO_ES_MONTO =
  /\b\d+\s*(anos|hijos?|hijas?|personas?|trabajos?|empleos?|tarjetas?|cuentas?|veces|%|por ciento|cuotas|kilos?|km|horas?|dias|semanas|quincenas|meses)\b|\b\d+x\d+\b/g

export function sinNoMontos(texto) {
  return texto
    .replace(PLAZOS, ' ')
    .replace(new RegExp(ANIO.source, 'g'), ' ')
    .replace(new RegExp(FECHA_CON_DIA.source, 'g'), ' ')
    .replace(new RegExp(MES_CON_ANIO.source, 'g'), ' ')
    .replace(NO_ES_MONTO, ' ')
}

// El monto de la meta sin confundirlo con el plazo, la fecha o la edad, y leyendo «14 mil» y «1.5k».
export function montoDeMeta(texto) {
  const limpio = sinNoMontos(numerosEnPalabras(texto)).replace(/\$\s*(?=\d)/g, ' ')
  const enMiles = limpio.match(/(\d[\d.,]*)\s*mil\b/)
  const monto = enMiles ? aNumero(enMiles[1]) * 1000 : montoEn(limpio)
  return monto > 0 ? monto : null
}

function cuando(fechaIso, hoy) {
  const meses = Math.round(diasEntre(hoy, fechaIso) / 30)
  if (meses <= 24) return `en ${MESES_LARGOS.format(new Date(`${fechaIso}T12:00:00`))}`
  // «634 años» no ayuda a decidir: pasado un plazo razonable basta decir que a ese ritmo no se llega.
  if (meses > 240) return 'en más de 20 años'
  return `en unos ${Math.round(meses / 12)} años`
}

function nombreFecha(fechaIso, hoy) {
  if (fechaIso === finDeAnio(hoy)) return 'fin de año'
  if (fechaIso.endsWith('-12-31')) return `fin de ${fechaIso.slice(0, 4)}`
  return `el ${fechaCorta(fechaIso)} de ${fechaIso.slice(0, 4)}`
}

function enSolesDe({ monto, enDolares }) {
  if (!monto) return 0
  return enDolares ? Math.round(monto * leerTipoCambio(RESPALDO.tipoCambio).tasa) : monto
}

// Lo que hay que juntar: la inicial si la dio, si no el precio; menos lo que ya tiene. `tiene` es lo dicho,
// `ahorrado` lo que cuenta para la meta (no puede pasar del objetivo).
function objetivoDe(meta, unico = 0) {
  const objetivo = meta.inicial ?? enSolesDe(meta)
  const tiene = (meta.ahorrado ?? 0) + unico
  const ahorrado = Math.min(objetivo, tiene)
  return { objetivo, tiene, ahorrado, falta: objetivo - ahorrado }
}

// «tu carro», «tus zapatillas»: la meta en plural concuerda.
function tuMeta(que) {
  if (!que) return 'tu meta'
  return que.endsWith('s') ? `tus ${que}` : `tu ${que}`
}

function mayuscula(texto) {
  return texto[0].toUpperCase() + texto.slice(1)
}

// Cada respuesta dice de qué meta habla: en una charla larga la persona puede haber cambiado de idea.
function presentarMeta({ monto, enDolares, que, inicial, ahorrado = 0 }, unico) {
  const cosa = tuMeta(que)
  const enSolesMonto = enSolesDe({ monto, enDolares })
  const cuesta = enDolares ? `US$ ${monto.toLocaleString('es-PE')}, unos ${enSoles(enSolesMonto)}` : enSoles(enSolesMonto)
  const verbo = que === 'deuda' ? 'es de' : que?.endsWith('s') ? 'cuestan' : 'cuesta'
  let frase = ''
  if (monto) frase = que ? `${mayuscula(cosa)} ${verbo} ${cuesta}` : `Tu meta es de ${cuesta}`
  if (inicial) frase = monto ? `${frase} y la inicial es de ${enSoles(inicial)}` : `La inicial de ${cosa} es de ${enSoles(inicial)}`
  frase += '. '
  const { tiene, falta } = objetivoDe({ monto, enDolares, inicial, ahorrado }, unico?.monto ?? 0)
  if (unico) {
    frase += falta
      ? `Si apartas tu ${unico.nombre} de ${enSoles(unico.monto)}, te faltarían ${enSoles(falta)}. `
      : `Con tu ${unico.nombre} de ${enSoles(unico.monto)} ya te alcanza. `
  } else if (ahorrado) {
    frase += falta ? `Ya tienes ${enSoles(tiene)}: te faltan ${enSoles(falta)}. ` : `Ya tienes ${enSoles(tiene)}: te alcanza. `
  }
  return frase
}

// `unico`: un monto que llegaría una sola vez (gratificación, bono), como supuesto que no se guarda.
function planDeAhorro(cliente, metaPedida, { unico = null } = {}) {
  const { monto, enDolares, fecha, que, inicial } = metaPedida
  if (!monto && !inicial) {
    const plan = `el plan de ${tuMeta(que)}`
    return {
      texto: fecha
        ? `Armemos ${plan} para ${nombreFecha(fecha, cliente.hoy)}. ¿Cuánto cuesta?`
        : `Armemos ${plan}. ¿Cuánto cuesta y para cuándo lo quieres? Por ejemplo: «S/ 3,000 para fin de año».`,
      cifras: [],
    }
  }
  const { hoy, proximoIngreso, finPronostico } = cliente
  const tipo = leerTipoCambio(RESPALDO.tipoCambio)
  const { objetivo, tiene, ahorrado, falta } = objetivoDe(metaPedida, unico?.monto ?? 0)
  const puedes = cliente.apartado?.monto ?? 0
  const conTips = cliente.apartadoConTodos?.monto ?? 0
  const contexto = { primerApartado: proximoIngreso.fecha, finPronostico, hoy }
  // Sin fecha se mide solo el ritmo: con la fecha del primer cobro, `llegaEl` dice cuándo se junta todo.
  const meta = { objetivo, ahorrado, fecha: fecha ?? proximoIngreso.fecha }
  const plan = planDeMeta(meta, { ...contexto, apartado: puedes })
  const planTips = conTips > puedes ? planDeMeta(meta, { ...contexto, apartado: conTips }) : null

  const cifras = [{ etiqueta: inicial ? 'Inicial' : 'Tu meta', valor: enSoles(objetivo) }]
  if (enDolares && monto) {
    cifras.push({ etiqueta: `Cambio referencial del ${fechaCorta(tipo.fecha)}`, valor: `S/ ${tipo.tasa.toFixed(2)} por dólar` })
  }
  if (ahorrado) cifras.push({ etiqueta: unico ? `Con tu ${unico.nombre}` : 'Ya tienes', valor: enSoles(tiene) })
  if (ahorrado) cifras.push({ etiqueta: 'Te falta', valor: enSoles(falta) })
  const precio = presentarMeta(metaPedida, unico)

  if (!falta) return { texto: precio.trim(), cifras }
  if (!puedes && !conTips) {
    return {
      texto: `${precio}Hoy no te queda margen para apartar sin quedar en rojo. Primero llega a tu cobro con aire y luego empezamos a juntar.`,
      cifras,
    }
  }
  if (fecha && plan.sinCobros) {
    return {
      texto: `${precio}No tienes cobros antes de esa fecha, así que no hay de dónde apartar. Elige una fecha después del ${fechaCorta(proximoIngreso.fecha)}.`,
      cifras,
    }
  }
  if (fecha && plan.alcanza) {
    return {
      texto: `${precio}Sí llegas para ${nombreFecha(fecha, hoy)}: aparta ${enSoles(plan.aporte)} al mes, desde tu cobro del ${fechaCorta(proximoIngreso.fecha)}. No te deja en rojo.`,
      cifras: [
        ...cifras,
        { etiqueta: 'Apartar al mes', valor: enSoles(plan.aporte) },
        { etiqueta: 'Meses de ahorro', valor: String(plan.veces) },
      ],
    }
  }

  // No alcanza para la fecha, o no la dio: se dice el ritmo posible y cuándo llegaría.
  const necesita = fecha
    ? `Para ${nombreFecha(fecha, hoy)} tendrías que apartar ${enSoles(plan.necesario)} al mes. `
    : ''
  const ritmo = puedes
    ? `Sin quedar en rojo puedes apartar ${enSoles(puedes)} al mes: así la juntas ${cuando(plan.llegaEl, hoy)}.`
    : 'Hoy no te queda margen para apartar sin quedar en rojo.'
  const tips = planTips
    ? ` Con los ${cliente.totalCambios} tips, ${enSoles(conTips)} al mes: ${cuando(planTips.llegaEl, hoy)}.`
    : ''
  if (fecha) cifras.push({ etiqueta: 'Necesitas al mes', valor: enSoles(plan.necesario) })
  if (puedes) cifras.push({ etiqueta: 'Puedes apartar al mes', valor: enSoles(puedes) })
  if (planTips) cifras.push({ etiqueta: 'Con los tips, al mes', valor: enSoles(conTips) })
  const pregunta = fecha ? '' : ' ¿Para cuándo lo quieres?'
  const evitar = queEvitar(cliente)
  return { texto: `${precio}${necesita}${ritmo}${tips}${evitar ? ` ${evitar}` : ''}${pregunta}`, cifras }
}

// Los tips que más mueven tu día más justo, con su efecto en S/: es lo que conviene cambiar para llegar antes.
function queEvitar(cliente) {
  const top = [...cliente.recomendaciones].sort((a, b) => b.mejora - a.mejora).slice(0, 2)
  if (!top.length) return ''
  return `Lo que más te ayuda: ${top.map((t) => `«${t.titulo}» (+${enSoles(t.mejora)})`).join(' y ')}.`
}

// «Explícame más» sobre el último tema: cómo sale la cifra, no la misma respuesta otra vez.
function masDetalle(cliente, persona, contexto) {
  const { apartado, apartadoConTodos, proximoIngreso, finPronostico, hoy, riesgo, gastoDiarioSeguro, categorias } = cliente
  const puedes = apartado?.monto ?? 0
  const base = `Cada vez que cobras miro tus pagos hasta el siguiente cobro y solo aparto lo que no te deja en rojo, ni en un mes malo. Hoy eso es ${enSoles(puedes)} al mes.`
  const evitar = queEvitar(cliente)
  if (contexto.tema === 'monto-suelto') {
    return {
      texto: `Para calcularlo necesito saber si ${enSolesRedondo(contexto.monto)} es para comprar ahora o una meta para juntar.`,
      cifras: [],
      pose: 'pensando',
    }
  }
  if (contexto.tema === 'campana' && contexto.campana) {
    return { ...detalleCampana(campanaPorId(contexto.campana)), pose: 'senala' }
  }
  if (contexto.tema === 'gasto' && contexto.monto) {
    // Se explica el gasto que consultó, no el mes sin ese gasto: las cifras tienen que ser las mismas.
    const r = gastoExtra(cliente, persona, contexto.monto)
    return {
      texto: `Sumo los ${enSoles(contexto.monto)} a tus pagos de aquí a tu cobro del ${fechaDia(cliente.proximoIngreso.fecha)} y lo calculo para un mes malo, en el que gastas un poco más de lo normal. ${r.texto}`,
      cifras: r.cifras,
      pose: 'pensando',
    }
  }
  if (contexto.tema === 'meta' && contexto.meta.monto && contexto.meta.fecha) {
    const { monto, enDolares, fecha } = contexto.meta
    const objetivo = enDolares ? Math.round(monto * leerTipoCambio(RESPALDO.tipoCambio).tasa) : monto
    const plan = planDeMeta(
      { objetivo, ahorrado: 0, fecha },
      { primerApartado: proximoIngreso.fecha, finPronostico, hoy, apartado: puedes },
    )
    const conTips = apartadoConTodos?.monto ?? 0
    const cuentaTips =
      conTips > puedes ? ` Con los tips: ${plan.veces} × ${enSoles(conTips)} = ${enSoles(plan.veces * conTips)}.` : ''
    const veces = `${plan.veces} ${plan.veces === 1 ? 'vez' : 'veces'}`
    return {
      texto: `${base} Hasta ${nombreFecha(fecha, hoy)} cobras ${veces}: ${plan.veces} × ${enSoles(puedes)} = ${enSoles(plan.veces * puedes)}.${cuentaTips} Tu meta es ${enSoles(objetivo)}. ${evitar}`.trim(),
      cifras: [],
      pose: 'pensando',
    }
  }
  if (contexto.tema === 'meta' || contexto.tema === 'ahorro') {
    return {
      texto: `${base} ${evitar} Si me dices para qué ahorras y cuánto cuesta, te armo el plan.`,
      cifras: [],
      pose: 'ahorra',
    }
  }
  if (contexto.tema === 'cobro' || contexto.tema === 'gasto' || contexto.tema === 'cuanto-gastar') {
    return {
      texto: riesgo
        ? `Lo calculo para un mes malo: si gastas un poco más o te pagan menos, ${textoDiasEnRojo(riesgo).toLowerCase()} quedarías en ${enSoles(riesgo.peorMonto)}. Si gastas hasta ${enSoles(gastoDiarioSeguro)} al día hasta tu cobro del ${fechaDia(proximoIngreso.fecha)}, eso no pasa. ${evitar}`.trim()
        : `Incluso en un mes malo llegas a tu cobro del ${fechaDia(proximoIngreso.fecha)} con plata en la cuenta. Tu límite seguro es ${enSoles(gastoDiarioSeguro)} al día.`,
      cifras: [],
      pose: 'pensando',
    }
  }
  const top = categorias.slice(0, 3).map((c) => `${c.nombre.toLowerCase()} ${enSolesRedondo(c.total)}`)
  return { texto: `Tus tres categorías más grandes en 30 días: ${top.join(', ')}. ${evitar}`.trim(), cifras: [] }
}

// --- Contexto de la conversación: cada mensaje se lee con todo lo que se habló antes, no solo el último.

// «el concierto está 450»: lo que se junta es la entrada.
const NOMBRE_META = { concierto: 'entrada', festival: 'entrada', entradas: 'entrada', deudas: 'deuda' }
// «¿y en 3 años?», «mejor 10 mil», «entonces para 2028»: siguen el tema anterior.
const SIGUE_EL_TEMA = /^(y|e|pero|mejor|entonces|ok|vale|bueno|y si|cambia|cambialo|ahora)\b/
const PIDE_MAS =
  /(explica|mas sobre|mas detalle|por que|porque|como asi|como es|como lo|que significa|no entiendo|dime mas|cuentame mas)/
const HABLA_DE_LA_META = /\b(eso|esa|ese|la meta|mi meta|el plan|ahorr|apart|junt|falta|cuanto|llego|llegaria|alcanz|tips?|plazo|fecha|cuota|inicial|que sea)/

export const CONTEXTO_VACIO = {
  tema: null,
  monto: null,
  meta: { monto: null, enDolares: false, fecha: null, que: null, ahorrado: null, inicial: null },
  campana: null,
  // La última respuesta mostró la campaña y preguntó «¿Quieres más info?»: solo entonces un «sí» o un «no» son sobre ella.
  ofrecida: false,
}

const SALUDA = /^(hola|holi|buenas|buen dia|buenos dias|buenas tardes|buenas noches|que tal|hey)\b[\s!.,?]*(lucas)?[\s!.,?]*$/
// Anclado al final: «perfecto, ¿y para fin de año?» sigue la meta, no es un agradecimiento.
const GRACIAS =
  /^((ok|ya|listo|no)[\s,!.]+)?(gracias|muchas gracias|mil gracias|genial|perfecto|chevere|bacan)[\s!.,?]*(lucas)?[\s!.,?]*$/
const PIDE_INGRESO =
  /\b(ingresos?|sueldo|salario|gano|ganara|ganaria|ganar|ganando|me pagan|me pagaran|me pagarian|me suben)\b/
// «¿y si gano 6000?» es un supuesto; «mi sueldo es 2600, ¿cuánto me falta?» es un dato y la pregunta es otra.
const ES_SUPUESTO = /\b(si|cuando|en caso|imagina|supon\w*|ganara|ganaria|pagaran|pagarian|me suben|subiera)\b/
const INGRESO_DICHO = /\b(?:ingresos?|sueldo|salario|gano|me pagan)\b[^,.;?]*?\d[\d.,]*(?:\s*mil)?/
// «un trabajo extra de 800 al mes» suma a lo que ya gana; «si gano 6000» es el total.
const ES_EXTRA = /\b(extra|adicional|aparte|cachuelo|chamba|ademas|mas al mes|me suben)\b/
const PIDE_EXTRA = /\b(trabajo|chamba|cachuelo|ingresos?)\s+(extra|adicional|aparte)\b|\b(cachuelo|chamba)\b/
// Plata que llega una sola vez: se mide como supuesto sobre la meta, no se guarda.
const UNICO = /\b(gratificacion|grati|cts|bono|aguinaldo|utilidades|herencia|premio)\b/
const NOMBRE_UNICO = { grati: 'gratificación', gratificacion: 'gratificación', cts: 'CTS' }
// «si aparto 500 al mes», «ahorrando 300 por quincena»: un ritmo propuesto, no el precio de la meta.
const PERIODO = '(al mes|mensual\\w*|cada mes|por mes|cada cobro|por cobro|cada quincena|por quincena|quincenal\\w*)'
const APORTE_PERIODICO = new RegExp(
  `\\b(?:apart|ahorr|guard|junt|pon|met|deposit)\\w*\\s+(?:unos\\s+)?(?:s\\/\\s*)?(\\d[\\d.,]*)\\s*(?:soles\\s+)?${PERIODO}`,
)
const SI_APARTO = /\bsi\s+(?:aparto|ahorro|guardo|junto|pongo|meto)\s+(?:unos\s+)?(?:s\/\s*)?(\d[\d.,]*)/
const PRECIO = /\b(cuesta|cuestan|vale|valen|precio|sale|esta en|esta a)\b/
// «¿puedo gastar 450 en el concierto?» pregunta por la liquidez de hoy: va antes que la meta y la campaña.
const PIDE_PERMISO = /\b(puedo|podria|me alcanza|alcanza para|me conviene)\b/
const PIDE_CAMPANA = /\b(campanas?|ofertas?|promos?|promociones?|descuentos?|beneficios?|convenios?)\b/
// «que sea X», «de marca X»: la persona prefiere una marca y Lucas le cuenta la campaña que sí hay.
// «que sea nuevo» o «que sea barato» describen el auto, no una marca.
const PIDE_MARCA = /\b(?:que sea|de (?:la )?marca|marca)\s+(?:un[ao]?\s+)?([a-z]{3,})\b/
const NO_ES_MARCA =
  /^(nuev|usad|seminuev|barat|car|economic|automatic|mecanic|electric|hibrid|grande|chic|pequen|bonit|buen|rapid|segur|propi|famil|del|para|con|sin|mas|menos|algo|este|ese|otr)/
// Solo un «sí» o «más info» a secas responde la oferta: «ok, ¿cuánto me falta?» sigue la meta.
const AFIRMA = '(si|sip|claro|dale|ya|ok|okey|bueno|pues|quiero|por favor|porfa|cuentame|me interesa|mas info\\w*|como funciona|como la uso|condiciones)'
const QUIERE_INFO = new RegExp(`^${AFIRMA}([\\s,!.?]+${AFIRMA})*[\\s,!.?]*$`)
// «no, pero ¿llego a mi cobro?» es otra pregunta: el rechazo va a secas, igual que el «sí».
const NO_QUIERE = /^(no|nop|nel|nah|paso|ahorita no|despues)([\s,!.]+(gracias|me interesa|no me interesa|quiero|nada mas|por ahora|esta vez|lucas))*[\s!.,?]*$/

const DEUDA = /\b(deudas?|debo|debe|prestamo|tengo que pagar)\b/
// «tengo 5000» o «tengo 5 mil» es plata; «tengo una deuda de 3000» o «tengo 2 trabajos», no.
const TENGO_PLATA = /\btengo\s+(?:s\/\s*)?\d[\d.,]*\s*(?:mil\b|soles|dolares|ahorr|juntad|guardad|en\b|[,.?!]|$)/

// Un monto dentro de una meta puede ser el precio, lo que ya tiene o la inicial.
function rolDelMonto(texto) {
  if (/\binicial\b/.test(texto)) return 'inicial'
  if (DEUDA.test(texto)) return 'precio'
  if (/(ahorrad|juntad|guardad|\bya tengo\b|\bllevo\b|\bya junte\b)/.test(texto) || TENGO_PLATA.test(texto)) {
    return PRECIO.test(texto) ? 'precio' : 'ahorrado'
  }
  return 'precio'
}

// Une lo nuevo de la meta con lo que ya se sabía. Si nombra otra cosa, es una meta nueva.
function metaCon(anterior, texto, hoy) {
  const hallado = texto.match(OBJETO_META)?.[1] ?? null
  const que = NOMBRE_META[hallado] ?? hallado
  const leido = montoDeMeta(texto)
  const rol = leido === null ? null : rolDelMonto(texto)
  const monto = rol === 'precio' ? leido : null
  const enSolesLeido = leido === null ? null : enSolesDe({ monto: leido, enDolares: EN_DOLARES.test(texto) })
  const fecha = fechaDeMeta(texto, hoy)
  // Nombrar otra cosa empieza una meta nueva: el precio del concierto no es el del carro.
  const nueva = que && anterior.que && que !== anterior.que
  const base = nueva ? CONTEXTO_VACIO.meta : anterior
  const meta = {
    que: que ?? base.que,
    monto: monto ?? base.monto,
    enDolares: monto !== null ? EN_DOLARES.test(texto) : base.enDolares,
    fecha: fecha ?? base.fecha,
    ahorrado: rol === 'ahorrado' ? enSolesLeido : (base.ahorrado ?? null),
    inicial: rol === 'inicial' ? enSolesLeido : (base.inicial ?? null),
  }
  // «la inicial es el 20 %»: sale del precio que ya se conoce.
  const porcentaje = /\binicial\b/.test(texto) && texto.match(/(\d+(?:[.,]\d+)?)\s*(%|por ciento)/)
  if (porcentaje && meta.monto) {
    meta.inicial = Math.round((enSolesDe(meta) * Number(porcentaje[1].replace(',', '.'))) / 100)
  }
  return meta
}

// «¿cuánto gasté en comida?»: palabras de la persona → categoría del motor.
const PALABRAS_CATEGORIA = [
  [/\b(comida|delivery|restaurant\w*|almuerzo\w*|cena\w*|menu)\b/, 'comida'],
  [/\b(transporte|taxi\w*|movilidad|uber|bus|combi|gasolina)\b/, 'transporte'],
  [/\b(salidas?|fiestas?|bar|tragos|juergas?)\b/, 'salidas'],
  [/\b(hormiga|cafes?|snacks?|golosinas?|antojos?)\b/, 'hormiga'],
  [/\b(suscripcion\w*|streaming|plataformas?)\b/, 'suscripciones'],
  [/\b(entretenimiento|cine|juegos?)\b/, 'entretenimiento'],
]
const PIDE_CATEGORIA = /\b(gaste|gastado|gastamos|gasto|gastos|se me va|se va|va en)\b/

function categoriaPedida(texto) {
  return PALABRAS_CATEGORIA.find(([regla]) => regla.test(texto))?.[1] ?? null
}

function gastoEnCategoria(cliente, id) {
  const c = cliente.categorias.find((x) => x.id === id)
  if (!c) return NO_ENTIENDO
  const diferencia = Math.round(c.total - c.promedio3m)
  const frente =
    diferencia > 0
      ? `Es ${enSoles(diferencia)} más que tu promedio.`
      : diferencia < 0
        ? `Es ${enSoles(-diferencia)} menos que tu promedio.`
        : 'Igual que tu promedio.'
  return {
    texto: `En los últimos 30 días gastaste ${enSolesRedondo(c.total)} en ${c.nombre.toLowerCase()}. ${frente}`,
    cifras: [
      { etiqueta: c.nombre, valor: enSolesRedondo(c.total) },
      { etiqueta: 'Tu promedio', valor: enSolesRedondo(c.promedio3m) },
    ],
  }
}

// Decide qué responder y cómo queda el contexto. Es puro: el chat entero se vuelve a leer en cada turno.
export function interpretar(pregunta, contexto, cliente) {
  const leido = leer(pregunta, contexto, cliente)
  let c = leido.contexto
  // Una campaña que no sirve a la meta no se muestra ni se guarda: así un «sí» no la trae de vuelta.
  const conMeta = leido.intencion === 'meta' || leido.intencion === 'aporte'
  if (conMeta && c.campana && !campanaUtil(cliente, c)) c = { ...c, campana: null }
  const conPrecio = Boolean(c.meta.monto || c.meta.inicial)
  const ofrecida =
    (leido.intencion === 'campana' && Boolean(c.campana) && conPrecio && Boolean(campanaUtil(cliente, c))) ||
    (leido.intencion === 'meta' && Boolean(c.campana) && c.campana !== contexto.campana)
  // «12000» y luego «hola»: el monto suelto ya no espera respuesta.
  const cierra = ['saludo', 'gracias', 'limites', 'no-entiendo'].includes(leido.intencion) && c.tema === 'monto-suelto'
  return { ...leido, contexto: { ...c, ofrecida, tema: cierra ? null : c.tema } }
}

function leer(pregunta, contexto, cliente) {
  const { hoy } = cliente
  let texto = normalizar(pregunta).trim().replace(/^[¿¡\s]+/, '')
  if (esPedidoDeOperacion(pregunta)) return { intencion: 'limites', contexto }
  if (SALUDA.test(texto)) return { intencion: 'saludo', contexto }
  if (contexto.ofrecida && NO_QUIERE.test(texto) && !/\d/.test(texto)) return { intencion: 'campana-no', contexto }
  if (GRACIAS.test(texto)) return { intencion: 'gracias', contexto }

  const noEsGasto = !/\b(gast|regalo)/.test(texto)
  // Supuestos sobre la meta que no cambian su precio: otro ingreso, un bono que llega una vez, otro ritmo.
  const hablaDeIngreso = PIDE_INGRESO.test(texto) || PIDE_EXTRA.test(texto)
  if (hablaDeIngreso && noEsGasto && montoDeMeta(texto)) {
    if (ES_SUPUESTO.test(texto) || PIDE_EXTRA.test(texto)) {
      return { intencion: 'ingreso', ingreso: { monto: montoDeMeta(texto), extra: ES_EXTRA.test(texto) }, contexto }
    }
    // Un dato de ingreso no es el precio de la meta: se quita y se responde lo demás.
    texto = texto.replace(INGRESO_DICHO, ' ').trim()
  }

  const conNumeros = numerosEnPalabras(texto)
  const monto = montoEn(sinNoMontos(conNumeros))
  const montoValido = monto > 0 ? monto : null
  const enMeta = contexto.tema === 'meta'
  const pideMeta = PIDE_META.test(texto)
  const sigueMeta = pideMeta || enMeta
  const montoLeido = montoDeMeta(texto)

  const imposible = fechaImposible(texto, hoy)
  if (imposible) {
    const meta = sigueMeta ? metaCon(contexto.meta, texto, hoy) : contexto.meta
    return { intencion: 'fecha-imposible', dicho: imposible, contexto: { ...contexto, tema: sigueMeta ? 'meta' : contexto.tema, meta } }
  }
  const compraHoy = !noEsGasto || (/\b(compr|pag)/.test(texto) && !/\b(junt|ahorr|apart|meta)/.test(texto))
  if (montoValido && PIDE_PERMISO.test(texto) && compraHoy) {
    return { intencion: 'gasto', contexto: { ...contexto, tema: 'gasto', monto: montoValido } }
  }

  const unico = texto.match(UNICO)?.[1]
  if (unico && enMeta && montoLeido && noEsGasto) {
    return { intencion: 'unico', unico: { monto: montoLeido, nombre: NOMBRE_UNICO[unico] ?? unico }, contexto }
  }
  const aporteHallado = conNumeros.match(APORTE_PERIODICO) ?? conNumeros.match(SI_APARTO)
  if (aporteHallado && noEsGasto) {
    const aporte = aNumero(aporteHallado[1]) * (/quincen/.test(aporteHallado[0]) ? 2 : 1)
    const meta = sigueMeta ? metaCon(contexto.meta, conNumeros.replace(aporteHallado[0], ' '), hoy) : contexto.meta
    if (meta.monto || meta.inicial) {
      const campana = campanaPara(meta.que)?.id ?? contexto.campana
      return { intencion: 'aporte', aporte, contexto: { ...contexto, tema: 'meta', meta, campana } }
    }
    return { intencion: 'ahorro', contexto: { ...contexto, tema: 'ahorro', monto: aporte } }
  }

  const categoria = categoriaPedida(texto)
  if (categoria && !montoValido && PIDE_CATEGORIA.test(texto)) {
    return { intencion: 'categoria', categoria, contexto: { ...contexto, tema: 'categorias' } }
  }

  const conMontoOFecha = montoLeido !== null || fechaDeMeta(texto, hoy) !== null
  const pideGasto = montoValido && /(gast|regalo|pag)/.test(texto)
  // «¿cuánto puedo gastar hoy?» es la pregunta de Lucas; «¿cuánto puedo gastar al mes para llegar?» dentro de una meta, no.
  const pideCuanto = /cuanto puedo gastar/.test(texto) && !(enMeta && /(al mes|para llegar|para juntar|apart|ahorr)/.test(texto))
  const pideCobro = pideCuanto || /(cobro|fin de mes|rojo)/.test(texto)
  const pideCategorias = /(gasto mas|en que gasto|categoria|donde se va)/.test(texto)
  const otroTema = pideGasto || pideCobro || pideCategorias
  const tema = (t, m = montoValido) => ({ intencion: t, contexto: { ...contexto, tema: t, monto: m } })

  // «12000» y luego «es una meta» o «para comprar ahora»: el monto de antes es el precio o el gasto.
  if (contexto.tema === 'monto-suelto' && montoLeido === null) {
    // «quiero comprarlo ahora» responde a la pregunta de Lucas: es un gasto, aunque diga «comprar».
    const hablaDeMeta = /\b(meta|ahorrar\w*|junt)/.test(texto)
    if (!hablaDeMeta && /\b(ahora|hoy|ya mismo|al toque)\b/.test(texto)) return tema('gasto', contexto.monto)
    if (pideMeta || hablaDeMeta) {
      const meta = metaCon({ ...CONTEXTO_VACIO.meta, monto: contexto.monto }, texto, hoy)
      return { intencion: 'meta', contexto: { ...contexto, tema: 'meta', meta, campana: campanaPara(meta.que)?.id ?? null } }
    }
    if (/(compr|gast|pag)/.test(texto)) return tema('gasto', contexto.monto)
  }
  if (contexto.tema && PIDE_MAS.test(texto) && !conMontoOFecha) return { intencion: 'detalle', contexto }

  // Campañas: se preguntan directo o salen al nombrar una marca dentro de una meta.
  const pedida = texto.match(PIDE_MARCA)?.[1] ?? null
  const marca = pedida && !NO_ES_MARCA.test(pedida) ? pedida : null
  const metaAhora = sigueMeta ? metaCon(contexto.meta, texto, hoy) : contexto.meta
  const campana = campanaPara(texto) ?? campanaPara(metaAhora.que)
  const pideCampana = PIDE_CAMPANA.test(texto)
  const marcaUtil = marca && campana && campanaUtil(cliente, { ...contexto, meta: metaAhora, campana: campana.id })
  if (!otroTema && (pideCampana || marcaUtil)) {
    return {
      intencion: 'campana',
      marca: pideCampana ? null : marca,
      contexto: { ...contexto, tema: sigueMeta ? 'meta' : 'campana', meta: metaAhora, campana: campana?.id ?? null },
    }
  }
  if (contexto.ofrecida && contexto.campana && QUIERE_INFO.test(texto)) {
    return { intencion: 'campana-detalle', contexto }
  }
  // Un «sí» o «no» suelto después de la meta contesta a «¿Para cuándo lo quieres?»: falta la fecha.
  if (hayMeta(contexto) && (QUIERE_INFO.test(texto) || NO_QUIERE.test(texto))) {
    return { intencion: 'sigue-meta', rechaza: NO_QUIERE.test(texto), contexto }
  }

  const esMeta =
    pideMeta || (enMeta && !otroTema && (conMontoOFecha || SIGUE_EL_TEMA.test(texto) || HABLA_DE_LA_META.test(texto)))
  if (esMeta) {
    const meta = metaCon(contexto.meta, texto, hoy)
    const deLaMeta = campanaPara(meta.que)?.id ?? null
    return { intencion: 'meta', contexto: { ...contexto, tema: 'meta', meta, campana: deLaMeta ?? contexto.campana } }
  }
  if (/(ahorr|apart|guardar|colchon)/.test(texto)) return tema('ahorro')
  if (montoValido && /(gast|compr|regalo|pag)/.test(texto)) return tema('gasto')
  if (pideCuanto) return tema('cuanto-gastar')
  if (pideCobro || /(llego|alcanza)/.test(texto)) return tema('cobro')
  if (pideCategorias) return tema('categorias')
  // «¿y 80?» después de un gasto o de un ahorro: el mismo cálculo con el monto nuevo.
  if (montoValido && (contexto.tema === 'gasto' || contexto.tema === 'ahorro')) return tema(contexto.tema)
  if (montoValido) return tema('monto-suelto')
  return { intencion: 'no-entiendo', contexto }
}

export function contextoDe(previas, cliente) {
  return previas.reduce((contexto, texto) => interpretar(texto, contexto, cliente).contexto, CONTEXTO_VACIO)
}

// Las campañas viven en el front: estas preguntas se responden aquí aunque el agente esté activo. Un «sí»
// solo es sobre la campaña si la oferta salió de aquí; si la meta la contestó el agente, la persona no la vio.
export function esPreguntaDeCampana(pregunta, previas, cliente) {
  const { intencion } = interpretar(pregunta, contextoDe(previas, cliente), cliente)
  if (intencion === 'campana') return true
  if (intencion !== 'campana-detalle' || !previas.length) return false
  const ultima = interpretar(previas.at(-1), contextoDe(previas.slice(0, -1), cliente), cliente)
  return ultima.intencion === 'campana'
}

// Cuándo se compraría: en la fecha pedida si se llega, si no cuando se junta todo al mejor ritmo sin rojo.
function fechaDeCompra(cliente, meta) {
  const { hoy, proximoIngreso, finPronostico } = cliente
  const { objetivo, ahorrado } = objetivoDe(meta)
  const apartado = Math.max(cliente.apartado?.monto ?? 0, cliente.apartadoConTodos?.monto ?? 0)
  const plan = planDeMeta(
    { objetivo, ahorrado, fecha: meta.fecha ?? proximoIngreso.fecha },
    { primerApartado: proximoIngreso.fecha, finPronostico, hoy, apartado },
  )
  if (meta.fecha && plan.alcanza) return meta.fecha
  return plan.llegaEl
}

// Una campaña que vence antes de juntar la plata no ayuda a la meta: no se ofrece (reglas/negocio.md, regla 7).
function campanaUtil(cliente, contexto) {
  const campana = campanaPorId(contexto.campana)
  if (!campana || campanaPara(contexto.meta.que) !== campana) return null
  if (!contexto.meta.monto && !contexto.meta.inicial) return campana
  const compra = fechaDeCompra(cliente, contexto.meta)
  return compra && compra <= campana.hasta ? campana : null
}

// Si la pide directo pero vence antes de juntar la plata, se cuenta sin «Pagarías» y con la fecha que importa.
function campanaPedida(cliente, contexto, marca) {
  const campana = campanaPorId(contexto.campana)
  const conPrecio = Boolean(contexto.meta.monto || contexto.meta.inicial)
  if (!campana || !conPrecio || campanaUtil(cliente, contexto)) {
    return respuestaCampana(campana, { precio: enSolesDe(contexto.meta), marca })
  }
  const r = respuestaCampana(campana, { marca })
  return {
    texto: `${r.texto.replace(/ ¿Cuánto cuesta\? Te digo cuánto pagarías\./, '')} Vence el ${fechaCorta(campana.hasta)} de ${campana.hasta.slice(0, 4)}; a tu ritmo de hoy juntas la plata después.`,
    cifras: [...r.cifras, { etiqueta: 'Vigente hasta', valor: `${fechaCorta(campana.hasta)} ${campana.hasta.slice(0, 4)}` }],
  }
}

// La meta suma su campaña: el aviso solo la primera vez y con lo que cambia el plan; las cifras, siempre que haya precio.
function metaConCampana(cliente, contexto, anterior) {
  const plan = planDeAhorro(cliente, contexto.meta)
  const campana = campanaUtil(cliente, contexto)
  if (!campana) return plan
  const precio = enSolesDe(contexto.meta)
  if (anterior.campana === campana.id) {
    return { ...plan, cifras: precio ? [...plan.cifras, ...cifrasDeCampana(campana, precio)] : plan.cifras }
  }
  const descuento = ahorroCon(campana, precio)
  // Con la inicial, el descuento baja el precio del carro pero no lo que hay que juntar ahora.
  let conDescuento = ''
  if (descuento && !contexto.meta.inicial) {
    const puedes = cliente.apartado?.monto ?? 0
    const conTips = cliente.apartadoConTodos?.monto ?? 0
    const rebajada = { ...contexto.meta, monto: precio - descuento, enDolares: false }
    const ritmo = metaConRitmo(cliente, rebajada, Math.max(puedes, conTips))
    conDescuento = `Con la campaña${conTips > puedes ? ' y los tips' : ''}, ${ritmo}`
  }
  return {
    texto: `${plan.texto.replace(/ ¿Para cuándo lo quieres\?$/, '')} ${avisoDeCampana(campana, precio, conDescuento)}`,
    cifras: precio ? [...plan.cifras, ...cifrasDeCampana(campana, precio)] : plan.cifras,
  }
}

// La meta medida con otro ritmo de apartado: cuándo llega, o si llega a la fecha que pidió.
function metaConRitmo(cliente, meta, apartado) {
  const { hoy, proximoIngreso, finPronostico } = cliente
  const { objetivo, ahorrado } = objetivoDe(meta)
  const plan = planDeMeta(
    { objetivo, ahorrado, fecha: meta.fecha ?? proximoIngreso.fecha },
    { primerApartado: proximoIngreso.fecha, finPronostico, hoy, apartado },
  )
  const nombre = tuMeta(meta.que)
  if (meta.fecha && plan.alcanza) return `sí llegas con ${nombre} para ${nombreFecha(meta.fecha, hoy)}.`
  const aTiempo = meta.fecha ? ` Para ${nombreFecha(meta.fecha, hoy)} necesitarías ${enSoles(plan.necesario)} al mes.` : ''
  return `juntas ${nombre} de ${enSoles(objetivo)} ${cuando(plan.llegaEl, hoy)}.${aTiempo}`
}

function hayMeta(contexto) {
  return contexto.tema === 'meta' && Boolean(contexto.meta.monto || contexto.meta.inicial)
}

// El mayor apartado (múltiplo de S/ 10) que el motor da por seguro si en el próximo cobro entra `suma` de más.
function apartadoConIngreso(cliente, persona, suma) {
  const ajuste = ajusteActual(cliente)
  const extra = { id: 'supuesto', fecha: cliente.proximoIngreso.fecha, monto: suma }
  const conIngreso = { ...ajuste, ingresosExtra: [...(ajuste.ingresosExtra ?? []), extra] }
  let bajo = 0
  let alto = Math.ceil(((cliente.apartado?.monto ?? 0) + suma) / 10) * 10
  if (apartadoSinRojo(persona, alto, conIngreso)) return alto
  while (alto - bajo > 10) {
    const medio = Math.floor((bajo + alto) / 20) * 10
    if (apartadoSinRojo(persona, medio, conIngreso)) bajo = medio
    else alto = medio
  }
  return bajo
}

// Supuesto visible: si cobra más y gasta lo mismo, el motor recalcula cuánto puede apartar sin rojo.
function conOtroIngreso(cliente, persona, contexto, { monto, extra }) {
  const actual = persona.ingresoMensual
  const puedes = cliente.apartado?.monto ?? 0
  const nuevo = extra ? actual + monto : monto
  const suma = nuevo - actual
  const cifras = [
    { etiqueta: extra ? 'Ingreso extra que consultas' : 'Ingreso que consultas', valor: enSoles(monto) },
    { etiqueta: 'Tu ingreso hoy', valor: enSoles(actual) },
  ]
  if (suma <= 0) {
    return {
      texto: `Hoy te llegan unos ${enSoles(actual)} al mes. Con ${enSoles(nuevo)} no tendrías más margen: lo primero sería ajustar tu gasto para no quedar en rojo.`,
      cifras,
    }
  }
  const apartado = apartadoConIngreso(cliente, persona, suma)
  cifras.push({ etiqueta: 'Podrías apartar al mes', valor: enSoles(apartado) })
  cifras.push({ etiqueta: 'Supuesto', valor: 'Gastas lo mismo que hoy' })
  const si = extra ? `Si te entran ${enSoles(monto)} más al mes` : `Si te llegan ${enSoles(nuevo)} al mes a la cuenta`
  const inicio = `${si} y gastas lo mismo que hoy, podrías apartar unos ${enSoles(apartado)} al mes en vez de ${enSoles(puedes)}.`
  if (!hayMeta(contexto)) return { texto: inicio, cifras }
  const ritmo = metaConRitmo(cliente, contexto.meta, apartado)
  return { texto: `${inicio} Así ${ritmo}`, cifras }
}

// «¿y si aparto 500 al mes?»: se mide con ese ritmo y se dice si hoy ese monto lo deja en rojo.
function conAporte(cliente, persona, contexto, aporte) {
  const puedes = cliente.apartado?.monto ?? 0
  const seguro = apartadoSinRojo(persona, aporte, ajusteActual(cliente))
  const riesgo = seguro
    ? ' Hoy ese monto no te deja en rojo.'
    : ` Ojo: hoy ese monto te dejaría en rojo; sin riesgo puedes apartar ${enSoles(puedes)}.`
  return {
    texto: `Apartando ${enSoles(aporte)} al mes, ${metaConRitmo(cliente, contexto.meta, aporte)}${riesgo}`,
    cifras: [
      { etiqueta: 'Apartas al mes', valor: enSoles(aporte) },
      { etiqueta: 'Sin riesgo hoy', valor: enSoles(puedes) },
    ],
  }
}

// Con recibo por honorarios no hay gratificación ni CTS: se dice y el monto se mide como un ingreso extra.
function conMontoUnico(cliente, persona, contexto, unico) {
  const deLey = unico.nombre === 'gratificación' || unico.nombre === 'CTS'
  if (deLey && /honorarios/i.test(persona.tipoIngreso ?? '')) {
    const plan = planDeAhorro(cliente, contexto.meta, { unico: { ...unico, nombre: 'ingreso extra' } })
    return { ...plan, texto: `Con recibo por honorarios no te toca ${unico.nombre}. ${plan.texto}` }
  }
  return planDeAhorro(cliente, contexto.meta, { unico })
}

// `previas`: todo lo que la persona escribió antes en este chat, en orden.
export function responder(pregunta, cliente, persona, previas = []) {
  const anterior = contextoDe(previas, cliente)
  const { intencion, contexto, marca, ingreso, aporte, unico, categoria, dicho, rechaza } = interpretar(
    pregunta,
    anterior,
    cliente,
  )
  switch (intencion) {
    case 'fecha-imposible':
      return { texto: `El ${dicho} no existe en el calendario. ¿Qué fecha quieres?`, cifras: [], pose: 'pensando' }
    case 'categoria':
      return gastoEnCategoria(cliente, categoria)
    case 'limites':
      return LIMITES
    case 'saludo':
      return SALUDO
    case 'detalle':
      return masDetalle(cliente, persona, contexto)
    case 'monto-suelto':
      return {
        texto: `¿${enSolesRedondo(contexto.monto)} es algo que quieres comprar ahora o una meta para juntar? Dímelo y lo calculo con tus datos.`,
        cifras: [],
        pose: 'pensando',
      }
    case 'sigue-meta':
      return {
        texto: contexto.meta.fecha
          ? 'Listo. Pregúntame cuánto te falta o qué tip te ayuda más.'
          : rechaza
            ? 'Listo. Si me dices una fecha, te digo si llegas; también puedo decirte qué tip te ayuda más.'
            : 'Dime para cuándo lo quieres, por ejemplo «para marzo» o «en 6 meses», y te digo si llegas.',
        cifras: [],
        pose: 'ahorra',
      }
    case 'campana-no':
      return { texto: 'Listo, seguimos con tu plan.', cifras: [], pose: 'neutral' }
    case 'gracias':
      return { texto: '¡De nada! Aquí estoy para lo que necesites.', cifras: [], pose: 'celebra' }
    case 'ingreso':
      return { ...conOtroIngreso(cliente, persona, contexto, ingreso), pose: 'ahorra' }
    case 'aporte':
      return { ...conAporte(cliente, persona, contexto, aporte), pose: 'ahorra' }
    case 'unico':
      return { ...conMontoUnico(cliente, persona, contexto, unico), pose: 'ahorra' }
    case 'campana':
      return {
        ...campanaPedida(cliente, contexto, marca),
        pose: 'senala',
      }
    case 'campana-detalle':
      return { ...detalleCampana(campanaPorId(contexto.campana), enSolesDe(contexto.meta)), pose: 'senala' }
    case 'meta':
      return { ...metaConCampana(cliente, contexto, anterior), pose: 'ahorra' }
    case 'ahorro':
      return { ...cuantoAhorrar(cliente, persona, contexto.monto), pose: 'ahorra' }
    case 'gasto':
      return gastoExtra(cliente, persona, contexto.monto)
    case 'cuanto-gastar':
      return cuantoPuedoGastar(cliente)
    case 'cobro':
      return llegarAlCobro(cliente)
    case 'categorias':
      return dondeGastoMas(cliente)
    default:
      return NO_ENTIENDO
  }
}
