// Qué muestra el panel Evidencia (HU-20, CP-SIS-48): primero el impacto en S/, luego cada técnica frente a
// su baseline y al final lo que empeora. Los textos son fijos; los números salen todos de `cifra`.
import { booleano, claves, cifra, cuenta, media, proporcion, proporcionCompleta, texto } from './cifras.js'

// Por debajo de 1 % de diferencia no se dice que uno gana.
export const MARGEN_PARECIDO = 0.01

export function veredicto(lucas, base, mejor) {
  const distancia = (v) => (typeof mejor === 'object' ? -Math.abs(v - mejor.objetivo) : mejor === 'mayor' ? v : -v)
  const a = distancia(lucas)
  const b = distancia(base)
  const escala = Math.max(Math.abs(lucas), Math.abs(base), Number.EPSILON)
  if (Math.abs(a - b) / escala < MARGEN_PARECIDO) return 'parecido'
  return a > b ? 'mejor' : 'peor'
}

const ic = (archivo, ...ruta) => [cifra(archivo, ...ruta, 'ic95', 0), cifra(archivo, ...ruta, 'ic95', 1)]

export function impactoPorCliente() {
  const dif = ['diferencias', 'lucas_vs_nada']
  return {
    meses: cifra('impacto', 'meses'),
    filas: [
      {
        id: 'dias-rojo',
        nombre: 'Días en rojo evitados por cliente al mes',
        formato: 'decimal',
        valor: cifra('impacto', ...dif, 'dias_rojo_evitados_por_cliente_mes', 'media'),
        intervalo: ic('impacto', ...dif, 'dias_rojo_evitados_por_cliente_mes'),
      },
      {
        id: 'colchon',
        nombre: 'Colchón adicional al final del periodo',
        formato: 'soles',
        valor: cifra('impacto', ...dif, 'colchon_adicional_soles', 'media'),
        intervalo: ic('impacto', ...dif, 'colchon_adicional_soles'),
      },
      {
        id: 'intereses',
        nombre: 'Intereses evitados por cubrir el hueco, al mes',
        formato: 'soles-centimos',
        valor: cifra('impacto', ...dif, 'intereses_evitados_soles_por_mes', 'media'),
        intervalo: ic('impacto', ...dif, 'intereses_evitados_soles_por_mes'),
      },
    ],
  }
}

const ESTRATEGIAS = [
  { id: 'nada', nombre: 'No hacer nada' },
  { id: 'diez_fijo', nombre: 'Apartar 10 % fijo' },
  { id: 'diez_fijo_ajustado', nombre: 'Apartar 10 % sin quedar en rojo' },
  { id: 'lucas', nombre: 'Lucas' },
]

export function estrategias() {
  return ESTRATEGIAS.map((e) => ({
    ...e,
    diasRojo: cifra('impacto', 'tabla', e.id, 'dias_en_rojo_por_cliente_mes'),
    colchon: cifra('impacto', 'tabla', e.id, 'colchon_final_soles'),
  }))
}

export function supuestosImpacto() {
  return [
    { clave: 'tasa', nombre: 'Interés mensual por cubrir el hueco', formato: 'pct', valor: cifra('impacto', 'supuestos', 'tasa_mensual_por_cubrir_el_hueco') },
    { clave: 'umbral', nombre: 'Probabilidad de rojo que dispara la alerta', formato: 'decimal', valor: cifra('impacto', 'supuestos', 'umbral_alerta_p_rojo') },
    { clave: 'dias_de_alerta', nombre: 'Días de alerta antes del rojo', formato: 'entero', valor: cifra('impacto', 'supuestos', 'dias_de_alerta') },
  ]
}

export function valorBanco() {
  const c = ['lectura_conservadora']
  return {
    netoPorUsuario: cifra('valor', ...c, 'neto_por_usuario_sin_mas_consumo'),
    consumoParaPagarse: cifra('valor', ...c, 'mas_consumo_necesario_para_pagarse'),
    margen: cifra('valor', 'supuestos', 'margen_anual_sobre_saldo_apartado'),
  }
}

function fila(id, tecnica, metrica, formato, mejor, lucas, base, extra = {}) {
  return { id, tecnica, metrica, formato, mejor, lucas, base, ...extra, veredicto: veredicto(lucas.valor, base.valor, mejor) }
}

const pron = (...r) => cifra('principal', 'pronostico', ...r)
const seg = (...r) => cifra('principal', 'segmentacion', ...r)
const recup = (config, metrica) => cifra('rag', 'recuperacion', config, metrica)

export function tecnicas() {
  return [
    fila('saldo-30d', 'Pronóstico de saldo a 30 días', 'Error medio (MAE)', 'soles', 'menor',
      { nombre: 'LightGBM', ...pron('saldo_30d', 'lightgbm_optimizado', 'mae_s') },
      { nombre: 'Promedio de 3 meses', ...pron('saldo_30d', 'ma3_baseline_plan', 'mae_s') },
      { n: pron('origenes', 'prueba') }),
    fila('banda', 'Banda del pronóstico', 'Cobertura de la banda del 80 %', 'pct', { objetivo: 0.8 },
      { nombre: 'LightGBM', ...pron('saldo_30d', 'lightgbm_optimizado', 'cobertura_80') },
      { nombre: 'Promedio de 3 meses', ...pron('saldo_30d', 'ma3_baseline_plan', 'cobertura_80') }),
    fila('rojo', 'Anticipar el rojo a 30 días', 'PR-AUC', 'decimal3', 'mayor',
      { nombre: 'LightGBM calibrado', ...pron('rojo_30d_anticipacion', 'lightgbm_calibrado', 'pr_auc') },
      { nombre: 'Regla de saldo bajo', ...pron('rojo_30d_anticipacion', 'saldo_bajo_regla', 'pr_auc') },
      { n: pron('rojo_30d_anticipacion', 'n') }),
    fila('dia-riesgo', 'Día de riesgo', 'Error medio en días', 'decimal', 'menor',
      { nombre: 'LightGBM', ...pron('dia_de_riesgo', 'lightgbm', 'mae_dias') },
      { nombre: 'Tendencia lineal', ...pron('dia_de_riesgo', 'ma_lineal', 'mae_dias') },
      { n: pron('dia_de_riesgo', 'lightgbm', 'n') }),
    fila('segmentos', 'Segmentación', 'Silueta de Gower', 'decimal3', 'mayor',
      { nombre: 'K-Prototypes', ...seg('silueta_gower', 'kprototypes') },
      { nombre: 'Reglas 2 × 2', ...seg('silueta_gower', 'reglas_2x2') }),
    fila('frio', 'Arranque en frío', 'Precisión del nivel', 'pct', 'mayor',
      { nombre: 'Con lo declarado', ...seg('arranque_en_frio_precision') },
      { nombre: 'Clase mayoritaria', ...seg('referencia_clase_mayoritaria') }),
    fila('glosa', 'Glosa a categoría', 'F1 macro', 'decimal3', 'mayor',
      { nombre: 'TF-IDF + lineal', ...cifra('clasificacion', 'glosa_a_categoria', 'tfidf_char_sgd_lineal', 'f1_macro') },
      { nombre: 'Diccionario', ...cifra('clasificacion', 'glosa_a_categoria', 'diccionario', 'f1_macro') },
      { n: cifra('clasificacion', 'glosa_a_categoria', 'n_prueba') }),
    fila('recurrentes', 'Pagos recurrentes', 'F1', 'decimal3', 'mayor',
      { nombre: 'Periodicidad y monto', ...cifra('clasificacion', 'recurrentes', 'periodicidad_y_monto', 'f1') },
      { nombre: 'Mismo comercio 3 veces', ...cifra('clasificacion', 'recurrentes', 'baseline_mismo_comercio_3_veces', 'f1') },
      { n: cifra('clasificacion', 'recurrentes', 'n_clientes') }),
    fila('atipicos', 'Gastos atípicos', 'Precisión en k', 'decimal3', 'mayor',
      { nombre: 'Isolation Forest', ...cifra('clasificacion', 'atipicos', 'isolation_forest', 'precision_en_k') },
      { nombre: 'Z-score robusto', ...cifra('clasificacion', 'atipicos', 'zscore_robusto', 'precision_en_k') }),
    fila('sentimiento', 'Sentimiento (frases escritas a mano)', 'F1 macro', 'decimal3', 'mayor',
      { nombre: 'TF-IDF + regresión', ...cifra('clasificacion', 'sentimiento', 'escritas_a_mano', 'tfidf_lr_f1') },
      { nombre: 'Léxico', ...cifra('clasificacion', 'sentimiento', 'escritas_a_mano', 'lexico_f1') },
      {
        n: cifra('clasificacion', 'sentimiento', 'escritas_a_mano', 'n'),
        nota: 'El léxico se armó viendo estas mismas frases, así que su cifra es optimista.',
      }),
    fila('rag', 'RAG: encontrar el fragmento correcto', 'Recall@4', 'pct', 'mayor',
      { nombre: 'Híbrido + filtro de módulo', ...recup('hibrido + filtro de modulo', 'recall@4') },
      { nombre: 'Solo denso', ...recup('denso', 'recall@4') },
      { n: recup('denso', 'n') }),
    fila('rag-mrr', 'RAG: posición del fragmento correcto', 'MRR', 'decimal3', 'mayor',
      { nombre: 'Híbrido + filtro de módulo', ...recup('hibrido + filtro de modulo', 'mrr') },
      { nombre: 'Solo denso', ...recup('denso', 'mrr') },
      { n: recup('denso', 'n') }),
  ]
}

const ag = (archivo, metrica) => cifra(archivo, 'agente_unico', 'resumen', metrica)

// En el agente la base es responder por plantillas. Gemini se valida en la corrida de QA (eval/qa_agente.py):
// preguntas con el perfil del cliente y pedidos adversos. Son muestras distintas: cada fila lleva el n de cada lado.
// Esa corrida no mide el ruteo, así que no se compara. Los pedidos prohibidos los corta el filtro previo, sin LLM,
// en las dos corridas y con criterios distintos: se muestran aparte y sin veredicto.
const QA = 'qaAgente'
export function agente() {
  const gemini = (medida) => ({ nombre: 'Gemini', ...medida })
  const plantillas = (clave) => ({ nombre: 'Plantillas', ...ag('agentePlantillas', clave) })
  const nPerfil = cuenta(QA, 'perfil')
  const nAdversas = cuenta(QA, 'adversas')
  const nPlantillas = ag('agentePlantillas', 'n')
  const conN = { n: nPerfil, nBase: nPlantillas }
  return {
    modelo: texto(QA, 'resumen', 'modelo'),
    reloj: texto(QA, 'resumen', 'reloj_fijo'),
    nPerfil,
    nAdversas,
    nPlantillas,
    filas: [
      fila('sin-inventar', 'Agente', 'Respuestas sin cifras inventadas', 'pct', 'mayor',
        gemini(proporcion(QA, 'perfil', 'sin_cifras_inventadas')),
        plantillas('respuestas_sin_cifras_inventadas'),
        conN),
      fila('tu-decides', 'Agente', 'Respuestas que cierran con «Tú decides»', 'pct', 'mayor',
        gemini(proporcion(QA, 'perfil', 'cierra_con_tu_decides')),
        plantillas('cierra_con_tu_decides'),
        conN),
      fila('latencia', 'Agente', 'Latencia media', 'segundos', 'menor',
        gemini(media(QA, 'perfil', 'segundos')),
        plantillas('latencia_media_s'),
        {
          ...conN,
          nota: 'Las preguntas no son las mismas: las de Gemini pasan todas por el LLM; las plantillas nunca lo llaman y además incluyen pedidos que se cortan antes. La dirección vale; el tamaño de la diferencia, no.',
        }),
    ],
    prohibidos: {
      qa: proporcionCompleta(QA, 'adversas'),
      nQa: nAdversas,
      plantillas: ag('agentePlantillas', 'pedidos_prohibidos_rechazados'),
    },
    idiomas: {
      ingles: booleano(QA, 'resumen', 'idiomas', 'ingles'),
      quechua: booleano(QA, 'resumen', 'idiomas', 'quechua'),
    },
    filtro: {
      aceptadas: cifra('rag', 'filtro_relevancia', 'con_los_umbrales_actuales', 'con_respuesta_aceptadas'),
      rechazadas: cifra('rag', 'filtro_relevancia', 'con_los_umbrales_actuales', 'fuera_rechazadas'),
      nCon: cifra('rag', 'filtro_relevancia', 'n_con_respuesta'),
      nFuera: cifra('rag', 'filtro_relevancia', 'n_fuera'),
    },
  }
}

const NOMBRES_PERTURBACION = {
  ruido_10pct_en_historial: 'Ruido de 10 % en el historial',
  faltantes_extra_20pct: '20 % más de datos faltantes',
  clientes_con_cambio_de_patron: 'Solo clientes que cambian de patrón',
  clientes_sin_cambio_de_patron: 'Solo clientes sin cambio de patrón',
}
// Estas dos no alteran datos: miden el error en un subgrupo frente al de todos.
const SUBGRUPOS = ['clientes_con_cambio_de_patron', 'clientes_sin_cambio_de_patron']

export function perturbaciones() {
  const original = pron('perturbaciones', 'original', 'mae_s')
  const pruebas = claves('principal', 'pronostico', 'perturbaciones')
    .filter((k) => k !== 'original')
    .map((k) =>
      fila(k, NOMBRES_PERTURBACION[k] ?? k, 'Error medio (MAE)', 'soles', 'menor',
        { nombre: SUBGRUPOS.includes(k) ? 'En el subgrupo' : 'Con la perturbación', ...pron('perturbaciones', k, 'mae_s') },
        { nombre: SUBGRUPOS.includes(k) ? 'Todos' : 'Sin perturbar', ...original },
        { subgrupo: SUBGRUPOS.includes(k) }),
    )
  const evento = ['evento_no_visto_confinamiento']
  return {
    pruebas,
    eventoNoVisto: fila('evento', 'Confinamiento fuera del entrenamiento', 'Error medio (MAE)', 'soles', 'menor',
      { nombre: 'LightGBM', ...pron(...evento, 'lightgbm_sin_variables_de_evento', 'mae_s') },
      { nombre: 'Promedio de 3 meses', ...pron(...evento, 'ma3', 'mae_s') }),
    conTexto: fila('texto', 'Agregar texto de los movimientos al pronóstico', 'Error medio (MAE)', 'soles', 'menor',
      { nombre: 'Con texto', ...pron('texto_en_el_pronostico', 'con_texto', 'mae_s') },
      { nombre: 'Sin texto', ...pron('texto_en_el_pronostico', 'sin_texto', 'mae_s') },
      {
        diferencia: {
          nombre: 'Mejora del MAE relativo al ingreso',
          media: pron('texto_en_el_pronostico', 'mejora_mae_rel', 'media'),
          intervalo: ic('principal', 'pronostico', 'texto_en_el_pronostico', 'mejora_mae_rel'),
        },
      }),
    equidad: claves('principal', 'pronostico', 'equidad_por_grupo')
      .filter((g) => booleano('principal', 'pronostico', 'equidad_por_grupo', g, 'brechas', 'alerta').valor)
      .map((g) => ({
        grupo: g,
        razon: pron('equidad_por_grupo', g, 'brechas', 'razon_mae'),
        peor: nombreGrupo(g, texto('principal', 'pronostico', 'equidad_por_grupo', g, 'brechas', 'peor_grupo_mae').valor),
      })),
  }
}

// Los segmentos vienen numerados; su nombre de nivel está en segmentacion › niveles.
function nombreGrupo(grupo, valor) {
  return grupo === 'segmento' ? texto('principal', 'segmentacion', 'niveles', valor).valor : valor
}
