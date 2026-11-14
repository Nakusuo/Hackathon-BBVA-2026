# Resumen de lo hecho: analitica e IA (Diego)

Registro de **que se hizo, que se cambio, que se mejoro, que se agrego y que se quito**, con el motivo. Las cifras salen de `models/metricas*.json` (ver [EVALUACION_ANALITICA.md](EVALUACION_ANALITICA.md)). Entidad y marca de ejemplo: **Banco Kawsay**, app **Lucas** (nombres inventados, `data/parametros/entidad.yaml`).

## 1. Como correrlo
```bash
python data/generator.py --perfil muestra      # 40 clientes, 12 meses, 1 s, queda en data/sample
python data/generator.py --perfil completo     # 500 clientes, 2019-2025, ~30 s, 0,5 GB de RAM
python -m src.datos_publicos.descargar         # fuentes oficiales y series del BCRP
python -m src.rag.indice                       # reconstruye el indice del RAG (requiere Ollama con nomic-embed-text)
python eval/entrenar_modelos.py                # entrena y evalua; guarda models/*.pkl y models/metricas_*.json
python eval/evaluar_agente.py --llm plantillas # evalua el agente (tambien --llm ollama o gemini)
python eval/construir_notebooks.py             # ejecuta los notebooks de notebooks/
python eval/generar_docs.py                    # regenera estos documentos
python -m pytest tests -q                      # 57 pruebas
```
Claves solo en `.env` (no se sube). `LLM_PROVIDER=ollama|gemini|plantillas`. Las rutas se calculan desde la raiz del repo (`src/comun/rutas.py`); una prueba impide rutas absolutas.

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
| No adoptado | Busqueda hibrida como defecto | La densa con filtro de modulo recupera mejor |
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
- RAG: mejor configuracion `denso + filtro de modulo` con recall@4 0.95 y MRR 0.89.
- Agente (plantillas): ruteo 0.978, respuestas sin cifras inventadas 1.000, pedidos prohibidos rechazados 1.0.

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
- La busqueda hibrida no supera a la densa con filtro de modulo; el filtro de relevancia separa bien pero con margen estrecho entre la pregunta con respuesta mas baja y la de fuera mas alta.
- Lucas baja los dias en rojo sin pedir cambios de habito, pero no construye colchon como lo hace apartar el 10 % recortando gasto (que supone recortes sin costo); el contrafactual solo incluye Sueldo Lucas, suscripcion duplicada, gasto hormiga y la alerta del pronostico.
- Con los supuestos del equipo, el valor neto anual para la entidad es **negativo** si el usuario promedio gana 120 puntos al mes: el fondeo de lo apartado deja menos de lo que cuestan los puntos. El programa se sostiene por debajo de unos 80 puntos al mes por usuario o premiando solo conductas que generen ingreso; la retencion, la mora evitada y la venta cruzada idonea no se valoran sin un piloto.
- Latencia medida el 14-nov en esta laptop (sin GPU NVIDIA): plantillas ~1 s, Gemini 3.5 flash-lite 3 a 12 s con juez, Ollama qwen2.5:3b en CPU ~67 s por respuesta (con cifras verificadas pero redaccion regular). Para la demo conviene Gemini o plantillas; Ollama en una laptop con GPU.
- La vigilancia en vivo detecto sola el comunicado N.o 20-2026 del ENFEN (13-nov), que el RAG no tenia; se agrego al indice y el mapa de zonas se actualizo (Ica pasa a exposicion media y la vigencia llega a julio de 2027).
- Las magnitudes de los eventos y de los retiros AFP son supuestos del equipo salvo donde se cita una fuente; una cifra sin fuente nunca se presenta como verificada.
- Los modelos pueden descubrir lo que el generador sembro: por eso hay baselines, perturbaciones, evento no visto y otra semilla (pendiente de correr la prueba con otra semilla completa).

## 7. Escalabilidad, rentabilidad, innovacion e impacto
**Escalabilidad medida** (esta laptop, 500 clientes): {"clientes": 500, "carga_modelos_y_datos_s": 4.1, "contexto_por_cliente_ms": 3.32, "recomendaciones_por_cliente_ms": 0.43, "recomendaciones_por_segundo": 2319.0, "pico_memoria_gb": 0.81, "pronostico_30d_filas": 500, "pronostico_30d_ms_por_cliente": 0.084}

**Valor para la entidad** (escenario conservador, supuestos visibles): por cliente, colchon adicional S/ 322, 0.24 dias en rojo evitados al mes. Con 100,000 usuarios: margen por fondeo S/ 965,094, costo de puntos S/ 1,440,000, neto S/ -474,906 al anio. solo cuenta el fondeo de lo apartado; retencion, mora evitada y venta cruzada idonea no se valoran sin piloto.

Supuestos: {"margen_anual_sobre_saldo_apartado": 0.03, "usuarios_activos_escenario_conservador": 100000, "puntos_promedio_por_usuario_al_mes": 120, "aceptacion_de_la_recomendacion": "ya incluida: el impacto se simulo con la probabilidad de aceptacion de cada cliente", "retencion_y_mora": "no se asigna valor: no hay evidencia publica causal; lo mediria un piloto con grupo de control"}

- **Escalable**: nada en el codigo depende de una entidad; nombre, catalogo, margenes y politicas estan en archivos de configuracion. El generador y el pronostico trabajan por lotes; el agente es sin estado entre llamadas (la memoria es un archivo por usuario, reemplazable por una base).
- **Innovacion**: banda de pronostico distinta para ingreso irregular, proyeccion por meses, alerta de El Nino por zona con fuente oficial, Sueldo Lucas, avisos en tiempo real, niveles con nombre, juez doble que impide cifras inventadas.
- **Impacto**: ver la seccion 5 de la evaluacion; el efecto en retencion y mora lo mediria un piloto con grupo de control.

## 8. Integracion con el equipo
- Modelos: `models/*.pkl` (joblib, versiones en el manifiesto; abrirlos solo desde este repo). Cargar con `src/agente_analitico/repositorio.py`.
- Funciones para el backend: `Repositorio.contexto(cid)`, `Repositorio.proyeccion_mensual(cid)`, `recomendador.recomendar(ctx)`, `grafo.construir_grafo(repo, buscador, modo)` y `grafo.responder(app, cid, pregunta | evento)`.
- Interfaz web: llama a `responder` y muestra `respuesta`, `citas`, `cifras_verificadas` y `recomendaciones`. La memoria del usuario (`src/agente_analitico/memoria.py`) permite ver y olvidar.
- Avisos: `src/agente_analitico/vigilancia.py` (baja de tasa, ingreso extra, comunicado del ENFEN, riesgo de rojo; maximo 3 por semana).
- Postgres y pgvector del equipo: el indice FAISS puede cargarse a pgvector desde `docs/rag/indice/` (mismo modelo de embeddings, 768 dimensiones).

## 9. Pendientes y preguntas a la organizacion
LLM externo autorizado (hoy Gemini gratuito solo con datos sin identificadores), datos publicos de calibracion (ENAHO), prueba de evolucion, formato de entrega, licencia de las guias de nivel C, verificar normas y fechas de los retiros AFP, set independiente de frases para el sentimiento.

## 10. Fuentes
INEI EPEN I trim. 2026 (cuadros 1.20, 1.28 a 1.30); ENFEN comunicados 15 a 19 de 2026; BCRP (API de series); SBS Res. 3274-2017; DS 016-2024-JUS; CFPB; Banco Mundial 2017; MEF PEM. Detalle y hash en `docs/fuentes/fuentes.csv` y `docs/rag/fuentes.csv`.
