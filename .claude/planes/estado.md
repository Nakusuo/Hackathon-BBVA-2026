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
| 2026-11-14 | Un solo agente en el producto: `/api/v1/chat` usa `src/agente_analitico` (reglas de Diego) con simular, ahorro y ofertas; `src/agent` queda sin uso hasta decidir si se borra | Pedido de Marcela: dos agentes daban respuestas distintas y ninguno llegaba al front |
| 2026-11-14 | Los modelos leen de Postgres (`LUCAS_FUENTE_DATOS=postgres`, esquema `lucas`); las pruebas siguen sobre los Parquet | La demo corre contra la base, las pruebas no dependen de Docker |
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
| 2026-11-14 | UI: React + Recharts con Vite, en `app/`. Identidad propia de Lucas: grises azulados para leer (tinta `#1b2433`), petróleo para datos (`#1f6b8a`) y ámbar como único acento de marca (`#e8a33d`); títulos Source Serif 4 y texto Plus Jakarta Sans, instaladas como paquete. Inspirada en los principios de banca empática (claridad, calma, accesibilidad), sin logos, tipografías ni colores de BBVA. Pantallas: Cómo estás, Qué viene, Qué hacer; las demás cuando hagan falta. Cada pantalla cabe en 1366×768 (Nakusuo/Marcela) | App que se ve real y lista para integrarse en un banco sin aparentar producto oficial; el juez-cumplimiento marcó dos azules muy cercanos a BBVA y se cambiaron |
| 2026-11-14 | UI v2 (Nakusuo/Marcela): Lucas dentro de una banca genérica «Mi Banca» (ingreso con datos ficticios → inicio de banca → Lucas al centro de la barra y tarjeta de aviso → espacio Lucas con Resumen, Gastos, Qué viene y Chat → guía de 3 pasos la primera vez). Solo modo claro, blancos y azul petróleo `#1b6378`, crema `#f5eedd` para Lucas. Íconos Phosphor. Chat por plantillas con cifras del motor hasta que exista el agente (JF-02) | Mostrar a Lucas como lo usaría un cliente dentro de su banca; investigación en `.claude/investigacion/ui-banca.md` |
| 2026-11-14 | Front en modo oscuro: fondo carbón neutro, un solo acento azul eléctrico (a más de 20 puntos de los azules de BBVA), vidrio y brillo solo en la tarjeta protagonista, sin morado ni rosa, celular primero (pantalla principal en 1.5 pantallas, detalle aparte) y gráficas con etiquetas visibles. Reemplaza «solo modo claro». Nakusuo/Marcela | Pedido de Marcela con referencias de apps financieras; el diseño claro se veía plano y con mucho scroll |
| 2026-11-14 | Bandeja de avisos (MC-03): solo avisan los pagos con algo que hacer (un tip que los pausa); los demás se ven en Qué viene sin gastar el tope. Con el rojo a más de 7 días, la tarjeta de la banca dice «Lucas lo ve venir» y no gasta aviso. Mientras no haya `p_rojo`, «qué tan seguro» sale de comparar lo esperado con el peor caso (Nakusuo/Marcela) | Juez-producto: los pagos sin acción eran relleno y la banca contradecía a la bandeja |
| 2026-11-14 | Casos de uso UML en `docs/casos-uso.md`: 11 casos de objetivo + CU-12 incluido, agrupados por objetivo con matriz HU → CU → CP-SIS; diagrama PlantUML exportado a SVG. Las fichas solo citan rutas de ARCHITECTURE.md (Michael) | Entregable formal para el jurado y referencia del equipo; `docs/api.md` pone `customer_id` en la URL y choca con HU-12 |
| 2026-11-14 | Front conectado a la API (MG-01, MC-02) con «motor manda, API detrás»: las cifras visibles y «Lo hago» siguen saliendo de `app/src/motor/`; `app/src/api/` lee y valida los 6 endpoints, pasa a `data/sample/mocks/` si la API falla y Lucas lo avisa. Nakusuo/Marcela | La API devuelve otra persona (`demo-001`: saldo 1500 −10/día, nunca en rojo, salud 72) que el motor (1240, rojo antes del cobro, salud 60); mostrarla tal cual contradecía las pantallas y borraba el aviso de la demo |
| 2026-11-14 | Documentación adecuada al MVP: historias, casos de uso (10 casos, diagrama regenerado), ARCHITECTURE.md, arquitectura de datos, README y README_BACKEND describen solo lo que corre en `develop`. Fuera: «Lucas en 5 preguntas», Sueldo Lucas, grati/CTS, cuadrante, ofertas, RAG en la app, sesión `/yo/...` con token, Postgres en uso, persona mixta, resumen de quincena y negocio/casa. Se conservan los números de historia que cita el código (Michael) | La documentación prometía rutas, base y pantallas que no existen; el jurado y el equipo necesitan ver lo que hay |

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
| 2026-11-14 | El impacto de `make eval` simula la alerta a 14 días y con `p_rojo` ≥ 0,25; la app avisa a 7 días y sin probabilidad, porque el front no tiene `p_rojo` (la bandeja lo dice en Evidencia) | ML (Diego) alinea `src/models/impacto.py` a 7 días y regenera, o el equipo cambia la regla; backend (Miguel) expone `p_rojo` en la ruta de avisos (MG-05) para que cada aviso muestre su confianza |
| 2026-11-14 | Pendientes del juez en el PR #10 que frenan pasar cifras de la API al front (sin arreglar en `feature/front-api`): 1) signo de `expense` en `POST /simulations` (el endpoint resta 200 y `simulation.json` suma 200: no se sabe si un recorte va como `expense` o como `income`); 2) `horizon_days`, `changes` y `amount` sin tope; 3) al forecast le faltan `first_risk_date`, `model` y `sample_only`, y no lee `days` (el front no puede tomar el día de riesgo de la API); 4) cifras escritas en el código en vez de leer `data/sample/mocks/`, y de otra persona que el motor del front; 5) `rate` sale como texto (el front lo convierte con `Number`) | Backend (Miguel). Al cerrar 1, 3 y 4 el front puede tomar sus cifras de la API; la ✓ espera además al verificador (Jeffrey) |
| 2026-11-14 | `simularCambios` (POST /simulations), el tipo de cambio y el resto de `fuentes` de `app/src/api/` se cargan y se validan, pero ninguna pantalla los muestra. No presentarlos en la demo como funcionando | Front (Nakusuo/Marcela) al cerrar los pendientes del PR #10; alinear `demo-001` con la persona del motor del front (Miguel) para que al menos el pronóstico o la salud salgan del servidor |
