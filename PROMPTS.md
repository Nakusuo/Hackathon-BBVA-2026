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

**La laptop de la demo va enchufada.** Con batería baja, la RTX 3050 baja de 72 a 9,6 tok/s y cada respuesta tarda de 8 a 18 s (medición de Michael).

`OLLAMA_HOST` puede ser `0.0.0.0:11434` para el servidor; el cliente lo convierte a `http://localhost:11434` (`host_ollama()`), porque a `0.0.0.0` no se puede conectar.

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

**CP-SIS-10 (simulación por LLM):** Dixon pidió mantenerlo y volver a probar en la RTX 3050. Para probarlo: `python -m agent --simular-con-llm`. Con el prompt v4 el 3b ya escribe bien el signo («quedarías en rojo con -S/ 200»), pero en 4 de 4 intentos llamó «saldo actual» al saldo final; el juez lo rechaza y responde la plantilla. La GPU cambia la velocidad, no la precisión: es el mismo modelo con los mismos pesos.
| Operación (dólares, transferir, «en qué invierto»), inyección, fuera de tema | Respuesta fija | Se corta en el router, sin tools ni LLM |

## Qué recibe el LLM

- La intención ya clasificada y un **resumen** de las salidas de las tools con nombres claros (`resumen_para_llm`): del pronóstico solo el último día, no la serie. Con la serie completa el modelo mezclaba cifras reales de días distintos y el juez no lo notaba.
- **Nunca** el texto del usuario ni `customer_id`. Una inyección de prompt no llega al modelo y Gemini no recibe texto libre (ISO 27001, control 8.12). Lo prueba `tests/agent/test_providers.py`.

## Prompt de sistema

Versión `redaccion-v4`, en `src/agent/prompts.py`.

| Versión | Cambio | Motivo |
|---|---|---|
| `redaccion-v1` | Primera versión | — |
| `redaccion-v2` | Pide mencionar las cifras clave | Con v1 el 3b respondió solo la frase de cierre |
| `redaccion-v3` | Sin cifras de ejemplo, sin día de la semana, hablar de tú, no numerar | El 3b copiaba las cifras del ejemplo de formato y se equivocaba en el día de la semana |
| `redaccion-v4` | Saldo negativo con «-S/» y «en rojo»; «saldo» solo para la cuenta y «puntaje de salud» para el puntaje. El resumen de salud trae `puntaje_maximo` y el de simulación dice si quedas en rojo | El 3b escribía «te sobraron S/ 50» por -50 y «saldo de salud 72»; la salud nunca la redactaba el LLM porque el 100 de «72 de 100» no estaba en los datos (Michael). Con v4, la salud pasa 2 de 2 |

## Juez (`src/agent/juez.py`)

1. Cada número debe salir de lo que vio el LLM. Con decimales solo vale el redondeo (`420.70` no pasa por `420`); sin decimales, hasta 0,5 % (`S/ 1 680` por `1 683.20`).
2. Un número escrito con `S/` debe venir de un campo de dinero (`saldo`, `amount`, `impact`, `bound`…): «S/ 72» no pasa si 72 es el puntaje.
3. «Jueves 18» se rechaza si el 18 de los datos cae miércoles.
4. Frases prohibidas en lo que escribe el LLM: invertir, comprar o vender dólares, transferir, rentabilidad garantizada. Lo vimos: «te conviene invertir en un colchón nuevo».
5. Las citas `[fuente: id]` deben existir. La numeración de listas no cuenta como cifra.
6. Si las tools trajeron montos, la respuesta debe usar al menos uno; la fecha sola no cuenta.
7. **Cifra mal descrita.** El juez sabe de qué campo salió cada cifra y mira las palabras de su frase:
   - si dice «saldo», la cifra tiene que ser de un campo de saldo («Tu saldo actual es S/ 120» con 120 = ahorro en delivery no pasa; lo vio Michael);
   - si dice «actual», «hoy» o «ahora», no puede ser un saldo final o previsto;
   - un saldo negativo escrito en positivo solo pasa si la frase dice «en rojo», «negativo», «falta» o algo similar («te sobraron S/ 50» por -50 no pasa; «S/ 200 te faltaron» sí).

**Límite conocido:** el juez revisa cifras, unidades, signos, fechas, palabras clave y frases prohibidas, pero no entiende todo el sentido. Por eso las preguntas donde un error cambia la decisión van por plantilla.

## Medición

**RTX 3050 de Michael** (100 % GPU, ctx 4096, flash attention, KV q8_0, enchufada, 72 tok/s), dos rondas:

| Pregunta | Ronda 1 | Ronda 2 | Quién respondió |
|---|---|---|---|
| ¿Llego a fin de mes? | 4,0 s | 1,0 s | Ollama |
| ¿Cómo está mi salud financiera? | 2,3 s | 2,4 s | Plantilla: el juez rechazó «100» de «72 de 100». Corregido en v4 |
| ¿Qué me conviene hacer? | 2,2 s | 1,1 s | Ollama (en la ronda 1 el juez rechazó un 2535 inventado y la segunda redacción pasó) |

**Todas por debajo de 8 s.** Falta repetirla con v4 y con `--simular-con-llm` (JF-07).

**Laptop de Jeffrey** (Intel Core Ultra 7 155H, Intel Arc, sin GPU dedicada): entre 8 y 15 s, con timeouts. No sirve para la demo.

## RAG (JF-05)

Se usa el índice que construyó Diego (`docs/rag/indice/`, traído tal cual de `feature/ml-segmentos-pronostico`): 3 833 fragmentos de 6 módulos, `nomic-embed-text` (768 dimensiones), FAISS. Configuración tomada de su evaluación (`models/metricas_rag.json`): búsqueda densa con filtro de módulo (recall@4 0,94), umbral de relevancia 0,70, top 3 y expansión de siglas.

- El router detecta preguntas de educación («¿qué es la TCEA?», «¿cómo funciona la CTS?») y elige el módulo con una lista cerrada de temas (`router.temas_rag`). Lo que llega al LLM como «tema» sale de esa lista, nunca del texto del usuario.
- El embedding de la pregunta es local (Ollama): la pregunta no sale de la máquina.
- Sin fragmento sobre el umbral, sin índice o sin Ollama, Lucas responde «no encontré una fuente oficial» y no inventa.
- **Responde la plantilla**: cita textual de la frase del fragmento que menciona el tema, con título, institución, página y `[fuente: frag-N]`. Si la guía es de EE. UU., lo avisa (CP-SIS-47). Con `qwen2.5:3b` el LLM no citó la fuente y metió cifras ajenas al fragmento en 4 de 4 intentos (el juez lo rechazó siempre).
- El juez (JF-04) acepta citas solo de los fragmentos que trajo el RAG y los números del fragmento citado o de su título («Res. SBS 3274-2017»), y con `exigir_cita` rechaza una respuesta educativa sin fuente.
- `/chat` devuelve en `sources` los fragmentos citados: `id`, `title`, `institution`, `page`, `url`, `context`.

Prueba con embeddings reales (laptop sin GPU): unos 2,3 s por pregunta. «¿Qué derechos tengo si me cobran de más en mi tarjeta?» no pasa el umbral y responde «no encontré una fuente»: falta ajustar con el conjunto de oro de Diego.
