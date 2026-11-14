# Jeffrey · Agente de IA de Lucas

**Rol:** IA Engineer (código JF). Agente LangGraph, tools, juez de cifras, RAG, proveedores LLM y BCRP.
**Revisa mis PR:** Diego. **Yo reviso:** los PR de Diego.
**Código:** `src/agent/`, `src/bcrp/servicio.py`, `eval/evaluar_chat.py`. **Detalle técnico:** [PROMPTS.md](PROMPTS.md). **Bitácora:** [.claude/equipo/jeffrey/registro.md](.claude/equipo/jeffrey/registro.md).
**Actualizado:** 14/11/2026, comparado con `develop` y con las ramas de Miguel (`feature/backend-fastapi`), Dixon (`smith`), Diego y Marcela.

---

## 1. Estado de mis actividades

| Tarea | Qué es | Estado | Dónde está |
|---|---|---|---|
| JF-01 | Ollama, modelos y PDFs del RAG | ✅ Hecha | `develop` (PR #5) |
| JF-02 | Grafo LangGraph: router → tools → redacción → juez → respuesta | ✅ Hecha | `develop` (PR #5) |
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

`responder` devuelve: `conversation_id`, `answer`, `provider` (`ollama` / `gemini` / `plantilla`), `verified`, `verified_figures`, **`figures`** (`[{label, value, text}]`), **`sources`** (`[{id, title, institution, page, url, context}]`), `tools_used` e `intent`. Tu `ChatResponse` necesita esos campos; si no, FastAPI los borra. Mi versión probada del router y del esquema está en la rama local `feature/ia-chat-api`: cuando unas la tuya, te la paso como un cambio chico sobre tus archivos.

**También falta `first_risk_date` en `ForecastResponse`.** Sin ese campo Lucas no puede avisar «el 18 podrías quedar en rojo» (paso 2 de la demo).

### Marcela · chat de la pantalla
- Cada cifra con su ✓: usa `figures` (`label` y `text` ya vienen formateados, con el signo real).
- Fuentes: usa `sources`. Si `context` no es `"Peru"`, muestra la etiqueta «EE. UU.» (CP-SIS-47).
- `intent: "sin_datos"` o `"sin_fuente"` significa que Lucas no inventó nada: no hay cifras que marcar.

### Diego · modelos y evaluación
- Uso **tu índice del RAG** (`docs/rag/indice/`) y tu configuración: densa + filtro de módulo, umbral 0,70 y siglas.
- La sección del chat para `EVALUATION.md` está lista en [docs/evaluacion-chat.md](docs/evaluacion-chat.md).
- Mis tools leen el **contrato** (`score`, `lower_bound`, `upper_bound`, `first_risk_date`…). Cuando tus modelos lleguen a la API (MG-06, o el cargador de Dixon en la rama `smith`), mi agente los usa sin cambios.

### Dixon · pruebas
- CP-SIS-10 (simulación por LLM): se prueba con `python -m agent --simular-con-llm`. Con el 3b el juez rechazó 4 de 4 redacciones (llamó «saldo actual» al saldo final), así que responde la plantilla.
- Casos del agente cubiertos por tests: CP-SIS-11, 13, 14, 15, 30 y 47. CP-SIS-12 en parte: se niega a recomendar en qué invertir, pero todavía no ofrece la educación del módulo de inversión.

### Probar el agente en 1 minuto
```powershell
pip install -r requirements-ia.txt
$env:PYTHONPATH = "src"
python -m agent --plantilla                              # con los mocks, sin LLM
python -m agent --api http://localhost:8000 --json       # contra la API de Miguel
python -m pytest -q tests/agent tests/bcrp tests/api     # 278 pruebas
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
