// Respuestas por plantilla mientras no exista el agente (JF-02). Toda cifra sale del motor, nunca del texto.
import { apartadoSinRojo, evaluarGastoExtra } from '../motor/motor.js'
import { conSigno, enSoles, fechaCorta, fechaDia, textoDiasEnRojo } from '../formato.js'

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
    texto: `Te alcanza solo si ajustas lo demás: con ese gasto, el ${fechaDia(r.fechaPeorDia)} podrías quedar en ${enSoles(r.peorDespues)} si gastas un poco más de lo normal. Para evitarlo, gasta hasta ${enSoles(r.gastoDiarioSeguro)} al día hasta tu cobro.`,
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
    texto: `En los últimos 30 días gastaste más en ${mayor.nombre.toLowerCase()}: ${enSoles(Math.round(mayor.total))}. ${subida}`,
    cifras: [
      { etiqueta: mayor.nombre, valor: enSoles(Math.round(mayor.total)) },
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
}

const NO_ENTIENDO = {
  texto: 'Todavía no sé responder eso. Prueba con una de las preguntas sugeridas.',
  cifras: [],
}

export function responder(pregunta, cliente, persona) {
  const texto = normalizar(pregunta)
  if (/(invert|inviert|inversion|dolar|accion|cripto|transfer|transfier|paga por mi|mueve)/.test(texto)) return LIMITES
  const monto = montoEn(texto)
  const montoValido = monto > 0 ? monto : null
  if (/(ahorr|apart|guardar|colchon)/.test(texto)) return cuantoAhorrar(cliente, persona, montoValido)
  if (montoValido && /(gast|compr|regalo|pag)/.test(texto)) return gastoExtra(cliente, persona, montoValido)
  if (/(llego|alcanza|fin de mes|cobro|rojo)/.test(texto)) return llegarAlCobro(cliente)
  if (/(gasto mas|en que gasto|categoria|donde se va)/.test(texto)) return dondeGastoMas(cliente)
  return NO_ENTIENDO
}
