// Recharts redondea el eje a -1000 por un rojo pequeño y el cero queda perdido; las marcas van a mano.
export function marcasDelEje(datos) {
  const minimo = Math.min(0, ...datos.map((p) => p.banda[0]))
  const maximo = Math.max(0, ...datos.map((p) => p.banda[1]))
  const piso = Math.floor(minimo / 250) * 250
  const paso = maximo > 1500 ? 1000 : 500
  const techo = Math.max(paso, Math.ceil(maximo / paso) * paso)
  const marcas = new Set([piso])
  for (let v = 0; v <= techo; v += paso) marcas.add(v)
  return { dominio: [piso, techo], marcas: [...marcas] }
}
