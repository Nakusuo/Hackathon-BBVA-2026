# Prompts, modelos y respaldo del agente

Responsable: Jeffrey. Código en `src/agent/`. Contrato del endpoint: `docs/api.md`, sección 12.

## Modelos (fijados el 2026-11-14)

| Uso | Modelo | Versión | Dónde corre |
|---|---|---|---|
| Redacción (por defecto) | `qwen2.5:3b` | Ollama 0.40.16, digest `357c53fb659c`, 1,9 GB | Local |
| Embeddings del RAG | `nomic-embed-text` | digest `0a109f422b47`, 274 MB, 768 dimensiones | Local, siempre |
| Redacción (respaldo con red) | `gemini-3.5-flash-lite` | `langchain-google-genai` 4.5.0, nivel gratuito | Google, apagado por defecto |
| Último respaldo | Plantillas (`src/agent/plantillas.py`) | — | Local, sin LLM |

```bash
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
```

Ajustes de la nota GPU del plan maestro (RTX 3050 de Michael): `num_ctx` 4096 y `keep_alive=-1` en cada llamada, más `calentar()` al arrancar la API. En el servidor Ollama: `OLLAMA_FLASH_ATTENTION=1` y `OLLAMA_KV_CACHE_TYPE=q8_0`. Comprobar con `ollama ps` que diga `100% GPU`.

Se probó `qwen2.5:1.5b`: inventó cifras en 2 de 5 preguntas. Se queda el 3b.

## Cadena de proveedores

| `LLM_PROVIDER` | Cadena |
|---|---|
| `ollama` (por defecto) | Ollama → plantillas |
| `gemini` | Ollama → Gemini → plantillas (solo si hay `GEMINI_API_KEY`) |
| `plantilla` | Solo plantillas |

Cada proveedor tiene un reintento. Error de red, timeout (8 s), error 429 o respuesta vacía → siguiente proveedor. Si el juez rechaza, se redacta una vez más; si vuelve a fallar, responde la plantilla.

## Qué responde el LLM y qué la plantilla

| Intención | Quién redacta | Motivo |
|---|---|---|
| Pronóstico, salud, recomendaciones | LLM, con juez | Explica en palabras |
| Simular un gasto, tipo de cambio, perfil | Siempre plantilla | Con el 3b, el LLM quitó el signo del saldo («te sobraron S/ 50» por -50), invirtió la unidad del tipo de cambio y llamó «actual» a un dato guardado. La plantilla es exacta y gratis (regla de costo) |
| Operación (dólares, transferir, «en qué invierto»), inyección, fuera de tema | Respuesta fija | Se corta en el router, sin tools ni LLM |

## Qué recibe el LLM

- La intención ya clasificada y un **resumen** de las salidas de las tools con nombres claros (`resumen_para_llm`): del pronóstico solo el último día, no la serie. Con la serie completa el modelo mezclaba cifras reales de días distintos y el juez no lo notaba.
- **Nunca** el texto del usuario ni `customer_id`. Una inyección de prompt no llega al modelo y Gemini no recibe texto libre (ISO 27001, control 8.12). Lo prueba `tests/agent/test_providers.py`.

## Prompt de sistema

Versión `redaccion-v3`, en `src/agent/prompts.py`.

| Versión | Cambio | Motivo |
|---|---|---|
| `redaccion-v1` | Primera versión | — |
| `redaccion-v2` | Pide mencionar las cifras clave | Con v1 el 3b respondió solo la frase de cierre |
| `redaccion-v3` | Sin cifras de ejemplo, sin día de la semana, hablar de tú, no numerar | El 3b copiaba las cifras del ejemplo de formato y se equivocaba en el día de la semana |

## Juez (`src/agent/juez.py`)

1. Cada número debe salir de lo que vio el LLM. Con decimales solo vale el redondeo (`420.70` no pasa por `420`); sin decimales, hasta 0,5 % (`S/ 1 680` por `1 683.20`).
2. Un número escrito con `S/` debe venir de un campo de dinero (`saldo`, `amount`, `impact`, `bound`…): «S/ 72» no pasa si 72 es el puntaje.
3. «Jueves 18» se rechaza si el 18 de los datos cae miércoles.
4. Frases prohibidas en lo que escribe el LLM: invertir, comprar o vender dólares, transferir, rentabilidad garantizada. Lo vimos: «te conviene invertir en un colchón nuevo».
5. Las citas `[fuente: id]` deben existir. La numeración de listas no cuenta como cifra.
6. Si las tools trajeron montos, la respuesta debe usar al menos uno; la fecha sola no cuenta.

**Límite conocido:** el juez verifica cifras, unidades, fechas y frases, pero no todo el sentido. Una cifra correcta puede quedar mal descrita («tu saldo actual» por un impacto mensual). Por eso las preguntas donde un error de sentido cambia la decisión van por plantilla.

## Medición (6 preguntas, mocks del contrato, Intel Core Ultra 7 155H con Intel Arc, sin GPU dedicada)

| Prueba | Respondió el LLM | Plantilla por rechazo del juez | Latencia |
|---|---|---|---|
| v1, tools falsas | 4 de 5 | 1 | 3,8 a 10 s |
| v3 + resumen + juez completo | 2 de 3 que van al LLM | 1 (cifras 100 y 235 inventadas) | 7,7 a 14,8 s |

En esta laptop la meta p95 < 8 s no se cumple: hay timeouts. Se mide en la RTX 3050 de Michael en JF-07.
