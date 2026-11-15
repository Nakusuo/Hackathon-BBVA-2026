# Gemini API gratuita como segundo proveedor del chat

Consulta: 2026-11-14. Fuentes oficiales de Google (ai.google.dev ahora redirige a aistudio.google.com/docs).

## 1. Pregunta

¿Podemos usar el nivel gratuito de la Gemini Developer API (Google AI Studio) como proveedor de respaldo del LLM que **solo redacta** a partir de salidas de tools, si Ollama local falla?

## 2. Respuesta corta

**Sí, como respaldo opcional y apagado por defecto.** Se puede según los términos, está disponible en Perú y entra en 2 días porque `ChatGoogleGenerativeAI` se cambia por el modelo de Ollama en LangGraph sin tocar las tools ni el nodo juez (1 o 2 horas). Condiciones: datos sintéticos, solo salidas de tools, sin PII, y que la organización lo autorice antes de la demo.

## 3. Lo verificado

| Tema | Dato | Fuente |
|---|---|---|
| ¿Sigue el nivel gratuito? | Sí. Columna «Free of charge» en `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-2.5-flash-lite`, `gemini-3.6-flash`, `gemini-3.8-flash`, `gemini-embedding-001` y `gemini-embedding-2` | [Pricing][p] |
| Perú | Está en la lista de regiones disponibles | [Regiones][r] |
| Uso de datos (gratis) | «Used to improve our products: **Yes**» (de pago: No). Revisores humanos «may read, annotate, and process your API input and output». «Do not submit sensitive, confidential, or personal information to the Unpaid Services» | [Términos, vigentes desde 23/03/2026][t] · [Pricing][p] |
| Otras condiciones | Mayores de 18 años. Uso «professional or business». En EEE, Suiza y Reino Unido solo de pago (no nos afecta) | [Términos][t] |
| Modelo sugerido | `gemini-3.5-flash-lite`: estable, con function calling y structured outputs, 1 048 576 tokens de entrada | [Ficha del modelo][m35] · [Modelos][mo] |
| Cuidado | `gemini-2.5-flash` está obsoleto y desde el 01/12/2026 pasa a responder con 3.5-flash-lite. No usarlo | [Modelos][mo] |
| SDK | `pip install google-genai` (3.3.0, 12/11/2026, Python ≥ 3.11). `google-generativeai` está obsoleto | [Librerías][l] · [PyPI][pg] |
| LangChain | `langchain-google-genai` 4.5.0 (11/11/2026). `ChatGoogleGenerativeAI` con `bind_tools` y `with_structured_output`. Lee `GOOGLE_API_KEY` y, si no existe, `GEMINI_API_KEY` | [Docs LangChain][lc] · [PyPI][plc] |
| Compatible con OpenAI | `https://generativelanguage.googleapis.com/v1beta/openai/`, con `tools`. Está en beta | [OpenAI compat][o] |
| Embeddings | `gemini-embedding-001` / `-2`: 3072 dimensiones por defecto, ajustable de 128 a 3072 (MRL) | [Embeddings][e] |

### Límites del nivel gratuito: **no verificado**

La página oficial de límites ya **no publica la tabla por modelo** del nivel gratuito. Solo dice que los límites se aplican por proyecto (no por clave), que la cuota diaria se reinicia a medianoche del Pacífico (03:00 en Lima) y que los límites «are not guaranteed». Las cifras reales se ven en la consola de AI Studio del proyecto ([Límites][rl]).

| Modelo | RPM | TPM | RPD | Estado |
|---|---|---|---|---|
| `gemini-3.5-flash-lite` / `3.1-flash-lite` | 10 a 15 | 250 000 | 500 | **No verificado** (blogs que no coinciden: [aifreeapi][b1], [tinkerllm][b2]) |
| `gemini-3.8-flash` | — | — | ~20 | **No verificado** ([imisofts][b3]) |
| Embeddings | — | — | — | Sin dato |

Hay que confirmarlo en la consola el mismo día. Con 500 consultas al día hay de sobra para la demo; con 20 no alcanza para ensayar.

### Precio del nivel de pago (USD por millón de tokens, texto) ([Pricing][p])

| Modelo | Entrada | Salida |
|---|---|---|
| `gemini-2.5-flash-lite` (el más barato, generación anterior) | 0,10 | 0,40 |
| `gemini-3.1-flash-lite` | 0,25 | 1,50 |
| `gemini-3.5-flash-lite` | 0,30 | 2,50 |
| `gemini-embedding-001` | 0,15 | — |

Ojo: `3.6-flash` y `3.8-flash` duplican su precio desde el 01/01/2027.

**Estimación propia (supuesto, no es dato de Google):** 30 mensajes al mes por usuario × (3 000 tokens de entrada + 300 de salida) = 90 000 de entrada y 9 000 de salida. Con 3.5-flash-lite: 0,09 × 0,30 + 0,009 × 2,50 ≈ **USD 0,05 por usuario al mes**. El razonamiento («thinking») se cobra aparte y puede subir esta cifra; hay que medirlo.

## 4. Qué implica para la privacidad

- Nuestros datos son sintéticos y solo enviamos salidas de tools (cifras ya calculadas). No hay PII, así que no rompemos la regla de las bases ni los términos.
- Igual hay que **suponer que Google lo lee y lo guarda**. Nunca mandar el prompt de sistema con secretos, la consulta cruda del usuario si pudiera traer datos reales, ni el contexto del RAG si tuviera algo sensible.
- Para el pitch: con clientes reales el nivel gratuito **no sirve**. Haría falta el nivel de pago (no se usa para mejorar productos) o un proveedor aprobado por el banco. Decimos «local por diseño».

## 5. Embeddings: siempre locales

Recomendación: **usar siempre embeddings locales** para pgvector. Los vectores de dos modelos distintos no se pueden comparar aunque tengan la misma dimensión (Gemini podría dar 768), así que mezclar obliga a reindexar todo y crear otra columna `vector(n)`. El RAG tiene que funcionar offline, y los documentos ya se indexan antes de la demo.

## 6. Baseline

**Plantillas** con las mismas salidas de tools. Siempre funcionan, sin red ni LLM. Son la última red de la demo.

## 7. Riesgos y cómo medirlos

| Riesgo | Mitigación |
|---|---|
| 429 por cuota o límites que cambian sin aviso | Un reintento con espera y, si falla, plantillas. Contar los 429 en el log |
| Latencia y red del local | Timeout de 8 s y luego plantillas. La demo principal va con Ollama |
| Clave filtrada | Solo en `.env` (ya está en `.gitignore`); `.env.example` con `GEMINI_API_KEY=xxxx`; no se registra en logs. Proyecto de AI Studio nuevo y sin facturación (así no hay cobros) |
| La organización no lo autoriza | Preguntar al mentor antes del 15/11. Si dicen que no, se apaga con `LLM_PROVIDER=ollama` y no se toca nada más |
| Modelo renombrado u obsoleto | Fijar el ID exacto `gemini-3.5-flash-lite` en la configuración |

**Cómo sabemos que funciona:** las mismas 20 a 30 preguntas fijas de `metricas.md` con Ollama, Gemini y plantillas. Metas: 100 % de cifras verificadas por el juez, p95 < 8 s, 0 bloqueos fallidos en las preguntas adversas y cuántos 429 hubo.

## 8. Recomendación final

1. **Ollama local**: por defecto en la demo.
2. **Gemini `gemini-3.5-flash-lite` gratis**: solo si Ollama falla, hay red, el mentor lo autorizó y `LLM_PROVIDER=gemini`. El juez de cifras sigue igual.
3. **Plantillas**: último respaldo, siempre disponibles.
4. Embeddings: siempre locales.

Cifras para `cifras-publicas.md`: ninguna. Son datos técnicos, no de calibración ni del pitch.

[p]: https://aistudio.google.com/docs/pricing
[r]: https://aistudio.google.com/docs/available-regions
[t]: https://aistudio.google.com/docs/terms
[rl]: https://aistudio.google.com/docs/rate-limits
[mo]: https://aistudio.google.com/docs/models
[m35]: https://aistudio.google.com/docs/models/gemini-3.5-flash-lite
[l]: https://aistudio.google.com/docs/libraries
[o]: https://aistudio.google.com/docs/openai
[e]: https://aistudio.google.com/docs/embeddings
[pg]: https://pypi.org/project/google-genai/
[plc]: https://pypi.org/project/langchain-google-genai/
[lc]: https://docs.langchain.com/oss/python/integrations/chat/google_generative_ai
[b1]: https://www.aifreeapi.com/en/posts/google-gemini-api-free-tier
[b2]: https://tinkerllm.com/blog/gemini-api-free-tier-limits-rate-quotas/
[b3]: https://imisofts.com/blog/gemini-api-free-tier-limits/

Todas las fuentes se consultaron el 2026-11-14.
