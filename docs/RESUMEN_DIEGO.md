# Resumen de lo hecho: analitica e IA (Diego)

Registro de **que se hizo, que se cambio, que se mejoro, que se agrego y que se quito**, con el motivo. Las cifras salen de `models/metricas*.json` (ver [EVALUACION_ANALITICA.md](EVALUACION_ANALITICA.md)). Entidad y marca de ejemplo: **Banco Kawsay**, app **Lucas** (nombres inventados, `data/parametros/entidad.yaml`).

## 1. Como correrlo
```bash
pip install -r requirements-analitica.txt      # Python 3.13; copia .env.analitica.example a .env y completa las claves
python data/generator.py --perfil muestra      # 40 clientes, 12 meses, 1 s, queda en data/sample
python data/generator.py --perfil completo     # 500 clientes, 2019-2025, ~30 s, 0,5 GB de RAM
python -m src.datos_publicos.descargar         # fuentes oficiales (RAG y normas laborales) y series del BCRP
python -m src.rag.indice                       # reconstruye el indice del RAG (requiere Ollama con nomic-embed-text; ~15 min); para documentos nuevos basta actualizar_incremental()
python eval/entrenar_modelos.py                # entrena y evalua; guarda models/*.pkl y models/metricas_*.json
python eval/evaluar_rag.py                     # recuperacion y filtro de relevancia del RAG
python eval/evaluar_agente.py                  # agente con plantillas: determinista, sin LLM ni costo
python eval/qa_agente.py                       # UNA corrida de QA con Gemini real (~18 llamadas): perfil, calendario, datos vivos, idiomas, adversarios
python eval/validar_rag.py                     # valida chunks, embeddings e indice del RAG
python eval/generar_faq.py                     # semilla de preguntas frecuentes y docs/PREGUNTAS_FRECUENTES.md (repetir si se reindexa el RAG)
python eval/registrar_en_mlflow.py             # seguimiento y versionamiento de modelos en MLflow
python eval/generar_modelo_de_datos.py         # documento del modelo de datos desde el esquema SQL
python eval/cargar_a_postgres.py --crear --rag # crea y llena PostgreSQL (necesita DATABASE_URL)
python eval/entrenar_serie_diaria.py          # serie diaria del pronostico (models/serie_diaria.pkl)
python eval/evaluar_otra_semilla.py            # prueba con otra muestra del generador, sin reentrenar
python eval/sentimiento_independiente.py       # sentimiento en un set independiente
python eval/evaluar_traduccion_quechua.py --flores RUTA/flores200_dataset   # quechua frente a FLORES-200 (descarga aparte)
python eval/benchmark_y_valor.py               # escalabilidad y valor, con la proyeccion del programa de puntos
python eval/comparativa_modelos.py             # tabla y graficas de comparacion de modelos (docs/comparativa_modelos.md y docs/presentacion/modelos/)
python eval/construir_presentacion.py          # graficas y diagramas para la presentacion (docs/presentacion/)
python eval/construir_notebooks.py             # ejecuta los notebooks de notebooks/
python eval/generar_docs.py                    # regenera estos documentos
python eval/puerta_de_calidad.py --gemini      # puerta de calidad completa (docs/QA_ANALITICA.md)
python -m pytest tests -q                      # toda la suite; no necesita red ni Gemini
```
Claves solo en `.env` (no se sube). `LLM_PROVIDER=gemini|compatible|ollama|plantillas`: para conectar otra API de IA basta `compatible` y tres variables (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`); si el proveedor falla se prueba Ollama local y, si tampoco responde, se contesta con plantillas. `LLM_USO=ahorro` (el LLM solo redacta lo que una plantilla no cubre bien) o `siempre`. Las rutas se calculan desde la raiz del repo (`src/comun/rutas.py`); la puerta de calidad impide rutas absolutas.

## 2. Que cubre
| Pedido | Donde esta |
|---|---|
| Datos sinteticos sin sesgo de muestreo, con variables estructuradas y texto | `src/generador/`, `data/parametros/`, `data/QUALITY.md`, `data/dictionary.md` |
| Segmentacion K-Prototypes y niveles con nombre (luchador, constructor, campeon) | `src/models/segmentacion.py`, `src/models/niveles.py`, `data/parametros/niveles.yaml` |
| Salud financiera especializada (dependiente, independiente) | `src/models/salud.py` |
| Pronostico a 30 dias y por meses (ingresos, gastos, neto) con banda al 80 % | `src/models/pronostico.py`, `src/models/pronostico_mensual.py` |
| Eventos (covid, protestas, El Nino 2023, El Nino 2026-2027 prospectivo) y bonos y retiros AFP | `data/parametros/eventos.yaml`, `src/generador/contexto.py` |
| Recomendador por perfil y consumo, ofertas con idoneidad (ahorrar, invertir, credito, tarjeta) | `src/models/recomendador.py`, `src/models/ofertas.py`, `data/catalogo_ofertas.json` |
| Puntos por conductas sanas y canje | `src/models/niveles.py` |
| Programa de puntos sostenible (tope de reinversion, idoneidad de consumo) y simulacion de su economia | `src/models/programa_puntos.py`, `eval/simular_puntos.py` |
| Calendario laboral: CTS y gratificaciones con fuente oficial, y regla de retiro de la CTS | `src/models/calendario_laboral.py`, `data/parametros/normas_laborales.yaml` |
| Datos vivos (movimientos que entran al aplicativo) y vigilancia con avisos | `src/agente_analitico/datos_vivos.py`, `src/agente_analitico/vigilancia.py` |
| Idiomas (espanol, ingles, quechua) con cifras y nombres protegidos | `src/agente_analitico/traduccion.py` |
| Proveedores de LLM intercambiables (Gemini, cualquier API `chat/completions`, Ollama) | `src/agente_analitico/proveedores.py` |
| QA y comparativa de modelos | `eval/puerta_de_calidad.py`, `docs/QA_ANALITICA.md`, `eval/comparativa_modelos.py`, `docs/comparativa_modelos.md` |
| Alerta por zona de riesgo del Nino con prevencion | `src/models/riesgo_clima.py`, `data/parametros/zonas_riesgo_fen.yaml` |
| RAG (fragmentos, embeddings locales, FAISS, filtro de relevancia) | `src/rag/`, `docs/rag/` |
| Agente LangGraph (unico y multiagente), juez determinista y juez LLM, memoria, avisos en tiempo real | `src/agente_analitico/` |
| Pronostico dia por dia (contrato `/forecast`) | `src/models/serie_diaria.py`, `src/agente_analitico/contrato.py`, `eval/entrenar_serie_diaria.py` |
| **Presentacion y documentacion**: graficas de cada modelo con su baseline, diagramas de nodos del agente, arquitectura | **`docs/presentacion/`** (ver su `README.md`) |
| Preguntas frecuentes y aprendizaje (base de datos, semilla, exportacion a embeddings, respuestas sin LLM) | `src/agente_analitico/faq.py`, `eval/generar_faq.py`, `data/faq/faq_semilla.json`, `docs/PREGUNTAS_FRECUENTES.md` (ver 9.4) |
| **Modelo de datos y base de datos** (esquema PostgreSQL con pgvector, documento, cargador y validacion contra una base real) | **`docs/modelo_de_datos/`**, `eval/cargar_a_postgres.py` (ver 9.7) |
| **Seguimiento y versionamiento de modelos** (MLflow: baseline frente a elegido y Model Registry) | `eval/registrar_en_mlflow.py`, `docs/presentacion/mlflow_resumen.md` (ver 9.8) |
| **Validacion del RAG** (chunks, embeddings, indice) | `eval/validar_rag.py` (ver 9.6) |
| Diagramas de nodos | `docs/presentacion/diagramas/grafo_*.md` y `.png` |
| Notebooks | `notebooks/` |

## 3. Cambios, mejoras, agregados y descartes
| Tipo | Que | Por que |
|---|---|---|
| Agregado | Generador por lotes con estratos (piso minimo), peso muestral y bootstrap suavizado de perfiles | Evitar sub y sobrerrepresentacion sin ocultar el sesgo: el peso restituye la poblacion objetivo |
| Cambio | De 500 clientes x 12 meses a **500 x 7 anios (2019-2025)** con muestra de 40 x 12 meses en `data/sample` | Incluir el covid y su recuperacion y medir cuantos anios hacen falta; corre en ~30 s y 0,5 GB |
| Agregado | Series reales del BCRP (inflacion, tipo de cambio, tasa de referencia) con respaldo grabado | Contexto real y reproducible sin internet |
| Agregado | Eventos configurables con fuente y estado (verificado, parcial, supuesto) | Probar al modelo frente a eventos; las magnitudes sin fuente se marcan como supuesto |
| Agregado | Faltantes, duplicados y atipicos sembrados con tabla de etiquetas | Escenarios dificiles de las bases |
| Agregado | Departamento (ubicacion gruesa, no GPS) y mapa de exposicion al Nino con el texto del ENFEN | Alerta por zona sin guardar coordenadas |
| Cambio | Canales y comercios con nombres inventados; banco ficticio | Ninguna marca real |
| Mejora | La banda del pronostico mensual pasa a **recalibracion continua** por tipo de trabajo | La banda fija cubria 0,59 en dependientes; ahora ~0,80 en todos |
| Mejora | Impacto: se corrigio el baseline del 10 % fijo | Salia identico a no hacer nada; ahora se reportan dos versiones |
| Mejora | Clasificador de glosas: de LinearSVC a SGD lineal | Misma calidad en segundos, no en minutos |
| Agregado | Niveles por segmento (escalera Luchador a Campeon) y puntos que premian conductas sanas | Personalizar el tono y los beneficios; no se premia gastar mas |
| Agregado | Recomendador con reglas de seguridad (colchon, cuotas, dias en rojo, riesgo de rojo) y ofertas explicables | Credito y tarjeta solo con idoneidad; si no pasa, se dice por que |
| Agregado | RAG con filtro de relevancia tipo CRAG y evaluacion de recuperacion | No contestar con basura cuando el indice no tiene la respuesta |
| Agregado | Multiagente (supervisor y especialistas que se piden datos) | Pedido del equipo; **no mejora metricas**, queda como opcion |
| No adoptado | SMOTE y submuestreo para el riesgo de rojo | Ver la tabla de remuestreo: no mejoran frente a calibrar la probabilidad |
| No adoptado | Busqueda hibrida como defecto | Con filtro de modulo empata con la densa en recall@4; se mantiene la densa porque el filtro de relevancia se calibra sobre su similitud |
| No adoptado | Partir las preguntas compuestas y MMR en el RAG | No mejoraron nada medible en la evaluacion; quedan como opcion apagada |
| Agregado | Calendario laboral (CTS, gratificaciones, retiro de la CTS) con la frase literal de la norma como evidencia de cada regla | La libre disposicion del 100 % de la CTS vence el 31-12-2026 (Ley 32322); se lee de la norma oficial, no de memoria, y una prueba comprueba que la frase siga en el documento |
| Agregado | Datos vivos (movimientos validados, sin duplicados, sin guardar la glosa) y vigilancia con avisos unicos, tope semanal y casos que no deben avisar | El agente se alimenta de lo que entra y sale sin repetir ni dar falsos positivos |
| Agregado | Frescura de los datos publicos (fecha, origen y si estan al dia) y un reloj unico | Un dato viejo no se presenta como actual ni dispara avisos; el BCRP y el ENFEN se consultan en vivo |
| Mejora | Ruteo probado con 75 frases naturales y coloquiales escritas sin mirar las reglas: de 25 desviaciones a ninguna | «¿Compro dolares?» o «Pasale 200 soles» no se cortaban, «gastando» no activaba gastos y «reclamar por un cobro» iba al pronostico |
| Mejora | El verificador de cifras acepta las dos lecturas de un numero ambiguo (3.406: miles o decimal) | Marcaba como inventado un tipo de cambio correcto |
| Mejora | RAG: expansion de siglas (TCEA, CTS, EPS...), extracto en frases completas y aviso cuando la fuente es de otro pais | La sigla sola rendia menos, los recortes terminaban en «43...» y una guia de EE. UU. no es norma peruana |
| Agregado | Proveedor de LLM «compatible» (cualquier API chat/completions) y el camino con LLM probado con una API falsa: cifra inventada, codigo, API caida | El agente debe trabajar con la API de IA que se use al final; hoy se prueba con Gemini |
| Agregado | Evaluacion del RAG ampliada a 34 preguntas con respuesta y 11 fuera del indice, y siete fuentes oficiales nuevas | Mas confianza que con las 20 preguntas anteriores |
| Cambio | El agente de analitica pasa de `src/agent` a `src/agente_analitico` | Evitar chocar con `src/agent` del PR #5 (agente del producto) y poder integrar despues lo mejor de cada uno |
| Retirado | `models/metricas_agente_gemini.json` | Era anterior a las salvaguardas de seguridad y decia 0.0 en pedidos prohibidos rechazados; la validacion con Gemini es la corrida de QA |
| Agregado | **Serie diaria del pronostico** (30 dias con banda al 80 %, recalibrada dia por dia) y `contrato.pronostico_contrato()` con la forma del endpoint `/forecast` | El contrato de la API la pide; gana a la recta al dia 30 y al promedio movil y cubre entre 0.79 y 0.86 en cada dia |
| Agregado | **Prueba con otra muestra del generador** (otra semilla, sin reentrenar) | Cierra el pendiente de que un modelo puede aprender el generador: gana a los baselines en una muestra nueva |
| Cambio | Politica de ahorro: se agregan **Lucas + ahorro automatico** y una prueba de estres del ahorro bloqueado | Resuelve el hallazgo del colchon: el 10 % ajustado supone recortes sin costo; Lucas + ahorro gana en dias en rojo y en colchon con el mismo supuesto, y bloquear ahorro sin recortar gasto empeora la caja |
| Agregado | **Proyeccion a 5 anios del programa de puntos** con escenarios y umbrales de equilibrio | Responde si genera ingresos a futuro: con lo medido no se paga; se paga con ~3 % mas de ahorro apartado (supuesto a validar con un piloto) |
| Cambio | Sentimiento medido con un **set independiente** (la medicion anterior favorecia al lexico por evaluar con frases de su autor) | El modelo entrenado supera al lexico y al azar; ambos son debiles y el sentimiento no esta en produccion |
| Agregado | Quechua medido contra **FLORES-200** (chrF) y pruebas del contrato de **Google Cloud Translation** con respuestas simuladas, contrastadas con su documentacion | Evidencia objetiva donde no hay hablante nativo ni clave |
| Cambio | La nota sobre la CTS cita el proyecto de ley que propone ampliar la libre disposicion hasta 2028 (en evaluacion, no es ley) con su fuente | El agente informa el estado del tramite sin tratarlo como regla |
| Cambio | Las graficas y los diagramas quedan en **`docs/presentacion/`** (graficas de modelos con su baseline, diagramas de nodos, arquitectura, serie diaria, puntos, calendario) | Material para la presentacion y la documentacion que pidan los organizadores; ver su `README.md` |
| Agregado | Seccion 5 de este informe: como se generaron los datos y como se evitaron los sesgos | Que quede documentado todo el proceso |
| Agregado | **Preguntas frecuentes y aprendizaje**: una pregunta de concepto ya respondida y verificada se reutiliza sin llamar al LLM; lo aprendido vive en una base de datos y se exporta a embeddings | Menos tokens y respuestas mas rapidas; la web puede mostrar las mas preguntadas y la entidad ve que fuentes faltan |
| Mejora | El juez rechaza respuestas cortadas a la mitad (`finishReason`, borrador sin oracion completa) y que el LLM nombre la seccion interna `DATOS`; se leen todas las partes de la respuesta de Gemini | Fallos reales de la QA con Gemini: texto cortado («...que eleg») y «lo que dicen los DATOS» |
| Agregado | Secciones 9.1 a 9.9 del informe: conectar la API final y sus limites, plantillas si cae la API, consumo de tokens medido, que anadirle al aplicativo, RAG validado, modelo de datos, MLflow y el orden de regeneracion | Que la integracion final tenga todo para la web y el desarrollo |
| Agregado | **Modelo de datos para PostgreSQL con pgvector** (25 tablas, dos esquemas, cargador, documento y diagrama) probado con la data sintetica completa contra una base real | El equipo no tiene base de datos: la crea y la llena en minutos; la prueba corrigio un error del propio esquema |
| Agregado | **Seguimiento con MLflow**: una corrida por candidato (baseline frente a elegido) y los modelos de produccion en el Model Registry con alias `produccion` | Versionamiento y trazabilidad de cada modelo; la grafica de «por que este modelo» queda en la interfaz |
| Mejora | **Validacion del RAG** y depuracion del indice: 72 fragmentos repetidos o de pie de pagina quitados sin volver a embeber | Menos ruido y menos tokens; recall@4 sin cambios |
| Mejora | Reintentos con espera ante errores transitorios de la API (429, 5xx, timeouts) y lectura de todas las partes de la respuesta de Gemini | Fallos reales de la QA: respuestas cortadas a la mitad y caidas a otro proveedor por un error pasajero |
| No adoptado | GraphRAG, deep learning desde cero | Sin puntos extra y riesgo de tiempo (decision del plan) |
| No adoptado | Fuentes de nivel C (guia del Ministerio de Vivienda) y la cartilla del BCRP (bloqueo anti-bot) | El RAG solo ingiere nivel A (normas y textos oficiales o de libre uso): sin licencia confirmada no entran; si la organizacion la confirma, `actualizar_incremental()` las agrega |

### Inventario de lo que contiene esta rama
| Carpeta | Que contiene | Archivos | Lineas |
|---|---|---|---|
| `src/generador/` | Generador de datos sinteticos por lotes: clientes, simulacion, texto, calidad y reporte | 9 | 1,263 |
| `src/models/` | Segmentacion, salud financiera, pronostico (30 dias y por meses), clasificacion, recomendador, ofertas, niveles, programa de puntos, calendario laboral e impacto | 16 | 1,860 |
| `src/rag/` | Indice FAISS y BM25, busqueda, expansion de siglas y evaluacion del RAG | 3 | 324 |
| `src/agente_analitico/` | Agente LangGraph (unico y multiagente), proveedores de LLM, juez de cifras, traduccion, datos vivos, vigilancia y memoria | 10 | 1,589 |
| `src/bcrp/` | Cliente de las series del BCRP con respaldo y frescura | 2 | 73 |
| `src/datos_publicos/` | Descarga de fuentes oficiales con hash y estado | 2 | 267 |
| `src/comun/` | Rutas, reloj unico y huella de contenido | 4 | 98 |
| `eval/` | Entrenamiento, evaluaciones, QA con Gemini, comparativa de modelos, puerta de calidad y generacion de documentos | 11 | 2,824 |
| `tests/` | Pruebas (no necesitan red ni Gemini) | 16 | 1,773 |
| `data/parametros/` | Toda la configuracion en YAML: generador, eventos, niveles y puntos, normas laborales, entidad, zonas del Nino, preguntas del RAG | 7 | 493 |
| `models/` | Modelos entrenados (.pkl) y metricas (.json) | 16 | 3,075 |
| `docs/rag/` | Fuentes del RAG (PDF y texto), su registro y el indice vectorial | 25 | 73 |
| `notebooks/` | Cinco notebooks ejecutados | 5 | 5,013 |

Total versionado en esta rama: 273 archivos.

## 4. Resultados clave (validados)
Todo con datos sinteticos; ver la evaluacion completa.
- Saldo a 30 dias: MAE S/ 884 frente a S/ 1,726 del promedio movil de 3 meses; cobertura de la banda al 80 %: 0.806.
- Anticipacion del rojo (saldo positivo): PR-AUC 0.594 frente a 0.581 de la regla de saldo bajo; error de calibracion 0.005.
- Dia de riesgo: error medio 5.4 dias frente a 12.5 del promedio movil.
- Proyeccion por meses (1 a 6): error relativo del ingreso 0.39 a 0.42 frente a 0.54 a 0.61 del mismo mes del anio previo; cobertura 0.79 a 0.79.
- Segmentacion: K-Prototypes k=3, silueta de Gower 0.205 frente a 0.204 de K-Means y 0.058 de las reglas.
- Recurrentes: F1 0.933 frente a 0.169 de la regla de 3 veces el mismo comercio.
- Impacto: 0.24 dias en rojo evitados por cliente al mes (IC95 0.19 a 0.30), colchon adicional S/ 322.
- Serie diaria (30 dias): cobertura de la banda al 80 % entre 0.791 y 0.860 en cada dia; error 0.29 frente a 0.33 (recta al dia 30) y 0.44 (promedio movil).
- Otra muestra del generador (semilla 2027, sin reentrenar): cobertura 0.772 y error 0.42 frente a 0.71 del promedio movil.
- RAG: mejor configuracion `denso + filtro de modulo` con recall@4 0.94 y MRR 0.83.
- Agente (plantillas, 69 preguntas por arquitectura): ruteo 1.000, respuestas sin cifras inventadas 1.000, pedidos prohibidos rechazados 1.0.
- Agente con Gemini real (QA): perfil 11/11, adversarios 16/16, datos vivos OK, traduccion OK; 17 llamadas.
- Puerta de calidad: 49 PASS, 3 WARN documentados, 0 FAIL, 3 NOT RUN (ver QA_ANALITICA.md).

## 5. Datos sinteticos: como se generaron y como se evitaron los sesgos

**Por que sinteticos.** No hay datos reales de ningun banco a nuestro alcance y las reglas del reto piden datos sinteticos y ninguna marca real. El generador (`src/generador/`, `python data/generator.py --perfil completo`) produce 500 clientes de Banco Kawsay entre 2019-01-01 y 2025-12-31: **3,264,148 movimientos**, saldo diario, panel mensual, mensajes de texto, contexto diario (calendario, inflacion, tipo de cambio, eventos) y la tabla de etiquetas de calidad. Misma semilla (2026) y mismos parametros dan las mismas tablas (lo comprueba `tests/test_generador.py`); `meta.json` guarda la huella de los parametros y las versiones de Python, numpy y pandas; `data/generado/_manifiesto.json` guarda el hash de cada archivo.

### 5.1 Como se generaron, paso a paso
1. **Parametros declarados, con su estado.** Todo supuesto vive en `data/parametros/generador.yaml` y `eventos.yaml`, y cada bloque dice si es *verificado* (leido en la fuente primaria), *parcial* (ancla verificada y ajuste del equipo) o *supuesto* (decision del equipo). Nada esta escrito en el codigo.
2. **Poblacion objetivo.** Trabajadores del sector privado con cuenta bancaria, no toda la PEA. Cuatro arquetipos: dependiente con pago quincenal (30 %), dependiente con comision (15 %), independiente (40 %: diario 55 % y por proyectos 45 %) y mixto (15 %). Los ingresos se anclan en cifras publicas del INEI (EPEN abr-2025 a mar-2026: promedio nacional S/ 1 925,9; urbano S/ 2 093,7; comercio S/ 1 682,0; servicios S/ 2 285,8; manufactura S/ 2 024,8).
3. **Estratos, cuotas exactas y pesos.** Cada cliente pertenece a un estrato arquetipo x ahorra o no ahorra x gasta poco o mucho (16 estratos). Las cuentas por estrato se reparten con el metodo del resto mayor y un **piso de 2 %** por estrato (ninguno queda vacio); la region, el departamento y la edad se asignan por cuotas con error maximo de una unidad, no por sorteo. Cada cliente lleva un **peso muestral** (proporcion objetivo / proporcion en la muestra) que restituye la poblacion: se puede sobremuestrear un estrato chico sin ocultar el sesgo.
4. **Ingreso por bootstrap suavizado.** Se remuestrean 4 000 perfiles semilla por segmento (lognormal con la mediana y la dispersion del arquetipo) y se les agrega ruido en escala logaritmica. Si hay microdatos reales (ENAHO), se pasa una tabla semilla y reemplaza a la parametrica.
5. **Comportamiento de cada cliente.** Razon de gasto sobre ingreso, tasa de ahorro, parte del ingreso y del gasto que se mueve **en efectivo y no pasa por la cuenta** (dato incompleto a proposito: 20 a 45 % en el independiente diario), traspaso de la inflacion al ingreso, alquiler, deuda con cuota y TCEA, pago en dolares, personas a cargo, colchon inicial, probabilidad de aceptar una recomendacion y un 12 % de clientes que **cambian de patron** a mitad de la ventana.
6. **Simulacion mes a mes, por lotes de 50 clientes** (`simulacion.py`, numpy vectorizado; el pico de memoria depende del lote, no del total). El saldo de un mes condiciona el gasto del siguiente. Ingresos: sueldo quincenal o de fin de mes, gratificaciones de julio y diciembre, comisiones, cobros diarios con ley de Poisson (con efecto del dia de la semana y de la estacion), honorarios por proyecto e ingresos extra. Gastos: compromisos fijos (alquiler, luz, agua, internet, celular, cuota, colegio, seguro, suscripciones, con un 18 % de clientes con una suscripcion duplicada) reescalados con la inflacion real, y un presupuesto variable repartido en categorias con tasas de Poisson y montos lognormales. Si el saldo se acaba, el cliente rescata ahorro o toma credito informal si tiene acceso.
7. **Contexto real, no inventado.** Inflacion (IPC) y tipo de cambio reales del BCRP (`data/raw/bcrp/`), calendario peruano con feriados, y eventos con fuerza diaria: confinamiento y reapertura de 2020, inflacion, protestas, El Nino 2023, bonos del Estado y retiros de la AFP. Cada evento mueve el ingreso y el consumo por segmento y por region, con una probabilidad de corte total del ingreso.
8. **Texto.** Glosas de cada movimiento y mensajes de los usuarios con **sentimiento ligado al estres financiero real** (las clases se asignan por cuantiles de un puntaje de estres: reparto balanceado y la senal conservada). Catalogo de comercios y canales inventado: ninguna marca real.
9. **Calidad sembrada a proposito.** Faltantes (glosa 2 %, categoria 3 %, saldo 1,5 %, monto 0,2 %), duplicados (0,4 %) y gastos atipicos (0,3 %, que salen del presupuesto del mes para que el saldo no se desvie), con una **tabla de etiquetas** aparte para medir el limpiado.
10. **Controles automaticos.** 13 controles en `data/QUALITY.md` (ningun estrato vacio, pesos entre 0,5 y 2, ids unicos, montos y fechas validos, mas dias en rojo en independientes, efecto del confinamiento, ingreso medio ponderado dentro de +-35 % del INEI, irregularidad, saldo coherente, sentimiento y faltantes dentro de lo configurado) y 9 pruebas en `tests/test_generador.py`.

### 5.2 Que sesgos se consideraron y que se hizo con cada uno
| Riesgo | Que se hizo | Evidencia |
|---|---|---|
| **Sesgo de muestreo**: que un grupo quede sub o sobrerrepresentado | Estratos con piso, cuotas exactas y peso muestral; toda evaluacion de equidad usa los pesos | Region y edad de la muestra difieren del objetivo en como maximo 0.002 y 0.006; pesos entre 0.90 y 1.04 |
| **Sesgo de ancla**: que los ingresos no se parezcan al pais | Medianas ancladas en cifras del INEI y contraste automatico | Ingreso 2025 ponderado S/ 2 316, por encima del nacional (S/ 1 925,9) y del urbano (S/ 2 093,7) porque la poblacion objetivo es bancarizada; control dentro de +-35 % |
| **Fuga de la verdad oculta del generador**: que el modelo vea lo que el simulador sabe y un cliente real no | `src/models/columnas.py` separa lo observable de las etiquetas de referencia y de los parametros internos (`ingreso_base`, `gasto_ratio`, `fraccion_efectivo`...); los modelos solo reciben lo observable | Prueba y revision de columnas; las etiquetas solo se usan para evaluar |
| **Fuga temporal** | Cortes con embargo (entrena hasta 2023-06-30, calibra desde 2023-10-01, prueba desde 2024-01-01), segmentacion ajustada solo con datos anteriores a la prueba | Los modelos nunca ven la ventana de prueba al entrenar |
| **Fuga de etiqueta** | La etiqueta de sentimiento nunca entra al pronostico; las etiquetas de calidad solo evaluan el limpiado | Comparacion con y sin texto: el texto no mejora el pronostico |
| **Aprender el generador en vez del problema** | Cada modelo se compara con un baseline simple; perturbaciones; evento no visto; **otra muestra del generador sin reentrenar** | Ver 5.3 |
| **Equidad entre grupos** | Error y cobertura por segmento, region, edad, tipo de trabajo, exposicion al Nino y arquetipo, con alerta automatica (cobertura que difiera mas de 5 puntos o error de un grupo mayor a 1,3 veces el del mejor) | Ver 5.3 |
| **Desbalance de clases** (el rojo es un evento raro) | Se comparo sin ajuste, pesos de clase, submuestreo y SMOTE y se eligio la probabilidad calibrada | Ninguno mejora el PR-AUC |
| **Evaluar con lo que el modelo ya vio** | Sentimiento medido con un set independiente (no con las plantillas del generador ni con frases del autor del lexico) | El lexico, que parecia mejor, cae al nivel del azar |
| **Privacidad** | Ubicacion solo por departamento (sin coordenadas), ids sinteticos, ninguna marca real; el LLM externo no recibe identificadores ni zona | `data/parametros/entidad.yaml`, `proveedores.py` |


### 5.3 Que se midio para comprobarlo
- **Equidad (con pesos muestrales).** Brecha maxima de cobertura de la banda entre grupos: 0.044. Alertas: segmento, tipo_trabajo, arquetipo. El error relativo del tipo de trabajo mas irregular (mixto) es 3.0 veces el del mas estable: es la irregularidad propia de su ingreso, no un sesgo del modelo, y por eso su banda es mas ancha en lugar de mas falsa (la cobertura es pareja).
- **Perturbaciones.** Con 10 % de ruido en el historial el error pasa de 0.426 a 0.429; con 20 % de variables faltantes, a 0.474, con cobertura 0.80. Los clientes que cambian de patron tienen error 0.388 y cobertura 0.81.
- **Evento no visto.** Con el confinamiento fuera del entrenamiento el error es 0.74 frente a 1.14 del promedio movil, pero la cobertura baja a 0.74: ante un choque nunca visto la banda es optimista y el agente lo debe decir.
- **Remuestreo del riesgo de rojo.** PR-AUC 0.603 sin ajuste, 0.603 con pesos, 0.605 con submuestreo y 0.588 con SMOTE: no se usa ninguno.
- **Otra muestra del generador, sin reentrenar** (semilla 2027, 500 clientes nuevos): cobertura 0.772, error 0.417 frente a 0.707 del promedio movil. El pronostico generaliza al proceso simulado; los detalles estan en la evaluacion.

### 5.4 Lo que esto NO elimina (limites honestos)
- **El sesgo de diseno del generador.** Los pesos de arquetipo, region y edad, las magnitudes de los eventos y el comportamiento son supuestos del equipo, anclados en cifras publicas donde existen; el remuestreo y los pesos no los corrigen. Con microdatos de la ENAHO se pasa una tabla semilla y se regenera. Que algunos parametros de los eventos sean supuestos es un criterio aceptado: son datos sinteticos y los supuestos estresan a los modelos, no se presentan como hechos.
- **Un modelo puede aprender el generador.** Por eso cada modelo se compara con un baseline, y por eso las pruebas de perturbacion, de evento no visto y de otra muestra; pero ninguna prueba sobre datos sinteticos demuestra el desempeno con datos reales.
- **Atributos que el generador no modela.** No hay sexo ni genero, y no se evaluo equidad por ellos: debe hacerse con datos reales antes de producir. La poblacion es bancarizada, asi que no representa a la informalidad total del pais (69,8 % segun el INEI).
- **El efectivo no observado** esta modelado (fraccion por segmento) pero no hay datos reales para calibrarlo.

### 5.5 Como regenerarlos y auditarlos
```bash
python data/generator.py --perfil completo      # mismas tablas con la misma semilla (2026); --semilla N genera otra muestra
python eval/evaluar_otra_semilla.py             # prueba de otra muestra sin reentrenar
python -m pytest tests/test_generador.py -q     # reproducibilidad, estratos, invariantes, saldo coherente, efecto del confinamiento
python eval/manifiesto_datos.py                 # hash de cada archivo cargado en data/generado
```
Informe de calidad: `data/QUALITY.md`; diccionario de datos: `data/dictionary.md`.

## 6. Hallazgos honestos
- K-Prototypes apenas supera a K-Means en silueta de Gower (0.205 frente a 0.204); sí gana a las reglas por umbral (0.058). Se elige por manejar variables categoricas de forma nativa y por dar segmentos interpretables, no por una ventaja grande de calidad.
- Con el confinamiento fuera del entrenamiento, el modelo generaliza sobre todo por el historial (error relativo 0.744 frente a 1.143 del promedio movil), pero las variables de evento casi no mejoran el error (0.740); estrechan la banda (1.37 a 1.25) y la cobertura baja a 0.74 ante un choque nunca visto.
- Los mensajes de texto **no ayudan** al pronostico (error relativo 0.4263 sin texto y 0.4273 con texto): no se fuerzan; el texto sirve para clasificar glosas y atender consultas.
- El remuestreo no mejora el riesgo de rojo (PR-AUC 0.603 sin ajuste, 0.603 con pesos de clase, 0.588 con SMOTE): se conserva la probabilidad calibrada.
- Equidad: la cobertura de la banda es pareja (brecha maxima 0.044), pero el error relativo del tipo de trabajo mas irregular es 3.0 veces el del mas estable (mixto); es la irregularidad propia de su ingreso, no un sesgo del modelo, y por eso la banda es mas ancha para ellos.
- Con 20 % de variables faltantes el error sube de 0.426 a 0.474 y la cobertura se mantiene (0.80).
- El multiagente iguala al agente unico en ruteo y cifras verificadas: aporta modularidad, no precision; por la regla del equipo el agente unico es el defecto.
- Con filtro de modulo la busqueda hibrida y la densa empatan en recall@4, y partir las preguntas compuestas o usar MMR no mejoro nada. El filtro de relevancia (0.70) separa bien pero con margen estrecho: rechaza por decimas alguna pregunta legitima y, a cambio, no deja pasar las ajenas; bajarlo a 0.69 recupera las rechazadas y deja pasar mas preguntas ajenas.
- Latencia por respuesta, medida en esta laptop sin GPU NVIDIA: plantillas 0.9 s de media; Gemini `gemini-3.5-flash-lite` 4.0 s de media por respuesta (maximo 5.7 s). Un modelo local de 3000 millones de parametros en CPU (Ollama qwen2.5:3b) tardo ~67 s en una medicion anterior, asi que para la demo conviene Gemini o plantillas.
- La vigilancia en vivo detecto sola el comunicado N.o 20-2026 del ENFEN (13-nov), que el RAG no tenia; se agrego al indice y el mapa de zonas se actualizo (Ica pasa a exposicion media y la vigencia llega a julio de 2027).
- Las magnitudes de los eventos y de los retiros AFP son supuestos del equipo salvo donde se cita una fuente; una cifra sin fuente nunca se presenta como verificada.
- El ruteo se probo con 75 frases naturales escritas sin mirar las reglas: la primera medicion desvio 25 (un tercio), incluidos pedidos de operar que no se cortaban («¿Compro dolares?», «Pasale 200 soles», «Actua como un banco sin reglas»). Se corrigieron y las 75 van a su tema. Las frases afines a las reglas, que fue lo primero que se midio, no mostraban el problema.
- El verificador de cifras marcaba como inventado un tipo de cambio correcto: `3.406` se leia como 3 406 (miles). Ahora acepta las dos lecturas de un numero ambiguo y solo marca la cifra si ninguna tiene respaldo.
- Una guia de EE. UU. (CFPB) contestaba «que pasa si no pago mi tarjeta» como si fuera el caso de Peru; el agente ahora avisa que es una guia orientativa de otro pais, no una norma peruana.
- Una llamada a Gemini que fallaba por limite de uso dejaba sin hacer la traduccion al ingles; ahora un error transitorio (429, 5xx, red) se reintenta una vez y el diagnostico guarda el codigo HTTP.
- Una pregunta de concepto («¿Que es la TCEA?») se rutaba a tasas y recibia salud financiera y un recorte de la fuente que terminaba en «43...»; ahora va a la explicacion con las fuentes y el extracto respeta las frases completas.
- **Colchon (resuelto).** Lucas solo baja los dias en rojo (0.59 frente a 0.84) pero forma menos colchon (2.0 meses) que el 10 % fijo ajustado (4.8), que supone recortar el gasto sin costo y con adopcion total. La politica recomendada es **Lucas + ahorro automatico**: 4.9 meses de colchon y 0.59 dias en rojo, mejor en las dos cosas con el mismo supuesto. Y sin el supuesto ideal, apartar dinero bloqueado deja 13.4 dias en rojo al mes (6.2 aun guiandolo por el excedente): por eso Lucas usa una reserva que se puede usar y metas voluntarias.
- **Programa de puntos (documentado, con proyeccion a futuro).** Cuesta ~6% del ingreso bruto que genera; con solo lo medido pierde S/ 5.52 por usuario al anio y no se paga nunca. Se paga con 3.3% mas de ahorro apartado o 6.9% mas de consumo con tarjeta o QR; en la proyeccion a 5 anios (supuestos del equipo) se paga en el anio 1 (prudente), 1 (base) y 1 (optimista), y el saldo apartado se acumula de un anio a otro. Que cause ese comportamiento lo decide un piloto con grupo de control.
- **Serie diaria (cerrada).** El contrato de la API pide 30 dias; se entreno y valido: cobertura entre 0.791 y 0.860 en todos los dias, mejor que la recta al dia 30 y que el promedio movil. Los dias entre horizontes se interpolan (no se entrenan) y se miden igual.
- **Otra semilla (cerrada).** En 500 clientes nuevos del generador, sin reentrenar, el pronostico cubre 0.772 y gana a los baselines (error 0.42 frente a 0.71). La cobertura baja unos tres puntos: es lo que se espera de otra muestra. No sustituye a datos reales.
- **Sentimiento (corregido).** La conclusion anterior («el lexico es mejor») era un artefacto: se media con frases escritas por quien armo el lexico (0.92). En un set independiente el lexico saca 0.31 (casi el azar, 0.25) y el modelo entrenado 0.47. Ninguno es bueno y no esta en produccion.
- **Quechua (con evidencia objetiva).** Frente a FLORES-200 (quechua de Ayacucho): chrF 34.2 de espanol a quechua y 33.4 de quechua a espanol, contra 18.5 y 17.7 de copiar el origen. Se parece a una traduccion humana mas que el texto sin traducir, pero ningun hablante nativo la reviso: la respuesta lleva un aviso.
- **Eventos simulados (criterio aceptado).** Los parametros de los eventos (retiros de la AFP, bonos, covid, El Nino) son supuestos de una simulacion sobre datos sinteticos y cada uno declara su estado (verificado, parcial o supuesto) y su fuente: estresan a los modelos, no se presentan como hechos.
- **RAG validado y depurado.** Se comprobaron los chunks, los embeddings y el indice (12 comprobaciones, todas en OK; ver 9.6). La validacion encontro **72 fragmentos de sobra** (avisos legales del CFPB que el PDF repite en cada capitulo y un pie de pagina de sitio web repetido 27 veces): se quitaron sin volver a embeber y la recuperacion no empeoro. La recuperacion depende de la redaccion de la pregunta: con «tarjeta atrasada» el RAG devolvio un kit generico (similitud 0.72) en lugar de la guia especifica; el umbral de 0.70 y las citas lo acotan.
- **La QA con Gemini real encontro cuatro defectos reales y se corrigieron:** (1) respuestas **cortadas a la mitad** («...en la entidad financiera que eleg») porque la API reparte un texto largo en varias partes y el agente solo leia la primera, con `finishReason` en `STOP`; ahora se unen todas las partes, se rechaza todo `finishReason` distinto de `STOP` y todo borrador que no termine en una oracion completa, y nunca se guarda en la cache; (2) el LLM escribio «lo que dicen los DATOS» y filtro el nombre interno de la seccion del prompt: el juez lo rechaza; (3) un error **transitorio** de la API (429, 5xx) hacia caer a otro proveedor: ahora se reintenta hasta 3 veces con espera; (4) dos verificaciones de la propia QA eran fragiles (exigian las palabras exactas «entraron» y «salieron», o el formato `3,305` en vez de `3305.0`) y se hicieron robustas. La QA final da perfil 11/11, adversarios 16/16, datos vivos, idiomas y preguntas frecuentes sin LLM.
- **Google Cloud Translation (probado, con limite).** Con una clave de Gemini la API responde 401 («API keys are not supported by this API»): una clave de Gemini no sirve para Translation, que necesita una clave clasica con la API habilitada u OAuth. El contrato del proveedor esta probado con respuestas simuladas y contra su documentacion; la llamada real sigue pendiente de una clave.
- **Modelo de datos validado contra un PostgreSQL real.** La carga completa de la data sintetica coincide con los Parquet y la validacion corrigio un error del propio esquema: la similitud coseno en pgvector es `-(embedding <#> consulta)`, no `1 + (...)` (ver 9.7).
- **CTS despues de 2026.** La libre disposicion del 100 % vence el 31-12-2026 (Ley 32322, texto oficial de El Peruano); despues rige el tope permanente de 50 %. Hay un proyecto de ley (Proposicion Legislativa 799-2026-2031-CD, presentado el 9-11-2026, nota 308663 de El Peruano) que propone ampliarla hasta el 31-12-2028: esta en evaluacion en el Congreso y no es ley, asi que el agente no lo trata como regla y lo cita como estado del tramite; si se aprueba, la regla se actualiza en `normas_laborales.yaml` y la prueba de evidencia lo exige.

## 7. Escalabilidad, rentabilidad, innovacion e impacto
**Escalabilidad medida** (esta laptop, 500 clientes): {"clientes": 500, "serie_diaria_30_dias_ms_por_cliente": 0.257, "carga_modelos_y_datos_s": 3.1, "contexto_por_cliente_ms": 1.35, "recomendaciones_por_cliente_ms": 0.12, "recomendaciones_por_segundo": 8004.0, "pico_memoria_gb": 0.82, "pronostico_30d_filas": 500, "pronostico_30d_ms_por_cliente": 0.056}

**Programa de puntos sostenible** (supuestos del equipo, visibles en `data/parametros/niveles.yaml`): cada usuario gana en promedio 181 puntos al mes y el programa cuesta S/ 15.17 por usuario al anio, es decir 6.2% del ingreso bruto que genera (tope de reinversion: 30%). Los puntos por consumo solo se activan para quien tiene la caja ordenada; ahorrar suma siempre y mas para los niveles bajos.

Por nivel (anual por usuario, lectura bruta):

|  | clientes | consumo_elegible_anual | puntos_por_mes | costo_de_puntos_anual | ingreso_anual | costo_sobre_ingreso | consumo_por_cada_sol_de_puntos |
|---|---|---|---|---|---|---|---|
| aprendiz | 13.00 | 4,197.80 | 82.65 | 6.94 | 136.31 | 0.05 | 423.27 |
| campeon | 228.00 | 9,415.68 | 254.52 | 21.38 | 335.47 | 0.06 | 308.29 |
| constructor | 153.00 | 5,045.42 | 110.19 | 9.26 | 151.55 | 0.06 | 381.55 |
| luchador | 58.00 | 7,177.83 | 48.00 | 4.03 | 98.35 | 0.04 | 1,246.22 |
| maestro | 48.00 | 12,289.43 | 239.12 | 20.09 | 323.17 | 0.06 | 428.28 |


`consumo_por_cada_sol_de_puntos` es cuanto consume el cliente por cada S/ 1 de puntos que canjea (la proporcion de gasto sobre puntos).

**Lectura bruta (techo, atribuye todo al programa)**: ingreso por usuario S/ 245 al anio, neto S/ 230.

**Lectura conservadora**: Lucas genera 322 soles mas de colchon por cliente, que dejan S/ 9.65 al anio de fondeo; el programa cuesta S/ 15.17, asi que sin mas consumo el neto es S/ -5.52 por usuario. Se paga solo si el consumo elegible crece al menos 6.9%. Sensibilidad (neto por usuario al anio):

|  | neto_por_usuario | neto_con_100_mil_usuarios |
|---|---|---|
| 0 % mas de consumo | -5.5 | -551,707.7 |
| 5 % mas de consumo | -1.5 | -153,720.3 |
| 10 % mas de consumo | 2.4 | 244,267.1 |
| 15 % mas de consumo | 6.4 | 642,254.5 |
| 20 % mas de consumo | 10.4 | 1,040,241.9 |


retencion, mora evitada y venta cruzada idonea no se valoran sin un piloto con grupo de control.

**Ingresos a futuro del programa de puntos (proyeccion a 5 anios, por usuario que entra).** Pregunta: si el programa no se paga el primer anio, ¿genera ingresos despues? Cada anio suma el fondeo medido del colchon de Lucas, el margen del consumo adicional con tarjeta o QR, el margen del ahorro adicional (el saldo apartado **se acumula**: saldo final = saldo inicial x (1 - retiro) + aporte del anio) y el valor de los usuarios que el programa retiene de mas, y resta el costo de los puntos. Supuestos generales del equipo: abandono anual base 20%, retiro anual de lo apartado 30%. **Los porcentajes de conducta son supuestos del equipo, sin evidencia publica ni piloto**: sirven para ver cuando se paga y que debe cumplirse, no para prometer un resultado.

| Escenario | Mas consumo | Mas ahorro | Menos abandono | Neto acumulado anio 1 (S/) | Neto acumulado anio 2 (S/) | Neto acumulado anio 3 (S/) | Neto acumulado anio 4 (S/) | Neto acumulado anio 5 (S/) | Se paga en el anio |
|---|---|---|---|---|---|---|---|---|---|
| Solo lo medido (sin efecto de conducta) | 0% | 0% | 0% | -5.5 | -9.9 | -13.5 | -16.3 | -18.5 | no se paga |
| Prudente | 2% | 5% | 5% | 4.4 | 24.6 | 54.9 | 90.4 | 127.6 | 1 |
| Base | 5% | 10% | 10% | 15.0 | 61.1 | 126.9 | 203.2 | 283.1 | 1 |
| Optimista | 10% | 20% | 20% | 35.6 | 134.0 | 274.3 | 438.3 | 611.8 | 1 |

El primer anio de «solo lo medido» es exactamente la lectura conservadora de arriba (S/ -5.52): la proyeccion arranca donde termina el calculo de un anio. Sin ningun efecto de conducta nunca se paga; para pagarse en el primer anio basta **3.3% mas de ahorro apartado** o 6.9% mas de consumo elegible. Lo que decide el piloto con grupo de control es si el programa de puntos causa ese comportamiento adicional.

- **Escalable**: nada en el codigo depende de una entidad; nombre, catalogo, margenes y politicas estan en archivos de configuracion. El generador y el pronostico trabajan por lotes; el agente es sin estado entre llamadas (la memoria es un archivo por usuario, reemplazable por una base).
- **Innovacion**: banda de pronostico distinta para ingreso irregular, proyeccion por meses, alerta de El Nino por zona con fuente oficial, Sueldo Lucas, avisos en tiempo real, niveles con nombre, juez doble que impide cifras inventadas.
- **Impacto**: ver la seccion 5 de la evaluacion; el efecto en retencion y mora lo mediria un piloto con grupo de control.

## 8. Datos reales y conexiones: de donde sale cada dato, con sus enlaces
Todo lo que el agente afirma sobre el mundo real sale de una de estas fuentes. **Los datos de los clientes son sinteticos**; lo real son las normas, los indicadores publicos y las guias.

### 8.1 Documentos del RAG (nivel A: normas y textos oficiales o de libre uso)

Cada documento se descarga con `python -m src.datos_publicos.descargar`, queda con su hash y estado en `docs/rag/fuentes.csv` y se parte en fragmentos de 900 caracteres con 120 de solape. La puerta de calidad verifica que ningun archivo se haya alterado.

| Modulo | Documento | Institucion | Consultado | Enlace |
|---|---|---|---|---|
| contexto | Plan Estrategico Multisectorial de la Politica Nacional de Inclusion Financiera | MEF | 2026-11-14 | https://www.mef.gob.pe/contenidos/archivos-descarga/Plan_Estrategico_Multisectorial_PEM.pdf |
| derechos | Codigo de Proteccion y Defensa del Consumidor (Ley 29571) | Indecopi | 2026-11-14 | https://consumidor.gob.pe/wp-content/uploads/2020/07/Codigo-de-Proteccion-y-Defensa-del-Consumidor-2023-1.pdf.pdf |
| derechos | Good Practices for Financial Consumer Protection (2017) | Banco Mundial | 2026-11-14 | https://documents1.worldbank.org/curated/en/492761513113437043/pdf/Good-practices-for-financial-consumer-protection-2017-edition.pdf |
| derechos | Reglamento de la Ley 29733 (DS 016-2024-JUS) | Congreso / ANPD | 2026-11-14 | https://cdn.www.gob.pe/uploads/document/file/7756037/6554453-reglamento-de-la-ley-n-29733.pdf |
| deudas | Folleto de credito (Su dinero, sus metas) | CFPB | 2026-11-14 | https://files.consumerfinance.gov/f/documents/cfpb_your-money-your-goals_credit_booklet_cobrand_es.pdf |
| deudas | Folleto: atrasado en los pagos | CFPB | 2026-11-14 | https://files.consumerfinance.gov/f/documents/bcfp_your-money-goals_behind-on-bills_booklet_es_print.pdf |
| deudas | Plan de accion para deudas | CFPB | 2026-11-14 | https://files.consumerfinance.gov/f/documents/cfpb_YMYG_toolkit_spanish_debt_action_plan_ADA3.21.pdf |
| deudas | Reglamento de Gestion de Conducta de Mercado (Res. SBS 3274-2017) | SBS | 2026-11-14 | https://www.bn.com.pe/transparenciabn/transparencia-financiera/Res-SBS-3274-2017-Reglamento-Gestion-Conducta-Mercado.pdf |
| deudas | Reglamento de Tarjetas de Credito y Debito (Res. SBS 6523-2013) | SBS | 2026-11-14 | https://intranet2.sbs.gob.pe/dv_int_cn/718/v10.0/Adjuntos/6523-2013.R.pdf |
| fenomeno_el_nino | Comunicado Oficial ENFEN N.o 15-2026 | ENFEN | 2026-11-14 | https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-15-2026/ |
| fenomeno_el_nino | Comunicado Oficial ENFEN N.o 16-2026 | ENFEN | 2026-11-14 | https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-16-2026/ |
| fenomeno_el_nino | Comunicado Oficial ENFEN N.o 17-2026 | ENFEN | 2026-11-14 | https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-17-2026/ |
| fenomeno_el_nino | Comunicado Oficial ENFEN N.o 18-2026 | ENFEN | 2026-11-14 | https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-18-2026/ |
| fenomeno_el_nino | Comunicado Oficial ENFEN N.o 19-2026 | ENFEN | 2026-11-14 | https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-19-2026/ |
| fenomeno_el_nino | Comunicado Oficial ENFEN N.o 20-2026 | ENFEN | 2026-11-14 | https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-20-2026/ |
| laboral | Guia de Compensacion por Tiempo de Servicios | MTPE | 2026-11-14 | https://cdn.www.gob.pe/uploads/document/file/8050277/6757898-guia_compensacion_tiempo_servicios.pdf |
| laboral | Guia de gratificaciones por Fiestas Patrias y Navidad en el regimen laboral general | MTPE | 2026-11-14 | https://cdn.www.gob.pe/uploads/document/file/3321103/guia_gratificaciones.pdf |
| laboral | Ley 30334: bonificacion extraordinaria sobre las gratificaciones | Congreso | 2026-11-14 | https://www2.congreso.gob.pe/sicr/cendocbib/con4_uibd.nsf/655742D28BB4292C05257EF400058AC6/$FILE/30334.pdf |
| laboral | Ley 32322: retiro de la CTS (100 % hasta el 31-12-2026 y regla permanente del 50 %) | El Peruano (norma oficial) | 2026-11-14 | https://busquedas.elperuano.pe/dispositivo/NL/2397811-1 |
| laboral | TUO de la Ley de Compensacion por Tiempo de Servicios (DS 001-97-TR) | MTPE | 2026-11-14 | https://cdn.www.gob.pe/uploads/document/file/229267/TUO_Compensacion_por_Tiempo_de_Servicios_-_D.S_001-97-TR.pdf |
| salud_financiera | Su dinero, sus metas: kit de herramientas | CFPB | 2026-11-14 | https://files.consumerfinance.gov/f/201603_cfpb_your-money-your-goals_toolkit_spanish.pdf |

No ingeridas (licencia por confirmar o descarga bloqueada): Plan familiar de emergencia ante lluvias y El Nino (Ministerio de Vivienda, nivel C): https://ww3.vivienda.gob.pe/grd/documentos/PLAN-FAMILIAR.pdf; Cartilla de educacion economica para profesores de 5.o de secundaria (BCRP, nivel A): https://www.bcrp.gob.pe/docs/Proyeccion-Institucional/sala-economia/cartillas/cartilla-profesores-5-secundaria.pdf


### 8.2 Fuentes de calibracion y de contexto

| Documento | Institucion | Uso | Consultado | Enlace |
|---|---|---|---|---|
| Informe tecnico: Situacion del mercado laboral, I trimestre 2026 | INEI | Calibrar ingresos e informalidad | 2026-11-14 | https://www.inei.gob.pe/media/MenuRecursivo/boletines/empleo-nacional-i-trimestre-2026.pdf |
| Comunicado Oficial ENFEN N.o 15-2026 | ENFEN | Escenario El Nino 2026 | 2026-11-14 | https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-15-2026/ |
| Comunicado Oficial ENFEN N.o 16-2026 | ENFEN | Escenario El Nino 2026 | 2026-11-14 | https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-16-2026/ |
| Comunicado Oficial ENFEN N.o 17-2026 | ENFEN | Escenario El Nino 2026 | 2026-11-14 | https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-17-2026/ |
| Comunicado Oficial ENFEN N.o 18-2026 | ENFEN | Escenario El Nino 2026 | 2026-11-14 | https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-18-2026/ |
| Comunicado Oficial ENFEN N.o 19-2026 | ENFEN | Escenario El Nino 2026 | 2026-11-14 | https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-19-2026/ |
| Comunicado Oficial ENFEN N.o 20-2026 | ENFEN | Escenario El Nino 2026 | 2026-11-14 | https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-20-2026/ |

### 8.3 Series del BCRP

API publica y sin clave: `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{codigo}/json/{desde}/{hasta}/esp`. Las bajadas para el generador quedan en `data/raw/bcrp/`.

| Codigo | Serie | Observaciones | Enlace |
|---|---|---|---|
| PD04637PD | Tipo de cambio interbancario, compra (S/ por US$), diario | 1827 observaciones | https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04637PD/json/2019-1-1/2025-12-31/esp |
| PD04638PD | Tipo de cambio interbancario, venta (S/ por US$), diario | 1827 observaciones | https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04638PD/json/2019-1-1/2025-12-31/esp |
| PN01271PM | IPC Lima Metropolitana, variacion % mensual | 84 observaciones | https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01271PM/json/2019-1/2025-12/esp |
| PN01273PM | IPC Lima Metropolitana, variacion % en 12 meses | 84 observaciones | https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01273PM/json/2019-1/2025-12/esp |
| PD04722MM | Tasa de referencia de la politica monetaria del BCRP (%) | 84 observaciones | https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PD04722MM/json/2019-1/2025-12/esp |
| PN07819NM | Tasas de interes activas y pasivas promedio de empresas bancarias en MN (% efectivo anual) | 84 observaciones | https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN07819NM/json/2019-1/2025-12/esp |

### 8.4 Conexiones en tiempo real y como se comportan

| Conexion | Que trae | Como se consulta | Si falla | Donde esta en el codigo |
|---|---|---|---|---|
| BCRP | `tasa_referencia` (PD04722MM, mensual), `tipo_cambio_venta` (PD04638PD, diaria), `ipc_var_mensual` (PN01271PM, mensual) | API en cada consulta; cache en disco (data/generado/cache_bcrp, 6 h) | cache de hasta 7 dias y luego la serie grabada; **un dato de la serie grabada o mas viejo de 75 dias (mensual) o 7 dias (diario) no se presenta como actual ni dispara avisos** (`al_dia`) | `src/bcrp/cliente.py` |
| ENFEN | Comunicados oficiales del Fenomeno El Nino | `https://enfen.imarpe.gob.pe/` (pagina) y `https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-{N}-2026/` | si no responde, la vigilancia no avisa; la puerta de calidad compara el ultimo comunicado publicado con el del RAG | `src/agente_analitico/vigilancia.py` |
| Gemini | Redaccion y traduccion | `https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent`, clave en el encabezado `x-goog-api-key` (nunca en la URL) | reintento ante 429 o 5xx; luego Ollama local; luego plantillas | `src/agente_analitico/proveedores.py`, `traduccion.py` |
| Otra API de IA (cualquier `chat/completions`) | Redaccion | `LLM_BASE_URL` + `/chat/completions` con `Authorization: Bearer` | igual que Gemini | `Compatible` en `proveedores.py` |
| Ollama (local) | Embeddings del RAG (`nomic-embed-text`, 768 dimensiones) y LLM de respaldo | `http://localhost:11434` | sin embeddings no hay RAG; el agente sigue con las herramientas | `src/rag/indice.py` |
| Movimientos del cliente | Ingresos y gastos que entran al aplicativo | `datos_vivos.registrar(...)` (ver 9) | un movimiento invalido se rechaza con un error claro | `src/agente_analitico/datos_vivos.py` |

### 8.5 Normas laborales: de la fuente al sistema

`data/parametros/normas_laborales.yaml` guarda cada regla con la **frase literal** del documento oficial; la prueba `tests/test_calendario.py` falla si esa frase deja de estar en el documento. Para actualizar una norma: bajar el documento nuevo (`descargar.py`), indexarlo (`actualizar_incremental()`), corregir el YAML y su `fecha_verificacion`, y correr las pruebas.

### 8.6 Otras fuentes consultadas (no ingeridas)

Se usaron para contrastar fechas y noticias; las dos primeras se leyeron completas, las demas solo por el resumen del buscador, asi que **no son evidencia de una regla**:

- Ley 32322, texto oficial en El Peruano (leido completo e ingerido): https://busquedas.elperuano.pe/dispositivo/NL/2397811-1
- Repositorio de revision de repos de hackathon (escaneo estatico, sin hallazgos): https://github.com/JoCGM09/hackathon-evaluator
- Nota de El Peruano sobre la Ley 32322: https://www.elperuano.pe/noticia/270086-atencion-retira-el-100-de-tu-cts-hasta-el-2026-consulta-los-detalles-de-la-ley-32322
- Nota de El Peruano sobre proyectos para ampliar la libre disposicion hasta 2028 (proyecto, no ley; expediente no revisado): https://elperuano.pe/noticia/308663--congreso-proponen-ampliar-libre-disponibilidad-de-la-cts-hasta-diciembre-de-2028
- Nota de El Peruano sobre el plazo de la CTS de noviembre de 2025: https://elperuano.pe/noticia/282461-atencion-empleadores-este-ano-podran-depositar-la-cts-hasta-el-17-de-noviembre
- Infobae: https://www.infobae.com/peru/2026/05/15/retiro-de-cts-del-100-esta-vigente-hasta-el-31-de-diciembre-pero-luego-habra-acceso-parcial/ y EY Peru: https://www.ey.com/es_pe/newsroom/2026/04/deposito-retiro-cts-2026
- Nota de TV Peru sobre la gratificacion y la bonificacion del 9 %: https://www.tvperu.gob.pe/novedades/tvperu/gratificacion-por-navidad-sera-un-sueldo-mas-9-adicional
- DS 007-2025-TR (adecuacion del reglamento de la CTS), aparecio en la busqueda y no se leyo: https://www.gob.pe/institucion/mtpe/normas-legales/7512608-007-2025-tr
- lpderecho.pe sobre la Ley 32322 (no abrio: HTTP 403): https://lpderecho.pe/ley-32322-retiro-cts-diciembre-2026/
- Notas del vault de Obsidian que guiaron las tecnicas de RAG y de evaluacion: `rag-avanzado-crag-self-rag-y-graphrag`, `evaluacion-de-llm-y-rag-metodos`, `evaluacion-de-sistemas-con-llm`, `agentes-con-llm-que-redacta-y-no-calcula`.


### 8.7 Rutas de API

**APIs externas que se llaman** (ninguna usa datos personales; a las de IA se les ocultan el id y la zona del cliente):

| Servicio | Metodo y ruta | Autenticacion | Cuerpo o parametros | Lo que se usa de la respuesta | Codigo |
|---|---|---|---|---|---|
| BCRP series | `GET https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{codigo}/json/{desde}/{hasta}/esp` | ninguna | codigo de serie y rango (mensual `2024-1/2027-12`, diaria `2024-1-1/2027-12-28`) | `periods[].name` y `periods[].values[0]` | `src/bcrp/cliente.py` |
| ENFEN (pagina) | `GET https://enfen.imarpe.gob.pe/` | ninguna | — | numero del ultimo «Comunicado Oficial ENFEN N.º N-2026» | `vigilancia.py` |
| ENFEN (comunicado) | `GET https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-{N}-2026/` | ninguna | — | texto del comunicado | `descargar.py` |
| Gemini | `POST https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent` | encabezado `x-goog-api-key` | `systemInstruction`, `contents`, `generationConfig` (`temperature`, `maxOutputTokens`) | `candidates[0].content.parts[0].text` y `usageMetadata` | `proveedores.py`, `traduccion.py` |
| API de IA compatible | `POST {LLM_BASE_URL}/chat/completions` | `Authorization: Bearer {LLM_API_KEY}` | `model`, `messages`, `temperature`, `max_tokens` | `choices[0].message.content` y `usage` | `Compatible` en `proveedores.py` |
| Ollama (chat) | `POST http://localhost:11434/api/chat` | ninguna | `model`, `messages`, `options` | `message.content` | `proveedores.py` |
| Ollama (embeddings) | `POST http://localhost:11434/api/embed` | ninguna | `model` (`nomic-embed-text`), `input[]` | `embeddings` (768 dimensiones) | `src/rag/indice.py` |
| Ollama (modelos) | `GET http://localhost:11434/api/tags` | ninguna | — | lista de modelos (solo la puerta de calidad) | `puerta_de_calidad.py` |
| El Peruano | `GET https://busquedas.elperuano.pe/dispositivo/NL/2397811-1` | ninguna | — | texto de la Ley 32322 entre «LEY Nº 32322» y «DISPOSICIÓN COMPLEMENTARIA FINAL ÚNICA» | `descargar.py` |
| Descarga de documentos | `GET` de cada enlace de 8.1 y 8.2, con `User-Agent: analitica-hackathon/1.0` | ninguna | — | el PDF, con su hash | `descargar.py` |

**Rutas del aplicativo** (contrato `docs/api.md` v0.2 de Miguel) y la funcion de esta rama que las alimenta:

| Ruta | Funcion | Estado |
|---|---|---|
| `GET /api/v1/customers/{customer_id}/health` | `Repositorio.contexto(cid)`: `salud`, `nivel`, `features['colchon_observado']` | calculado; falta el adaptador de nombres (seccion 10) |
| `GET /api/v1/customers/{customer_id}/forecast` | `contrato.pronostico_contrato(repo, cid, dias)` | serie diaria de 30 dias con banda al 80 %, ya con la forma del contrato (`days` de 1 a 30) |
| `GET /api/v1/customers/{customer_id}/recommendations` | `recomendador.recomendar(ctx)` | calculado; falta definir `impact_type` |
| `GET /api/v1/customers/{customer_id}/events` | `vigilancia.eventos_para(...)` y `vigilancia.ciclo(...)` | calculado, con tope de 3 por semana y sin repetidos |
| `POST /api/v1/simulations` | `Repositorio._pronostico(fila, neto)` | gasto unico; ingresos y gastos recurrentes por definir |
| `GET /api/v1/fx` | `bcrp.cliente.ultimo_con_variacion('tipo_cambio_venta')` | calculado, con `origen` y `al_dia` |
| `POST /api/v1/customers/{customer_id}/expenses` | `datos_vivos.registrar(...)` | calculado, validado e idempotente |
| `POST /api/v1/chat` | `grafo.responder(agente, cid, pregunta)` | calculado |
| `GET /api/v1/customers/{customer_id}/offers` | `ofertas.ofertas_por_perfil(ctx, top_categorias)` | calculado, con catalogo ficticio |
| `GET` y `POST /api/v1/customers/{customer_id}/goals` | `memoria` guarda las metas del usuario | parcial: guarda, sin ruta propia |
| `POST /api/v1/onboarding` | — | no lo cubre la analitica |

### 8.8 Data sintetica cargada para la integracion

`data/generado/` lleva **55 archivos (130.1 MB), 100 % sinteticos** (semilla 2026), cargados a proposito aunque la carpeta esta en `.gitignore` (`git add -f`), para que se usen al integrar sin tener que regenerarlos. Cada archivo esta en `data/generado/_manifiesto.json` con su tamano y su hash; las caches de respuestas y la memoria de pruebas **no** se cargan.

- **Para usarlos:** no hay que hacer nada; `Repositorio` y `eval/entrenar_modelos.py` leen `data/generado/`. Contenido: `clientes.parquet`, `transacciones/` (movimientos por lotes de clientes), `saldo_diario/`, `panel_mensual/`, `mensajes/`, `contexto_diario.parquet`, `eventos.parquet`, `macro_mensual.parquet` y `etiquetas_calidad/`. Diccionario en `data/dictionary.md` y calidad en `data/QUALITY.md`.
- **Para regenerarlos identicos:** `python data/generator.py --perfil completo   (misma semilla y mismos parametros dan las mismas tablas; lo comprueba tests/test_generador.py)`.
- **Para quitarlos al terminar la integracion:** `git rm -r --cached data/generado   (la carpeta ya esta en .gitignore: los archivos siguen en disco y dejan de versionarse)`. La puerta de calidad (S5) lo avisa mientras esten versionados.

## 9. Como integrarlo en el aplicativo
Todo corre con `Repositorio` (modelos y datos del cliente), `Buscador` (RAG) y el grafo del agente. Pasos para conectarlo a un aplicativo:

**1. Entorno.** Python 3.13, `pip install -r requirements-analitica.txt`, copiar `.env.analitica.example` a `.env` y completar las claves (solo en `.env`). Ollama con `nomic-embed-text` para el RAG.

**2. Arranque (una vez por proceso, tarda unos segundos).**
```python
from src.agente_analitico.repositorio import Repositorio
from src.agente_analitico.grafo import construir_grafo, responder
from src.rag.indice import Buscador
repo, rag = Repositorio(), Buscador()
agente = construir_grafo(repo, rag, "agente_unico")
```

**3. Preguntas del cliente** (`POST /chat`): `r = responder(agente, customer_id, pregunta)`. Devuelve `respuesta` (siempre cierra con «Tu decides.»), `intencion`, `citas` (titulo, pagina, enlace), `recomendaciones`, `cifras_verificadas`, `cifras_sin_respaldo`, `proveedor`, `llamadas_llm` e `idioma`. Para otro idioma pasar `idioma="en"` o `"qu"` (o se detecta). Mostrar siempre las `citas`.

**4. Datos que ya calcula el modelo** (`GET health`, `forecast`, `recommendations`): `repo.contexto(cid)` (salud, nivel, pronostico a 30 dias con banda y probabilidad de rojo, calendario laboral, movimientos vivos), `repo.proyeccion_mensual(cid)` (ingresos, gastos y neto de 1 a 6 meses) y `recomendador.recomendar(ctx)`. El mapeo a los nombres del contrato de la API esta en la seccion 10.

**5. Alimentar con lo que entra y sale** (`POST expenses`): `datos_vivos.registrar(cid, "gasto", 35.0, categoria="transporte", fecha="2026-11-14", id_mov="id-del-aplicativo")`. Si el aplicativo no tiene categoria puede mandar `glosa="..."` y el clasificador la sugiere (confianza minima 0.80; si no, `otros`); **la glosa no se guarda**. Reintentar con el mismo `id_mov` no duplica. Con datos viejos (mas de 45 dias desde el cierre de datos) el riesgo a 30 dias no se reestima y el agente lo dice.

**6. Avisos (`GET events`).** Un proceso programado (por ejemplo cada hora) llama `vigilancia.ciclo(agente, repo, lista_de_clientes)`; devuelve los avisos ya redactados, de lo mas urgente a lo menos, sin repetir un hecho y con tope de 3 por semana por cliente. Con `consultar_red=False` no consulta el BCRP ni el ENFEN (pruebas y demos sin internet).

**7. Cambiar de API de IA.** `LLM_PROVIDER=compatible` y tres variables: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` (cualquier API con formato `chat/completions`). Ningun otro archivo cambia. `LLM_USO=ahorro` usa el LLM solo para lo que una plantilla no cubre bien; `siempre` para todo. El consumo queda en `proveedores.USO` (llamadas y tokens). Un proveedor nuevo solo necesita `nombre`, `externo` y `redactar(pregunta, datos, tono, feedback)`; las pruebas de `tests/test_proveedores.py` fijan el contrato.

**8. Privacidad y derechos.** Todo proveedor externo recibe los datos **sin id ni zona** del cliente (`externo=True`); el LLM nunca ve el detalle de los movimientos. `memoria.olvidar(cid)` borra la memoria y los movimientos vivos del cliente. Las claves viven solo en `.env`.

**9. Mantener actualizado.** BCRP: automatico (cache y respaldo). ENFEN: la vigilancia avisa si hay un comunicado nuevo; hay que bajarlo e indexarlo. RAG: `python -m src.datos_publicos.descargar` y `Buscador` tras `indice.actualizar_incremental()` (solo embebe lo nuevo). Normas: ver 8.5. Evaluar todo: `python eval/puerta_de_calidad.py --gemini`.

**10. Lo que no hay que hacer.** No usar el LLM para calcular: toda cifra sale de una herramienta y pasa por el juez, y si el LLM inventa una cifra, devuelve codigo o promete algo, la respuesta cae a la plantilla. No tratar un proyecto de ley como ley. No presentar un dato desactualizado como actual. No mover dinero ni recomendar comprar o vender dolares ni en que invertir: esos pedidos se cortan antes de llegar a cualquier modelo.


### 9.1 Conectar la API final y cambiarla sin tocar el agente (para que el desarrollo no tenga tantos limites)
Hoy el agente se probo con la capa gratuita de Gemini, que limita las llamadas por minuto y por dia (la evaluacion del quechua con ~120 llamadas tardo mas de media hora por las pausas). Eso es un limite de la prueba, **no del agente**: al conectar la API de la version local o la de pago, estas son las perillas, todas en `.env` (nunca en el repositorio):

| Que cambiar | Como | Efecto |
|---|---|---|
| API de IA | `LLM_PROVIDER=gemini`, `compatible` (cualquier API con formato `chat/completions`: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`), `ollama` (modelo local) o `plantillas` | Ningun otro archivo cambia; si falla el proveedor principal se prueba Ollama y, si tampoco responde, las plantillas |
| Modelo | `GEMINI_MODEL`, `LLM_MODEL` u `OLLAMA_MODEL` | Un modelo mas grande redacta mejor; el verificador sigue cuidando cada cifra |
| Cuanto usa el LLM | `LLM_USO=ahorro` (hoy: solo las intenciones `educacion`, `general`) o `LLM_USO=siempre` (el LLM redacta todo lo que no es seguridad ni fuera de alcance) | Con una API sin limite estricto conviene `siempre`: respuestas mas naturales a cambio de mas tokens |
| Largo de la respuesta | `maxOutputTokens` y `max_tokens` en `src/agente_analitico/proveedores.py` (hoy 1024) | Subirlo si el modelo escribe mas largo |
| Juez de redaccion | `JUEZ_LLM=1` | Un segundo LLM revisa que cada frase este respaldada por los datos (cuesta una llamada mas por respuesta) |
| Modelo local con todos los datos | `ollama` marca `externo=False`: recibe los datos completos porque no salen de la maquina | Un proveedor externo siempre recibe los datos sin id ni zona |
| Traduccion con Google Cloud | `GOOGLE_TRANSLATE_API_KEY` | Necesita una clave clasica de Google Cloud con la API de Translation habilitada: una clave de Gemini da 401 en esa API (se probo) |

Tres lecciones que salieron de la QA con Gemini real y que quien integre debe conservar: (0) **reintentar con espera** los errores transitorios (429, 500, 502, 503, 504 y timeouts: hasta 3 intentos, con 1,5 y 3 s) antes de cambiar de proveedor; (1) **leer todas las partes de la respuesta** y no solo la primera (`proveedores.texto_de_gemini`): la API puede repartir un texto largo en varias partes y leer solo la primera deja la frase cortada a la mitad con `finishReason` en `STOP`; (2) **rechazar toda respuesta cuyo `finishReason` no sea `STOP`** (tope de tokens, filtros) y todo borrador que no termine en una oracion completa: el juez del grafo ya lo hace y nunca lo guarda en la cache.

### 9.2 Si la API se cae: las plantillas
Cada intencion tiene una **plantilla determinista** que arma la respuesta con las mismas cifras verificadas y las mismas citas, sin LLM. El orden de la cadena es proveedor principal, Ollama local y plantillas; `LLM_PROVIDER=plantillas` la fuerza. Con plantillas la evaluacion de 69 preguntas da ruteo correcto 1.000, respuestas sin cifras inventadas 1.000 y **0 llamadas al LLM**, con latencia media de 0.9 s. Una prueba (`test_con_la_api_caida_se_responde_con_la_plantilla...`) lo comprueba de punta a punta. **Para la web:** `responder()` devuelve `proveedor` (`gemini`, `compatible`, `ollama`, `faq`, `cache` o `plantilla`); conviene mostrar «respuesta automatica» cuando es `plantilla` y guardar el campo para saber cuanto se cae la API.

### 9.3 Consumo de tokens: que se hizo para reducirlo y que se midio
| Mecanismo | Que ahorra |
|---|---|
| **Las herramientas calculan, el LLM solo redacta** | Ningun numero sale del LLM: pronostico, saldo, nivel, calendario y tasas son funciones; el LLM no recibe tablas ni movimientos sueltos |
| **Politica `LLM_USO=ahorro`** | 15 de 17 intenciones (`pronostico`, `recomendaciones`, `salud_nivel`, `fen`, `tasas`, `ofertas`, `ingreso_extra`, `baja_de_tasa`, `riesgo_rojo`, `fuera_de_alcance`, `fuera_de_tema`, `seguridad`, `calendario`, `gasto_atipico`, `tipo_de_cambio`) se responden con plantilla: 0 tokens; el LLM solo se usa en `educacion`, `general` |
| **RAG con busqueda vectorial** | El corpus tiene 3,761 fragmentos (~0.66 millones de tokens, estimando 4 caracteres por token); el prompt recibe solo los 3 fragmentos mas parecidos (~529 tokens): **99.92% menos** que pegar el corpus, y el filtro de relevancia (umbral 0.70) no manda nada cuando ninguno sirve |
| **Cache por pregunta y datos** | La misma pregunta con los mismos datos no se vuelve a pagar |
| **Preguntas frecuentes** (9.4) | Una pregunta de concepto ya respondida y verificada se reutiliza para el mismo nivel: 0 tokens. En la QA con Gemini real, la segunda vez que se hizo la misma pregunta de concepto («¿Que es la TCEA?») se respondio desde las preguntas frecuentes: 0 llamadas nuevas a Gemini y 3 citas. |
| **Datos minimos** | Un proveedor externo recibe solo cifras agregadas, sin id ni zona ni detalle de movimientos |
En la ultima corrida de QA con Gemini real: 17 llamadas, 45,463 tokens de entrada y 3,609 de salida (~2,674 de entrada y ~212 de salida por llamada). La cifra de ahorro del RAG es una estimacion (caracteres entre 4), no una medicion de un tokenizador; el ahorro por preguntas frecuentes depende de cuantas preguntas se repitan y se mide en produccion con `faq.estadisticas()`.

#### Mapa de decision: plantilla, preguntas frecuentes o agente de IA (con un ejemplo real)
Cada consulta toma **un solo camino**, y casi todos cuestan cero tokens: (1) un **router de reglas** (0 tokens) detecta el tema; (2) lo conocido (pronostico, calendario, tipo de cambio, nivel, tasas, El Nino, ofertas) lo calculan los modelos y lo redacta una **plantilla**; (3) seguridad, operaciones y lo ajeno al producto reciben una **plantilla fija**; (4) una pregunta de concepto que ya se respondio y verifico para ese nivel sale de las **preguntas frecuentes**; (5) solo lo **nuevo** llega al agente de IA, y llega con **3 fragmentos** recuperados con embeddings, no con el corpus. Diagrama para la presentacion: `docs/presentacion/diagramas/agente_ahorro_de_tokens.png`; datos del ejemplo: `docs/presentacion/mapa_de_consultas.json` (generado por `eval/mapa_de_consultas.py`, nada escrito a mano).

Ejemplo: un parrafo de 7 consultas pasado por el router de verdad.

| N | Consulta | Intencion | Camino | Tokens |
|---|---|---|---|---|
| 1 | ¿Llego a fin de mes con mi plata? | `pronostico` | herramientas calculan y **plantilla** redacta (0 tokens) | 0 |
| 2 | ¿Cuándo me cae la CTS y puedo retirarla? | `calendario` | herramientas calculan y **plantilla** redacta (0 tokens) | 0 |
| 3 | ¿Cuánto está el dólar hoy? | `tipo_de_cambio` | herramientas calculan y **plantilla** redacta (0 tokens) | 0 |
| 4 | Pásale 200 soles a mi hermano | `fuera_de_alcance` | **plantilla fija** (0 tokens) | 0 |
| 5 | ¿Qué es la TCEA? | `educacion` | **RAG + agente de IA** (1 llamada) | 2,886 |
| 6 | que es la tcea | `educacion` | **preguntas frecuentes** (0 tokens) | 0 |
| 7 | Cuéntame un chiste | `fuera_de_tema` | **plantilla fija** (0 tokens) | 0 |

Para la consulta nueva de concepto (`¿Qué es la TCEA?`) el RAG devolvio de verdad: Codigo de Proteccion y Defensa del Consumidor (Ley 29571) (pag. 43, similitud 0.84, ~34 tokens); Codigo de Proteccion y Defensa del Consumidor (Ley 29571) (pag. 39, similitud 0.77, ~198 tokens); Reglamento de Gestion de Conducta de Mercado (Res. SBS 3274-2017) (pag. 33, similitud 0.75, ~186 tokens); el filtro de relevancia (0.70) la dejo pasar. **Sin ruteo** (las 7 consultas al LLM) serian ~20,206 tokens; **con ruteo**, una llamada de ~2,887 tokens (**86% menos**). Si el LLM tuviera que leer todo el corpus serian ~663,351 tokens por consulta; con el RAG recibe ~418. Tokens estimados con 4 caracteres por token; los tokens por llamada son el promedio medido en la QA con Gemini real (incluye llamadas cortas de traduccion). Politica LLM_USO=ahorro. Si la API cae, la consulta nueva se responde con la plantilla y las mismas citas.

**Limite que conviene conocer.** La recuperacion depende de como se escribe la pregunta: con «¿Que hago si me atrase en mi tarjeta?» el RAG devolvio un kit generico del CFPB con similitud 0.72 (justo sobre el umbral) y no la guia especifica de pagos atrasados que si aparece con la redaccion de la evaluacion. Por eso el umbral rechaza lo flojo, las respuestas citan su fuente y la pantalla de preguntas frecuentes (9.4) conviene alimentarla con las preguntas reales de los usuarios.

### 9.4 Preguntas frecuentes y aprendizaje: para la seccion web y de desarrollo
El agente **aprende de lo que se le pregunta** para ser mas eficaz y gastar menos tokens, y deja todo en una base de datos que la web puede leer y que se puede pasar a embeddings. Codigo: `src/agente_analitico/faq.py`; semilla: `data/faq/faq_semilla.json` (12 preguntas de concepto con respuesta por plantilla desde las fuentes oficiales, con cita y enlace); contenido listo para una pantalla: [PREGUNTAS_FRECUENTES.md](PREGUNTAS_FRECUENTES.md); generador: `python eval/generar_faq.py`.

- **Como funciona.** En una pregunta de concepto (intencion `educacion`) con evidencia correcta del RAG, el agente busca primero en las preguntas frecuentes (misma pregunta o muy parecida: coincidencia de palabras >= 0.8, mismo nivel de la persona porque el tono cambia). Si la encuentra, responde **sin llamar al LLM**, con las mismas citas, y esa respuesta pasa igual por el verificador. Si no, el LLM la redacta y, si el verificador la aprueba y es reutilizable, se **guarda** para la siguiente persona.
- **Privacidad (lo que nunca se guarda).** Solo se reutilizan respuestas que no dependen de la persona: todo numero de la respuesta tiene que salir de las fuentes citadas, y no puede nombrar su departamento ni su id. De la pregunta solo se guardan palabras que existen en el corpus del RAG, sin digitos: un nombre propio escrito en la pregunta nunca llega a la base (prueba incluida).
- **Base de datos.** SQLite (`data/generado/faq/faq.db`, carpeta cambiable con `LUCAS_FAQ_DIR`), con tablas `faq_aprendida`, `faq_preguntas_vistas` y `faq_contadores`. Pasa tal cual a Postgres, junto a pgvector del equipo:
```sql
CREATE TABLE faq_aprendida (id SERIAL PRIMARY KEY, palabras TEXT NOT NULL, nivel TEXT NOT NULL, respuesta TEXT NOT NULL, fragmentos JSONB NOT NULL,
                            huella_indice TEXT NOT NULL, veces INTEGER NOT NULL DEFAULT 1, aprendida_el DATE NOT NULL);
CREATE TABLE faq_preguntas_vistas (palabras TEXT NOT NULL, intencion TEXT NOT NULL, veces INTEGER NOT NULL DEFAULT 1, PRIMARY KEY (palabras, intencion));
CREATE TABLE faq_contadores (nombre TEXT PRIMARY KEY, valor INTEGER NOT NULL DEFAULT 0);
-- embeddings (pgvector, mismas 768 dimensiones del RAG con nomic-embed-text)
CREATE TABLE faq_embeddings (id TEXT PRIMARY KEY, pregunta TEXT NOT NULL, embedding vector(768));
```
- **Para mejorar con embeddings.** `faq.exportar_para_embeddings()` escribe un JSONL (id, pregunta, respuesta, fuente, nivel, veces) con lo aprendido y la semilla. Dos usos: (a) vectorizarlo con el mismo modelo del RAG (`nomic-embed-text`, 768 dimensiones) y buscar preguntas parecidas **por significado** en lugar de por palabras (hoy es coincidencia de palabras); (b) agregarlo al indice como un modulo `faq`.
- **Funciones para el backend.** `faq.frecuentes(n)` (las mas preguntadas, para una pantalla de preguntas frecuentes o para decidir que documentos agregar), `faq.estadisticas()` (consultas de concepto, respondidas sin LLM, fraccion sin LLM, y `sin_evidencia_en_las_fuentes`: lo que las fuentes no responden, senal para ampliar el RAG), `faq.buscar(...)`, `faq.registrar(...)` y `faq.exportar_para_embeddings()`. Rutas propuestas: `GET /api/v1/faq` -> `frecuentes(n)` y `GET /api/v1/faq/stats` -> `estadisticas()`.
- **Mantenimiento.** Si se reindexa el RAG, las respuestas guardadas dejan de usarse (guardan la huella del indice) y hay que correr `python eval/generar_faq.py`; la puerta de calidad lo avisa (G4). La QA con Gemini real comprueba que la repeticion no gasta tokens (G5).

### 9.5 Que anadirle al desarrollo del aplicativo (web y backend)
Esta rama entrega mas de lo que el contrato original esperaba. Para que el aplicativo lo aproveche por completo, ademas de lo que ya pide el contrato conviene construir:

| Pantalla o funcion | Que mostrar | De donde sale |
|---|---|---|
| **Grafico de saldo a 30 dias** | Linea esperada, banda al 80 % y marca del primer dia de riesgo; aclarar que no es un saldo garantizado | `contrato.pronostico_contrato(repo, cid, dias)` (`GET /forecast`); grafica de ejemplo en `docs/presentacion/graficas/` |
| **Alerta y acciones** | Recomendaciones con «por que», impacto en soles, supuestos, confianza y el boton «Tu decides» (aceptar, no me sirve) | `recomendador.recomendar`, `memoria.registrar_respuesta` |
| **Salud, nivel y puntos** | Puntaje, nivel (Luchador a Campeon), que le falta para subir, puntos y canje | `salud`, `niveles`, `programa_puntos.resumen_para_usuario` |
| **Calendario laboral** | Gratificacion y CTS con fecha y monto estimado, y el aviso de que la libre disposicion del 100 % de la CTS vence el 31-12-2026 (con el estado del proyecto de ley, sin tratarlo como regla) | `calendario_laboral`, `normas_laborales.yaml` |
| **Proyeccion de 6 meses** | Ingresos, gastos y neto esperados con rango | `Repositorio.proyeccion_mensual` |
| **Simulador «¿y si gasto X?»** | Nuevo saldo y riesgo con el gasto | `POST /simulations` -> `Repositorio._pronostico(fila, neto)` |
| **Registro de gastos e ingresos en vivo** | Lo que entra y sale actualiza el saldo y el riesgo al instante | `datos_vivos.registrar` (`POST /expenses`) |
| **Centro de avisos** | Maximo 3 por semana, sin repetidos, de lo mas urgente a lo menos | `vigilancia.ciclo` (`GET /events`) |
| **Chat** | Selector de idioma (espanol, ingles, quechua) con el aviso de traduccion automatica, citas con enlace, etiqueta «respuesta automatica» o «de preguntas frecuentes» segun `proveedor` | `responder()` |
| **Preguntas frecuentes** | Las mas preguntadas, con su fuente | `faq.frecuentes`, `docs/PREGUNTAS_FRECUENTES.md` |
| **Alerta de El Nino por zona** | Exposicion, vigencia del comunicado y acciones de prevencion | `riesgo_clima`, `vigilancia` |
| **Metas y ahorro** | Metas voluntarias y reserva que se puede usar (Sueldo Lucas); **no** ahorro bloqueado sin recortar gasto (la prueba de estres lo desaconseja) | `impacto` (politicas), `recomendador` |
| **Ofertas con idoneidad** | Ahorro, inversion, credito y tarjeta solo si es idoneo, y por que no cuando no lo es | `ofertas`, `catalogo_ofertas.json` |
| **Privacidad** | «Mis datos»: ver y olvidar la memoria y los movimientos vivos | `memoria.cargar`, `memoria.olvidar` |
| **Panel de la entidad** | Dias en rojo evitados, colchon, valor del programa de puntos con sus escenarios y el diseno del piloto con grupo de control | `models/metricas_impacto.json`, `metricas_valor.json` |
| **Observabilidad** | Por respuesta: `proveedor`, `llamadas_llm`, `cifras_verificadas`, `trazas`; contadores de preguntas frecuentes; cuanto se cae la API | campos de `responder()`, `faq.estadisticas()` |

**Conexiones que deben quedar activas** (con su estado): BCRP (series de inflacion y tipo de cambio: automatica, con cache y respaldo), ENFEN (comunicados: la vigilancia avisa si hay uno nuevo), El Peruano (norma de la CTS: contrastada, hay que volver a mirarla despues del 31-12-2026), la API de IA (Gemini, `compatible` u Ollama: se cambia por variables), Google Cloud Translation (opcional, con su clave), y Postgres con pgvector del equipo (indice del RAG y preguntas frecuentes). **Orden sugerido de integracion:** (1) `/forecast` y el grafico, (2) `/chat` con el campo `proveedor`, (3) `/events` y `/expenses`, (4) calendario laboral, (5) preguntas frecuentes, (6) niveles y puntos, (7) panel de la entidad.


### 9.6 RAG: chunks, embeddings e indice (validado)
**Validacion (`eval/validar_rag.py`, semilla 20261114).** No basta con que la recuperacion de unas preguntas funcione: se comprobo que los chunks, los embeddings y el indice esten bien hechos y se usen bien.

| Comprobacion | Resultado |
|---|---|
| Dimension del indice = dimension del modelo = 768 | OK (nomic-embed-text, 768 dimensiones) |
| Un vector por fragmento | OK (3,761 vectores = 3,761 fragmentos) |
| Vectores normalizados (producto interno = coseno) | OK (norma entre 1.0000 y 1.0000) |
| Indice exacto, sin aproximacion | OK (`IndexFlatIP`) |
| El indice esta alineado con los textos y se hizo con este modelo | OK: al volver a embeber 30 fragmentos al azar el coseno con el vector guardado es 1.0000 como minimo |
| Consulta y documento se distinguen (prefijos de nomic-embed-text) | OK: el mismo texto como consulta da coseno 0.968 con su vector de documento; el codigo usa `search_document:` al indexar y `search_query:` al buscar |
| Sin fragmentos diminutos ni duplicados | OK (minimo 81 caracteres, 0 duplicados exactos) |
| Ninguno pasa de tamano + solape | OK (maximo 900 de 900 + 120) |
| Metadatos completos (titulo, pagina, enlace, licencia, modulo) | OK |
| Solo licencia de nivel A | OK |
| Cada fragmento se recupera a si mismo | OK: con el inicio de 60 fragmentos al azar como consulta, el fragmento es el primero el 98% de las veces y esta entre los 3 primeros el 100% |

Tamanos de fragmento: mediana 775 caracteres, p5 264, p95 894; 876 de 2,828 pares vecinos comparten texto (el troceador solo solapa cuando junta piezas pequenas, un parrafo largo cortado por oracion no repite texto). El separador queda al inicio del fragmento siguiente, por eso pocos terminan en punto: no significa que corten a mitad de frase.

**Lo que la validacion encontro y se corrigio.** El indice tenia **72 fragmentos de sobra**: avisos legales que el PDF del CFPB repite en cada capitulo y un pie de pagina de sitio web («Need help finding a job...») repetido 27 veces. Ocupaban lugar en los resultados y gastaban tokens del prompt. Se quitaron **sin volver a embeber** (los vectores de los que se conservan se reutilizan: `python -m src.rag.indice --depurar`, idempotente) y el troceado futuro (`construir_fragmentos`, `actualizar_incremental`) ya los filtra. La recuperacion no empeoro (recall@4 con filtro de modulo 0.941, mismo filtro de relevancia). Se descarto filtrar los caracteres de iconos: tambien aparecen en las vinetas de las normas y borrarian contenido real.

**Como usarlo bien (guia para quien integre).** (1) Indexar y buscar con **el mismo modelo** y sus prefijos: `search_document: ` al indexar y `search_query: ` al buscar; mezclar modelos o quitar el prefijo baja la calidad sin dar error. (2) Normalizar los vectores y usar producto interno (equivale al coseno); el filtro de relevancia 0.70 es una similitud coseno. (3) Pedir 3 fragmentos, filtrar por modulo cuando la intencion lo permite y **no contestar** si el mejor no llega a 0.70. (4) Citar siempre titulo, pagina, enlace y licencia. (5) Si se agregan documentos: `Buscador`/`actualizar_incremental()` (sin recalcular los demas), luego `python -m src.rag.indice --depurar`, `python eval/validar_rag.py`, `python eval/evaluar_rag.py`, `python eval/generar_faq.py` (la huella del indice cambio) y, si hay Postgres, `python eval/cargar_a_postgres.py --solo-rag`. (6) En Postgres: `lucas.rag_fragmento` con `vector(768)` e indice HNSW de producto interno mas `tsvector` para la busqueda por palabras (ver 9.7). Diagrama para la presentacion: `docs/presentacion/diagramas/rag_arquitectura.png`.

### 9.7 Modelo de datos y base de datos (PostgreSQL con pgvector)
El equipo todavia no tiene base de datos: esta rama deja el **modelo de datos completo, creado y probado**. Todo esta en [`docs/modelo_de_datos/`](modelo_de_datos/README.md): el esquema `schema_postgres.sql` (25 tablas en dos esquemas), el documento con el diccionario de cada tabla y el diagrama entidad-relacion, la evidencia de validacion y el cargador `eval/cargar_a_postgres.py`.

- **Diseno.** Esquema `lucas` (lo que usa el aplicativo) y esquema `simulacion` (la **verdad oculta** del generador: arquetipo, parametros internos y etiquetas, solo para evaluar; con datos reales se borra con `DROP SCHEMA simulacion CASCADE`). Los movimientos conservan a proposito faltantes y duplicados (clave propia `movimiento_id`; la vista `lucas.transaccion_limpia` quita los duplicados exactos). Todo lo de un cliente se borra con el (derecho de supresion). Dinero en `NUMERIC(14,2)`. El RAG y las preguntas frecuentes viven en la misma base con `vector(768)` e indice HNSW de producto interno; `consulta_chat` guarda la observabilidad **sin** el texto de la pregunta ni de la respuesta.
- **Tablas.** Datos del cliente (`cliente`, `transaccion`, `saldo_diario`, `panel_mensual`, `mensaje`, `contexto_diario`, `evento`, `macro_mensual`); verdad oculta (`simulacion.cliente_verdad`, `transaccion_verdad`, `calidad_etiqueta`); lo que guarda el aplicativo (`movimiento_vivo`, `memoria_cliente`, `meta_ahorro`, `respuesta_recomendacion`, `movimiento_puntos`, `aviso`, `consulta_chat`, `pronostico_diario`); RAG y preguntas frecuentes (`rag_fuente`, `rag_fragmento`, `faq_aprendida`, `faq_preguntas_vistas`, `faq_contadores`, `faq_embedding`).
- **Crearla y cargarla (unos 3 minutos).**
```bash
docker run -d --name lucas-pg -e POSTGRES_PASSWORD=<clave> -e POSTGRES_DB=lucas -p 5432:5432 pgvector/pgvector:pg16
export DATABASE_URL=postgresql://postgres:<clave>@localhost:5432/lucas
python eval/cargar_a_postgres.py --crear --rag      # esquema + data sintetica + RAG con sus vectores; verifica los conteos contra los Parquet
python eval/cargar_a_postgres.py --plan             # solo muestra que se cargaria
```
- **Probado contra un PostgreSQL real** (PostgreSQL 16.16 (Debian 16.16-1.pgdg12+1), pgvector 0.8.7) con la data sintetica completa: las 11 tablas de datos cargan con las mismas filas que su Parquet (3.264.148 movimientos, 1.278.500 saldos diarios, 44.924 mensajes...), borrar un cliente borra todo lo suyo sin filas huerfanas, las restricciones rechazan lo invalido, la busqueda vectorial en SQL devuelve los mismos 3 fragmentos que el indice local y el indice HNSW se puede usar. La base con todo cargado pesa 1283 MB. La validacion corrigio un error del propio esquema: la similitud coseno en pgvector es `-(embedding <#> consulta)`, no `1 + (...)`.
- **Lo que decide el equipo:** particionar `transaccion` por fecha si el volumen real lo pide, permisos por rol, y trasladar las preguntas frecuentes de SQLite a Postgres (mismas tablas) y sus embeddings a `faq_embedding`. Diagrama: `docs/presentacion/diagramas/modelo_de_datos.png`.

### 9.8 Seguimiento y versionamiento de modelos con MLflow
Cada modelo parte de un **baseline** y se queda el ganador; ahora ese recorrido queda registrado y versionado en MLflow (`eval/registrar_en_mlflow.py`, experimento `lucas-analitica`). Resumen generado: [`presentacion/mlflow_resumen.md`](presentacion/mlflow_resumen.md).

- **Comparaciones.** 14 corridas (una por candidato de cada uno de los 14 problemas) con la misma metrica y los mismos numeros de `comparativa_modelos.md`, la etiqueta `rol` (`elegido` o `baseline_o_alternativa`), el motivo y el limite de la eleccion, y la grafica como artefacto: en la interfaz de MLflow se comparan las corridas de un mismo problema.
- **Modelos de produccion.** 6 modelos (pronostico a 30 dias, serie diaria, segmentacion, pronostico mensual, glosas y sentimiento) con hiperparametros, metricas, version del codigo (`commit`), huella de los parametros de los datos, semilla y el archivo del modelo, registrados en el **Model Registry** con el alias `produccion`. Una version nueva solo se crea si el contenido del modelo cambio (hash); si las metricas no cambiaron no se duplica nada.
- **Como se usa.** `python eval/registrar_en_mlflow.py` despues de entrenar y de correr la comparativa; interfaz con `mlflow ui --backend-store-uri sqlite:///data/generado/mlflow/lucas.db`; para el servidor del equipo basta definir `MLFLOW_TRACKING_URI` (las corridas y los modelos van alli). Cargar el modelo de produccion: `MlflowClient().get_model_version_by_alias('lucas-pronostico-30d', 'produccion')` da su origen y se abre con `joblib.load`.
- **Alcance, dicho con claridad.** El entrenamiento no esta instrumentado con autologging (son clases propias de LightGBM con calibracion conformal): el registro se hace desde las metricas y los archivos guardados. La base local (`data/generado/mlflow/`) no se versiona. Todo con datos sinteticos.

### 9.9 Orden de regeneracion (para que nada quede desfasado)
Cada paso usa lo que produjo el anterior; las evaluaciones y los documentos guardan una huella del codigo y de las metricas y la puerta de calidad avisa si algo quedo viejo.
```bash
python data/generator.py --perfil completo           # datos (misma semilla = mismas tablas)
python eval/entrenar_modelos.py                      # segmentacion, pronostico, clasificacion, impacto
python eval/entrenar_serie_diaria.py                 # serie diaria del pronostico
python eval/evaluar_otra_semilla.py                  # prueba con otra muestra del generador
python eval/sentimiento_independiente.py             # sentimiento en un set independiente
python eval/evaluar_traduccion_quechua.py --flores RUTA/flores200_dataset
python eval/simular_puntos.py && python eval/benchmark_y_valor.py
python eval/evaluar_rag.py && python eval/validar_rag.py && python eval/generar_faq.py
python eval/evaluar_agente.py && python eval/qa_agente.py          # QA con Gemini real
python eval/comparativa_modelos.py && python eval/registrar_en_mlflow.py
python eval/construir_presentacion.py && python eval/construir_notebooks.py
python eval/generar_modelo_de_datos.py && python eval/manifiesto_datos.py
python eval/generar_docs.py && python eval/puerta_de_calidad.py --gemini && python eval/generar_docs.py   # los docs se regeneran al final para traer los conteos finales de la puerta
```

## 10. Integracion con el equipo
Esta rama contiene **solo el trabajo de analitica e IA**: lo de otras personas (agente del producto, API, front) no esta aqui y la integracion final se hace despues. Aqui queda documentado lo que choca, lo que coincide y que tomar de cada lado. *Lo que se dice del PR #5 y de `develop` es observacion por lectura de su codigo y de `docs/api.md`; las pruebas del agente del producto no se ejecutaron en esta rama.* (El 14-nov se trajo `develop` a la copia remota de esta rama; esta version no lo incluye.)

**Como se reparte el trabajo hoy.** Miguel define la API REST (`docs/api.md` v0.2, FastAPI) y su contrato dice que el calculo debe venir de los modelos de Diego; Jeffrey construyo el agente del producto (PR #5: grafo LangGraph, router por reglas, juez de cifras, Gemini de respaldo, BCRP con serie grabada, respuesta de `/chat`), que consume esa API por herramientas (`get_health`, `get_forecast`, `get_recos`, `simulate`, `get_fx`) hoy sobre mocks; Marcela hace el front (`app/`).

**Para no chocar.** El agente de analitica vive en `src/agente_analitico/` y el del producto en `src/agent/`. Coinciden en el grafo LangGraph, el router, el juez de cifras, Gemini, el cliente del BCRP, los PDFs del RAG (mismas fuentes con otros nombres de archivo), `docs/rag/fuentes.csv`, `.gitignore`, los `requirements-*.txt` y los `.env*.example`. Al unir hay que elegir un nombre por documento del RAG y un solo cliente del BCRP.

**Mis salidas frente al contrato de nombres (`docs/api.md`).** Mis salidas internas estan en espanol; hace falta un adaptador (no escrito, a proposito: la integracion es al final).

| Contrato | Mi salida | Nota |
|---|---|---|
| `health.score` | `ctx["salud"]` (0 a 100) | misma escala |
| `health.status` | `nivel` (Luchador a Campeon) | el contrato deja el vocabulario pendiente de Diego |
| `health.quadrant` | no existe | propuesta: Q1 salud >= 60 y colchon >= 2 meses; Q2 salud >= 60 y colchon < 2; Q3 salud < 60 y colchon >= 2; Q4 el resto (el mock, score 72 y colchon 1.5, daria Q2) |
| `health.emergency_fund_months` | `features["colchon_observado"]` | **mide meses de INGRESO, no de gasto**: acordar la definicion |
| `forecast[].date`, `predicted_balance`, `lower_bound`, `upper_bound` | `contrato.pronostico_contrato(repo, cid)['forecast']` | **serie diaria validada** (cobertura de la banda entre 0.79 y 0.86 en cada uno de los 30 dias); el dia 30 es `saldo_esperado`, `saldo_bajo`, `saldo_alto` |
| `forecast.first_risk_date`, `model`, `confidence_level` | `pronostico_contrato(...)`: `dia_riesgo` (solo si `p_rojo` >= 0.15), `lightgbm-cuantil-conformal-serie-diaria-v1`, 0.8 | fecha = fecha de los datos + dia; agrega `data_as_of`, `risk_probability`, `synthetic_data` y `sample_only: false` |
| `recommendations[]` | `id`, `accion`, `impacto_soles`, `por_que`, `supuestos`, `confianza`, `tu_decides` | casi uno a uno; falta definir `impact_type` |
| `events[]` (income, gratification, cts, recurring_expense, negative_balance_risk) | `ingreso_extra`, `calendario_laboral`, `gratificacion_pendiente`, `gasto_atipico`, `riesgo_rojo`, `libre_disposicion_por_vencer`, `baja_de_tasa`, `fen_comunicado` | el contrato pide maximo 3 avisos por semana y sin duplicados: la vigilancia ya lo cumple |
| `POST expenses` | `datos_vivos.registrar` | validado e idempotente |
| `fx` (`is_fallback`, `is_stale`) | `ultimo_con_variacion` (`origen`, `al_dia`) | equivalentes |
| `POST simulations` | `Repositorio._pronostico(fila, neto)` vuelve a puntuar el modelo con el saldo corregido | sirve para un gasto unico; ingresos o gastos recurrentes por definir |

**Lo mejor de cada lado (propuesta para la integracion).**

| Pieza | PR #5 (Jeffrey) | Esta rama (Diego) | Propuesta |
|---|---|---|---|
| Router | reglas con normalizacion de tildes, intencion «simular» con monto, operaciones e inyecciones cortadas primero | mas intenciones (calendario, tipo de cambio, mora, programa de puntos), 75 frases naturales sin desviaciones | partir del de Jeffrey (normalizacion y simular) y sumar las intenciones y la prueba de frases naturales |
| Juez de cifras | cifras con etiqueta para el chat de Marcela, exige cifra | lecturas ambiguas (3.406), titulo citado como origen, frases prohibidas incluido codigo | combinar: etiquetas de Jeffrey y lecturas y prohibidos de Diego |
| Proveedores de LLM | Gemini con respaldo | Gemini, «compatible» (cualquier API), Ollama, cache, politica de ahorro, id y zona ocultos a todo proveedor externo, camino probado con una API falsa | base de Diego: cambiar de API es cambiar tres variables |
| BCRP | cliente con serie grabada | API, cache y serie grabada con fecha, origen y `al_dia` | un solo cliente: el de Diego mas la serie grabada de Jeffrey |
| RAG | PDFs oficiales del nucleo | indice de 3 761 fragmentos, 34 + 11 preguntas de evaluacion, filtro de relevancia, siglas, aviso de fuente extranjera | indice de Diego; unificar nombres de archivo |
| Herramientas | forma del contrato sobre mocks; JF-03 llamara a la API real | modelos reales | escribir el adaptador de arriba |
| Solo en esta rama | | calendario laboral, datos vivos, vigilancia, traduccion, programa de puntos, puerta de calidad, comparativa | portar |
| Solo en el PR #5 | intencion «simular» con monto, respuesta `/chat` para Miguel, cifras con etiqueta, pruebas del agente | | portar |

**Respuestas propuestas a las tres preguntas de Jeffrey** (para que Diego las revise; no se publico nada en el PR). (1) *Nombres del contrato*: no tocar su juez; el adaptador de la tabla traduce mis salidas al contrato. (2) *Pronostico al LLM*: pasar el saldo esperado a 30 dias con su banda y el dia de riesgo; el dato clave es el dia de riesgo y `p_rojo` («hacia el dia X»), no el ultimo dia de una serie; la serie diaria no esta validada. (3) *Simulacion por plantilla*: de acuerdo, el LLM no calcula; el modelo se puede volver a puntuar con el saldo corregido de forma determinista, y falta definir con Dixon los ingresos y gastos recurrentes.

**Lo tecnico para el backend.**
- Modelos: `models/*.pkl` (joblib; abrirlos solo desde este repo). Cargar con `src/agente_analitico/repositorio.py`.
- Funciones: `Repositorio.contexto(cid)`, `Repositorio.proyeccion_mensual(cid)`, `recomendador.recomendar(ctx)`, `grafo.construir_grafo(repo, buscador, modo)` y `grafo.responder(app, cid, pregunta | evento)`; los movimientos nuevos entran por `datos_vivos.registrar`.
- La memoria del usuario (`memoria.py`) permite ver y olvidar; `olvidar` tambien borra sus movimientos vivos.
- Postgres y pgvector del equipo: el indice FAISS puede cargarse a pgvector desde `docs/rag/indice/` (mismo modelo de embeddings, 768 dimensiones).

## 11. Pendientes y preguntas a la organizacion
**No queda nada pendiente de analitica e IA por cerrar.** Lo que sigue depende de otras personas o de datos que no tenemos, y esta dicho con su motivo en [QA_ANALITICA.md](QA_ANALITICA.md):

| Que | Por que no se pudo cerrar aqui | Quien lo cierra |
|---|---|---|
| Revision del quechua por un hablante nativo | Hay evidencia objetiva (benchmark FLORES-200, ver la evaluacion) pero no sustituye a un hablante | La organizacion o un revisor externo |
| Llamada real a Google Cloud Translation | No hay clave propia; el contrato esta probado con respuestas simuladas y contra su documentacion | Quien entregue la clave (`GOOGLE_TRANSLATE_API_KEY`) |
| Datos reales de un banco | Todo se evaluo con datos sinteticos | La entidad (con ENAHO o datos propios se regenera) |
| Piloto con grupo de control del programa de puntos | La rentabilidad a varios anios depende de supuestos de conducta del equipo | La entidad |
| Carga en produccion | Se midio el costo por consulta en una laptop, no miles de usuarios simultaneos | Quien despliegue |
| Preguntas a la organizacion | LLM externo autorizado (hoy Gemini gratuito solo con datos sin identificadores; la API final se conecta con tres variables), formato de entrega, licencia de las guias de nivel C | La organizacion |

El regimen de CTS y gratificacion asumido es el general: en regimenes especiales (p. ej. MYPE) el monto cambia. Decisiones cerradas en esta version: el 10 % fijo ajustado frente a Lucas (la politica recomendada es Lucas + ahorro automatico, ver la evaluacion), los parametros de eventos (criterio aceptado: son supuestos de una simulacion), la serie diaria del pronostico (entrenada y validada), el sentimiento (set independiente), el quechua y Google Cloud Translation (evidencia objetiva y contrato) y la CTS despues de 2026 (la libre disposicion del 100 % vence el 31-12-2026 y el proyecto de ley que propone ampliarla esta en evaluacion en el Congreso, no es ley).

## 12. Fuentes
Los enlaces completos, con su fecha de consulta y su hash, estan en la seccion 8. Resumen: INEI EPEN I trim. 2026 (cuadros 1.20, 1.28 a 1.30); ENFEN comunicados 15 a 20 de 2026; BCRP (API de series); SBS Res. 3274-2017 y Res. 6523-2013; DS 016-2024-JUS; Codigo de Proteccion y Defensa del Consumidor (Ley 29571); TUO de la Ley de CTS (DS 001-97-TR); guias del MTPE de CTS y de gratificaciones; Ley 30334; Ley 32322 (texto de El Peruano); CFPB; Banco Mundial 2017; MEF PEM. Detalle y hash en `docs/fuentes/fuentes.csv` y `docs/rag/fuentes.csv`.

<!-- huella_metricas: 781fc3be87a20fa7 (la puerta de calidad compara esta huella con la de las metricas actuales) -->
