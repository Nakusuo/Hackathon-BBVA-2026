# Registro de Jeffrey (Jeffrey-Salvatierra) · IA Engineer

Rol: agente de Lucas (código JF). Agente de apoyo: `ia-chat`. Revisa mis PR: Diego. Yo reviso los PR de Diego.

## Lo que hice

| Fecha | Tarea | Rama | Qué quedó |
|---|---|---|---|
| 2026-11-14 | JF-01 Ollama y RAG núcleo | `feature/ia-jeffrey-actividades` | Ollama 0.40.16 con `qwen2.5:3b` y `nomic-embed-text` (versiones en `PROMPTS.md`). 9 PDFs de nivel A en `docs/rag/<modulo>/` con `fuentes.csv`: SBS 3274-2017, SMV 011-2026, DS 016-2024-JUS, Ley 29571 (versión SPIJ de Indecopi), Banco Mundial 2017 y 4 guías del CFPB (bajadas a mano: el sitio bloquea descargas automáticas) |
| 2026-11-14 | JF-02 Grafo LangGraph | `feature/ia-jeffrey-actividades` | router por reglas → tools → redacción → juez → respuesta, con un reintento y luego plantilla. Las operaciones y las inyecciones se cortan en el router, sin tools ni LLM |
| 2026-11-14 | JF-04 Juez | `feature/ia-jeffrey-actividades` | Cifras con tolerancia de redondeo, montos con «S/» solo de campos de dinero, día de la semana correcto, frases prohibidas (invertir, comprar dólares, transferir), citas que existen. Falta: aceptar los números del fragmento citado (necesita JF-05) |
| 2026-11-14 | JF-06 Preguntas fijas y adversas | `feature/ia-jeffrey-actividades` | 30 fijas y 10 adversas en `tests/agent/preguntas.json`, sobre los mocks de MG-01 |
| 2026-11-14 | JF-08 BCRP | `feature/ia-jeffrey-actividades` | TC venta (PD04638PD) e inflación a 12 meses (PN01273PM): API → caché 6 h → último valor → serie grabada. `fx_contrato` da la forma de `/fx` |
| 2026-11-14 | JF-11 Gemini de respaldo | `feature/ia-jeffrey-actividades` | `gemini-3.5-flash-lite`, apagado salvo `LLM_PROVIDER=gemini`. Ante red caída, timeout o 429: reintento y plantilla |
| 2026-11-14 | MG-01 Revisión del contrato | — | Propuesta de `/chat` (`verified_figures`, `intent`, `provider` = ollama/gemini/plantilla) y `/fx` aceptada por Miguel. `agent.chat.responder` listo para que la API lo llame |
| 2026-11-14 | Prueba con `qwen2.5:3b` real | `feature/ia-jeffrey-actividades` | El juez atrapó cifras inventadas, pero aparecieron errores de sentido («S/ 72» por el puntaje, «invertir en un colchón nuevo», signo del saldo invertido). Se endureció el juez y el LLM ve solo un resumen por intención. Detalle en `PROMPTS.md` |
| 2026-11-14 | Push y PR #5 | `feature/ia-jeffrey-actividades` | PR a `develop`: https://github.com/MaickolO/Hackathon-BBVA-2026-Equipo-2/pull/5 (revisa Diego). 147 tests en verde |
| 2026-11-14 | Cifras con etiqueta para el chat de Marcela | `feature/ia-jeffrey-actividades` | `/chat` suma el campo `figures`: `[{label, value, text}]`, por ejemplo «Saldo mínimo probable: -S/ 310», con el signo real de la tool. `verified_figures` sigue igual. Rama al día con `develop` (PR #6 de Marcela). 149 tests en verde |
| 2026-11-14 | Correcciones de la medición de Michael (JF-07) | `feature/ia-jeffrey-actividades` | `OLLAMA_HOST=0.0.0.0` normalizado a localhost. Salud vuelve al LLM (faltaba el 100 de «72 de 100»). El juez rechaza cifras mal descritas: «saldo» que no es saldo, «actual» que es final y negativos escritos como positivos. Prompt v4. Opción `--simular-con-llm` para que Michael pruebe CP-SIS-10. 166 tests en verde |
| 2026-11-14 | PR #5 unido a `develop` (por Marcela) | — | Marcela subió 2 arreglos al juez antes de unirlo: regla de signo con negaciones y «a favor», redondeo solo a decena (≥ 100) o centena (≥ 1 000), y prohibidas «préstamo», «un crédito» y «sin riesgo». Sin aprobación formal de Diego en GitHub |
| 2026-11-14 | Correcciones de la medición en rama nueva | `feature/ia-medicion-rtx` | Las correcciones de la medición de Michael no alcanzaron a entrar al PR #5. Van sobre `develop` y se combinan con la regla de signo de Marcela (se queda la suya, que es más completa, y se le suma «S/ 200 te faltaron»). 210 tests en verde |
| 2026-11-14 | JF-03 Tools sobre la API de Miguel | `feature/ia-tools` | `HerramientasAPI` llama a los endpoints del contrato (`/health`, `/forecast`, `/recommendations`, `POST /simulations`, `/fx`); `simulate` devuelve también lo que pidió. Si la API cae, el agente responde «no puedo ver tus datos» sin cifras (CP-SIS-15). Probado de punta a punta contra el servidor real de `feature/backend-fastapi`: todo verificado. El juez ahora acepta montos que FastAPI manda como texto (`"rate": "3.75"`). `python -m agent --api URL`. 222 tests en verde |
| 2026-11-14 | JF-05 RAG con el avance de Diego (y cierre de JF-04) | `feature/ia-rag` | Por pedido de Diego se reutiliza su índice (`docs/rag/indice/`, idéntico al de su rama para que no choquen) y su configuración (densa + filtro de módulo, umbral 0,70, siglas). Nueva intención «educación» con módulo por lista cerrada de temas; responde la plantilla con cita textual, fuente y aviso si la guía es de EE. UU.; sin evidencia dice «no encontré una fuente». El juez acepta citas de los fragmentos traídos y los números del fragmento citado. `/chat` llena `sources`. Probado con embeddings reales: ~2,3 s. 242 tests en verde |

## Lo que acordamos

| Fecha | Acuerdo | Por qué |
|---|---|---|
| 2026-11-14 | Una sola rama para mis primeras tareas, con commits separados por tarea | Pedido mío, para revisar todo junto |
| 2026-11-14 | El LLM nunca recibe el texto del usuario ni `customer_id`: solo la intención y un resumen de las tools | Una inyección no llega al modelo y Gemini no recibe texto libre (ISO 8.12) |
| 2026-11-14 | Simular un gasto, el tipo de cambio y el perfil van siempre por plantilla | Con el 3b, el LLM invirtió el signo del saldo y la unidad del tipo de cambio |
| 2026-11-14 | CP-SIS-10 se mantiene; se vuelve a probar en la RTX 3050 con `--simular-con-llm` y, si el LLM se equivoca, se cambia el caso a «responde la plantilla» (Dixon) | Decisión de Dixon |
| 2026-11-14 | Mi agente se mantiene junto a los modelos de Diego: son complementarios y él los contrasta (Diego) | Respuesta de Diego al PR #5 |
| 2026-11-14 | Campo `figures` de `/chat` acordado con Marcela y Miguel | Su chat muestra `{etiqueta, valor}` |
| 2026-11-14 | La demo va enchufada | En batería baja la RTX 3050 baja a 9,6 tok/s y tarda de 8 a 18 s (Michael) |
| 2026-11-14 | `qwen2.5:3b` y no 1.5b | El 1.5b inventó cifras en 2 de 5 preguntas |
| 2026-11-14 | Contrato `/chat` y `/fx` con Miguel | `docs/api.md`, secciones 11 y 12 |
| 2026-11-14 | Usar parte del avance de Diego para ir a la par: su índice y configuración del RAG en mi agente (Diego) | Evitar hacer dos veces el mismo RAG |
| 2026-11-14 | Las preguntas de educación las responde la plantilla con cita textual | El 3b no citó y metió cifras ajenas en 4 de 4 intentos |

## Lo que falta

- [x] PR #5 unido a `develop` (Marcela, con sus arreglos al juez)
- [ ] PR #7 (`feature/ia-tools`: medición + JF-03) y PR de `feature/ia-rag` (revisa Diego)
- [x] RAG: se usa el índice de Diego
- [ ] Decidir con Diego qué agente va a la demo y qué `src/bcrp` se queda; mis PDFs de `docs/rag/<modulo>/` y su `fuentes.csv` tienen otros nombres que los suyos
- [ ] Michael: repetir la medición con el prompt v4 y con `--simular-con-llm` (CP-SIS-10); pasarle el resultado a Dixon
- [x] Campo `figures` acordado con Marcela y Miguel
- [ ] Miguel anota `figures` en `docs/api.md` y lo declara en la respuesta de `/chat`
- [ ] `/chat` real: Miguel subió un `/chat` de prueba en `feature/backend-fastapi` (respuesta fija, `provider: "mock"`, sin `figures`, `sources` como lista de textos). Cuando lo una, cambiar el cuerpo de su función para llamar a `agent.chat.responder` y ampliar su esquema. Mi versión probada está solo en local (`feature/ia-chat-api`)
- [x] JF-03 sobre la API de Miguel (`feature/ia-tools`)
- [ ] JF-03 con el rol `lucas_agente` directo a Postgres o a `estado_cliente` de `ARCHITECTURE.md`, cuando existan (MI-03, `src/nucleo.py`). Hoy las tools pasan por la API
- [ ] Miguel: agregar `first_risk_date` a `ForecastResponse` (sin eso Lucas no avisa el día en rojo; confirmado con su servidor)
- [x] JF-04 Números del fragmento citado (`feature/ia-rag`)
- [x] JF-05 RAG por módulo con el índice FAISS de Diego (`feature/ia-rag`)
- [ ] JF-05 cargar el índice a pgvector cuando exista MI-02 (Diego dice que se puede desde `docs/rag/indice/`)
- [ ] JF-09 Memoria con listas cerradas y «olvidar lo que sabes de mí» (espera MI-03)
- [x] JF-07 Métricas del agente con plantilla y Ollama (`eval/evaluar_chat.py`, `docs/evaluacion-chat.md`, rama local `feature/ia-eval`): 100 % de intención, cifras, juez, bloqueo y citas con plantilla; 97 % de cifras con Ollama y ninguna inventada
- [ ] JF-07 repetir con Ollama en la RTX 3050 de Michael (p95 < 8 s) y pasarle la sección a Diego para `EVALUATION.md`
- [ ] JF-10 / MG-12 Aprendizaje por respuestas (espera MG-04 y DX-02)
- [ ] Juntar `pyproject.toml` y `requirements-ia.txt` con lo de MI-01
- [ ] Demo en vivo con Marcela (minuto 2 a 6 del pitch)
