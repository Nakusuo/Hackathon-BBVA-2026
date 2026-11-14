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
