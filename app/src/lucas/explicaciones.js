// «Explícamelo fácil»: la misma pantalla en palabras simples. Solo repite cifras que ya están en ella (HU-23),
// por eso cada texto se arma con los mismos campos de la vista y nunca calcula nada nuevo.
import { enSoles, fechaDia, textoDiasEnRojo } from '../formato.js'

function peorCaso(cliente) {
  return {
    termino: 'Peor caso',
    texto: cliente.ingresoVariable
      ? 'Es lo que pasaría si el mes te sale un poco peor de lo normal: gastas algo más o tus clientes te pagan menos. No es lo que creo que pasará; es el límite de abajo, para que nada te agarre por sorpresa.'
      : 'Es lo que pasaría si el mes te sale un poco peor de lo normal, por ejemplo si gastas algo más. Como tu sueldo llega fijo, tu peor caso queda cerca de lo más probable.',
  }
}

function enRojo(riesgo) {
  return {
    termino: 'Quedar en rojo',
    texto: riesgo
      ? `Es que tu cuenta baje de cero. En el peor caso te pasaría ${textoDiasEnRojo(riesgo).toLowerCase()}, antes de que cobres.`
      : 'Es que tu cuenta baje de cero. Ahora no te pasa antes de tu cobro, ni en el peor caso.',
  }
}

export function explicarResumen(cliente) {
  const { gastoDiarioSeguro, gastoDiarioActual, proximoIngreso } = cliente
  const ritmo =
    gastoDiarioActual > gastoDiarioSeguro
      ? `Hoy gastas ${enSoles(gastoDiarioActual)} al día: más de lo que te alcanza.`
      : `Hoy gastas ${enSoles(gastoDiarioActual)} al día, dentro de lo que te alcanza.`
  return [
    {
      termino: 'Lo que puedes gastar',
      texto: `Si gastas hasta ${enSoles(gastoDiarioSeguro)} por día, llegas a tu cobro del ${fechaDia(proximoIngreso.fecha)} con plata en la cuenta, aunque el mes salga peor. ${ritmo}`,
    },
    peorCaso(cliente),
    enRojo(cliente.riesgo),
    {
      termino: 'Los tips',
      texto:
        'Son cambios chicos. Si tocas «Lo hago», vuelvo a calcular todo con ese cambio: el aviso, lo que puedes gastar y lo que puedes apartar. Nada sale de tu cuenta: tú decides si lo haces.',
    },
  ]
}

export function explicarQueViene(cliente) {
  const { riesgo } = cliente
  return [
    {
      termino: 'La línea',
      texto: 'Es lo más probable: cuánta plata tendrías cada día si todo sigue como siempre.',
    },
    {
      termino: 'La franja de color',
      texto: cliente.ingresoVariable
        ? 'Es el rango posible. Se hace más ancha con los días y da un salto en cada cobro, porque tus clientes no siempre te pagan lo mismo.'
        : 'Es el rango posible. Es angosta porque tu sueldo llega fijo: solo cambia lo que gastas día a día.',
    },
    { ...peorCaso(cliente), texto: `Es el borde de abajo de la franja. ${peorCaso(cliente).texto}` },
    {
      termino: 'La línea roja',
      texto: riesgo
        ? `Marca el cero. El punto rojo es tu día más justo, el ${fechaDia(riesgo.peorFecha)}: ahí, en el peor caso, tendrías ${enSoles(riesgo.peorMonto)}.`
        : 'Marca el cero. Tu franja no la cruza antes de tu cobro: llegas sin quedar en rojo.',
    },
  ]
}
