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

## Lo que acordamos

| Fecha | Acuerdo | Por qué |
|---|---|---|
| 2026-11-14 | Una sola rama para mis primeras tareas, con commits separados por tarea | Pedido mío, para revisar todo junto |
| 2026-11-14 | El LLM nunca recibe el texto del usuario ni `customer_id`: solo la intención y un resumen de las tools | Una inyección no llega al modelo y Gemini no recibe texto libre (ISO 8.12) |
| 2026-11-14 | Simular un gasto, el tipo de cambio y el perfil van siempre por plantilla | Con el 3b, el LLM invirtió el signo del saldo y la unidad del tipo de cambio. **Choca con CP-SIS-10**, que pide LLM: lo deciden Diego y Dixon en el PR #5 |
| 2026-11-14 | `qwen2.5:3b` y no 1.5b | El 1.5b inventó cifras en 2 de 5 preguntas |
| 2026-11-14 | Contrato `/chat` y `/fx` con Miguel | `docs/api.md`, secciones 11 y 12 |

## Lo que falta

- [ ] Revisión de Diego del PR #5 y merge
- [ ] Decidir CP-SIS-10 con Diego y Dixon (simulación por LLM o por plantilla)
- [ ] Confirmar con Marcela y Miguel el campo nuevo `figures` de `/chat` (su pantalla usa `{etiqueta, valor}`) y anotarlo en `docs/api.md`
- [ ] JF-03 Tools reales sobre `estado_cliente` y `src/tipos.py` (espera MG-03 de Miguel y MI-03 de Michael)
- [ ] JF-04 Números del fragmento citado (con JF-05)
- [ ] JF-05 RAG en pgvector por módulo (espera MI-02 de Michael)
- [ ] JF-09 Memoria con listas cerradas y «olvidar lo que sabes de mí» (espera MI-03)
- [ ] JF-07 Métricas del agente y latencia en la RTX 3050 de Michael (p95 < 8 s)
- [ ] JF-10 / MG-12 Aprendizaje por respuestas (espera MG-04 y DX-02)
- [ ] Juntar `pyproject.toml` y `requirements-ia.txt` con lo de MI-01
- [ ] Demo en vivo con Marcela (minuto 2 a 6 del pitch)
