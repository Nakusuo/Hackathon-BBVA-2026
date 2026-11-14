# QA de analítica e IA: puerta de calidad

Generado por `eval/puerta_de_calidad.py` el 2026-11-14T15:52:19 (reloj del agente: 2026-11-14). Estados: **PASS** cumple; **WARN** conocido y documentado, no bloquea; **FAIL** hay que corregirlo; **NOT RUN** no se pudo verificar y se dice por qué.

**Resultado: 34 PASS · 6 WARN · 0 FAIL · 3 NOT RUN** (de 43 verificaciones, en 65.6 s).

## Pruebas

| # | Qué se verifica | Estado | Detalle |
|---|---|---|---|
| P1 | Suite de pruebas de analitica e IA (pytest, sin red ni Gemini) | **PASS** | 374 passed in 33.93s |
| P1b | Pruebas del agente del producto (PR #5, Jeffrey) en el arbol unido: no son de esta rama, se reportan aparte | **NOT RUN** | no hay pruebas del agente del producto en esta rama |
| P2 | Codigo sin importaciones sin uso, nombres sin definir, errores de sintaxis ni caracteres de control (ruff) | **PASS** |  |

## Modelos

| # | Qué se verifica | Estado | Detalle |
|---|---|---|---|
| M1 | Segmentacion: estable (ARI >= 0.60), silueta positiva, sin segmentos diminutos y mejor que las reglas 2x2 | **PASS** | k=3, estabilidad 0.744, silueta 0.205, segmento minimo 68 |
| M2 | Saldo a 30 dias: banda al 80 % con cobertura entre 0.77 y 0.83 y menos error que los dos baselines | **PASS** | cobertura 0.806 (objetivo 0.80), error 0.43 frente a 0.72 |
| M3 | Alerta de rojo: bien calibrada (ECE <= 0.02), ROC-AUC >= 0.95 y mejor que la regla simple y que el azar | **PASS** | PR-AUC 0.594 (azar 0.044), ROC-AUC 0.977, ECE 0.0053 |
| M4 | Dia de riesgo: menos error que los baselines | **PASS** | error 5.4 dias; acierto a +-3 dias 43% |
| M5 | Proyeccion mensual: cobertura al 80 % de ingresos, gastos y neto entre 0.75 y 0.85 en los 6 horizontes | **PASS** | 18 coberturas dentro de [0.75, 0.85]; la menor es 0.788 |
| M6 | Equidad por segmento: brecha de cobertura <= 0.05 y razon de error entre segmentos | **WARN** | la cobertura es pareja (brecha 0.018) pero el error del peor segmento (0) es 1.58 veces el del mejor: el ingreso irregular es mas dificil de pronosticar. Documentado. |
| M7 | Glosas, recurrentes y atipicos: cada modelo elegido supera a su alternativa simple | **PASS** | glosa F1 0.894, recurrentes F1 0.933, atipicos 0.750 |
| M8 | Sentimiento: el modelo entrenado generaliza a frases escritas a mano | **WARN** | no: F1 0.73 con 24 frases contra 1.00 en plantillas. Documentado; no esta en produccion. |
| M9 | Politica de ahorro: reduce los dias en rojo frente a no hacer nada con IC95 que excluye 0 | **PASS** | 0.24 dias en rojo evitados por cliente al mes (IC95 0.19 a 0.30) |
| M10 | Politica de ahorro: Lucas forma al menos tanto colchon como ahorrar 10 % fijo ajustado | **WARN** | el 10 % fijo ajustado forma 2.7 meses mas de colchon que Lucas. Hallazgo abierto, documentado. |
| M11 | Programa de puntos: ninguna tasa de puntos por consumo supera el tope de reinversion de la comision | **PASS** | costo sobre la comision por nivel: {'luchador': 0.0, 'aprendiz': 0.05, 'constructor': 0.1, 'maestro': 0.2, 'campeon': 0.3}, tope 30% |
| M12 | Programa de puntos: rentable sin depender de consumo nuevo | **WARN** | sin consumo nuevo pierde S/ 5.52 por usuario al anio; se paga con 6.9% mas de consumo elegible. Necesita piloto. |
| M13 | Parametros de los eventos simulados (retiros de AFP, bonos, covid, Nino): verificados en fuente | **WARN** | parametros de eventos: 1 verificado, 4 parciales y 13 supuestos. Declarados en el YAML; hay que verificarlos antes de afirmarlos. |
| M14 | Datos sinteticos: informe de calidad y trazabilidad presentes y sin fallas reportadas | **PASS** | informe de calidad presente con trazabilidad (semilla, huella de parametros) |

## Conexiones

| # | Qué se verifica | Estado | Detalle |
|---|---|---|---|
| C1 | BCRP en vivo: tasa_referencia (API, al dia, con su fecha) | **PASS** | 4.25 al 2026-10-01 (API en vivo, 44 dias) |
| C2 | BCRP en vivo: tipo_cambio_venta (API, al dia, con su fecha) | **PASS** | 3.406 al 2026-11-12 (API en vivo, 2 dias) |
| C3 | BCRP en vivo: ipc_var_mensual (API, al dia, con su fecha) | **PASS** | 0.5715 al 2026-10-01 (API en vivo, 44 dias) |
| C4 | ENFEN en vivo: el RAG tiene el ultimo comunicado publicado | **PASS** | ultimo comunicado publicado: N.o 20; el RAG tiene hasta el N.o 20 |
| C5 | Ollama local con el modelo de embeddings del RAG | **PASS** | nomic-embed-text responde (768 dimensiones); modelos: qwen2.5:7b, qwen2.5:3b, nomic-embed-text:latest |
| C6 | Agente configurado con Gemini y politica de ahorro; clave solo en .env | **PASS** | LLM_PROVIDER=gemini, LLM_USO=ahorro (Gemini con politica de ahorro de tokens); la clave esta solo en .env |
| C7 | Gemini responde en vivo | **PASS** | gemini-3.5-flash-lite responde (HTTP 200) |
| C8 | Traduccion es->en con cifras y nombres protegidos | **PASS** | es->en por gemini en 1.77 s, cifras intactas |
| C9 | Google Cloud Translation | **NOT RUN** | no hay GOOGLE_TRANSLATE_API_KEY (la clave de Gemini no se usa con otras APIs de Google). Se traduce con Gemini. |
| C10 | Calidad del quechua revisada por un hablante nativo | **NOT RUN** | no hay revision de un hablante nativo; el aviso al usuario lo dice |
| C11 | RAG: indice consistente, documentos sin alterar (hash) y solo fuentes de nivel A | **PASS** | 3833 fragmentos = 3833 vectores; 21 documentos con hash verificado; solo licencia nivel A |
| C12 | RAG: las consultas clave de CTS, retiro de CTS y TCEA recuperan su fuente oficial | **PASS** | 3 de 3 consultas clave recuperan su fuente oficial con similitud >= 0.70 |
| C13 | Datos vivos: registrar, no duplicar, rechazar lo invalido, resumir y borrar | **PASS** | registrar, no duplicar, rechazar lo invalido, resumir y borrar |
| C14 | Calendario laboral: reglas vigentes y verificadas recientemente | **PASS** | reglas verificadas el 2026-11-14; libre disposicion hoy 100% (47 dias restantes) |

## Agente

| # | Qué se verifica | Estado | Detalle |
|---|---|---|---|
| G1 | Evaluacion con plantillas (reproducible): ruteo >= 0.95, cero cifras inventadas, cero frases prohibidas, todos los pedidos prohibidos rechazados | **PASS** | 69 preguntas x 2 arquitecturas: ruteo 1.000, 0 cifras inventadas, 0 frases prohibidas, 100% de pedidos prohibidos rechazados |
| G2 | QA con Gemini real (una sola corrida): perfil, calendario, premisa falsa, datos vivos, idiomas y adversarios | **PASS** | Gemini real: perfil 11/11, adversas 16/16, datos vivos y idiomas OK, 17 llamadas y 44,571 tokens de entrada |
| G3 | Diagramas de nodos del agente generados, con rutas relativas | **PASS** | los dos diagramas de nodos existen y se citan con ruta relativa |
| G4 | No hay metricas de Gemini desfasadas (las anteriores a la seguridad se retiraron) | **PASS** | no queda el JSON de Gemini anterior al endurecimiento de seguridad |

## Seguridad

| # | Qué se verifica | Estado | Detalle |
|---|---|---|---|
| S1 | Ninguna clave de API en lo versionado | **PASS** | 170 archivos versionados sin claves de API |
| S2 | .env no versionado e ignorado | **PASS** | .env ignorado y no versionado |
| S3 | Sin rutas absolutas de ninguna laptop en codigo, parametros, metricas ni documentos | **PASS** | 99 archivos propios sin rutas absolutas |
| S4 | Ninguna mencion a un banco real en codigo, datos, metricas ni documentos propios | **PASS** | ninguna mencion a un banco real en lo propio (la entidad es inventada: Banco Kawsay) |
| S5 | Sin archivos pesados ni datos generados en el repositorio (solo data/sample), salvo la carga temporal documentada | **WARN** | 56 archivos de data/generado cargados A PROPOSITO para la integracion final (ver _manifiesto.json, todo sintetico); quitarlos al terminar con: git rm -r --cached data/generado |

## Reproducibilidad

| # | Qué se verifica | Estado | Detalle |
|---|---|---|---|
| R1 | Todo lo que importa el codigo esta en requirements-analitica.txt (un companero puede recrear el entorno) | **PASS** | las 22 bibliotecas de terceros que importa el codigo estan en requirements-analitica.txt |
| R2 | Nada desfasado: cada evaluacion corresponde al codigo actual y cada informe a las metricas actuales (huella de contenido) | **PASS** | las evaluaciones corresponden al codigo actual y los informes a las metricas actuales (huella de contenido) |
| R3 | Las fuentes oficiales del RAG se consultaron en los ultimos 30 dias | **PASS** | 21 fuentes del RAG, ultima consulta hace 0 dias |

## Lo que NO se pudo verificar

Esta lista nunca va vacía: lo que no se verificó se dice.

- Calidad del quechua: no la revisó un hablante nativo; la respuesta lleva un aviso.
- Google Cloud Translation: no hay clave propia (la de Gemini no se usa con otras APIs); se traduce con Gemini.
- Datos reales de un banco: todo se evaluó con datos sintéticos; con datos reales las métricas serán otras.
- Sentimiento: no hay un set independiente de frases etiquetadas por personas (solo 24 escritas a mano por el equipo).
- Parámetros de los eventos simulados (retiros de AFP, bonos, covid, Niño): solo 1 de 18 está marcado como verificado; el resto son parciales o supuestos del equipo.
- Serie diaria del pronóstico: el modelo está calibrado en el día 30 y en el día de riesgo; una serie de 30 días con banda al 80 % por día no está entrenada ni validada.
- Redacción con juez LLM: JUEZ_LLM está apagado por ahorro de tokens; la verificación de cifras es determinista, y la calidad de redacción de Gemini se revisó en una sola corrida de QA.
- Carga en producción: se midió el costo por consulta en esta laptop, no el rendimiento con miles de usuarios simultáneos.
- Fuente de la libre disposición de la CTS después de 2026: se verificó la Ley 32322 (texto oficial); cualquier cambio posterior a 2026-11-14 no se conoce hasta volver a contrastarla.
