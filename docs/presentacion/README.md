# Presentacion y documentacion: graficas y diagramas

Esta carpeta reune **todas las graficas, diagramas y artefactos generados** para la presentacion final y para la documentacion que pidan los organizadores. Nada esta dibujado a mano: salen de `models/*.json` y de los grafos reales del agente. Se regeneran con `python eval/comparativa_modelos.py` (modelos) y `python eval/construir_presentacion.py` (el resto).

**Como usarlas en la presentacion:** una imagen por diapositiva; el titulo de cada grafica ya dice el mensaje. En las de modelos, azul rayado = el modelo elegido y gris = su baseline o alternativa descartada: es la respuesta a «por que este modelo». Todo es con datos sinteticos y lo dice en el pie de cada imagen.

| Archivo | Que mensaje defiende |
|---|---|
| `modelos/comparativa_modelos.png` | Panel general: para cada problema, el modelo elegido (azul rayado) frente a sus baselines y alternativas (gris). Por que cada modelo. |
| `modelos/mejora_en_porcentaje.png` | Cuanto mejora el modelo elegido, en porcentaje: frente al rival mas fuerte de cada problema (numero conservador) y frente al mas debil; los empates se dicen. |
| `modelos/01_segmentacion.png` | Segmentacion: K-Prototypes recupera los arquetipos reales que K-means y las reglas 2x2 no. |
| `modelos/02_saldo_30_dias.png` | Pronostico a 30 dias: menos error que el promedio movil y banda al 80 % que de verdad cubre el 80 %. |
| `modelos/03_alerta_rojo.png` | Alerta de saldo en rojo: mejor PR-AUC que una regla simple (evento raro). |
| `modelos/04_dia_de_riesgo.png` | Dia de riesgo: error en dias del modelo frente a las alternativas. |
| `modelos/05_proyeccion_mensual_error.png` | Proyeccion mensual de ingresos, gastos y neto: error frente a baselines. |
| `modelos/06_proyeccion_mensual_cobertura.png` | Proyeccion mensual: cobertura de la banda al 80 %. |
| `modelos/07_glosas.png` | Categoria de cada movimiento (glosa): el modelo supera al diccionario. |
| `modelos/08_gastos_recurrentes.png` | Gastos fijos y suscripciones duplicadas: periodicidad y monto superan a la regla de tres veces el mismo comercio. |
| `modelos/09_atipicos.png` | Movimientos atipicos: IsolationForest frente al z-score robusto. |
| `modelos/10_sentimiento.png` | Sentimiento: en un set independiente el modelo entrenado supera al lexico; el lexico solo parecia bueno con frases de su propio autor. No esta en produccion. |
| `modelos/11_politica_de_ahorro.png` | Politica de ahorro: Lucas + ahorro automatico evita dias en rojo y forma colchon; apartar a ciegas empeora la caja. |
| `modelos/12_agente.png` | Arquitectura del agente: agente unico y multiagente miden igual; se usa el mas simple y auditable. |
| `modelos/13_rag.png` | Recuperacion de fuentes (RAG): recall@4 con filtro de modulo para cada configuracion. |
| `modelos/14_serie_diaria.png` | Serie diaria del pronostico: mejor que la recta al dia 30 y que el promedio movil, con la banda medida en cada uno de los 30 dias. |
| `graficas/serie_diaria_cobertura_y_error_por_dia.png` | La banda al 80 % cubre entre 0.79 y 0.86 en los 30 dias; el error es menor que el de las dos lineas base en cada dia. |
| `graficas/serie_diaria_ejemplo_de_un_cliente.png` | Lo que ve un cliente: su saldo esperado, la banda y el primer dia de riesgo (contrato del endpoint /forecast). |
| `graficas/politica_de_ahorro_dias_en_rojo_y_colchon.png` | Impacto: dias en rojo evitados y colchon formado por cada politica, con la prueba de estres del ahorro bloqueado. |
| `graficas/programa_de_puntos_proyeccion_a_futuro.png` | Rentabilidad del programa de puntos a 5 anios: cuando se paga y con que supuestos (sin piloto, no es una promesa). |
| `graficas/segmentacion_eleccion_de_k.png` | Por que 5 segmentos: mayor silueta entre los k con estabilidad suficiente. |
| `graficas/calendario_laboral_2026_2027.png` | El agente conoce gratificacion y CTS y avisa que la libre disposicion del 100 % de la CTS vence el 31 de diciembre de 2026. |
| `diagramas/arquitectura_del_sistema.png` | Arquitectura: modelos calculan, el LLM solo redacta, un verificador determinista cuida cada cifra; salvaguardas si el LLM falla. |
| `diagramas/agente_ahorro_de_tokens.png` | Como optimizamos tokens: un parrafo de consultas, el router, plantillas, preguntas frecuentes y solo lo nuevo al agente de IA con RAG (chunks, embeddings, top-3), con tokens medidos. |
| `graficas/ahorro_en_porcentaje_y_soles.png` | Cuanto ahorra Lucas, en porcentajes y en soles: ruteo (menos tokens), RAG (99.9 % menos lectura), en que se va una llamada (mensaje, lectura, respuesta) y soles por cada 100 mil consultas. |
| `mapa_de_consultas.json` | Los datos de ese ejemplo: intencion y camino de cada consulta, fragmentos que devolvio el RAG, tokens, precio, tipo de cambio y costos en soles. |
| `diagramas/rag_arquitectura.png` | RAG de punta a punta: fuentes, troceado 900/120, embeddings nomic-embed-text, indice, consulta con filtro de relevancia, verificador, citas y preguntas frecuentes que ahorran tokens. |
| `diagramas/modelo_de_datos.png` | Modelo de datos de PostgreSQL con pgvector: 25 tablas en dos esquemas (lucas y simulacion), probado con la data sintetica completa. |
| `diagramas/grafo_agente_unico.png` | Nodos del agente unico (LangGraph), dibujado desde el grafo real. |
| `diagramas/grafo_multiagente.png` | Nodos del multiagente (supervisor), dibujado desde el grafo real. |
| `diagramas/grafo_agente_unico.md` | El mismo grafo en Mermaid (se ve en GitHub); fuente: app.get_graph().draw_mermaid(). |
| `diagramas/grafo_multiagente.md` | El mismo grafo del multiagente en Mermaid. |
| `mlflow_resumen.md` | Seguimiento con MLflow: cada comparacion (baseline frente a elegido) como corrida y cada modelo de produccion registrado con alias produccion. |

Tablas y explicacion de cada eleccion (con su limite): `docs/comparativa_modelos.md`. Informe completo: `docs/RESUMEN_DIEGO.md`. QA: `docs/QA_ANALITICA.md`.
