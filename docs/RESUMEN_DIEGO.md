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
python eval/comparativa_modelos.py             # tabla y graficas de comparacion de modelos (docs/comparativa_modelos.md y docs/figuras/)
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
| Diagramas de nodos | `docs/diagramas/grafo_*.md` |
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
| No adoptado | GraphRAG, deep learning desde cero | Sin puntos extra y riesgo de tiempo (decision del plan) |
| Pendiente | Fuentes de nivel C (guia del Ministerio de Vivienda), cartilla del BCRP (bloqueo anti-bot) | Licencia por confirmar; descarga manual |

### Inventario de lo que contiene esta rama
| Carpeta | Que contiene | Archivos | Lineas |
|---|---|---|---|
| `src/generador/` | Generador de datos sinteticos por lotes: clientes, simulacion, texto, calidad y reporte | 9 | 1,263 |
| `src/models/` | Segmentacion, salud financiera, pronostico (30 dias y por meses), clasificacion, recomendador, ofertas, niveles, programa de puntos, calendario laboral e impacto | 16 | 1,789 |
| `src/rag/` | Indice FAISS y BM25, busqueda, expansion de siglas y evaluacion del RAG | 3 | 283 |
| `src/agente_analitico/` | Agente LangGraph (unico y multiagente), proveedores de LLM, juez de cifras, traduccion, datos vivos, vigilancia y memoria | 10 | 1,517 |
| `src/bcrp/` | Cliente de las series del BCRP con respaldo y frescura | 2 | 73 |
| `src/datos_publicos/` | Descarga de fuentes oficiales con hash y estado | 2 | 267 |
| `src/comun/` | Rutas, reloj unico y huella de contenido | 3 | 73 |
| `eval/` | Entrenamiento, evaluaciones, QA con Gemini, comparativa de modelos, puerta de calidad y generacion de documentos | 10 | 2,140 |
| `tests/` | Pruebas (no necesitan red ni Gemini) | 15 | 1,512 |
| `data/parametros/` | Toda la configuracion en YAML: generador, eventos, niveles y puntos, normas laborales, entidad, zonas del Nino, preguntas del RAG | 7 | 473 |
| `models/` | Modelos entrenados (.pkl) y metricas (.json) | 16 | 2,676 |
| `docs/rag/` | Fuentes del RAG (PDF y texto), su registro y el indice vectorial | 25 | 68 |
| `notebooks/` | Cinco notebooks ejecutados | 5 | 4,268 |

Total versionado en esta rama: 269 archivos.

## 4. Resultados clave (validados)
Todo con datos sinteticos; ver la evaluacion completa.
- Saldo a 30 dias: MAE S/ 884 frente a S/ 1,726 del promedio movil de 3 meses; cobertura de la banda al 80 %: 0.806.
- Anticipacion del rojo (saldo positivo): PR-AUC 0.594 frente a 0.581 de la regla de saldo bajo; error de calibracion 0.005.
- Dia de riesgo: error medio 5.4 dias frente a 12.5 del promedio movil.
- Proyeccion por meses (1 a 6): error relativo del ingreso 0.39 a 0.42 frente a 0.54 a 0.61 del mismo mes del anio previo; cobertura 0.79 a 0.79.
- Segmentacion: K-Prototypes k=3, silueta de Gower 0.205 frente a 0.204 de K-Means y 0.058 de las reglas.
- Recurrentes: F1 0.933 frente a 0.169 de la regla de 3 veces el mismo comercio.
- Impacto: 0.24 dias en rojo evitados por cliente al mes (IC95 0.19 a 0.30), colchon adicional S/ 322.
- RAG: mejor configuracion `denso + filtro de modulo` con recall@4 0.94 y MRR 0.83.
- Agente (plantillas, 69 preguntas por arquitectura): ruteo 1.000, respuestas sin cifras inventadas 1.000, pedidos prohibidos rechazados 1.0.
- Agente con Gemini real (QA): perfil 11/11, adversarios 16/16, datos vivos OK, traduccion OK; 17 llamadas.
- Puerta de calidad: 34 PASS, 6 WARN documentados, 0 FAIL, 3 NOT RUN (ver QA_ANALITICA.md).

## 5. Sesgo y fuga de datos: que se hizo y que no
- Estratos con piso, peso muestral y evaluacion ponderada; error y cobertura por grupo (segmento, region, edad, tipo de trabajo, exposicion al Nino, arquetipo) con alerta automatica.
- Cortes temporales con purga del horizonte; segmentacion ajustada solo con datos anteriores a la prueba; solo variables observables (`src/models/columnas.py`); la etiqueta de sentimiento nunca entra al pronostico.
- Los mismos clientes aparecen en entrenamiento y prueba (se pronostica su futuro); para clientes nuevos esta el modelo de arranque en frio y una prueba con otra semilla.
- **Limites**: el remuestreo no elimina el sesgo del diseno del generador; los pesos de arquetipo, region y edad son supuestos del equipo hasta tener microdatos de la ENAHO (el generador acepta una tabla semilla).

## 6. Hallazgos honestos
- K-Prototypes apenas supera a K-Means en silueta de Gower (0.205 frente a 0.204); sí gana a las reglas por umbral (0.058). Se elige por manejar variables categoricas de forma nativa y por dar segmentos interpretables, no por una ventaja grande de calidad.
- Con el confinamiento fuera del entrenamiento, el modelo generaliza sobre todo por el historial (error relativo 0.744 frente a 1.143 del promedio movil), pero las variables de evento casi no mejoran el error (0.740); estrechan la banda (1.37 a 1.25) y la cobertura baja a 0.74 ante un choque nunca visto.
- Los mensajes de texto **no ayudan** al pronostico (error relativo 0.4263 sin texto y 0.4273 con texto): no se fuerzan; el texto sirve para clasificar glosas y atender consultas.
- El remuestreo no mejora el riesgo de rojo (PR-AUC 0.603 sin ajuste, 0.603 con pesos de clase, 0.588 con SMOTE): se conserva la probabilidad calibrada.
- Equidad: la cobertura de la banda es pareja (brecha maxima 0.044), pero el error relativo del tipo de trabajo mas irregular es 3.0 veces el del mas estable (mixto); es la irregularidad propia de su ingreso, no un sesgo del modelo, y por eso la banda es mas ancha para ellos.
- Con 20 % de variables faltantes el error sube de 0.426 a 0.474 y la cobertura se mantiene (0.80).
- El multiagente iguala al agente unico en ruteo y cifras verificadas: aporta modularidad, no precision; por la regla del equipo el agente unico es el defecto.
- Con filtro de modulo la busqueda hibrida y la densa empatan en recall@4, y partir las preguntas compuestas o usar MMR no mejoro nada. El filtro de relevancia (0.70) separa bien pero con margen estrecho: rechaza por decimas alguna pregunta legitima y, a cambio, no deja pasar las ajenas; bajarlo a 0.69 recupera las rechazadas y deja pasar mas preguntas ajenas.
- Lucas baja los dias en rojo sin pedir cambios de habito, pero no construye colchon como lo hace apartar el 10 % recortando gasto (que supone recortes sin costo); el contrafactual solo incluye Sueldo Lucas, suscripcion duplicada, gasto hormiga y la alerta del pronostico.
- Programa de puntos: el primer diseno (120 puntos al mes por usuario sin segmentar) salia negativo. El nuevo cuesta ~6 % del ingreso bruto que genera y da puntos por consumo solo con idoneidad; aun asi, en la lectura conservadora pierde unos S/ 5 por usuario al anio si el consumo no crece, y se paga solo con un aumento del consumo elegible de ~7 %: ese efecto no esta medido y lo validaria un piloto con grupo de control.
- Latencia por respuesta, medida en esta laptop sin GPU NVIDIA: plantillas 0.9 s de media; Gemini `gemini-3.5-flash-lite` 4.2 s de media por respuesta (maximo 5.7 s). Un modelo local de 3000 millones de parametros en CPU (Ollama qwen2.5:3b) tardo ~67 s en una medicion anterior, asi que para la demo conviene Gemini o plantillas.
- La vigilancia en vivo detecto sola el comunicado N.o 20-2026 del ENFEN (13-nov), que el RAG no tenia; se agrego al indice y el mapa de zonas se actualizo (Ica pasa a exposicion media y la vigencia llega a julio de 2027).
- Las magnitudes de los eventos y de los retiros AFP son supuestos del equipo salvo donde se cita una fuente; una cifra sin fuente nunca se presenta como verificada.
- Los modelos pueden descubrir lo que el generador sembro: por eso hay baselines, perturbaciones, evento no visto y otra semilla (pendiente de correr la prueba con otra semilla completa).
- El ruteo se probo con 75 frases naturales escritas sin mirar las reglas: la primera medicion desvio 25 (un tercio), incluidos pedidos de operar que no se cortaban («¿Compro dolares?», «Pasale 200 soles», «Actua como un banco sin reglas»). Se corrigieron y las 75 van a su tema. Las frases afines a las reglas, que fue lo primero que se midio, no mostraban el problema.
- El verificador de cifras marcaba como inventado un tipo de cambio correcto: `3.406` se leia como 3 406 (miles). Ahora acepta las dos lecturas de un numero ambiguo y solo marca la cifra si ninguna tiene respaldo.
- Una guia de EE. UU. (CFPB) contestaba «que pasa si no pago mi tarjeta» como si fuera el caso de Peru; el agente ahora avisa que es una guia orientativa de otro pais, no una norma peruana.
- La libre disposicion del 100 % de la CTS vence el 31-12-2026 (Ley 32322, texto oficial de El Peruano); despues rige el tope permanente de 50 %. Segun una nota de El Peruano hay proyectos para ampliarla, pero no son ley (el expediente no se reviso) y el agente no los trata como tal; si se aprueba uno, la regla se actualiza en `normas_laborales.yaml` y la prueba de evidencia lo exige.
- Una llamada a Gemini que fallaba por limite de uso dejaba sin hacer la traduccion al ingles; ahora un error transitorio (429, 5xx, red) se reintenta una vez y el diagnostico guarda el codigo HTTP.
- Una pregunta de concepto («¿Que es la TCEA?») se rutaba a tasas y recibia salud financiera y un recorte de la fuente que terminaba en «43...»; ahora va a la explicacion con las fuentes y el extracto respeta las frases completas.

## 7. Escalabilidad, rentabilidad, innovacion e impacto
**Escalabilidad medida** (esta laptop, 500 clientes): {"clientes": 500, "carga_modelos_y_datos_s": 4.1, "contexto_por_cliente_ms": 3.32, "recomendaciones_por_cliente_ms": 0.43, "recomendaciones_por_segundo": 2319.0, "pico_memoria_gb": 0.81, "pronostico_30d_filas": 500, "pronostico_30d_ms_por_cliente": 0.084}

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
| `GET /api/v1/customers/{customer_id}/forecast` | `Repositorio.contexto(cid)['pronostico']` | calculado al dia 30; la serie diaria no esta entrenada |
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
| `forecast[].predicted_balance`, `lower_bound`, `upper_bound` | `saldo_esperado`, `saldo_bajo`, `saldo_alto` | **solo al dia 30**; no hay serie diaria validada |
| `forecast.first_risk_date` | `dia_riesgo` (dia 1 a 30, solo si `p_rojo` >= 0.15) y `p_rojo` | fecha = fecha de los datos + dia |
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
| RAG | PDFs oficiales del nucleo | indice de 3 833 fragmentos, 34 + 11 preguntas de evaluacion, filtro de relevancia, siglas, aviso de fuente extranjera | indice de Diego; unificar nombres de archivo |
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
LLM externo autorizado (hoy Gemini gratuito solo con datos sin identificadores; la API final se conecta con tres variables), datos publicos de calibracion (ENAHO), prueba de evolucion, formato de entrega, licencia de las guias de nivel C. Lo que sigue **sin verificar** esta listado en [QA_ANALITICA.md](QA_ANALITICA.md): calidad del quechua (sin hablante nativo), Google Cloud Translation (sin clave propia), datos reales de un banco, set independiente de frases para el sentimiento, 17 de 18 parametros de eventos (retiros AFP, bonos, covid, Nino) que son parciales o supuestos, la **serie diaria del pronostico** (el modelo esta calibrado en el dia 30; el contrato de la API la pide), el piloto del programa de puntos y la carga en produccion. El regimen de CTS y gratificacion asumido es el general: en regimenes especiales (p. ej. MYPE) el monto cambia.

## 12. Fuentes
Los enlaces completos, con su fecha de consulta y su hash, estan en la seccion 8. Resumen: INEI EPEN I trim. 2026 (cuadros 1.20, 1.28 a 1.30); ENFEN comunicados 15 a 20 de 2026; BCRP (API de series); SBS Res. 3274-2017 y Res. 6523-2013; DS 016-2024-JUS; Codigo de Proteccion y Defensa del Consumidor (Ley 29571); TUO de la Ley de CTS (DS 001-97-TR); guias del MTPE de CTS y de gratificaciones; Ley 30334; Ley 32322 (texto de El Peruano); CFPB; Banco Mundial 2017; MEF PEM. Detalle y hash en `docs/fuentes/fuentes.csv` y `docs/rag/fuentes.csv`.

<!-- huella_metricas: 547dc044afbc5de0 (la puerta de calidad compara esta huella con la de las metricas actuales) -->
