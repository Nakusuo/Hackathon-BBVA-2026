# PLAN MAESTRO v2: «Lucas», tu compañero de plata

**Hackathon BBVA · AI Financial Life · 14 y 15 de noviembre de 2026 · Equipo 2**

> **Principio rector (bases):** la mejor solución no es la más compleja, sino la que convierte datos e IA en una decisión financiera más clara, segura y demostrablemente útil.

> **Indicación del juez (14/11):** la IA tiene que ser el **compañero bancario** del cliente. Debe atacar necesidades reales de clientes actuales (**fidelización**) y futuros (**atracción**). No basta una demo cosmética ni un chatbot genérico.

Versión 1 (brief del 13/11 y bases finales): `~/Escritorio/PLAN_MAESTRO_LUCAS.md`. Esta versión suma lo decidido el sábado 14 por la mañana.

---

## 0. Qué cambió en la v2

| Antes (v1) | Ahora (v2) | Motivo |
|---|---|---|
| Lucas responde cuando le preguntan | **Lucas se adelanta**: motor de eventos con avisos (ingresos, grati, CTS, fechas, gastos, riesgo) | Compañero, no chatbot |
| DuckDB | **PostgreSQL** con esquema seguro (roles, RLS, cifrado), JSONB para datos variables y **pgvector** para el RAG | Seguridad demostrable y una sola base |
| Sin texto | **Texto**: glosa de cada movimiento (clasificación) y mensajes del usuario (sentimiento) | Análisis NLP ligado a una decisión |
| Perfiles K-Prototypes en DEBERÍA | **K-Prototypes en DEBE**: alimenta recomendaciones, Sueldo Lucas y arranque en frío | Personalización medible |
| Un agente con tools | **Un agente LangGraph** con nodos: router, herramientas (nuestros modelos), RAG, BCRP, redacción y **juez** | Cero cifras inventadas, con fuentes |
| Recomendador igual para todos | **Segmento + comportamiento individual + reglas de seguridad**, con ofertas de tipos de producto genéricos según necesidad | Fidelización responsable |
| Sin nombres | **6 personas con roles y microtareas** ([tareas.md](tareas.md)) | Trabajo en paralelo |
| Recomendaciones según la situación del momento | **Lucas aprende del usuario**: perfil de ahorro y gasto, metas con proyección a fin de año, memoria de metas, preferencias y respuestas a cada recomendación | Mejorar, no solo informar |
| Segmentos sin nombre de negocio | **Matriz ahorro × gasto** (ahorrador/no ahorrador × gasta mucho/gasta poco) encima de los clusters | Segmentos que el banco entiende |
| Datos generados solo por reglas | **Generación estratificada** + **bootstrap** de perfiles para que ningún segmento quede sub o sobrerrepresentado | Evitar sesgo |
| RAG con manuales sueltos | **RAG por módulos**: salud financiera, ahorro, deudas, inversión básica, seguros y derechos del usuario | Educación que acompaña cada recomendación |

**Se descarta:** segunda base NoSQL (Postgres con JSONB la cubre), GraphRAG, deep learning entrenado desde cero, multimodal, varios agentes, ubicación exacta.

---

## 1. Problema, usuario y decisión

**Población:** trabajadores dependientes e independientes del sector privado en Perú: cobran por quincena, con comisiones o con pagos irregulares; usan Yape/Plin y tarjeta; tienen cuotas o deudas.

**Problema principal: liquidez a 30 días.** No saben si les alcanzará la plata hasta el próximo ingreso ni qué cambio concreto mejora su situación. Es más agudo en independientes porque su ingreso varía.
*(El 61 % sin colchón de un mes está pendiente de fuente exacta: ver `estadisticas/cifras-publicas.md`.)*

**Decisión que mejoramos:**
> «¿Cuánto puedo gastar o ahorrar este mes sin quedarme en rojo antes de mi próximo ingreso, y qué cambio me conviene más?»

**Arquetipos:** formal con quincena (banda estrecha), base + comisiones (media), independiente con recibo por honorarios (ancha), mixto (media-ancha). Un solo motor. El arquetipo nunca entra a un modelo.

**Para el banco:**
- **Fidelización:** avisos a tiempo y ahorro medible hacen que el cliente vuelva.
- **Atracción:** «Lucas en 5 preguntas» da valor a quien todavía no es cliente.
- **Oferta responsable:** tipos de producto genéricos solo cuando hay una necesidad detectada y pasan las reglas de idoneidad.
- **Camino de crecimiento:** quien gasta de más recibe metas de ahorro; cuando ya ahorra, Lucas le muestra promociones y productos de ahorro e inversión del catálogo del banco. El cliente crece con el banco y eso lo fideliza.

### Criterios de éxito

1. Pronóstico a 30 días con **menor MAE** que el promedio móvil; bandas al 80 % con cobertura entre 75 % y 85 %.
2. **100 %** de las cifras del agente rastreables a una herramienta; **100 %** de las afirmaciones del RAG con cita real.
3. Día de riesgo y recomendación accionable en **menos de 60 s**.
4. Recurrentes y duplicadas con **F1 ≥ 0,85**.
5. Banda más ancha para independientes que para dependientes, manteniendo cobertura.
6. Avisos: mejor precision que «avisar en cada evento», con máximo 3 por semana.
7. Ofertas: mejor precision@3 sobre necesidades sembradas que «lo más popular para todos».
8. Metas: mayor probabilidad simulada de llegar a la meta de fin de año que la regla fija del 10 %.
9. Aprendizaje: con la memoria de respuestas, la tasa simulada de recomendaciones aceptadas sube frente a un recomendador sin memoria.

---

## 2. Alcance (MoSCoW)

### DEBE

| # | Módulo | Responsable |
|---|---|---|
| D1 | Generador sintético: tabular + glosas + mensajes, calendario peruano, escenarios difíciles, necesidades sembradas | Dixon |
| D2 | PostgreSQL seguro: esquemas `seguro` y `app`, roles, RLS, pgcrypto, pgvector, Docker | Michael |
| D3 | Motor: categorías, fijo/variable, hormiga, recurrentes; clasificador de glosa | Diego |
| D4 | Segmentación K-Prototypes por cliente | Diego |
| D5 | Salud financiera 0–100 con componentes | Diego |
| D6 | Pronóstico de saldo a 30 días con banda y día de riesgo (global vs por segmento vs baseline) | Diego |
| D7 | Recomendador híbrido: segmento + comportamiento + reglas de seguridad + ofertas genéricas | Miguel |
| D8 | Motor de eventos y avisos (ingreso, grati/CTS, calendario, gasto frecuente, riesgo) con límite semanal | Miguel |
| D9 | Simulador «qué pasaría si» y Sueldo Lucas | Miguel + Diego |
| D10 | Agente LangGraph: tools sobre nuestros modelos, RAG con pgvector, nodo juez, fallback a plantillas | Jeffrey |
| D11 | UI interactiva: Cómo estás, Qué viene, Qué hacer, Avisos, Chat, Evidencia | Marcela |
| D12 | Panel Evidencia + EVALUATION.md | Diego + Marcela |
| D13 | Perfil de ahorro y gasto (matriz 2×2) y **metas de ahorro** con proyección a fin de año | Diego + Miguel |
| D14 | **Memoria del usuario**: metas, preferencias, resúmenes de conversación y respuesta a cada recomendación (útil / no me sirve) | Jeffrey + Michael |
| D15 | **RAG por módulos** con PDFs públicos de educación financiera y metadatos (fuente, licencia, módulo, nivel) | Jeffrey + Dixon |

### DEBERÍA
- Lucas en 5 preguntas (arranque en frío por cluster). *Prioridad alta.*
- Aprendizaje por respuestas: el ranking de recomendaciones se ajusta con lo que el usuario aceptó o rechazó.
- Catálogo de ofertas y promociones para ahorradores (configurable, ver sección 5).
- Bootstrap de perfiles desde microdatos públicos de la ENAHO (INEI), si la licencia y el tiempo lo permiten.
- Sentimiento de mensajes con modelo preentrenado en español (ajusta tono y urgencia).
- Tipo de cambio e indicadores del BCRP con caché y respaldo grabado.
- Plata del negocio y plata de la casa.
- Resumen de la quincena con cambios del puntaje.
- Consentimiento y botón «explícamelo fácil».

### PODRÍA
- Plan de grati y CTS completo. Explicación contrafactual. Alerta de atípicos. Equipo rojo en vivo. Servidor MCP con los modelos.

### NO AHORA
NoSQL aparte, GraphRAG, deep learning desde cero, multimodal, varios agentes, ubicación exacta/GPS, WhatsApp, app nativa, modo familia, vista para el banco.

**Orden de recorte** si a mitad del sábado no hay flujo de punta a punta: sentimiento → BCRP → modelos por segmento (queda el global) → Lucas en 5 preguntas.

---

## 3. Arquitectura

```
┌──────────────────────── 1. INGESTA / DATOS ──────────────────────────────┐
│ generator/ (semilla) → validación Pydantic → PostgreSQL                  │
│   esquema seguro: clientes, deudas  (roles, RLS, pgcrypto)               │
│   esquema app: transacciones, glosas, mensajes, avisos (JSONB)           │
│   pgvector: fragmentos de manuales públicos para el RAG (por módulo)     │
│   memoria: metas, preferencias, resúmenes y respuestas a recomendaciones │
│ bcrp_service (API → caché → último valor → serie grabada)                │
└───────────────────────────────────┬──────────────────────────────────────┘
┌──────────────────────── 2. ANALÍTICA / IA ───────────────────────────────┐
│ engine: categorías, recurrentes, clasificador de glosa, calendario PE    │
│ segment: K-Prototypes por cliente                                        │
│ health, forecast (+ banda bootstrap), sentiment (preentrenado)           │
│ events: detector de eventos → candidatos → puntaje → filtros → límite    │
│ recommender: segmento + comportamiento → impacto × facilidad → seguridad │
│ agent (LangGraph):                                                       │
│   memoria → router → tools (modelos) / RAG / BCRP → redacción → juez     │
│   → guarda en memoria lo aprendido (metas, preferencias, respuestas)     │
│   juez: cifras en salida de tools + citas reales → si no, plantilla      │
└───────────────────────────────────┬──────────────────────────────────────┘
┌──────────────────────── 3. INTERACCIÓN ──────────────────────────────────┐
│ FastAPI (REST) ← UI: Cómo estás · Qué viene · Qué hacer · Avisos ·       │
│                       Chat · Evidencia                                   │
└──────────────────────────────────────────────────────────────────────────┘
```

**Stack:** Python 3.11, pandas, scikit-learn, `kmodes`, statsmodels, SciPy, `holidays`, PostgreSQL 16 + pgvector (Docker), SQLAlchemy/psycopg, FastAPI + Pydantic, LangGraph + Ollama, pytest, ruff.
**UI:** React + Recharts si Marcela lo domina; si no, Streamlit. Se decide a las 11:30 y no se cambia.
**LLM:** Ollama local por defecto; API externa solo si la organización la autoriza y sin datos personales; plantillas siempre. **La demo funciona con la red apagada.**

### Seguridad de datos demostrable
- Roles: `lucas_app` (lee y escribe `app`), `lucas_agente` (solo lectura, sin columnas sensibles), `lucas_admin`.
- RLS por `customer_id`. Columnas sensibles cifradas con pgcrypto.
- En la demo: el agente intenta leer `seguro.clientes.deuda_total` y Postgres lo bloquea.

---

## 4. Datos sintéticos

Generador propio con semilla fija (`--seed`), ~500 clientes × 12 meses, calibrado con cifras públicas verificadas. No hay dataset peruano público a nivel de transacción.

### Cómo evitamos el sesgo
1. **Generación estratificada:** se fija cuántos clientes hay en cada combinación de arquetipo × perfil de ahorro × perfil de gasto, para que ningún grupo quede vacío o domine. Las proporciones se reportan en `QUALITY.md`.
2. **Bootstrap de perfiles:** las variables de cada cliente (ingreso, gasto, deuda, colchón) se obtienen remuestreando con reemplazo desde una base de perfiles semilla y agregando un ruido pequeño. La base semilla, en orden de preferencia:
   - microdatos públicos de la **ENAHO (INEI)**, que traen ingreso y gasto reales de hogares peruanos (DEBERÍA: revisar licencia y tiempo de preparación);
   - si no da el tiempo, distribuciones paramétricas calibradas con las cifras públicas verificadas.
3. Las **transacciones** se generan por reglas a partir de cada perfil (quincena, calendario, recurrentes, escenarios difíciles).
4. **Bootstrap para la evaluación:** todas las métricas se reportan con intervalo de confianza por bootstrap por cliente.

Ojo: remuestrear datos sintéticos no les quita el sesgo que ya traen; por eso la base semilla debe venir de datos públicos reales cuando sea posible.

### Tabla `seguro.clientes`
`customer_id`, `rango_edad`, `region` (Lima, norte, sur, centro, oriente), `tipo_trabajo`, `frecuencia_ingreso`, `personas_a_cargo`, `deuda_total`, `n_creditos`, `cuota_mensual`, `tcea_promedio`, `colchon_meses`, `antiguedad_cliente_meses`, `meta_ahorro`, `paga_en_usd`, `necesidad_oculta` (etiqueta), `perfil_ahorro_real` y `perfil_gasto_real` (etiquetas), `prob_acepta_reco` (etiqueta oculta para simular respuestas), `arquetipo` (etiqueta).

### Tablas de memoria (esquema `app`, con RLS por cliente)
- `app.metas`: `customer_id`, `nombre`, `monto_objetivo`, `fecha_objetivo`, `aporte_quincenal`, `estado`.
- `app.memoria`: `customer_id`, `tipo` (preferencia, hecho, resumen), `contenido` (JSONB), `embedding` (vector), `fecha`.
- `app.respuestas_reco`: `customer_id`, `reco_id`, `tipo_reco`, `respuesta` (aceptó, ignoró, no me sirve), `fecha`.

### Tabla `app.transacciones`
`customer_id`, `transaction_id`, `fecha_hora`, `monto` (>0), `moneda`, `tipo`, `categoria`, `comercio` (ficticio), `glosa` (texto), `canal`, `saldo`, `es_recurrente` (etiqueta), `es_atipico` (etiqueta).

### Tabla `app.mensajes`
`customer_id`, `fecha_hora`, `texto`, `sentimiento` (etiqueta). Frases variadas por plantillas; **set de evaluación de 100 frases escritas a mano por el equipo**.

### Variables por cliente (entrada del K-Prototypes)
Volatilidad del ingreso, fijo/ingreso, cuota/ingreso, % hormiga, % delivery, n.º de suscripciones, % Yape/Plin, ahorro neto mensual, días en rojo (3 meses), tipo de trabajo, frecuencia de ingreso, región.

### Calendario y escenarios
- Quincena, grati (jul/dic), CTS (may/nov), feriados (`holidays` PE), campaña escolar (mar), Día de la Madre, 28 de julio, Cyber Wow, Navidad, con **subida de gasto sembrada**.
- Escenarios difíciles: ingresos irregulares, suscripciones duplicadas, cambio de patrón a mitad de año, faltantes y duplicados, atípicos.
- Necesidades ocultas sembradas (pago en USD, deuda cara, ingreso irregular) para medir ofertas.

### Particiones sin fuga
Pronóstico: walk-forward (entrena 1–9, valida 10, test 11–12). Recurrentes, glosa y atípicos: GroupKFold por cliente. Clusters: sin etiquetas; ARI con arquetipo solo después.

**Honestidad:** los modelos pueden descubrir lo que sembramos. Pruebas con perturbaciones (ruido, otra semilla, patrón no visto, faltantes extra) y set de texto escrito a mano.

---

## 5. Inteligencia: cada técnica con su baseline

| Módulo | Técnica | Baseline | Métrica |
|---|---|---|---|
| Glosa → categoría | TF-IDF + regresión logística | Diccionario de comercios | F1 por categoría |
| Recurrentes | Comercio + periodicidad + tolerancia de monto | «Mismo comercio ≥ 3 veces» | Precision, recall, F1 |
| Segmentación | K-Prototypes, k por codo, silueta y estabilidad | Reglas por umbral | Silueta, estabilidad, ARI |
| Pronóstico | Calendario + fijos + variable (ETS/regresión), banda bootstrap | Promedio móvil 3 meses | MAE, MAPE, cobertura |
| Personalización del pronóstico | Global + cluster como variable / un modelo por cluster | Global sin cluster | MAE por segmento |
| Salud | Puntaje ponderado transparente | — | Monotonicidad en tests |
| Sentimiento (DEBERÍA) | Modelo preentrenado en español | Léxico de palabras | F1 en las 100 frases a mano |
| Eventos y avisos | Probabilidad de rojo + impacto en S/ + límite semanal | Avisar en cada evento | Precision, recall, anticipación en días |
| Recomendador | Segmento + comportamiento → impacto × facilidad → seguridad | Top 3 fijo para todos | Ahorro simulado, % que evita día en rojo |
| Ofertas | Necesidad detectada + idoneidad | Lo más popular para todos | Precision@3 sobre necesidades sembradas |
| Arranque en frío (DEBERÍA) | Asignación a cluster con 5 respuestas | Promedio poblacional | MAE con 0, 1 y 3 meses de historia |
| Agente | LangGraph + tools + RAG + juez | Respuestas por plantilla | % cifras verificadas, % citas válidas, exactitud en 30 preguntas, bloqueo adverso |

### Lucas aprende del usuario

**Perfil de ahorro y gasto (matriz 2×2).** Se calcula con la tasa de ahorro y la intensidad de gasto frente a su ingreso, y se pone encima de los clusters K-Prototypes para darles un nombre que se entiende:

| | Gasta poco | Gasta mucho |
|---|---|---|
| **Ahorra** | *Ahorrador firme*: promociones y productos de ahorro e inversión del catálogo | *Ahorra pero se le escapa*: bajar gasto hormiga y suscripciones |
| **No ahorra** | *Ingreso justo*: colchón mínimo y Sueldo Lucas | *Gastador*: metas de ahorro, límites por categoría, avisos de riesgo |

Baseline de la matriz: umbrales fijos. Métrica: estabilidad del perfil mes a mes y acuerdo con las etiquetas sembradas.

**Camino de crecimiento.** El objetivo es que el usuario suba de cuadrante:
- *Gastador* → Lucas propone una meta: «Si apartas S/ 120 por quincena, en diciembre tendrás S/ 1 680». La proyección usa el pronóstico y su banda, no una cuenta lineal.
- Al cumplir metas → pasa a *ahorrador* → Lucas muestra contenidos del módulo de inversión del RAG y ofertas del catálogo según idoneidad.

**Metas de ahorro.** El usuario crea una meta o Lucas la sugiere. Se calcula el aporte por quincena que no lo deja en rojo y la probabilidad de llegar a la fecha (simulación con la banda del pronóstico). Baseline: ahorrar el 10 % fijo.

**Catálogo de ofertas y promociones.** Archivo configurable (`data/catalogo_ofertas.json`) con tipos de producto y promociones **ficticias o genéricas** (depósito a plazo, cuenta de ahorro con meta, promociones en categorías donde el usuario ya gasta). En el pitch: «se conecta al catálogo real del banco que integre a Lucas». Solo se muestra a quien pasa la idoneidad (colchón ≥ 3 meses y sin deuda cara para productos de inversión).

**Memoria del usuario.** Dos memorias distintas:
1. **Memoria de conocimiento (RAG):** PDFs públicos, iguales para todos.
2. **Memoria del usuario:** metas, preferencias («no me hables de inversión»), resúmenes de conversaciones y respuestas a cada recomendación. Se guarda en Postgres con RLS: solo la ve ese usuario. Hay un botón «olvidar lo que sabes de mí».

El agente lee la memoria del usuario antes de responder y guarda lo nuevo al final. Las cifras siguen saliendo de los modelos, nunca de la memoria.

**Aprendizaje por respuestas (DEBERÍA).** Cada recomendación tiene «útil / no me sirve». El ranking sube los tipos de recomendación que el usuario acepta y baja los que rechaza (pesos por tipo y segmento, estilo bandit simple). Con datos sintéticos se simulan las respuestas con `prob_acepta_reco` y se compara frente al recomendador sin memoria. Se dice que es simulado.

### RAG por módulos

Fuentes con licencia verificada: [../investigacion/rag-fuentes.md](../investigacion/rag-fuentes.md).

| Módulo | Para qué lo usa Lucas | Fuentes (nivel A salvo indicación) |
|---|---|---|
| Salud financiera | Explicar el puntaje y sus componentes | CFPB «Su dinero, sus metas» (español), FDIC Money Smart |
| Ahorro | Acompañar metas y colchón | CFPB, cartillas del BCRP, FDIC |
| Deudas y crédito | TCEA, costo real de cuotas, sobreendeudamiento | Res. SBS 3274-2017, folletos de deudas del CFPB |
| Inversión básica | Para *ahorradores*: tipos, riesgo y plazo, sin recomendar uno | Res. SMV 011-2026 (perfil de riesgo), FDIC |
| Seguros | Qué cubre cada tipo | Res. SBS 3274-2017; guía SBS «Para vivir seguros» (nivel C, por confirmar) |
| Derechos y privacidad | Reclamos, transparencia, memoria del usuario | Ley 29571, Res. SBS 3274-2017, Ley 29733 + DS 016-2024-JUS, Banco Mundial 2017 |

Las normas peruanas se pueden cargar porque el DL 822, artículo 9, excluye del derecho de autor a los textos oficiales. Las guías del CFPB y la FDIC son de dominio público, pero hablan de EE. UU.: solo se usan sus capítulos generales, con la etiqueta `contexto: EE. UU.`.

Cada PDF va en `docs/rag/<modulo>/` con su fila en `docs/rag/fuentes.csv`: título, institución, enlace, fecha de consulta, licencia, nivel de licencia (A/B), contexto (Perú/EE. UU./internacional) y nivel de lectura (básico/intermedio). Cada fragmento lleva su módulo para que el agente busque solo en el que toca. Sin licencia clara, no entra.

### Reglas de seguridad (globales)
1. Nada de crédito a colchón < 1 mes o deuda alta.
2. Nunca «compra/vende dólares»; el tipo de cambio solo como contexto de pagos propios en USD.
3. Sin promesas de rentabilidad, sin operaciones, sin tools que muevan dinero.
4. Toda recomendación u oferta: acción, impacto en S/, por qué, supuestos, confianza, «tú decides».
5. Productos solo como tipos genéricos, nunca reales ni con marca.
6. Máximo 3 avisos por semana.
7. Inversión solo como educación (tipos, riesgo, plazo) y simulación con tasa supuesta y visible; nunca «invierte en X» ni rentabilidad prometida.
8. Ofertas de inversión o ahorro a plazo solo con colchón ≥ 3 meses y sin deuda cara.
9. La memoria del usuario se puede ver y borrar; nunca se usa para ofrecer crédito a quien no pasa la regla 1.

---

## 6. Flujo de la demo

1. Consentimiento y elección de persona: independiente con recibo por honorarios.
2. **Aviso** al entrar: «el jueves 27 podrías quedar en rojo (confianza media)».
3. **Cómo estás:** salud con componentes, segmento en palabras, gasto hormiga, 2 suscripciones de streaming.
4. **Qué viene:** saldo con banda y día de riesgo.
5. **Qué hacer:** 3 tarjetas con «¿por qué?», **Sueldo Lucas** y simulador: la banda se mueve y el día de riesgo desaparece.
6. **En vivo:** se agrega «gratificación de julio» → salta el aviso con reparto propuesto (se viene el 28) → todo se recalcula.
7. **Chat:** «¿llego a fin de mes si gasto S/ 150 en un regalo?» → cifras ✓; «¿qué es la TCEA?» → respuesta con fuente del RAG.
8. **Metas:** el usuario es *gastador*; Lucas propone «S/ 120 por quincena = S/ 1 680 en diciembre» con su probabilidad. Marca una reco como «no me sirve» y la siguiente cambia (memoria).
9. **Contraste:** se cambia a un *ahorrador firme*; Lucas le muestra el módulo de inversión básica y una promoción del catálogo.
10. **Seguridad:** el agente intenta leer un dato sensible y Postgres lo bloquea.
11. **Atracción:** alguien sin historial responde 5 preguntas y ve su pronóstico.
12. **Evidencia:** cada técnica frente a su baseline.

Si el tiempo de demo no alcanza, se quitan los pasos 9 y 11.

Accesibilidad: contraste AA, texto ≥ 16 px, no depender solo del color, incertidumbre en palabras.

---

## 7. Seguridad y controles

Secretos en `.env` (nunca en el repo). Validación Pydantic. Timeouts del LLM y del BCRP con fallback. Latencia: < 2 s sin LLM, < 8 s con LLM. System prompt fijo, tools de solo lectura, casos de prompt injection en tests. Dependencias con versión fija. Sin marca ni colores de BBVA. Licencias de los manuales del RAG y del modelo de sentimiento revisadas.

---

## 8. Prueba de evolución

| Cambio probable | Ya preparado |
|---|---|
| Ingresos variables | Arquetipo independiente, banda bootstrap, Sueldo Lucas |
| Movimientos duplicados | Inyección en el generador + dedup en la ingesta con test |
| Explicabilidad | Cada reco y aviso con por qué, supuestos y confianza; juez del agente |
| Otro | Generador parametrizable, reglas fáciles de agregar, `make test` < 1 min |

Protocolo: leer el cambio → escenario en el generador → test que falla → arreglo → antes/después en Evidencia.

---

## 9. Estructura del repositorio

```
├── README.md  ARCHITECTURE.md  EVALUATION.md  PROMPTS.md
├── .env.example  Makefile  requirements.txt  docker-compose.yml
├── db/              # init.sql: esquemas, roles, RLS, pgcrypto, pgvector
├── data/            # generator.py, dictionary.md, QUALITY.md, sample/
├── docs/rag/        # <modulo>/*.pdf + fuentes.csv (fuente, licencia, nivel)
├── src/
│   ├── ingest/      # validación, dedup, carga a Postgres
│   ├── engine/      # categorías, glosa, recurrentes, calendario
│   ├── models/      # segment, health, forecast, sentiment
│   ├── events/      # detector de eventos y avisos
│   ├── recommender/ # recos, metas, ofertas, catálogo, reglas de seguridad
│   ├── agent/       # LangGraph: nodos, tools, rag, memoria, juez, providers
│   ├── bcrp/
│   └── api/         # FastAPI
├── app/             # UI
├── eval/            # genera EVALUATION.md
├── tests/
└── demo/            # guion, video de respaldo, capturas
```

---

## 10. Equipo

| Persona | Rol | Módulos | Agente de apoyo | Revisa a |
|---|---|---|---|---|
| **Diego** | Analítica IA | Features, glosa, K-Prototypes, salud, pronóstico, sentimiento, evaluación | `ml-analitica` | Jeffrey |
| **Miguel** | Desarrollo backend | FastAPI, ingesta, recomendador, ofertas, motor de eventos, simulador | `backend` | Michael |
| **Jeffrey** | Desarrollo IA (AI Engineer) | Agente LangGraph, tools, RAG pgvector, juez, providers, BCRP | `ia-chat` | Diego |
| **Marcela** | Desarrollo frontend | UI interactiva, avisos, simulador, chat, evidencia, accesibilidad | `frontend-ux` | Dixon |
| **Michael** | Arquitectura de sistema | Postgres seguro, Docker, contratos de API, Makefile, CI de tests, ARCHITECTURE.md | `backend` / `juez-cumplimiento` | Miguel |
| **Dixon** | Arquitectura de datos y diagramas | Generador sintético, diccionario, QUALITY.md, diagramas, README, guion del pitch | `datos` / `pitch-docs` | Marcela |

- **Revisión cruzada:** cada persona revisa los PR de su pareja antes del merge, además del juez correspondiente.
- **El pitch es de todos:** Dixon lo coordina; cada persona presenta su parte.
- Microtareas, horarios y avisos: [tareas.md](tareas.md). Comandos: [comandos.md](comandos.md).

---

## 11. Cronograma

| Bloque | Objetivo | Hecho cuando… |
|---|---|---|
| Sáb 11:00–12:00 | Contratos: esquema de datos, endpoints con JSON de ejemplo, decisión de UI, Docker con Postgres | Todos pueden trabajar en paralelo con datos falsos |
| Sáb 12:00–15:00 | Generador v1, Postgres cargado, baselines, UI navegable con mocks, esqueleto del agente | `make data` y `make run` funcionan |
| Sáb 15:00–19:00 | Modelos v1, recomendador, eventos, tools del agente, API conectada a la UI | **Primer flujo de punta a punta** (checkpoint 19:00) |
| Sáb 19:00–23:00 | RAG, juez, avisos en UI, simulador, escenarios difíciles, tests | Demo completa aunque fea |
| Dom 08:00–10:00 | `make eval`, EVALUATION.md, panel Evidencia, perturbaciones | Números reales |
| Dom 10:00–12:00 | DEBERÍA según tiempo, pulido de UX, prueba de evolución | **12:00 congelamiento** |
| Dom 12:00–14:00 | `release/entrega`, docs, video de respaldo, juez de cumplimiento | Entrega en `main` |
| Dom tarde | 3 ensayos cronometrados y simulacro de preguntas | 10:00 min exactos |

*(Ajustar a los horarios oficiales.)*

---

## 12. Pitch (10 min + 3 de preguntas)

| Min | Contenido | Presenta |
|---|---|---|
| 0:00–1:00 | Persona y dolor: «faltan 5 días para la quincena y no sabe si llega» | Dixon |
| 1:00–2:00 | Decisión, criterios de éxito, por qué es compañero y no chatbot | Dixon |
| 2:00–6:00 | Demo en vivo (sección 6) | Marcela + Jeffrey |
| 6:00–7:30 | Evidencia: baselines, cobertura, % verificado, errores conocidos | Diego |
| 7:30–8:30 | Arquitectura, seguridad de datos, offline | Michael |
| 8:30–10:00 | Valor para el banco (fidelización, atracción), límites y siguiente paso | Miguel |

Preguntas probables: ¿por qué no bastan reglas? ¿Cómo evitan que el LLM invente? ¿Qué pasa sin internet? ¿Los datos son plausibles? ¿No es venta disfrazada? ¿Qué harían con datos reales? Respuesta de 20 s para cada una.

---

## 13. Riesgos

| Riesgo | Mitigación |
|---|---|
| Alcance grande para 2 días | MoSCoW, orden de recorte, checkpoint 19:00 |
| Postgres/Docker falla en una laptop | `data/sample/` + script que carga en un Postgres local; la máquina de demo se prueba el sábado |
| LLM lento o sin red | Ollama con modelo pequeño ya descargado + plantillas |
| Métricas demasiado buenas | Perturbaciones, set de texto a mano, decirlo |
| Ofertas que suenan a venta | Solo por necesidad, idoneidad, tipos genéricos, «tú decides» |
| Parecer app de BBVA | Marca Lucas, paleta propia |
| Conflictos de Git | Ramas cortas, `pull --rebase` frecuente, contratos fijados temprano |

---

## 14. Preguntas a la organización

LLM externo permitido · dataset común · APIs públicas en la demo · formato y hora de entrega · prueba de evolución · modelos descargados de antemano. Respuestas en `estado.md`.

---

## 15. Checklist de salida

- [ ] Problema y usuario definidos
- [ ] Datos legales y reproducibles (`make data`, semilla, QUALITY.md)
- [ ] MVP ejecutable (`make run`, también offline)
- [ ] IA/ML con valor medido (EVALUATION.md)
- [ ] Baselines y casos adversos
- [ ] Seguridad y explicabilidad
- [ ] README y ARCHITECTURE
- [ ] Demo ensayada 3 veces + video de respaldo
- [ ] Entrega en `main`, repo accesible al jurado
