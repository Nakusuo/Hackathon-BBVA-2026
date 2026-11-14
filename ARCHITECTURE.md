# Arquitectura de Lucas (v1: fronteras)

Responsable: Michael (arquitectura de sistema y seguridad). Diagramas finales: Dixon (DX-06, DX-09).
Fuente de alcance: [plan maestro v3](.claude/planes/plan-maestro.md). Si este documento y el plan se contradicen, manda el plan y se corrige este.

Este documento fija **quién puede llamar a quién, con qué tipos y con qué rol de base de datos**, para que los seis trabajemos en paralelo sin pisarnos. No repite el alcance ni las métricas del plan.

## 1. Intención

Lucas responde una pregunta: «¿cuánto puedo gastar o ahorrar este mes sin quedarme en rojo antes de mi próximo ingreso, y qué cambio me conviene más?». La arquitectura existe para que:

1. **Cada cifra salga de un solo camino de cálculo.** La pantalla, el simulador, el agente y `make eval` llaman a la misma función. Si dieran números distintos, el juez del agente no podría verificarlos y la demo se contradiría.
2. **La seguridad sea demostrable y no solo declarada.** El agente usa su propio rol de Postgres y no puede leer datos sensibles aunque una inyección de prompt se lo pida.
3. **Todo funcione con la red apagada** en la laptop de la demo.
4. **La prueba de evolución se resuelva en minutos**: un cambio en el generador, un test que falla y un arreglo en un módulo.

### Objetivos, no objetivos y antiobjetivos

| Objetivos | No objetivos | Antiobjetivos (fracaso aunque funcione) |
|---|---|---|
| Monolito modular en Python, un proceso para la API | Microservicios, colas, varios agentes | Que la UI, el simulador y el chat muestren cifras distintas para el mismo cliente |
| Núcleo de cálculo puro (DataFrames entran, tipos Pydantic salen) | ORM con modelos para cada tabla | Que el agente pueda leer `seguro.*` o elegir el `customer_id` |
| Un rol de Postgres por componente, RLS por cliente | Autenticación real de usuarios | Que la demo dependa de internet |
| Entrenar por lotes, inferir en línea por cliente | Reentrenar en cada request | Que `make test` necesite Postgres para los tests del núcleo |

## 2. Enfoques considerados

| Enfoque | Qué gana | Qué pierde | Decisión |
|---|---|---|---|
| **1. Entrenar por lotes + inferir en línea** | Un solo camino de cálculo para pantalla, simulador, chat y evaluación; el gasto agregado en vivo se recalcula solo | Hay que vigilar la latencia del bootstrap (< 2 s por cliente) | **Elegido** (Michael, 14/11) |
| 2. Todo precalculado en tablas | API rapidísima | El simulador y el gasto en vivo recalculan igual: dos caminos que pueden divergir | Descartado |
| 3. Todo en vivo, incluido el entrenamiento | Lo más simple | K-Prototypes y TF-IDF por request son lentos y dejan de ser reproducibles | Descartado |

## 3. Capas y regla de dependencias

```
                    ┌──────────────── 3. INTERACCIÓN ────────────────┐
                    │ app/  (UI: React o Streamlit, solo habla HTTP) │
                    └───────────────────────┬────────────────────────┘
                                            │ HTTP (JSON = tipos de src/tipos.py)
┌───────────────────────────────── 2. ANALÍTICA / IA ─────────────────────────────────┐
│ src/api/ (FastAPI, rol lucas_app)         src/agent/ (LangGraph, rol lucas_agente)    │
│        │                                          │ tools                            │
│        └──────────────► src/nucleo.py ◄───────────┘                                  │
│                         estado_cliente(conn, customer_id, cambios)                   │
│                              │                                                       │
│        ┌─────────────┬───────┴──────┬──────────────┬──────────────┐                  │
│   src/engine/   src/models/   src/recommender/   src/events/   src/bcrp/             │
│   (puros: reciben DataFrames y tipos, no tocan la base ni la red, salvo bcrp)        │
└────────────────────────────────────────┬─────────────────────────────────────────────┘
                                         │ src/db/lecturas.py (única puerta a Postgres)
┌──────────────────────────────── 1. INGESTA / DATOS ─────────────────────────────────┐
│ data/generator.py → Parquet → src/ingest/ (Pydantic + dedup) → PostgreSQL 16         │
│ esquemas: seguro (sensible) · app (interno, RLS) · rag (público, pgvector)           │
│ make train (rol lucas_batch) → models/artefactos/*.joblib + app.segmentos            │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

Reglas, que el `juez-tecnico` revisa en cada PR:

1. **Una capa nunca importa a una de arriba.** `engine`, `models`, `recommender` y `events` no importan `api`, `agent` ni `db`.
2. **Solo `src/db/` habla con Postgres.** Todo lo demás recibe DataFrames o tipos. Así los tests del núcleo no necesitan Docker.
3. **Solo `src/nucleo.py` orquesta el cálculo.** La API, las tools del agente, el simulador y `eval/` llaman a `estado_cliente`. Nadie vuelve a llamar a `pronosticar` por su cuenta para mostrar una cifra.
4. **La UI solo habla con la API por HTTP**, también si es Streamlit. Si importara `src/` directamente, se saltaría la validación y los roles.
5. **Los tipos de `src/tipos.py` son el contrato.** Los usan los módulos entre sí y FastAPI como `response_model`. Los JSON de ejemplo de `docs/api.md` (MG-01) se generan desde ellos, no a mano.

## 4. El contrato entre módulos

### 4.1 Tipos compartidos (`src/tipos.py`, Pydantic v2)

Montos en S/, positivos, redondeados a 2 decimales al serializar. Fechas en `America/Lima`. Los nombres de campo siguen el diccionario de datos (DX-01).

| Tipo | Campos mínimos | Lo produce |
|---|---|---|
| `Perfil` | `customer_id`, `tipo_trabajo`, `frecuencia_ingreso`, `colchon_meses`, `cuota_ingreso`, `nivel_deuda` (bajo/medio/alto), `personas_a_cargo`, `region`, `paga_en_usd` | `db.lecturas` desde `app.perfil` |
| `Salud` | `total` (0–100), `componentes: dict[str, float]`, `explicacion: list[str]` | `models.health` |
| `Pronostico` | `dias: list[DiaPronostico]` (`fecha`, `p10`, `p50`, `p90`), `dia_riesgo: date \| None`, `prob_rojo: float`, `confianza` (alta/media/baja) | `models.forecast` |
| `Segmento` | `cluster`, `cuadrante` (ahorrador firme, se le escapa, ingreso justo, gastador), `descripcion` | `models.segment` (umbrales en la ola 1) |
| `Recurrente` | `comercio`, `categoria`, `monto`, `periodicidad_dias`, `proxima_fecha`, `duplicada: bool` | `engine.recurrentes` |
| `Reco` | `id`, `tipo`, `accion`, `impacto_soles`, `por_que`, `supuestos`, `confianza`, `datos_usados` | `recommender` |
| `Aviso` | `id`, `tipo`, `fecha_evento`, `mensaje`, `prob`, `impacto_soles` | `events` |
| `Cambio` | Unión discriminada por `tipo`: `cancelar_recurrente`, `reducir_categoria`, `agregar_movimiento`, `quitar_ingreso`, `apartar_quincenal` | UI y simulador |
| `Memoria` | `respuestas: list[RespuestaReco]`, `preferencias: list[Preferencia]` (`clave`, `valor`) | `db.lecturas` desde `app.respuestas_reco` y `app.memoria` |
| `Estado` | `perfil`, `salud`, `pronostico`, `segmento`, `recurrentes`, `recos`, `avisos`, `sueldo_lucas` | `nucleo.estado_cliente` |

Agregar un campo opcional no rompe a nadie. Renombrar o quitar uno se avisa en el grupo antes del merge.

### 4.2 Firmas que implementa cada módulo

Todas son funciones puras: mismo dato de entrada, mismo resultado. `tx` es el DataFrame de transacciones con las columnas de `app.transacciones`.

```python
# src/engine/            (Diego)
categorizar(tx) -> DataFrame                         # agrega columna categoria
recurrentes(tx) -> list[Recurrente]
calendario(desde: date, hasta: date, perfil: Perfil) -> DataFrame   # quincena, grati, CTS, feriados

# src/models/            (Diego)
puntaje(tx, perfil) -> Salud
pronosticar(tx, recurrentes, perfil, hoy: date, dias=30, artefacto=None) -> Pronostico
asignar_segmento(features: dict, artefacto) -> Segmento
features_cliente(tx, perfil) -> dict                 # entrada del K-Prototypes y de la matriz

# src/recommender/       (Miguel)
recomendar(estado_parcial, memoria) -> list[Reco]    # candidatos → impacto×facilidad → segmento → seguridad → top 3
sueldo_lucas(pronostico, tx, perfil) -> float
plan_meta(meta, pronostico) -> PlanMeta

# src/events/            (Miguel)
avisos(estado_parcial, avisos_previos, hoy: date) -> list[Aviso]   # máximo 3 por semana

# src/nucleo.py          (Michael, con Miguel y Diego)
calcular_estado(tx, perfil, segmento, avisos_previos, memoria: Memoria, hoy: date,
                cambios: list[Cambio] = ()) -> Estado        # puro: el único cálculo
estado_cliente(conn, customer_id, hoy: date, cambios=()) -> Estado   # lee la base y llama a calcular_estado
aplicar_cambios(tx, recurrentes, cambios) -> tuple[DataFrame, list[Recurrente]]

# src/models/entrenar.py (Diego)
entrenar(conn_batch, hasta: date) -> Artefactos     # solo usa datos con fecha_hora <= hasta
```

- **`calcular_estado` es el único cálculo.** `estado_cliente` es solo la versión que lee de la base. El **simulador** es `estado_cliente(..., cambios=[...])`. **«Lucas en 5 preguntas»** arma un `Perfil` y una `tx` sintética con las respuestas y llama directo a `calcular_estado`, sin `customer_id` ni base.
- **`hoy` siempre es explícito** y `calcular_estado` descarta todo movimiento posterior. La API lo toma de `HOY_DEMO` en `.env`. Su valor lo eligen Dixon y Marcela según el guion (la demo pasa cerca de la grati de julio). `eval/` lo usa para el walk-forward: el mismo camino de cálculo con otra fecha de corte.
- **Sin fuga en la evaluación.** `make train` usa `hasta = HOY_DEMO`. `eval/` entrena sus propios artefactos con `hasta` = fin del mes 9 y nunca usa los de `models/artefactos/`.
- **`Memoria`** (en `tipos.py`) tiene `respuestas` (de `app.respuestas_reco`, las escribe la API con «útil / no me sirve») y `preferencias: list[Preferencia]` (de `app.memoria` con `tipo = 'preferencia'`, las escribe el agente). `Preferencia` tiene `clave` (por ejemplo `excluir_tipo_reco`) y `valor`. Así lo que se dice en el chat cambia las tarjetas de «Qué hacer», y el contrato entre Jeffrey y Miguel es ese tipo, no el JSONB libre.

## 5. Base de datos

### 5.1 Esquemas y clasificación (ISO 5.12)

| Esquema | Nivel | Tablas | RLS |
|---|---|---|---|
| `seguro` | Sensible | `clientes` (con `deuda_total`, `tcea_promedio`, `cuota_mensual` y las etiquetas, cifradas con pgcrypto) | No hace falta: ni la app ni el agente tienen permiso |
| `app` | Interno | `perfil` (derivado y sin montos de deuda), `transacciones`, `movimientos_usuario`, `segmentos`, `metas`, `memoria`, `respuestas_reco`, `avisos`, `mensajes` | Sí, por `customer_id` |
| `rag` | Público | `fuentes`, `fragmentos` (`modulo`, `texto`, `embedding vector(n)`) | No |

`app.perfil` es la frontera de privacidad. La ingesta, que tiene la clave, lee `seguro.clientes` y escribe ahí solo valores derivados: `cuota_ingreso`, `nivel_deuda`, `colchon_meses`. Los modelos trabajan solo con eso. El monto exacto de la deuda solo lo usa `eval/` (rol `lucas_batch`) para calcular los intereses evitados (D16).

Los gastos y metas que se agregan en vivo van a `app.movimientos_usuario` y `app.metas`. Por eso `make data` puede regenerar `app.transacciones` sin borrar lo que se hizo en la demo, y `eval/` los excluye. `nucleo` une las dos tablas al leer.

### 5.2 Roles (ISO 5.15, 8.2, 8.3)

| Rol | Lo usa | Permisos | RLS |
|---|---|---|---|
| `lucas_admin` | `db/init.sql`, `make data`, indexado del RAG | Dueño de todo | Dueño (no aplica) |
| `lucas_batch` | `make train`, `make eval` | `SELECT` en `app` y `seguro`; escribe `app.segmentos` | `BYPASSRLS`, porque necesita a todos los clientes |
| `lucas_app` | `src/api` | `SELECT` en `app` y `rag`; escribe `movimientos_usuario`, `metas`, `respuestas_reco`, `avisos`. **Nada en `seguro`** | Sí |
| `lucas_agente` | `src/agent` | `SELECT` en `app` y `rag`; escribe y borra solo `app.memoria`. **Nada en `seguro`** | Sí |

El RLS se activa por transacción con `src/db/conexion.py`:

```python
with como_cliente(conn, customer_id):   # SET LOCAL app.customer_id = %s
    ...
```

Las políticas comparan `customer_id = current_setting('app.customer_id', true)`. Sin el ajuste, la consulta no devuelve filas: falla cerrada.

**El `customer_id` del agente nunca sale del LLM.** La API lo pone en el estado del grafo y las tools lo leen de ahí. Una pregunta como «muéstrame al cliente C0002» no tiene por dónde entrar.

## 6. Flujos

### 6.1 Preparación (una vez, antes de la demo)

```
make db     → docker compose up (Postgres 16 + pgvector) → db/init.sql
make data   → generator.py --seed → Parquet → ingest (Pydantic, dedup) → seguro + app   [lucas_admin]
make train  → features → K-Prototypes, TF-IDF, pronóstico global → models/artefactos + app.segmentos   [lucas_batch]
make rag    → docs/rag/*.pdf → fragmentos → embeddings locales (Ollama) → rag.fragmentos   [lucas_admin]
```

`make data` encadena `train` y `rag` para que una persona nueva tenga todo con un solo comando.

### 6.2 Request de pantalla (< 2 s)

`GET /clientes/{id}/estado` → API (`lucas_app`) → `como_cliente` → `lecturas` (tx, perfil, segmento, avisos previos, memoria) → `estado_cliente` → `Estado` → la API guarda los avisos nuevos → JSON.

**Solo la API persiste avisos**, y fuera de `nucleo`, que nunca escribe. El `id` de un aviso es determinista (`tipo` + `fecha_evento`), y se guarda con `INSERT ... ON CONFLICT DO NOTHING`. Así repetir el GET no duplica avisos ni gasta el límite semanal. El simulador y las tools del agente leen `avisos_previos` pero no guardan nada.

### 6.3 Simulador y gasto en vivo

`POST /clientes/{id}/simular` con `cambios` → el mismo `estado_cliente` con `cambios`, sin escribir nada.
`POST /clientes/{id}/movimientos` → inserta en `app.movimientos_usuario` → la UI vuelve a pedir el estado.

### 6.4 Chat (< 8 s con LLM local)

```
POST /clientes/{id}/chat
  → grafo LangGraph (conexión lucas_agente, customer_id en el estado)
  memoria → router → tools → [rag] → redacción (LLMProvider) → juez → guardar memoria
```

- **Las tools llaman a `estado_cliente`** con la conexión del agente y devuelven `model_dump()` de los tipos. Son de solo lectura; no existe ninguna que mueva dinero.
- **El juez** extrae cada número de la respuesta y lo busca, con tolerancia de redondeo, en las salidas de las tools de ese turno. Cada cita del RAG debe existir en `rag.fragmentos`. Si falla, reintenta una vez y si no, responde la plantilla.
- **`LLMProvider`** es la única interfaz con varias implementaciones (excepción acordada en calidad-codigo): `OllamaProvider` (por defecto), `GeminiProvider` (apagado, `LLM_PROVIDER=gemini`) y `TemplateProvider` (siempre). Recibe la pregunta y las salidas de las tools; nunca el perfil crudo ni identificadores.

## 7. Configuración y comandos

`.env` (valores ficticios en `.env.example`):

```
DB_URL_ADMIN, DB_URL_BATCH, DB_URL_APP, DB_URL_AGENTE   # una URL por rol
CLAVE_DATOS                                              # pgcrypto, solo admin y batch
LLM_PROVIDER=ollama   OLLAMA_MODEL=qwen2.5:3b   OLLAMA_EMBED_MODEL=...
GEMINI_API_KEY=xxxx
SEED=42
HOY_DEMO=2026-07-14                                      # ejemplo; lo fijan Dixon y Marcela con el guion
```

Los supuestos de negocio (TCEA supuesta, umbrales) van en `config/supuestos.yaml`, versionado y visible.

`make` no está en todas las laptops (Windows). Cada objetivo del `Makefile` es **una sola línea** `python -m ...` que se puede copiar y correr a mano:

| Objetivo | Equivale a |
|---|---|
| `make db` | `docker compose up -d` |
| `make data` | `python -m src.ingest` (genera, valida, carga y encadena train y rag) |
| `make train` | `python -m src.models.entrenar` (con `hasta = HOY_DEMO`) |
| `make test` | `pytest -q -m "not db"` (< 1 min, sin Docker) |
| `make check` | `ruff check . && ruff format --check . && pytest -q && pip-audit` |
| `make eval` | `python -m eval` |
| `make run` | `uvicorn src.api.main:app` + la UI |
| `make e2e` | `pytest -q tests/e2e` (con Docker) |

Los tests que necesitan Postgres llevan `@pytest.mark.db`. Los de seguridad de roles y RLS (MI-03, MI-11) son de ese tipo.

## 8. Estructura de carpetas

```
├── ARCHITECTURE.md  README.md  EVALUATION.md  PROMPTS.md
├── .env.example  Makefile  requirements.txt  pyproject.toml  docker-compose.yml
├── config/supuestos.yaml
├── db/init.sql
├── data/            generator.py, dictionary.md, QUALITY.md, catalogo_ofertas.json, sample/
├── docs/            api.md (MG-01), rag/<modulo>/*.pdf + fuentes.csv
├── models/artefactos/   (generado, en .gitignore)
├── src/
│   ├── tipos.py     contrato
│   ├── nucleo.py    único orquestador del cálculo
│   ├── db/          conexion.py (roles + como_cliente), lecturas.py, escrituras.py
│   ├── ingest/  engine/  models/  recommender/  events/  bcrp/
│   ├── agent/       grafo, tools, rag, memoria, juez, providers
│   └── api/         main.py, rutas, middleware de latencia y log
├── app/  eval/  demo/
└── tests/           espejo de src/ + e2e/ + seguridad/ + agent/ + sistema/
```

## 9. Dueños y tareas

| Pieza | Dueño | Tarea |
|---|---|---|
| Esqueleto, `pyproject.toml`, `Makefile`, `tipos.py`, `nucleo.py`, `db/conexion.py` | Michael | MI-01, MI-04 |
| `docker-compose.yml`, `db/init.sql` (esquemas, roles, RLS, pgcrypto, pgvector) | Michael | MI-02, MI-03 |
| `data/generator.py`, `dictionary.md` (con columna de clasificación) | Dixon | DX-01, DX-02 |
| `src/ingest/`, `src/api/`, `recommender/`, `events/` | Miguel | MG-01 a MG-13 |
| `src/engine/`, `src/models/`, `eval/` | Diego | DI-01 a DI-13 |
| `src/agent/`, `src/bcrp/`, `PROMPTS.md` | Jeffrey | JF-01 a JF-11 |
| `app/` | Marcela | MC-01 a MC-11 |

`nucleo.py` arranca con implementaciones falsas de cada módulo que devuelven tipos válidos. Así la API y la UI funcionan con datos de mentira desde el bloque 1 y cada dueño reemplaza su pieza cuando la tiene.

## 10. Riesgos de arquitectura

| Riesgo | Mitigación |
|---|---|
| Docker o Postgres fallan en la laptop de la demo | La máquina de demo se instala desde cero el sábado (MI-07). Imagen `pgvector/pgvector:pg16` descargada de antemano. `data/sample/` permite cargar en minutos |
| `estado_cliente` pasa de 2 s | Medir con el middleware de latencia. Si pasa, caché en memoria por `(customer_id, versión de movimientos)` |
| Alguien calcula una cifra fuera de `nucleo` | Regla 3 de la sección 3; lo revisa el juez técnico |
| Cambiar un tipo rompe a otro equipo | Campos nuevos opcionales; renombres avisados en el grupo |

## 11. Decisiones a cargo de cada constructor

- Técnica interna de cada modelo: ETS o regresión, y cómo se hace el bootstrap (Diego). La firma no cambia.
- Si el router del agente usa reglas o tool calling del LLM (Jeffrey). Recomendación: reglas primero, porque `qwen2.5:3b` falla seguido con tool calling, y que el LLM solo redacte. Se mide contra plantillas como cualquier técnica.
- Modelo de embeddings y su dimensión (Jeffrey, JF-01). Tiene que estar decidido antes de cerrar `db/init.sql`.
- Formato exacto de las rutas y los JSON de ejemplo (Miguel, MG-01), respetando la sección 6.
- React o Streamlit (Marcela, 11:30). No cambia nada de lo anterior.
