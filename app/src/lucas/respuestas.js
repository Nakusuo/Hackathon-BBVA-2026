// Respuestas por plantilla: respaldo cuando el agente (JF-02) no está o no contesta. Toda cifra sale del motor, nunca del texto.
import { apartadoSinRojo, evaluarGastoExtra } from '../motor/motor.js'
import { conSigno, diasEntre, enSoles, enSolesRedondo, fechaCorta, fechaDia, textoDiasEnRojo } from '../formato.js'
import { leerTipoCambio } from '../api/contrato.js'
import { RESPALDO } from '../api/respaldo.js'
import { finDeAnio, planDeMeta } from './metas.js'

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

const PIDE_META =
  /\b(metas?|plan de ahorro|juntar|junto|reunir|quiero comprar\w*|comprarme|carro|auto|moto|viaje|laptop|computadora|celular|depa|departamento|casa|terreno|matricula|boda)\b/
const EN_DOLARES = /(\bdolar|\busd\b|us\$|\$\s*\d)/
const MESES_LARGOS = new Intl.DateTimeFormat('es-PE', { month: 'long', year: 'numeric' })

function sumarMeses(fechaIso, meses) {
  const [anio, mes, dia] = fechaIso.split('-').map(Number)
  const ultimo = new Date(Date.UTC(anio, mes - 1 + meses + 1, 0)).getUTCDate()
  return new Date(Date.UTC(anio, mes - 1 + meses, Math.min(dia, ultimo))).toISOString().slice(0, 10)
}

// «para 2027» es un año; «una meta de 2000» es un monto.
const ANIO = /\b(?:para|en|hasta|del)\s+(?:el\s+)?(?:ano\s+)?(20\d\d)\b(?!\s*(soles|dolares|mil))/
const NUMERO_PALABRA = { un: 1, una: 1, dos: 2, tres: 3, cuatro: 4, cinco: 5, seis: 6, ocho: 8, diez: 10, doce: 12 }

// «fin de año», «diciembre», «en 6 meses», «en 2 años», «para 2027». Sin fecha devuelve null.
export function fechaDeMeta(texto, hoy) {
  if (/\b(fin de (ano|anio)|fin del (ano|anio)|diciembre|navidad)\b/.test(texto)) return finDeAnio(hoy)
  const plazo = texto.match(/\ben\s+(\d+|un|una|dos|tres|cuatro|cinco|seis|ocho|diez|doce)\s+(mes|meses|ano|anos)\b/)
  if (plazo) {
    const n = NUMERO_PALABRA[plazo[1]] ?? Number(plazo[1])
    return sumarMeses(hoy, plazo[2].startsWith('mes') ? n : n * 12)
  }
  const anio = texto.match(ANIO)
  if (anio && anio[1] >= hoy.slice(0, 4)) return `${anio[1]}-12-31`
  return null
}

// El monto de la meta sin confundirlo con el plazo («en 6 meses», «para 2027») y leyendo «14 mil».
export function montoDeMeta(texto) {
  const sinPlazo = texto
    .replace(/\ben\s+\d+\s+(mes|meses|ano|anos)\b/g, ' ')
    .replace(new RegExp(ANIO.source, 'g'), ' ')
    .replace(/\$\s*(?=\d)/g, ' ')
  const enMiles = sinPlazo.match(/(\d[\d.,]*)\s*mil\b/)
  const monto = enMiles ? aNumero(enMiles[1]) * 1000 : montoEn(sinPlazo)
  return monto > 0 ? monto : null
}

function cuando(fechaIso, hoy) {
  const meses = Math.round(diasEntre(hoy, fechaIso) / 30)
  if (meses <= 24) return `en ${MESES_LARGOS.format(new Date(`${fechaIso}T12:00:00`))}`
  return `en unos ${Math.round(meses / 12)} años`
}

function nombreFecha(fechaIso, hoy) {
  if (fechaIso === finDeAnio(hoy)) return 'fin de año'
  if (fechaIso.endsWith('-12-31')) return `fin de ${fechaIso.slice(0, 4)}`
  return `el ${fechaCorta(fechaIso)} de ${fechaIso.slice(0, 4)}`
}

function planDeAhorro(cliente, { monto, enDolares, fecha, que }) {
  if (!monto) {
    const plan = que ? `el plan de tu ${que}` : 'tu plan'
    return {
      texto: fecha
        ? `Armemos ${plan} para ${nombreFecha(fecha, cliente.hoy)}. ¿Cuánto cuesta?`
        : `Armemos ${plan}. ¿Cuánto cuesta y para cuándo lo quieres? Por ejemplo: «S/ 3,000 para fin de año».`,
      cifras: [],
    }
  }
  const { hoy, proximoIngreso, finPronostico } = cliente
  const tipo = leerTipoCambio(RESPALDO.tipoCambio)
  const objetivo = enDolares ? Math.round(monto * tipo.tasa) : monto
  const puedes = cliente.apartado?.monto ?? 0
  const conTips = cliente.apartadoConTodos?.monto ?? 0
  const contexto = { primerApartado: proximoIngreso.fecha, finPronostico, hoy }
  // Sin fecha se mide solo el ritmo: con la fecha del primer cobro, `llegaEl` dice cuándo se junta todo.
  const meta = { objetivo, ahorrado: 0, fecha: fecha ?? proximoIngreso.fecha }
  const plan = planDeMeta(meta, { ...contexto, apartado: puedes })
  const planTips = conTips > puedes ? planDeMeta(meta, { ...contexto, apartado: conTips }) : null

  const cifras = [{ etiqueta: 'Tu meta', valor: enSoles(objetivo) }]
  if (enDolares) {
    cifras.push({ etiqueta: `Cambio referencial del ${fechaCorta(tipo.fecha)}`, valor: `S/ ${tipo.tasa.toFixed(2)} por dólar` })
  }
  // Cada respuesta dice de qué meta habla: en una charla larga la persona puede haber cambiado de idea.
  const cuesta = enDolares ? `US$ ${monto.toLocaleString('es-PE')}, unos ${enSoles(objetivo)}` : enSoles(objetivo)
  const precio = que ? `Tu ${que} cuesta ${cuesta}. ` : `Tu meta es de ${cuesta}. `

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
function masDetalle(cliente, contexto) {
  const { apartado, apartadoConTodos, proximoIngreso, finPronostico, hoy, riesgo, gastoDiarioSeguro, categorias } = cliente
  const puedes = apartado?.monto ?? 0
  const base = `Cada vez que cobras miro tus pagos hasta el siguiente cobro y solo aparto lo que no te deja en rojo, ni en un mes malo. Hoy eso es ${enSoles(puedes)} al mes.`
  const evitar = queEvitar(cliente)
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
  if (contexto.tema === 'cobro' || contexto.tema === 'gasto') {
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

const OBJETO_META =
  /\b(carro|auto|moto|viaje|vacaciones|laptop|computadora|celular|depa|departamento|casa|terreno|matricula|boda|bicicleta|televisor|tele|consola|concierto|entrada|evento|fiesta|curso|estudios|maestria|ropa|zapatillas|mascota|negocio)\b/
// «¿y en 3 años?», «mejor 10 mil», «entonces para 2028»: siguen el tema anterior.
const SIGUE_EL_TEMA = /^(y|e|pero|mejor|entonces|ok|vale|bueno|y si|cambia|cambialo|ahora)\b/
const PIDE_MAS =
  /(explica|mas sobre|mas detalle|por que|porque|como asi|como es|como lo|que significa|no entiendo|dime mas|cuentame mas)/
const SALUDA = /^(hola|holi|buenas|buen dia|buenos dias|buenas tardes|buenas noches|que tal|hey)[\s!.,?]*$/

const HABLA_DE_LA_META = /\b(eso|esa|ese|la meta|mi meta|el plan|ahorr|apart|junt|falta|cuanto|llego|llegaria|alcanz|tips?|plazo|fecha|cuota)/

export const CONTEXTO_VACIO = { tema: null, monto: null, meta: { monto: null, enDolares: false, fecha: null, que: null } }

// Une lo nuevo de la meta con lo que ya se sabía. Si nombra otra cosa con su precio, es una meta nueva.
function metaCon(anterior, texto, hoy) {
  const que = texto.match(OBJETO_META)?.[1] ?? null
  const monto = montoDeMeta(texto)
  const fecha = fechaDeMeta(texto, hoy)
  // Nombrar otra cosa empieza una meta nueva: el precio del concierto no es el del carro.
  const nueva = que && anterior.que && que !== anterior.que
  const base = nueva ? CONTEXTO_VACIO.meta : anterior
  return {
    que: que ?? base.que,
    monto: monto ?? base.monto,
    enDolares: monto !== null ? EN_DOLARES.test(texto) : base.enDolares,
    fecha: fecha ?? base.fecha,
  }
}

// Decide qué responder y cómo queda el contexto. Es puro: el chat entero se vuelve a leer en cada turno.
export function interpretar(pregunta, contexto, hoy) {
  const texto = normalizar(pregunta).trim().replace(/^[¿¡\s]+/, '')
  if (esPedidoDeOperacion(pregunta)) return { intencion: 'limites', contexto }
  if (SALUDA.test(texto)) return { intencion: 'saludo', contexto }
  const monto = montoEn(texto)
  const montoValido = monto > 0 ? monto : null
  const conMontoOFecha = montoDeMeta(texto) !== null || fechaDeMeta(texto, hoy) !== null
  const pideGasto = montoValido && /(gast|regalo|pag)/.test(texto)
  const pideCobro = /(cobro|fin de mes|rojo)/.test(texto)
  const pideCategorias = /(gasto mas|en que gasto|categoria|donde se va)/.test(texto)
  const otroTema = pideGasto || pideCobro || pideCategorias
  const enMeta = contexto.tema === 'meta'
  if (contexto.tema && PIDE_MAS.test(texto) && !conMontoOFecha) return { intencion: 'detalle', contexto }

  const esMeta =
    PIDE_META.test(texto) ||
    (enMeta && !otroTema && (conMontoOFecha || SIGUE_EL_TEMA.test(texto) || HABLA_DE_LA_META.test(texto)))
  if (esMeta) {
    return { intencion: 'meta', contexto: { ...contexto, tema: 'meta', meta: metaCon(contexto.meta, texto, hoy) } }
  }
  const tema = (t, m = montoValido) => ({ intencion: t, contexto: { ...contexto, tema: t, monto: m } })
  if (/(ahorr|apart|guardar|colchon)/.test(texto)) return tema('ahorro')
  if (montoValido && /(gast|compr|regalo|pag)/.test(texto)) return tema('gasto')
  if (/(llego|alcanza|fin de mes|cobro|rojo)/.test(texto)) return tema('cobro')
  if (pideCategorias) return tema('categorias')
  // «¿y 80?» después de un gasto o de un ahorro: el mismo cálculo con el monto nuevo.
  if (montoValido && (contexto.tema === 'gasto' || contexto.tema === 'ahorro')) return tema(contexto.tema)
  if (montoValido) return { intencion: 'monto-suelto', contexto: { ...contexto, monto: montoValido } }
  return { intencion: 'no-entiendo', contexto }
}

export function contextoDe(previas, hoy) {
  return previas.reduce((contexto, texto) => interpretar(texto, contexto, hoy).contexto, CONTEXTO_VACIO)
}

// `previas`: todo lo que la persona escribió antes en este chat, en orden.
export function responder(pregunta, cliente, persona, previas = []) {
  const { intencion, contexto } = interpretar(pregunta, contextoDe(previas, cliente.hoy), cliente.hoy)
  switch (intencion) {
    case 'limites':
      return LIMITES
    case 'saludo':
      return SALUDO
    case 'detalle':
      return masDetalle(cliente, contexto)
    case 'monto-suelto':
      return {
        texto: `¿${enSolesRedondo(contexto.monto)} es algo que quieres comprar ahora o una meta para juntar? Dímelo y lo calculo con tus datos.`,
        cifras: [],
        pose: 'pensando',
      }
    case 'meta':
      return { ...planDeAhorro(cliente, contexto.meta), pose: 'ahorra' }
    case 'ahorro':
      return { ...cuantoAhorrar(cliente, persona, contexto.monto), pose: 'ahorra' }
    case 'gasto':
      return gastoExtra(cliente, persona, contexto.monto)
    case 'cobro':
      return llegarAlCobro(cliente)
    case 'categorias':
      return dondeGastoMas(cliente)
    default:
      return NO_ENTIENDO
  }
}
