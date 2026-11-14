import { Bus, Coffee, DotsThree, FilmSlate, ForkKnife, Martini, Repeat } from '@phosphor-icons/react'

export const ICONOS_CATEGORIA = {
  comida: ForkKnife,
  transporte: Bus,
  salidas: Martini,
  hormiga: Coffee,
  suscripciones: Repeat,
  entretenimiento: FilmSlate,
  otros: DotsThree,
}

// Diferencias de hasta S/ 5 no se señalan: con montos así cualquier mes varía un poco.
export const UMBRAL = 5

export function diferenciaConPromedio(categoria) {
  const diferencia = Math.round(categoria.total - categoria.promedio3m)
  return Math.abs(diferencia) <= UMBRAL ? 0 : diferencia
}

// El gráfico circular se lee bien hasta 6 partes: las categorías chicas se juntan en «Otros».
export function partesDelGrafico(categorias, maximo = 6) {
  if (categorias.length <= maximo) return categorias
  const grandes = categorias.slice(0, maximo - 1)
  const resto = categorias.slice(maximo - 1)
  return [
    ...grandes,
    {
      id: 'resto',
      nombre: 'Otros',
      total: resto.reduce((s, c) => s + c.total, 0),
      promedio3m: resto.reduce((s, c) => s + c.promedio3m, 0),
    },
  ]
}

// Porcentajes enteros que siempre suman 100 (método del mayor resto): redondear cada parte por
// separado puede dar 99 o 101, y el gráfico se lee como si faltara o sobrara algo.
export function porcentajes(partes) {
  const total = partes.reduce((s, p) => s + p.total, 0)
  if (!total) return partes.map(() => 0)
  const exactos = partes.map((p) => (p.total / total) * 100)
  const enteros = exactos.map(Math.floor)
  const faltan = 100 - enteros.reduce((s, n) => s + n, 0)
  exactos
    .map((x, i) => ({ i, resto: x - enteros[i] }))
    .sort((a, b) => b.resto - a.resto || a.i - b.i)
    .slice(0, faltan)
    .forEach(({ i }) => enteros[i]++)
  return enteros
}
