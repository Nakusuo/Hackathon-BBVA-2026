// Convierte el texto de una respuesta en bloques para pintarlo ordenado: párrafos, listas (líneas que empiezan con «- ») y cifras resaltadas.

// Montos en soles, porcentajes y plazos: lo que la persona busca con la vista en una respuesta.
const CIFRA = /((?:[-−]\s?)?S\/\s?[\d.,]*\d|\d+(?:[.,]\d+)?\s?%|\d+(?:[.,]\d+)?\s(?:meses|mes|días|dias|día|dia)\b)/g

export function partesDe(linea) {
  return linea
    .split(CIFRA)
    .map((trozo, i) => ({ texto: trozo, fuerte: i % 2 === 1 }))
    .filter((parte) => parte.texto !== '')
}

export function bloquesDe(texto) {
  const bloques = []
  for (const cruda of String(texto ?? '').split('\n')) {
    const linea = cruda.trim()
    if (!linea) continue
    const item = /^[-•]\s+/.test(linea)
    const partes = partesDe(linea.replace(/^[-•]\s+/, ''))
    const ultimo = bloques.at(-1)
    if (item && ultimo?.tipo === 'lista') ultimo.items.push(partes)
    else if (item) bloques.push({ tipo: 'lista', items: [partes] })
    else bloques.push({ tipo: 'parrafo', partes })
  }
  return bloques
}
