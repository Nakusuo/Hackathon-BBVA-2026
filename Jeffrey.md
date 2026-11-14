# Jeffrey · Agente de IA de Lucas

**Rol:** IA Engineer (código JF). Agente LangGraph, tools, juez de cifras, RAG, proveedores LLM y BCRP.
**Revisa mis PR:** Diego. **Yo reviso:** los PR de Diego.
**Código:** `src/agent/`, `src/bcrp/servicio.py`, `eval/evaluar_chat.py`. **Detalle técnico:** [PROMPTS.md](PROMPTS.md). **Bitácora:** [.claude/equipo/jeffrey/registro.md](.claude/equipo/jeffrey/registro.md).
**Actualizado:** 14/11/2026, comparado con `develop` y con las ramas de Miguel (`feature/backend-fastapi`), Dixon (`smith`), Diego (`feature/ml-segmentos-pronostico`, con su `PROMPT_INTEGRACION.md`) y Marcela (`feature/front-chat-agente`).

---

## 1. Estado de mis actividades

| Tarea | Qué es | Estado | Dónde está |
|---|---|---|---|
| JF-01 | Ollama, modelos y PDFs del RAG | ✅ Hecha | `develop` (PR #5) |
| JF-02 | Grafo LangGraph: router → tools → redacción → juez → respuesta | ✅ Hecha · router reforzado con las 75 frases de Diego (28 desvíos → 0) | `develop` (PR #5) + PR #7 |
| JF-03 | Tools sobre la API del contrato | ✅ Hecha sobre la API · falta la versión con rol `lucas_agente` | PR #7 |
| JF-04 | Juez de cifras, signos, unidades, fechas, frases prohibidas y citas | ✅ Hecha | PR #7 |
| JF-05 | RAG por módulos con el índice de Diego | ✅ Hecha con FAISS · falta pasarlo a pgvector | PR #7 |
| JF-06 | 30 preguntas fijas y 10 adversas | ✅ Hecha | `develop` (PR #5) |
| JF-07 | Métricas del agente | ✅ Hecha con plantilla y Ollama · falta repetir en la RTX 3050 | PR #7 |
| JF-08 | BCRP: tipo de cambio e inflación con respaldo | ✅ Hecha | `develop` (PR #5) |
| JF-09 | Memoria del usuario y «olvidar lo que sabes de mí» | ⏳ Espera las tablas de Michael (MI-03) | — |
| JF-10 | Aprendizaje con «útil / no me sirve» | ⏳ Espera el recomendador (MG-04 o el de Diego) | — |
| JF-11 | Gemini como respaldo, apagado por defecto | ✅ Hecha | `develop` (PR #5) |
| `/chat` | Endpoint real del agente | 🔄 Listo en local, se integra con Miguel | Rama local `feature/ia-chat-api` |

## 2. Resultados medidos (JF-07)

46 preguntas sobre los mocks del contrato. Detalle en [docs/evaluacion-chat.md](docs/evaluacion-chat.md).

| Métrica | Plantilla | Ollama `qwen2.5:3b` |
|---|---|---|
| Intención correcta (30 fijas) | 100 % | 100 % |
| Cifras esperadas verificadas | 100 % | 97 % |
| Bloqueo de preguntas adversas (10) | 100 % | 100 % |
| Educación con cita válida (6) | 100 % | 100 % |
| Latencia p95 (laptop sin GPU) | 2,3 s | 17,4 s |

En la RTX 3050 de Michael: entre 1,0 y 4,0 s por respuesta, todas por debajo de 8 s. **Ninguna cifra inventada llegó al usuario.**

## 3. Cómo usar mi avance (para el equipo)

### Miguel · conectar `/chat` al agente
Tu `/chat` de `feature/backend-fastapi` todavía responde un texto fijo. El agente ya está listo:

```python
from src.agent.chat import responder
from src.agent.grafo import construir
from src.agent.providers import cadena_desde_entorno
from src.agent.rag import Buscador
from src.agent.tools import HerramientasAPI

agente = construir(HerramientasAPI(), cadena_desde_entorno(), buscador=Buscador())
respuesta = responder(agente, {"customer_id": "...", "message": "...", "conversation_id": None})
```

`responder` devuelve: `conversation_id`, `answer`, `provider` (`ollama` / `gemini` / `plantilla`), `verified`, `verified_figures`, **`figures`** (`[{label, value, text, unit}]`), **`sources`** (`[{id, title, institution, page, url, context}]`), `tools_used` e `intent`. Tu `ChatResponse` necesita esos campos; si no, FastAPI los borra. Mi versión probada del router y del esquema está en la rama local `feature/ia-chat-api`: cuando unas la tuya, te la paso como un cambio chico sobre tus archivos.

**También falta `first_risk_date` en `ForecastResponse`.** Sin ese campo Lucas no puede avisar «el 18 podrías quedar en rojo» (paso 2 de la demo).

**`provider` queda en `plantilla`** (pendiente de `docs/api.md` §12): el mock decía `template`. `data/sample/mocks/chat.json` ahora es la respuesta real del agente para `chat-request.json` y un test avisa si dejan de coincidir. Tu `/chat` de prueba devuelve `"mock"`: al conectarlo al agente sale `plantilla`, `ollama` o `gemini`.

### Marcela · chat de la pantalla
- Cada cifra con su ✓: usa `figures` (`label` y `text` ya vienen formateados, con el signo real). Ya trae **`unit`** con los valores de `docs/api.md` §12 (`PEN`, `percent`, `months`, `days`, `score`), como espera tu `clienteChat.js` (PR #16).
- Pendientes de §12 que me tocaban: `unit: "score"` para el puntaje ✅; `provider` unificado en `plantilla` ✅; el texto del usuario nunca llega a Gemini ✅, ahora con un test explícito (`test_iso_8_12_el_texto_del_usuario_nunca_llega_al_llm`). Criterio de `verified`: el juez aprobó todas las cifras y citas de la respuesta final. `sources`: solo fragmentos del índice que la respuesta cita. Error del proveedor: un reintento y luego plantilla.
- Revisé tu `clienteChat.js`: es compatible con mi `/chat` sin cambios. Ojo: tu espera es de 12 s y en una laptop sin GPU el p95 de Ollama es 17 s; en la RTX 3050 de Michael no pasa de 4 s.
- Fuentes: usa `sources`. Si `context` no es `"Peru"`, muestra la etiqueta «EE. UU.» (CP-SIS-47).
- `intent: "sin_datos"` o `"sin_fuente"` significa que Lucas no inventó nada: no hay cifras que marcar.

### Diego · modelos y evaluación
- Uso **tu índice del RAG** (`docs/rag/indice/`) y tu configuración: densa + filtro de módulo, umbral 0,70 y siglas.
- La sección del chat para `EVALUATION.md` está lista en [docs/evaluacion-chat.md](docs/evaluacion-chat.md).
- Mis tools leen el **contrato** (`score`, `lower_bound`, `upper_bound`, `first_risk_date`…). Cuando tus modelos lleguen a la API (MG-06, o el cargador de Dixon en la rama `smith`), mi agente los usa sin cambios.
- Pasé **tus 75 frases naturales** por mi router (como pide tu `PROMPT_INTEGRACION.md`): desviaba 28 de 68 (sin contar las 7 de puntos, que son de tu agente), entre ellas 8 de seguridad. Ahora 0; quedan como test en `tests/agent/test_router_natural.py`.
- **Requirements alineados:** bajé `langgraph` a 1.2.20, `pypdf` a 7.0.1 y `ruff` a 0.17.4, como los tuyos; mis 354 pruebas pasan. Queda `numpy`: tu 2.5.4 no existe para Python 3.11 (la versión del plan); yo uso 2.4.6.
- **Tu índice no tiene el módulo de inversión:** la Res. SMV 011-2026 está en `docs/rag/inversion/` pero no se indexó. Sin eso, «¿qué es invertir?» no encuentra fuente. ¿Puedes agregarla con tu `actualizar_incremental`? No toco tu índice para no chocar.

### Dixon · pruebas
- CP-SIS-10 (simulación por LLM): se prueba con `python -m agent --simular-con-llm`. Con el 3b el juez rechazó 4 de 4 redacciones (llamó «saldo actual» al saldo final), así que responde la plantilla.
- **TODOS-05 hecho:** agregué 13 casos `CP-JF-01` a `CP-JF-13` en `.claude/planes/pruebas.md`, cada uno con su técnica (partición de equivalencia, valores límite, tabla de decisión, predicción de errores, adversa, falla controlada) y el nombre de los tests que lo automatizan. En la matriz llené «Tests de componente» de HU-10, 11, 12, 19 y 20. Solo agregué filas; no cambié las tuyas.
- Casos de sistema cubiertos por tests: CP-SIS-11, 12, 13, 14, 15, 30 y 47. En CP-SIS-12 Lucas se niega, explica que para recomendar una inversión hay que evaluar el perfil de riesgo y ofrece lo que sí puede explicar con fuente (depósito a plazo, fondo de emergencia). Cuando el índice tenga el módulo de inversión, podrá explicar también qué es invertir.

### Probar el agente en 1 minuto
```powershell
pip install -r requirements-ia.txt
$env:PYTHONPATH = "src"
python -m agent --plantilla                              # con los mocks, sin LLM
python -m agent --api http://localhost:8000 --json       # contra la API de Miguel
python -m pytest -q tests/agent tests/bcrp tests/api     # 354 pruebas
```

## 4. Lo que espero de otros

| De quién | Qué | Para qué tarea mía |
|---|---|---|
| Diego | Revisar y aprobar el PR #7 | JF-03, 04, 05, 07 |
| Miguel | Unir su `/chat` para reemplazar el mock por el agente; `first_risk_date` | `/chat`, demo |
| Michael | MI-02 (Postgres + pgvector) y MI-03 (roles, RLS, tablas de memoria) | JF-05 en pgvector, JF-03 con `lucas_agente`, JF-09 |
| Michael | Segunda medición en la RTX 3050 con `--simular-con-llm` | JF-07, CP-SIS-10 |
| Miguel o Diego | Recomendador con tipos de recomendación | JF-10 |
| Marcela | Conectar su chat a `/chat` (MC-06) | Demo |

## 5. Decisiones del agente (y por qué)

- **El LLM explica, no calcula.** Toda cifra sale de una tool y pasa por el juez; si el juez rechaza dos veces, responde la plantilla.
- **El LLM nunca recibe el texto del usuario ni el `customer_id`**, solo la intención y un resumen de las tools. Así una inyección no llega al modelo y Gemini no recibe datos personales (ISO 27001, control 8.12).
- **Simulación, tipo de cambio, perfil y educación van siempre por plantilla.** Con `qwen2.5:3b` el LLM invirtió signos, cambió la unidad del tipo de cambio y no citó fuentes. Lo medimos.
- **Cadena de respaldo:** Ollama → Gemini (solo si se autoriza) → plantillas. La demo funciona sin internet.
- **Demo enchufada:** en batería la RTX 3050 baja a 9,6 tok/s.
