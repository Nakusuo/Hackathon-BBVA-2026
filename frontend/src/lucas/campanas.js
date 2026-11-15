// Campañas de ejemplo de un banco que integre a Lucas. Los aliados son inventados: nunca marcas reales.
// El catálogo es el mismo archivo que lee el agente (src/models/campanas.py): el chat y las pantallas ofrecen lo mismo.
import catalogo from '../../../data/catalogo_campanas.json' with { type: 'json' }
import { enSoles, fechaCorta } from '../formato.js'

export const CAMPANAS = catalogo.campanas

export function campanaPorId(id) {
  return CAMPANAS.find((c) => c.id === id) ?? null
}

// `texto` ya viene normalizado (minúsculas, sin tildes).
export function campanaPara(texto) {
  if (!texto) return null
  return CAMPANAS.find((c) => c.temas.some((t) => new RegExp(`\\b${t}s?\\b`).test(texto))) ?? null
}

export function beneficio(c) {
  return c.fijo ? `${enSoles(c.fijo)} de descuento` : `${c.porcentaje} % de descuento (hasta ${enSoles(c.tope)})`
}

export function ahorroCon(c, precio) {
  if (!precio) return 0
  return c.fijo ? Math.min(c.fijo, precio) : Math.min(Math.round((precio * c.porcentaje) / 100), c.tope)
}

export function cifrasDeCampana(c, precio) {
  const ahorro = ahorroCon(c, precio)
  if (!ahorro) return [{ etiqueta: `Descuento con ${c.aliado}`, valor: c.fijo ? enSoles(c.fijo) : `${c.porcentaje} %` }]
  return [
    { etiqueta: `Descuento con ${c.aliado}`, valor: enSoles(ahorro) },
    { etiqueta: 'Pagarías', valor: enSoles(precio - ahorro) },
  ]
}

// Se dice desde la primera oferta, no solo en el detalle: es un ejemplo y decide la persona.
const DE_EJEMPLO = 'Campaña de ejemplo, tú decides.'

// Una línea para sumar a otra respuesta: «Ojo: …». Un descuento es pagar menos, no ahorrar.
// `enElPlan`: lo que cambia la meta con el descuento, para que la pregunta quede al final.
export function avisoDeCampana(c, precio, enElPlan = '') {
  const ahorro = ahorroCon(c, precio)
  const cuanto = ahorro ? `: pagarías ${enSoles(ahorro)} menos` : ''
  const plan = enElPlan ? ` ${enElPlan}` : ''
  return `Ojo: tu banco tiene ${beneficio(c)} en ${c.rubro} con ${c.aliado}${cuanto}.${plan} ${DE_EJEMPLO} ¿Quieres más info?`
}

export function respuestaCampana(c, { precio = 0, marca = null } = {}) {
  if (!c) {
    const rubros = CAMPANAS.map((x) => x.corto).join(', ').replace(/, ([^,]+)$/, ' y $1')
    return {
      texto: `Ahora tu banco tiene campañas en ${rubros}. ¿Para qué es tu compra?`,
      cifras: [],
    }
  }
  const ahorro = ahorroCon(c, precio)
  const inicio = marca
    ? `Para eso no hay campaña. La que hay es con ${c.aliado}: ${beneficio(c)} en ${c.rubro}, ${c.condicion}.`
    : `Sí: con ${c.aliado} tu banco tiene ${beneficio(c)} en ${c.rubro}, ${c.condicion}.`
  const cierre = ahorro
    ? ` Pagarías ${enSoles(precio - ahorro)}, ${enSoles(ahorro)} menos. ${DE_EJEMPLO} ¿Quieres más info?`
    : ` ¿Cuánto cuesta? Te digo cuánto pagarías. ${DE_EJEMPLO}`
  return { texto: `${inicio}${cierre}`, cifras: cifrasDeCampana(c, precio) }
}

export function detalleCampana(c, precio = 0) {
  return {
    texto: `${c.aliado}: ${beneficio(c)} en ${c.rubro}, ${c.condicion}. Vale hasta el ${fechaCorta(c.hasta)} de ${c.hasta.slice(0, 4)}. Es una campaña de ejemplo: las condiciones reales las pone tu banco. Tú decides.`,
    cifras: [...cifrasDeCampana(c, precio), { etiqueta: 'Vigente hasta', valor: `${fechaCorta(c.hasta)} ${c.hasta.slice(0, 4)}` }],
  }
}
