# Estado del proyecto

Actualizar en cada checkpoint (12:00, 15:00, 19:00, 23:00, dom 10:00 y 12:00).
El avance tarea por tarea se marca en [tareas.md](tareas.md).

## Equipo y roles

| Persona | Rol | Agentes de apoyo | Revisa a |
|---|---|---|---|
| Diego | Analítica IA | `ml-analitica` | Jeffrey |
| Miguel | Backend | `backend` | Michael |
| Jeffrey | IA Engineer (agente) | `ia-chat` | Diego |
| Marcela | Frontend | `frontend-ux` | Dixon |
| Michael | Arquitectura de sistema y seguridad (ISO 27001) | `backend`, `juez-cumplimiento` | Miguel |
| Dixon | Arquitectura de datos, diagramas y QA (ISTQB) | `datos`, `pitch-docs`, `tester` | Marcela |

Todos pueden usar `investigador`, `codificador`, `juez-tecnico` y `juez-producto`.

## Decisiones tomadas

| Fecha | Decisión | Motivo |
|---|---|---|
| 2026-11-14 | Problema principal: liquidez a 30 días | Bases: un problema, una población |
| 2026-11-14 | Lucas como compañero bancario: avisos anticipados, Sueldo Lucas, Lucas en 5 preguntas | Indicación del juez: fidelización y atracción |
| 2026-11-14 | PostgreSQL único (esquemas seguro/app, RLS, pgcrypto, JSONB, pgvector). Sin NoSQL ni DuckDB | Seguridad demostrable, una sola base |
| 2026-11-14 | Texto: glosa de movimientos (clasificación) y mensajes (sentimiento con modelo preentrenado) | NLP ligado a decisiones |
| 2026-11-14 | K-Prototypes pasa a DEBE; pronóstico global vs por segmento vs baseline | Personalización medible |
| 2026-11-14 | Un agente LangGraph con tools sobre nuestros modelos, RAG en pgvector y nodo juez | Sin cifras inventadas, con fuentes |
| 2026-11-14 | Motor de eventos (ingreso, grati/CTS, calendario, gasto, riesgo), máximo 3 avisos por semana | Lucas habla primero sin hacer spam |
| 2026-11-14 | Ofertas solo de tipos genéricos, por necesidad e idoneidad | Fidelización responsable |
| 2026-11-14 | Lucas aprende del usuario: matriz ahorro × gasto, metas a fin de año, memoria del usuario en Postgres, «útil / no me sirve» | Mejorar al usuario y fidelizarlo |
| 2026-11-14 | Ofertas y promociones desde un catálogo ficticio configurable, no productos reales de BBVA | Bases: prohibido aparentar producto oficial |
| 2026-11-14 | Datos: generación estratificada + bootstrap de perfiles; ENAHO como base semilla si la licencia lo permite | Evitar sesgo |
| 2026-11-14 | RAG por módulos (salud, ahorro, deudas, inversión básica, seguros, derechos) con fuentes y licencia | Educación ligada a cada recomendación |
| 2026-11-14 | Seguridad alineada con 23 controles de ISO/IEC 27001:2022 (sin certificación); responsable Michael | Confianza bancaria y calidad técnica |
| 2026-11-14 | Pruebas con método ISTQB: 4 niveles, 3 ciclos, criterios de salida; coordina Dixon con el agente tester | Pruebas funcionales del sistema demostrables |
| 2026-11-14 | Descartado: NoSQL, GraphRAG, deep learning desde cero, multimodal, varios agentes, ubicación exacta | Sin puntos extra y riesgo de tiempo |
| 2026-11-14 | Gitflow simplificado; flujo investigador, codificador y jueces; revisión cruzada en parejas | Control y verificación |
| — | UI: React + Recharts o Streamlit (Marcela decide a las 11:30) | — |

## Respuestas de la organización

| Pregunta | Respuesta |
|---|---|
| LLM externo con clave propia | — |
| Dataset común | — |
| APIs públicas en la demo | — |
| Formato de entrega y hora de cierre | — |
| Prueba de evolución | — |
| Modelos/dependencias descargados de antemano | — |
| Uso de las guías de la SBS en el RAG | — |

## Checkpoints

| Hora | Meta | Estado | Notas |
|---|---|---|---|
| Sáb 12:00 | Contratos listos, esqueleto en develop | — | |
| Sáb 15:00 | `make data` y `make run` funcionan | — | |
| Sáb 19:00 | Primer flujo de punta a punta | — | |
| Sáb 23:00 | Demo completa | — | |
| Dom 10:00 | EVALUATION.md con números reales | — | |
| Dom 12:00 | Congelamiento | — | |

## Bloqueos y recortes

| Fecha y hora | Qué | Acción |
|---|---|---|
| — | — | — |
