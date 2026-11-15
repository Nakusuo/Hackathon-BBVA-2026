// «Explícamelo fácil»: la misma pantalla en palabras simples. Solo repite cifras que ya están en ella (HU-23),
// por eso cada texto se arma con los mismos campos de la vista y nunca calcula nada nuevo.
import { enSoles, fechaDia, textoDiasEnRojo } from '../formato.js'

function peorCaso(cliente) {
  return {
    termino: 'Peor caso',
    texto: cliente.ingresoVariable
      ? 'Lo que pasaría en un mes malo: gastas más o te pagan menos. No es lo que espero, es el límite.'
      : 'Lo que pasaría en un mes malo, si gastas más. Con sueldo fijo queda cerca de lo normal.',
  }
}

function enRojo(riesgo) {
  return {
    termino: 'Quedar en rojo',
    texto: riesgo
      ? `Que tu cuenta baje de cero. Te podría pasar ${textoDiasEnRojo(riesgo).toLowerCase()}.`
      : 'Que tu cuenta baje de cero. Antes de tu cobro no te pasa.',
  }
}

export function explicarResumen(cliente) {
  const { gastoDiarioSeguro, gastoDiarioActual, proximoIngreso, riesgo } = cliente
  // Con gasto seguro 0 «hasta S/ 0 al día y llegas» sería falso: ni sin gastar se llega sin rojo.
  const sinMargen = riesgo && gastoDiarioSeguro === 0
  return [
    {
      termino: 'Lo que puedes gastar',
      texto: sinMargen
        ? `Ni sin gastar nada llegas a tu cobro del ${fechaDia(proximoIngreso.fecha)} sin quedar en rojo: hay que mover o pausar un pago. Gastas ${enSoles(gastoDiarioActual)} al día.`
        : `Hasta ${enSoles(gastoDiarioSeguro)} al día y llegas a tu cobro del ${fechaDia(proximoIngreso.fecha)}. Gastas ${enSoles(gastoDiarioActual)} al día.`,
    },
    peorCaso(cliente),
    enRojo(cliente.riesgo),
    { termino: 'Los tips', texto: 'Cambios chicos. Tocas «Lo hago» y recalculo todo. Tú decides.' },
  ]
}

export function explicarQueViene(cliente) {
  const { riesgo } = cliente
  return [
    { termino: 'La línea', texto: 'Lo más probable, día a día.' },
    {
      termino: 'La franja de color',
      texto: cliente.ingresoVariable
        ? 'El rango posible. Se hace más ancha con los días.'
        : 'El rango posible. Es angosta porque tu sueldo llega fijo.',
    },
    { ...peorCaso(cliente), texto: 'El borde de abajo de la franja: tu mes malo.' },
    {
      termino: 'La línea roja',
      texto: riesgo
        ? `El cero. El punto rojo es tu día más justo, el ${fechaDia(riesgo.peorFecha)}: ${enSoles(riesgo.peorMonto)}.`
        : 'El cero. Tu franja no lo cruza antes de tu cobro.',
    },
  ]
}
