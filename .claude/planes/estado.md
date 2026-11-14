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
| 2026-11-14 | Verificación de rentabilidad: 6 palancas de ingreso, calculadora con supuestos visibles, modelo B2B2C (gratis para el usuario, licencia al banco). Descartada la comisión por producto vendido | El jurado preguntará por qué un banco pagaría; coherente con «no es venta disfrazada» |
| 2026-11-14 | Métricas de impacto en S/ por cliente (D16, tarea MG-13) | Impacto entendible y medido frente a baseline |
| 2026-11-14 | Movimientos planificados: el usuario registra gastos o ingresos hasta `hoy + 30` y entran al pronóstico en su fecha (revisión adversarial C1) | Sin esto Lucas no puede adelantarse a lo que el usuario ya sabe que viene |
| 2026-11-14 | Sesión de demo: elegir persona = `POST /sesion`, token HMAC con `SESION_CLAVE`, rutas `/yo/...` (revisión adversarial C2) | Sin sesión, cualquiera pedía los datos de otro cliente cambiando el id de la URL |
| 2026-11-14 | `app.perfil` suma `deuda_cara` y `deuda_cara_tramo`, derivados en la ingesta; umbrales de deuda alta y cara en `supuestos.yaml` (revisión adversarial C3) | La regla de idoneidad necesitaba saber si hay deuda cara sin exponer la TCEA |
| 2026-11-14 | Impacto D16 por repetición: Lucas decide al cierre del mes 9 y sus cambios se aplican a los meses 10 a 12 reales del generador, con adherencia 100 % y simulada (revisión adversarial C4) | Medir con el mismo pronóstico que elige las acciones era circular |
| 2026-11-14 | «Lucas en 5 preguntas» mínimo pasa a DEBE al cierre de la ola 1 y sale del orden de recorte; la comparación de MAE queda en ola 2 (revisión adversarial C5) | Era la única pieza de atracción y la primera que se recortaba |
| 2026-11-14 | Avisos: riesgo a 3–7 días normal, 1–2 urgente, > 7 sin aviso; semana lunes a domingo; un aviso por hueco (`riesgo` + próximo ingreso, se actualiza); lugar reservado para riesgo (revisión adversarial A1) | El guion no disparaba el aviso y un gasto en vivo duplicaba avisos y tapaba el de la grati |
| 2026-11-14 | Fuentes de cifras en lista cerrada (estado_cliente, eval, bcrp, fragmento RAG); las tools devuelven sus entradas y el juez solo acepta números que pasaron por una tool o por la cita (revisión adversarial A2) | Toda pregunta «¿me alcanza con S/ X?» caía en plantilla y las citas de normas fallaban |
| 2026-11-14 | Memoria estructurada (listas cerradas, sin texto libre), tipos de reco protegidos y filtro de frases prohibidas en el juez (revisión adversarial A3) | Una inyección quedaba guardada entre sesiones y una preferencia podía ocultar la deuda cara |
| 2026-11-14 | Sueldo Lucas: elegible por volatilidad del ingreso, monto prudente con piso en los fijos (si no alcanza, alerta y reco), sin pago apartar 0; éxito medido en conjunto (revisión adversarial A4) | Podía recomendar un sueldo que deja en rojo y su criterio fallaba por azar |
| 2026-11-14 | Trazabilidad por historia: cada criterio apunta a un caso de sistema o a un test de componente con nombre; catálogo con 48 casos (revisión adversarial A5) | La matriz por módulo marcaba como cubiertos criterios sin ninguna prueba |
| 2026-11-14 | Construcción en dos olas: núcleo rentable hasta las 19:00, profundidad después | 15 módulos DEBE no caben sin orden |
| 2026-11-14 | LLM: Ollama → Gemini `gemini-3.5-flash-lite` en nivel gratuito (apagado por defecto, solo salidas de tools) → plantillas. Embeddings siempre locales | Respaldo sin costo si Ollama falla; el nivel gratuito usa los prompts, por eso nada personal |
| 2026-11-14 | LLM local `qwen2.5:3b` 100 % en la RTX 3050 (4 GB), contexto 4096, flash attention, KV q8 y modelo siempre cargado (Michael) | Cabe entero en VRAM y cumple < 8 s; el resto del pipeline va en CPU |
| — | UI: React + Recharts o Streamlit (Marcela decide a las 11:30) | — |

## Respuestas de la organización

| Pregunta | Respuesta |
|---|---|
| LLM externo con clave propia (Gemini gratis, datos sintéticos) | — |
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
