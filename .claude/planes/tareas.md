# Microtareas del equipo

Cada tarea dura entre 30 y 90 minutos. Si una se alarga más de 2 horas, se avisa y se parte.
Comandos para todo: [comandos.md](comandos.md). Plan completo: [plan-maestro.md](plan-maestro.md).
Estado al cierre del MVP (2026-11-14): las tareas hechas llevan `[x]` y una nota «MVP». Qué quedó conectado y qué no: [ARCHITECTURE.md](../../ARCHITECTURE.md).

## Equipo

| Código | Persona | Rol | Revisa los PR de |
|---|---|---|---|
| DI | Diego | Analítica IA | Jeffrey |
| MG | Miguel | Backend | Michael |
| JF | Jeffrey | IA Engineer (agente) | Diego |
| MC | Marcela | Frontend | Dixon |
| MI | Michael | Arquitectura de sistema y seguridad ISO 27001 | Miguel |
| DX | Dixon | Arquitectura de datos, diagramas y QA ISTQB | Marcela |

## Cómo nos avisamos

**Cada vez que terminas una tarea**, mandas al grupo:

```
[LISTO] DI-06 Pronóstico v1
Rama: feature/ml-pronostico   PR: #12
Probar: make test
Resultado: MAE 312 vs baseline 455
Desbloquea: MG-06, JF-03
Revisa: Jeffrey
```

**Si estás trabado más de 20 minutos:**

```
[BLOQUEO] MG-02 Ingesta
Qué pasa: falla la carga de glosas con tildes
Necesito: a Dixon (generador)
```

**Cada hora en punto**, una línea por persona: `DI: en DI-05, termino 16:30, sin bloqueos`.

**Checkpoints de 10 minutos (todos):** 12:00, 15:00, 19:00, 23:00, domingo 10:00 y 12:00. Se revisa: qué está hecho, qué bloquea, qué se recorta.

**Testing en equipo:**
1. Quien termina corre `make check` y abre el PR a `develop`.
2. Su revisor baja la rama, corre `make check` y prueba lo que dice «Probar».
3. Si el cambio se ve en la demo, también corre el flujo completo con `make e2e`.
4. Con aprobación, el autor une el PR y avisa `[MERGE] DI-06 en develop`.
5. Todos hacen `git pull` en develop cuando ven un `[MERGE]`.

Marca tus tareas con `[x]` en este archivo dentro de tu mismo PR.

---

## Bloque 1 · Sábado 11:00–12:00 · Contratos (para trabajar en paralelo)

- [ ] **MI-01** Esqueleto del repo: carpetas del plan, `requirements.txt`, `.env.example`, `Makefile` con objetivos vacíos, config de ruff y pytest. *Hecho:* `make check` corre en verde. **Entra a develop antes de las 11:45.** Rama `feature/arq-esqueleto`
- [ ] **MI-02** `docker-compose.yml` con Postgres 16 + pgvector y `make db`. *Hecho:* `make db` levanta y `make psql` conecta. Rama `feature/arq-docker`
- [x] **DX-01** Diccionario de datos v1 (`data/dictionary.md`) junto con Michael y Diego: tablas, columnas, tipos, etiquetas. *Hecho:* los tres lo aprueban. Rama `feature/datos-diccionario` — MVP: `data/dictionary.md`, con test de columnas en `tests/test_generador.py`
- [x] **MG-01** Contrato de la API (`docs/api.md`) junto con Marcela y Jeffrey: endpoints y JSON de ejemplo en `data/sample/mocks/`. *Hecho:* los tres lo aprueban. Rama `feature/backend-contrato` — Miguel, PR #4; aprobado el 2026-11-14 por Marcela, Jeffrey, Diego y Michael fuera de GitHub (registrado en `docs/api.md`, secciones 15 y 16)
- [x] **MC-01** Decidir la UI a las 11:30 (React + Recharts o Streamlit) y esqueleto que navega las 6 pantallas vacías. *Hecho:* se abre en el navegador. Rama `feature/front-esqueleto` — Nakusuo/Marcela, 2026-11-14: React + Recharts; pantallas Cómo estás, Qué viene y Qué hacer con datos de prueba (las demás se agregan cuando hagan falta)
- [x] **JF-01** Instalar Ollama con `qwen2.5:3b` (ajustes de GPU del plan maestro, sección 3) y un modelo de embeddings; anotar versiones en `PROMPTS.md`. Descargar los PDFs del «núcleo del RAG» de `.claude/investigacion/rag-fuentes.md` en `docs/rag/<modulo>/` y armar `docs/rag/fuentes.csv`. Buscar el texto oficial de la Ley 29571. Rama `feature/ia-setup`
- [ ] **DI-01** Lista de variables por cliente y firma de las funciones de baseline (`src/models/baselines.py` con tests vacíos). Rama `feature/ml-baselines`

## Bloque 2 · Sábado 12:00–15:00 · Base que funciona

- [x] **DX-02** Generador v1 **estratificado**: cuotas fijas por arquetipo × perfil de ahorro × perfil de gasto; perfiles por bootstrap desde distribuciones calibradas; transacciones por reglas; quincena; `--seed`. *Hecho:* genera en < 1 min; test «misma semilla = mismo resultado»; test «ningún estrato vacío». Rama `feature/datos-generador` — Diego, PR #9 (`eaac673`), 2026-11-14: `src/generador/`, 500 clientes × 12 meses en 15 s (medido 2026-11-14); pruebas `test_misma_semilla_misma_salida` y `test_ningun_estrato_vacio_ni_peso_extremo`
- [ ] **DX-11** Con el agente `investigador`: ¿se pueden usar los microdatos de la ENAHO (INEI) como base del bootstrap? Licencia, variables útiles, tiempo de preparación. Informe en `.claude/investigacion/enaho.md`. *No bloquea a DX-02.*
- [x] **DX-03** Calendario: grati, CTS, feriados, campaña escolar, Día de la Madre, 28 de julio, Cyber Wow, Navidad, con subida de gasto. *Depende:* DX-02 — MVP: calendario peruano en `src/generador/contexto.py`
- [x] **DX-04** Texto: glosas por comercio y canal, y mensajes con etiqueta de sentimiento (plantillas variadas). *Depende:* DX-02 — Diego, PR #9 (`eaac673`), 2026-11-14: `src/generador/texto.py`
- [ ] **MI-03** `db/init.sql`: esquemas `seguro` y `app`, roles `lucas_app`, `lucas_agente`, `lucas_admin`, RLS, pgcrypto, extensión vector, tablas de memoria (`app.metas`, `app.memoria`, `app.respuestas_reco`). *Hecho:* tests «lucas_agente no puede leer deuda_total» y «un cliente no ve la memoria de otro». Rama `feature/arq-db-seguridad` — MVP: `db/init.sql` existe (esquemas, roles, RLS, pgcrypto); faltan los dos tests y en el MVP nada se conecta a la base
- [ ] **MG-02** Ingesta: validación Pydantic, dedup y carga a Postgres. `make data` completo. *Depende:* DX-02, MI-03. Rama `feature/backend-ingesta`
- [x] **MG-03** FastAPI con los endpoints del contrato devolviendo los mocks. `make run`. *Depende:* MG-01. Rama `feature/backend-api` — MVP: Miguel, PR #10 y #24: 12 rutas con datos fijos de `demo-001` y 99 pruebas; sin `make run`
- [x] **MC-02** Pantallas Cómo estás y Qué viene (gráfico con banda) usando mocks. *Depende:* MG-01. Rama `feature/front-estado-pronostico` — Nakusuo/Marcela, PRs #6, #8 y #15, 2026-11-14: `app/src/api/` lee y valida el contrato con respaldo a `data/sample/mocks/`; las cifras visibles siguen saliendo de `app/src/motor/` hasta que Miguel alinee `demo-001` con la persona del motor (ver `estado.md`)
- [x] **JF-11** `GeminiProvider` como segundo proveedor (Ollama → Gemini → plantillas) según [gemini-api.md](../investigacion/gemini-api.md): clave solo en `.env`, envía solo salidas de tools, timeout y paso a plantilla ante error 429 o sin red. Test: con la red apagada responde por plantilla. *No bloquea a nadie.* Rama `feature/ia-gemini`
- [x] **JF-02** Esqueleto LangGraph: router → tool falsa → redacción → juez → respuesta, con `TemplateProvider`. *Hecho:* test de punta a punta del grafo. Rama `feature/ia-grafo`
- [ ] **DI-02** Variables por cliente calculadas desde transacciones, con test. *Depende:* DX-02. Rama `feature/ml-features`
- [ ] **DI-03** Baselines: promedio móvil de saldo, «mismo comercio ≥ 3 veces», diccionario de glosas. Con tests. *Depende:* DI-02

**Checkpoint 15:00:** `make data` y `make run` funcionan en develop.

## Bloque 3 · Sábado 15:00–19:00 · Primer flujo de punta a punta

- [x] **DI-04** Recurrentes y duplicadas v1; F1 frente al baseline. Rama `feature/ml-recurrentes` — MVP: Diego, PR #25: recurrentes y suscripciones duplicadas en `src/models/clasificacion.py`
- [x] **DI-05** K-Prototypes: k por silueta y estabilidad, cluster por cliente guardado en Postgres, descripción de cada segmento en palabras. Rama `feature/ml-segmentos` — MVP: Diego, PR #25: `src/models/segmentacion.py`, k por silueta; queda en `models/segmentacion.pkl`, no en Postgres
- [x] **DI-06** Pronóstico v1 + banda bootstrap + día de riesgo; MAE frente al baseline. Rama `feature/ml-pronostico` — Diego, PR #9 (`d0f3e2c`), 2026-11-14: `src/models/pronostico.py`, banda al 80 % por conformal (no bootstrap) frente al promedio móvil de 3 meses: MAE S/ 884 contra S/ 1726 y cobertura 80,6 % (`models/metricas.json`)
- [x] **DI-07** Salud 0–100 con componentes y test de monotonicidad. Rama `feature/ml-salud` — Diego, PR #9 (`d0f3e2c`), 2026-11-14: `src/models/salud.py`, prueba `test_salud_es_monotona`
- [ ] **DI-13** Matriz ahorro × gasto encima de los clusters: umbrales (baseline) frente a perfil derivado de K-Prototypes; estabilidad mes a mes y acuerdo con las etiquetas sembradas. *Depende:* DI-05. Rama `feature/ml-perfil-ahorro`
- [ ] **MG-04** Recomendador v1: candidatos por reglas, puntaje impacto × facilidad, ajuste por segmento, reglas de seguridad con un test cada una; tipos protegidos (`bajar_deuda_cara`, `colchon_minimo`) que una preferencia no excluye y exclusiones que nunca dejan entrar crédito (CP-SIS-32). *Depende:* DI-05, DI-07. Rama `feature/backend-recomendador`
- [ ] **MG-05** Motor de eventos v1: ingreso, grati/CTS, fecha de calendario, gasto frecuente, riesgo; máximo 3 avisos por semana (lunes a domingo, Lima) con lugar reservado para el de riesgo; riesgo a 3–7 días normal, a 1–2 urgente, a más de 7 sin aviso; `id` de riesgo = `riesgo` + fecha del próximo ingreso (se actualiza, no se duplica). Con tests de CP-SIS-05, 28 y 29. *Depende:* DI-06. Rama `feature/backend-eventos`
- [ ] **MG-06** Conectar los endpoints a los modelos reales (fuera mocks). *Depende:* DI-05, DI-06, DI-07
- [x] **JF-03** Tools del agente: `get_health`, `get_forecast`, `get_recos`, `simulate`, `get_segment`, con el rol `lucas_agente`; cada tool devuelve también las entradas que usó. *Depende:* MG-03. Rama `feature/ia-tools` — MVP: Jeffrey: `HerramientasAPI` en `src/agent/tools.py`; la API no llama al agente en el MVP
- [x] **JF-04** Nodo juez: verificador de cifras con tolerancia, reintento y plantilla; acepta salidas y entradas de las tools del turno, sus fechas y los números del fragmento citado; filtro de frases prohibidas según las reglas que el cliente no pasa; tests con respuestas trampa (CP-SIS-10, 11, 30 y 31). Rama `feature/ia-juez`
- [x] **MC-03** Pantallas Qué hacer (tarjetas con «¿por qué?») y Avisos (bandeja). Rama `feature/front-recos-avisos` — MVP: PR #17: bandeja de avisos; «Qué hacer» quedó como los tips del Resumen
- [ ] **MC-04** Conectar la UI a la API real. *Depende:* MG-06
- [ ] **MI-04** Makefile completo: `data`, `db`, `test`, `check` (ruff + tests con cobertura + `pip-audit`), `eval`, `run`, `e2e`. Rama `feature/arq-makefile`
- [x] **MG-13** Impacto y valor (D16): Lucas decide al cierre del mes 9 (artefactos de `eval/`) y sus cambios se repiten con `aplicar_cambios` sobre las transacciones reales de los meses 10 a 12, igual que los baselines «no hacer nada» y «apartar 10 % fijo»; adherencia 100 % y simulada con `prob_acepta_reco`, intervalo por bootstrap de clientes; calcula días en rojo evitados, S/ de colchón a 3 meses, intereses evitados (TCEA supuesta en `config/supuestos.yaml`) y % que sube de cuadrante. `eval/valor_banco.py` aplica la calculadora de [rentabilidad-impacto.md](../reglas/rentabilidad-impacto.md) con supuestos visibles. Con Diego. *Depende:* MG-07, DI-06. Rama `feature/backend-impacto` — MVP: lo hizo Diego: `src/models/impacto.py` y `eval/benchmark_y_valor.py` → `models/metricas_impacto.json` y `metricas_valor.json`
- [ ] **MI-10** ISO 27001: completar la evidencia de la declaración de aplicabilidad (`reglas/seguridad-iso27001.md`), sección Activos en `ARCHITECTURE.md`, proteger las ramas `main` y `develop` en GitHub. Rama `feature/arq-iso27001`
- [ ] **DX-13** Plan de pruebas: revisar el catálogo de `planes/pruebas.md` con el agente `tester`, crear la etiqueta `defecto` y la plantilla de issue en GitHub, armar `tests/sistema/` para los casos automatizables. Rama `feature/docs-pruebas-plan`
- [ ] **TODOS-05** Cada persona agrega al catálogo los casos de su módulo (`CP-<código>-NN`) con al menos una técnica de caja negra.
- [ ] **MI-05** `make e2e`: genera muestra → carga → llama a cada endpoint → valida respuestas. Middleware de latencia por endpoint. Rama `feature/arq-e2e`
- [ ] **DX-05** Escenarios difíciles: ingresos irregulares, duplicadas, cambio de patrón, faltantes, atípicos y necesidades ocultas sembradas. Rama `feature/datos-escenarios`
- [ ] **DX-06** Diagramas v1 (Mermaid): arquitectura en 3 capas, flujo de datos, grafo del agente. En `ARCHITECTURE.md`. Rama `feature/docs-diagramas`

**Checkpoint 19:00:** todo el equipo corre el flujo de la demo en develop. Si no funciona, se aplica el orden de recorte del plan. Primero se cierra la **ola 1 (núcleo rentable)** del plan maestro, sección 2; DI-05 puede entregar primero el segmento por umbrales y K-Prototypes después.

## Bloque 4 · Sábado 19:00–23:00 · Demo completa

- [ ] **DX-17 / MG-14 / MC-12** Lucas en 5 preguntas, versión mínima (HU-21, cierra la ola 1 y va antes que cualquier tarea de ola 2): `generar_cliente(respuestas, seed)` en el generador, con las mismas reglas que los 500 clientes (Dixon); endpoint sin token que llama a `calcular_estado` sin base (Miguel); formulario y resultado (Marcela). Segmento por umbrales. Caso CP-SIS-22. Rama `feature/backend-cinco-preguntas`
- [x] **JF-05** RAG por módulos: PDFs en `docs/rag/<modulo>/` con `fuentes.csv`; fragmentos con su módulo en pgvector; el agente busca solo en el módulo que toca; el juez valida que cada cita exista. Rama `feature/ia-rag` — MVP: Jeffrey: `src/agent/rag.py` sobre el índice de Diego en `docs/rag/indice/`
- [x] **JF-06** 30 preguntas fijas y 10 adversas (inyección, «compra dólares», «transfiere») en `tests/agent/`. Rama `feature/ia-tests`
- [ ] **MG-07** Endpoints de simulador y Sueldo Lucas (con Diego). Sueldo Lucas: solo si la volatilidad del ingreso supera el umbral; monto prudente con piso en los fijos (si no los cubre, `falta_para_fijos` y reco, nunca un monto que deje en rojo); sin pago actual, apartar 0 y días con colchón. Caso CP-SIS-33. Rama `feature/backend-simulador`
- [ ] **MG-08** Ofertas: `data/catalogo_ofertas.json` con productos y promociones ficticias o genéricas; reglas por necesidad, cuadrante de la matriz e idoneidad (inversión solo con colchón ≥ 3 meses y sin deuda cara); precision@3 frente a «lo más popular». Rama `feature/backend-ofertas`
- [ ] **MG-11** Metas de ahorro: aporte por quincena que no deja en rojo, proyección a fin de año con la banda del pronóstico y probabilidad de cumplir; frente a la regla del 10 %. Con Diego. *Depende:* DI-06. Rama `feature/backend-metas`
- [ ] **JF-09** Memoria del usuario: nodo que lee memoria al inicio y guarda al final (metas, preferencias y resumen, todo con valores de listas cerradas; nunca texto libre del usuario); endpoint «olvidar lo que sabes de mí». Usa las tablas de MI-03. Rama `feature/ia-memoria`
- [x] **MC-05** Simulador con controles deslizantes y banda que se mueve; formulario «agregar ingreso o gasto» que recalcula. Rama `feature/front-simulador` — MVP: PR #21: simulador en Qué viene, sin controles deslizantes
- [ ] **MC-06** Chat con cifras marcadas ✓ y fuentes del RAG. Rama `feature/front-chat` — Nakusuo/Marcela, PR #16, 2026-11-14: el front ya muestra ✓, fuentes y respaldo a plantillas; `POST /api/v1/chat` existe pero es un mock sin verificar, así que en el MVP el chat responde con plantillas
- [x] **MC-11** Pantalla Metas (crear meta, aporte por quincena, proyección a diciembre) y botones «útil / no me sirve» en cada recomendación; opción «olvidar lo que sabes de mí». Rama `feature/front-metas` — MVP: PR #21: pantalla Metas; «útil / no me sirve» quedó en Avisos y «olvidar» es retirar el permiso
- [ ] **DI-08** Pronóstico global frente a global + cluster frente a uno por cluster; MAE por segmento. Rama `feature/ml-por-segmento`
- [x] **DI-09** Clasificador de glosa TF-IDF frente a diccionario; F1 por categoría. Rama `feature/ml-glosa` — MVP: Diego: `models/glosa.pkl`, métricas en `models/metricas_clasificacion.json`
- [ ] **MI-06** Demo de seguridad: script que muestra a `lucas_agente` bloqueado por Postgres; documentarlo. Rama `feature/arq-demo-seguridad`
- [ ] **MI-11** Pruebas de seguridad (ISO 8.29): `tests/seguridad/` con inyección SQL, acceso a otro cliente, logs sin datos sensibles (8.11) y `pip-audit` sin vulnerabilidades altas. Rama `feature/arq-pruebas-seguridad`
- [ ] **DX-14** **Ciclo 1 de pruebas de sistema (23:00)** con el agente `tester`: ejecutar el catálogo, registrar resultados y abrir defectos. Resumen en el checkpoint.
- [ ] **MI-07** Instalar desde cero en la laptop de la demo siguiendo solo el README; anotar lo que falte. 
- [x] **DX-07** `QUALITY.md` generado por script y calibración con cifras públicas (con el agente `investigador`). Rama `feature/datos-calidad` — MVP: `data/QUALITY.md`, generado por `src/generador/reporte.py`
- [ ] **TODOS-01** Cada persona escribe 17 frases reales sobre plata (alegría, preocupación, neutras) para el set de 100 de sentimiento. Dixon las junta en `data/eval/frases.csv`.

**Checkpoint 23:00:** demo completa, aunque fea. Se decide qué DEBERÍA entra el domingo.

## Bloque 5 · Domingo 08:00–10:00 · Evidencia

- [x] **DI-10** `make eval` → `EVALUATION.md` con intervalos y pruebas con perturbaciones. Rama `feature/ml-eval` — MVP: Diego: `docs/EVALUACION_ANALITICA.md`, generado por `eval/generar_docs.py`; no hay `make eval` ni `EVALUATION.md`
- [x] **JF-07** Métricas del agente (% cifras verificadas, % citas válidas, exactitud, bloqueo adverso) en `EVALUATION.md`. Rama `feature/ia-eval` — MVP: `eval/evaluar_chat.py` → `models/metricas_chat_*.json`
- [x] **MC-07** Panel Evidencia con los resultados de `make eval`, empezando por el impacto en S/ de MG-13. Rama `feature/front-evidencia` — MVP: PR #17: panel `/evidencia` leído de `models/metricas*.json`
- [ ] **MG-09** Manejo de errores y timeouts; tests de la API. Rama `feature/backend-robustez`
- [ ] **MI-08** Pasar el agente `juez-cumplimiento`; `git grep` de secretos; corregir lo bloqueante. Rama `fix/arq-cumplimiento`
- [ ] **DX-08** README v1 y guion del pitch v1, con el minuto de impacto y valor para el banco de [rentabilidad-impacto.md](../reglas/rentabilidad-impacto.md) y respuestas de 20 s a «¿por qué pagaría un banco?», «¿cuánto cuesta?» y «¿qué tiene de nuevo?». Rama `feature/docs-readme-pitch`
- [ ] **DX-15** **Ciclo 2: regresión completa (10:00)**. Pruebas de confirmación de los defectos cerrados. Informe de pruebas en `EVALUATION.md`.

## Bloque 6 · Domingo 10:00–12:00 · DEBERÍA y pulido

- [x] **DI-11** Sentimiento con modelo preentrenado frente a léxico, medido en las 100 frases. — MVP: Diego: `models/sentimiento.pkl`, métricas en `models/metricas_clasificacion.json`
- [ ] **DI-12** Lucas en 5 preguntas, ola 2: asignación a cluster K-Prototypes y MAE con 0, 1 y 3 meses frente al promedio poblacional. *Depende:* DX-17 / MG-14 / MC-12.
- [x] **JF-08** BCRP: tipo de cambio e inflación con caché y serie grabada de respaldo.
- [ ] **JF-10 / MG-12** Aprendizaje por respuestas: pesos por tipo de recomendación y segmento que suben o bajan con «útil / no me sirve»; simulación con `prob_acepta_reco` frente al recomendador sin memoria.
- [ ] **DX-12** Si DX-11 dio luz verde: base semilla del bootstrap desde la ENAHO y regenerar datos (`make data`); comparar métricas antes y después.
- [x] **MC-09** Pulido: claro y oscuro, 1366×768, celular, checklist anti-slop de `reglas/calidad-codigo.md`. — MVP: rediseño móvil (PR #29): claro y oscuro, 1366×768 y 390 px
- [ ] **TODOS-02** Prueba de evolución si la anuncian (protocolo del plan, sección 8).
- [ ] **TODOS-03** Pasar el agente `juez-producto` y aplicar los 3 cambios que más suben la nota.

**12:00 congelamiento:** no entran funcionalidades nuevas.

## Bloque 7 · Domingo 12:00 en adelante · Entrega

- [ ] **DX-16** **Prueba de aceptación** sobre `release/entrega`: casos críticos y flujo de la demo. Solo si cumple los criterios de salida se hace el merge a `main`.
- [ ] **MI-09** Rama `release/entrega`, `make check` y `make e2e` en verde, DX-16 aprobada, merge a `main` y etiqueta `v1.0-entrega`.
- [ ] **DX-09** `ARCHITECTURE.md` final con diagramas y `PROMPTS.md` revisado con Jeffrey.
- [ ] **MC-10 / DX-10** Video de respaldo de la demo (3 a 4 min) y capturas en `demo/`. — MVP: capturas listas en `demo/capturas/`; falta el video
- [ ] **TODOS-04** 3 ensayos cronometrados (10:00 exactos) y simulacro de preguntas del jurado.
