// Respuestas por plantilla mientras no exista el agente (JF-02). Toda cifra sale del motor, nunca del texto.
import { evaluarGastoExtra } from '../mocks/motor.js'
import { conSigno, enSoles, fechaDia, textoDiasEnRojo } from '../formato.js'

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

function montoEn(texto) {
  const hallado = texto.replace(/,/g, '').match(/(\d+(?:\.\d+)?)/)
  return hallado ? Number(hallado[1]) : null
}

function llegarAlCobro(cliente) {
  const { riesgo, gastoDiarioActual, gastoDiarioSeguro, proximoIngreso } = cliente
  if (!riesgo) {
    return {
      texto: `Sí. Llegas a tu cobro del ${fechaDia(proximoIngreso.fecha)} sin quedar en rojo, incluso en el peor caso.`,
      cifras: [],
    }
  }
  return {
    texto: `Si sigues gastando unos ${enSoles(gastoDiarioActual)} al día, ${textoDiasEnRojo(riesgo).toLowerCase()} podrías quedar en rojo. Si bajas a ${enSoles(gastoDiarioSeguro)} al día, llegas a tu cobro del ${fechaDia(proximoIngreso.fecha)} incluso si este mes cobras menos o gastas más de lo normal.`,
    cifras: [
      { etiqueta: 'Gasto de hoy por día', valor: enSoles(gastoDiarioActual) },
      { etiqueta: `Peor caso el ${fechaDia(riesgo.peorFecha)}`, valor: enSoles(riesgo.peorMonto) },
      { etiqueta: 'Gasto seguro por día', valor: enSoles(gastoDiarioSeguro) },
    ],
  }
}

function gastoExtra(persona, monto) {
  const r = evaluarGastoExtra(persona, monto)
  const quedaEnRojo = r.peorDespues < 0
  return {
    texto: quedaEnRojo
      ? `Puedes, pero tu día más justo, el ${fechaDia(r.fechaPeorDia)}, bajaría de ${enSoles(r.peorAntes)} a ${enSoles(r.peorDespues)} en el peor caso. Si lo compras, te conviene gastar hasta ${enSoles(r.gastoDiarioSeguro)} al día hasta tu cobro.`
      : `Sí. Aun con ese gasto tu día más justo queda en ${conSigno(r.peorDespues)} en el peor caso.`,
    cifras: [
      { etiqueta: 'Gasto que consultas', valor: enSoles(monto) },
      { etiqueta: 'Peor caso con el gasto', valor: enSoles(r.peorDespues) },
      { etiqueta: 'Gasto seguro por día después', valor: enSoles(r.gastoDiarioSeguro) },
    ],
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

function cuantoAhorrar(cliente) {
  const { apartado, proximoIngreso } = cliente
  if (!apartado) {
    return { texto: 'Este mes no te conviene apartar al cobrar: primero toca pasar tus días más justos.', cifras: [] }
  }
  return {
    texto: `Cuando cobres el ${fechaDia(proximoIngreso.fecha)}, podrías apartar ${enSoles(apartado.monto)}. Lo comprobé con tus pagos de diciembre y no te deja en rojo. En ${apartado.cobros} cobros tendrías ${enSoles(apartado.total)} de colchón.`,
    cifras: [
      { etiqueta: 'Apartado por cobro', valor: enSoles(apartado.monto) },
      { etiqueta: `Colchón en ${apartado.cobros} cobros`, valor: enSoles(apartado.total) },
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
  if (monto && /(gastar|comprar|regalo|pagar|gasto de)/.test(texto)) return gastoExtra(persona, monto)
  if (/(llego|alcanza|fin de mes|cobro|rojo)/.test(texto)) return llegarAlCobro(cliente)
  if (/(gasto mas|en que gasto|categoria|donde se va)/.test(texto)) return dondeGastoMas(cliente)
  if (/(ahorr|apart|guardar|colchon)/.test(texto)) return cuantoAhorrar(cliente)
  return NO_ENTIENDO
}
