# QA de analítica e IA: puerta de calidad

Generado por `eval/puerta_de_calidad.py` el 2026-11-14T23:27:27 (reloj del agente: 2026-11-14). Estados: **PASS** cumple; **WARN** conocido y documentado, no bloquea; **FAIL** hay que corregirlo; **NOT RUN** no se pudo verificar y se dice por qué.

**Resultado: 52 PASS · 3 WARN · 0 FAIL · 3 NOT RUN** (de 58 verificaciones, en 122.0 s).

## Pruebas

| # | Qué se verifica | Estado | Detalle |
|---|---|---|---|
| P1 | Suite de pruebas de analitica e IA (pytest, sin red ni Gemini) | **PASS** | 602 passed, 1 skipped in 89.58s (0:01:29) |
| P1b | Pruebas del agente del producto (PR #5, Jeffrey): no estan en esta rama; se corren en la rama develop al integrar todo (proximo paso) | **NOT RUN** | no hay pruebas del agente del producto en esta rama |
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
| M8 | Sentimiento: el modelo elegido supera al lexico y al azar en un set independiente del codigo y de las plantillas | **PASS** | set independiente de 140 frases: TF-IDF+LR F1 0.47, lexico 0.31, azar 0.25. No esta en produccion (el texto no mejora el pronostico) y el set lo escribio un LLM, no personas |
| M9 | Politica de ahorro: reduce los dias en rojo frente a no hacer nada con IC95 que excluye 0 | **PASS** | 0.24 dias en rojo evitados por cliente al mes (IC95 0.19 a 0.30) |
| M10 | Politica recomendada (Lucas + ahorro automatico): forma al menos tanto colchon como el 10 % fijo ajustado y evita mas dias en rojo, con IC95 sobre cero | **PASS** | Lucas + ahorro automatico forma 4.91 meses de colchon frente a 4.76 del 10 % ajustado y evita 0.24 dias en rojo mas al mes (IC95 sobre 0). Lucas solo forma 2.02 porque no obliga a apartar |
| M11 | Programa de puntos: ninguna tasa de puntos por consumo supera el tope de reinversion de la comision | **PASS** | costo sobre la comision por nivel: {'luchador': 0.0, 'aprendiz': 0.05, 'constructor': 0.1, 'maestro': 0.2, 'campeon': 0.3}, tope 30% |
| M12 | Programa de puntos: rentable sin depender de consumo nuevo | **WARN** | solo con lo medido pierde S/ 5.52 por usuario al anio y no se paga nunca; se paga con 6.9% mas de consumo o con 3.3% mas de ahorro apartado. Proyeccion a 5 anios (supuestos del equipo): se paga en el anio 1 (prudente), 1 (base) y 1 (optimista). Aceptado por el equipo: lo decide un piloto con grupo de control. |
| M13 | Eventos simulados (retiros de AFP, bonos, covid, Nino): cada parametro declara su estado (verificado, parcial o supuesto) y su fuente | **PASS** | 6 eventos con estado y fuente declarados (0 verificado, 2 parcial, 4 supuesto). Son parametros de una simulacion sobre datos sinteticos: los supuestos estresan los modelos, no se presentan como hechos (criterio aceptado por el equipo) |
| M14 | Datos sinteticos: informe de calidad y trazabilidad presentes y sin fallas reportadas | **PASS** | informe de calidad presente con trazabilidad (semilla, huella de parametros) |
| M15 | Serie diaria del pronostico (contrato de la API): 30 dias, cobertura 0.75 a 0.86 en cada dia, mejor que las dos lineas base y coincide con el modelo de 30 dias | **PASS** | 30 dias con banda al 80 %: cobertura entre 0.791 y 0.860, error 0.29 frente a 0.33 (recta) y 0.44 (promedio movil); el dia 30 es el modelo validado |
| M16 | Programa de puntos a futuro: la proyeccion multianual cuadra con la lectura de un anio y sus escenarios estan ordenados | **PASS** | la proyeccion a varios anios arranca en S/ -5.52, igual que la lectura de un anio, y los escenarios se ordenan (acumulado a 5 anios: S/ -19, S/ 128, S/ 283, S/ 612); son supuestos del equipo |
| M17 | Prueba de estres del diseno: apartar dinero bloqueado sin recortar el gasto empeora la caja (por eso Lucas no lo hace) | **PASS** | apartar dinero bloqueado sin recortar el gasto deja 6.2 dias en rojo al mes (Lucas: 0.59): por eso Lucas usa una reserva que se puede usar y metas voluntarias |
| M18 | Otra muestra del generador (otra semilla, sin reentrenar): cobertura entre 0.72 y 0.88, gana a los baselines y la serie diaria no baja de 0.70 | **PASS** | 500 clientes nuevos (semilla 2027), sin reentrenar: cobertura 0.772, error 0.417 frente a 0.707 (promedio movil) y 0.749 (estructural); serie diaria 0.750 a 0.806 |

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
| C8 | Traduccion es->en con cifras y nombres protegidos | **PASS** | es->en por gemini en 1.72 s, cifras intactas |
| C9 | Google Cloud Translation: el proveedor cumple el contrato publico de la API v2 (respuestas simuladas) | **PASS** | 7 pruebas del proveedor contra el contrato publico de la API v2 (cabecera de clave, cuerpo q/source/target/format, respuesta, marcadores, errores, caida a Gemini), contrastado con su documentacion oficial. No se llamo a la API real |
| C9b | Google Cloud Translation: llamada real con clave (proximo paso) | **NOT RUN** | proximo paso: no hay GOOGLE_TRANSLATE_API_KEY propia (una clave de Gemini da 401 en esa API). El contrato esta probado con respuestas simuladas y se traduce con Gemini. |
| C10 | Quechua: la traduccion se parece a las referencias humanas de FLORES-200 mas que el texto sin traducir | **PASS** | FLORES-200 quechua de Ayacucho, 60 oraciones por sentido: es->qu chrF 34.2 (IC95 desde 31.6; piso de copiar el espanol 18.5), qu->es chrF 33.4 (IC95 desde 30.9; piso 17.7). Evidencia objetiva, no reemplaza a un hablante |
| C10b | Calidad del quechua revisada por un hablante nativo (proximo paso) | **NOT RUN** | proximo paso: hay evidencia objetiva (FLORES-200) pero la revision de un hablante nativo queda para despues; el aviso al usuario lo dice |
| C11 | RAG: indice consistente, documentos sin alterar (hash) y solo fuentes de nivel A | **PASS** | 3761 fragmentos = 3761 vectores; 21 documentos con hash verificado; solo licencia nivel A |
| C12 | RAG: chunks, embeddings e indice bien hechos y bien usados (prefijos del modelo, normalizacion, alineacion con los textos, sin duplicados, autorrecuperacion) | **PASS** | 3,761 fragmentos = 3,761 vectores de 768 dimensiones (nomic-embed-text, prefijos search_document/search_query, normalizados, indice exacto de producto interno); al re-embeber una muestra el coseno minimo con lo guardado es 1.0000; fragmentos de 81 a 900 caracteres, 0 duplicados, metadatos completos; cada fragmento se recupera a si mismo (100% en los 3 primeros) |
| C12 | RAG: las consultas clave de CTS, retiro de CTS y TCEA recuperan su fuente oficial | **PASS** | 3 de 3 consultas clave recuperan su fuente oficial con similitud >= 0.70 |
| C13 | Datos vivos: registrar, no duplicar, rechazar lo invalido, resumir y borrar | **PASS** | registrar, no duplicar, rechazar lo invalido, resumir y borrar |
| C14 | Calendario laboral: reglas vigentes y verificadas recientemente | **PASS** | reglas verificadas el 2026-11-14; libre disposicion hoy 100% (47 dias restantes) |

## Agente

| # | Qué se verifica | Estado | Detalle |
|---|---|---|---|
| G1 | Evaluacion con plantillas (reproducible): ruteo >= 0.95, cero cifras inventadas, cero frases prohibidas, todos los pedidos prohibidos rechazados | **PASS** | 69 preguntas x 2 arquitecturas: ruteo 1.000, 0 cifras inventadas, 0 frases prohibidas, 100% de pedidos prohibidos rechazados |
| G2 | QA con Gemini real (una sola corrida): perfil, calendario, premisa falsa, datos vivos, idiomas y adversarios | **PASS** | Gemini real: perfil 11/11, adversas 16/16, datos vivos y idiomas OK, 51 llamadas y 140,543 tokens de entrada |
| G3 | Diagramas de nodos del agente generados, con rutas relativas | **PASS** | los dos diagramas de nodos existen y se citan con ruta relativa |
| G4 | Preguntas frecuentes: semilla vigente (huella del indice del RAG), con fuentes y enlaces | **PASS** | 12 preguntas de concepto con respuesta por plantilla (0 tokens), todas con fuente y enlace, vigentes para el indice actual del RAG; docs/PREGUNTAS_FRECUENTES.md generado |
| G5 | Preguntas frecuentes en la QA con Gemini real: la repeticion de una pregunta de concepto no gasta tokens | **PASS** | con Gemini real: la segunda pregunta igual («¿Que es la TCEA?») se respondio desde las preguntas frecuentes, con 0 llamadas nuevas a Gemini y 3 citas |
| G6 | QA final con tokens reales: conversaciones de varias preguntas seguidas (sin cortarse ni repetirse) y preguntas-trampa que no deben inventar datos | **PASS** | con Gemini real: 14/14 respuestas de conversaciones seguidas completas, sin repetirse ni quedarse a medias, y 9/9 preguntas-trampa (datos que no existen) sin inventar nada ni prometer; mayor tiempo de respuesta 7 s |
| G7 | Chat conversacional con tokens reales: saludos de cualquier hora e idioma, ayuda sin tema y emociones se acogen con calidez y opciones (sin tokens en los saludos); lo que ninguna regla entiende lo interpreta la IA; cada boton lleva a una respuesta real y la conversacion de varios turnos nunca se cuelga | **PASS** | con Gemini real: 25/25 mensajes de apertura (saludos de cualquier hora e idioma, ayuda sin tema, emociones, mensajes que ninguna regla reconoce; 2 obligando a la IA a saludar) acogidos con calidez y opciones, sin «no entiendo»; 8/8 botones que llevan a una respuesta real; 19/19 turnos de recorridos de varias preguntas (saludo, algo que no entiende, pregunta ajena y luego una consulta concreta) sin colgarse ni cerrarse, con la IA entrando en 10 turnos; los saludos no gastan tokens; reintentos por cuota del plan gratuito: 0 |
| G4 | No hay metricas de Gemini desfasadas (las anteriores a la seguridad se retiraron) | **PASS** | no queda el JSON de Gemini anterior al endurecimiento de seguridad |

## Seguridad

| # | Qué se verifica | Estado | Detalle |
|---|---|---|---|
| S1 | Ninguna clave de API en lo versionado | **PASS** | 205 archivos versionados sin claves de API |
| S2 | .env no versionado e ignorado | **PASS** | .env ignorado y no versionado |
| S3 | Sin rutas absolutas de ninguna laptop en codigo, parametros, metricas ni documentos | **PASS** | 125 archivos propios sin rutas absolutas |
| S4 | Ninguna mencion a un banco real en codigo, datos, metricas ni documentos propios | **PASS** | ninguna mencion a un banco real en lo propio (la entidad es inventada: Banco Kawsay) |
| S5 | Sin archivos pesados ni datos generados en el repositorio (solo data/sample), salvo la carga temporal documentada | **WARN** | 56 archivos de data/generado cargados A PROPOSITO para la integracion final (ver _manifiesto.json, todo sintetico); quitarlos al terminar con: git rm -r --cached data/generado |

## Reproducibilidad

| # | Qué se verifica | Estado | Detalle |
|---|---|---|---|
| R1 | Todo lo que importa el codigo esta en requirements-analitica.txt (un companero puede recrear el entorno) | **PASS** | las 25 bibliotecas de terceros que importa el codigo estan en requirements-analitica.txt |
| R2 | Nada desfasado: cada evaluacion corresponde al codigo actual y cada informe a las metricas actuales (huella de contenido) | **PASS** | las evaluaciones corresponden al codigo actual y los informes a las metricas actuales (huella de contenido) |
| R3 | Las fuentes oficiales del RAG se consultaron en los ultimos 30 dias | **PASS** | 21 fuentes del RAG, ultima consulta hace 0 dias |
| R4 | Carpeta de presentacion y documentacion completa: cada artefacto indexado existe, hay una grafica por problema y no quedan figuras sueltas ni duplicadas | **PASS** | 33 artefactos indexados en docs/presentacion/README.md, todos existen: una grafica por cada uno de los 14 problemas de la comparativa, diagramas de nodos y graficas de valor |
| R5 | Seguimiento con MLflow: comparaciones y modelos de produccion registrados, resumen al dia con las metricas | **PASS** | 14 comparaciones (baseline frente a elegido) y 6 modelos de produccion registrados con alias «produccion»; resumen vigente (huella 89259a180d49264b) |
| R6 | Modelo de datos para PostgreSQL: esquema, documento y cargador validados contra una base real | **PASS** | esquema de 25 tablas (lucas y simulacion) probado contra PostgreSQL 16.16 (Debian 16.16-1.pgdg12+1) con pgvector 0.8.7: carga completa con conteos iguales a los Parquet, cascadas, restricciones y busqueda vectorial; documento al dia |
| R7 | Informe final guardado en la rama con el formato del equipo (.claude/equipo/<nombre>/registro.md) | **PASS** | informe final guardado en el formato del equipo (.claude/equipo/diego/registro.md): lo que hice, lo que acordamos, lo que falta y el informe completo (1071 lineas) |

## Proximos pasos y limites (lo que no se verifico aqui)

Esta lista nunca va vacía: lo que no se verificó se dice, con su motivo y quién lo cierra.

- Proximo paso: revision del quechua por un hablante nativo (hoy hay evidencia objetiva: FLORES-200, chrF 34 frente a un piso de 18; la respuesta lleva un aviso).
- Proximo paso: llamada real a Google Cloud Translation con clave propia (el contrato esta probado con respuestas simuladas y contra su documentacion; una clave de Gemini da 401 en esa API). Se traduce con Gemini.
- Proximo paso: piloto con grupo de control del programa de puntos (la rentabilidad a varios anios depende de supuestos de conducta del equipo; con solo lo medido pierde S/ 5.52 por usuario al anio).
- Proximo paso, en la rama develop al integrar: las pruebas del agente de Jeffrey (PR #5) y el adaptador al contrato de la API.
- Proximo paso: medir la carga en produccion (se midio el costo por consulta en esta laptop, no miles de usuarios simultaneos).
- Limite: el set independiente de sentimiento lo escribio un modelo de lenguaje (no personas) y el sentimiento no esta en produccion.
- Limite: JUEZ_LLM esta apagado por ahorro de tokens; la verificacion de cifras es determinista y la calidad de redaccion de Gemini se reviso en corridas de QA.
- Estado verificado el 2026-11-14 (CTS): la libre disposicion del 100 % vence el 31-12-2026 (Ley 32322, texto oficial) y el proyecto de ley que propone extenderla hasta 2028 (El Peruano, nota 308663, 9-11-2026) esta en evaluacion en el Congreso, no es ley; el agente dice las dos cosas.
- Criterio del MVP (cerrado): todo se evaluo con datos sinteticos, como pide el reto; con datos reales de una entidad las metricas seran otras y el generador acepta una tabla semilla (ENAHO) para regenerar.
