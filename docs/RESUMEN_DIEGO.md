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
- Puerta de calidad: 35 PASS, 5 WARN documentados, 0 FAIL, 2 NOT RUN (ver QA_ANALITICA.md).

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
- Latencia por respuesta, medida en esta laptop sin GPU NVIDIA: plantillas 0.9 s de media; Gemini `gemini-3.5-flash-lite` 4.2 s de media por respuesta (maximo 5.8 s). Un modelo local de 3000 millones de parametros en CPU (Ollama qwen2.5:3b) tardo ~67 s en una medicion anterior, asi que para la demo conviene Gemini o plantillas.
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

## 8. Integracion con el equipo
Esta rama se mantiene **separada** hasta la integracion final; aqui queda documentado lo que choca, lo que coincide y que tomar de cada lado. *Lo que sigue del PR #5 y de `develop` es observacion por lectura: no ejecute sus pruebas; compararlo con mediciones es parte de la integracion.*

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

## 9. Pendientes y preguntas a la organizacion
LLM externo autorizado (hoy Gemini gratuito solo con datos sin identificadores; la API final se conecta con tres variables), datos publicos de calibracion (ENAHO), prueba de evolucion, formato de entrega, licencia de las guias de nivel C. Lo que sigue **sin verificar** esta listado en [QA_ANALITICA.md](QA_ANALITICA.md): calidad del quechua (sin hablante nativo), Google Cloud Translation (sin clave propia), datos reales de un banco, set independiente de frases para el sentimiento, 17 de 18 parametros de eventos (retiros AFP, bonos, covid, Nino) que son parciales o supuestos, la **serie diaria del pronostico** (el modelo esta calibrado en el dia 30; el contrato de la API la pide), el piloto del programa de puntos y la carga en produccion. El regimen de CTS y gratificacion asumido es el general: en regimenes especiales (p. ej. MYPE) el monto cambia.

## 10. Fuentes
INEI EPEN I trim. 2026 (cuadros 1.20, 1.28 a 1.30); ENFEN comunicados 15 a 20 de 2026; BCRP (API de series); SBS Res. 3274-2017 y Res. 6523-2013; DS 016-2024-JUS; Codigo de Proteccion y Defensa del Consumidor (Ley 29571); TUO de la Ley de CTS (DS 001-97-TR); guias del MTPE de CTS y de gratificaciones; Ley 30334; Ley 32322 (texto de El Peruano); CFPB; Banco Mundial 2017; MEF PEM. Detalle y hash en `docs/fuentes/fuentes.csv` y `docs/rag/fuentes.csv`.
