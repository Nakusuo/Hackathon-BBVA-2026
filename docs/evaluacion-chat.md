# Evaluación del chat de Lucas (JF-07)

Sección del agente del chat (`src/agent`) para `EVALUATION.md`. Se regenera con:

```bash
python eval/evaluar_chat.py --llm plantilla
python eval/evaluar_chat.py --llm ollama
```

Resultados en `models/metricas_chat_plantilla.json` y `models/metricas_chat_ollama.json`.

## Qué se mide

- **30 preguntas fijas** (`tests/agent/preguntas.json`): pronóstico, simulación, salud, recomendaciones, perfil, tipo de cambio y fuera de tema, con la intención y las cifras esperadas.
- **10 preguntas adversas**: comprar o vender dólares, transferir, «en qué invierto» e inyección de prompt.
- **6 preguntas de educación** contra el índice del RAG de Diego (TCEA, CTS, gratificación, El Niño, derechos del consumidor, fondo de emergencia).
- Datos: los mocks del contrato MG-01 (`data/sample/mocks/`), cliente `demo-001`.
- Baseline: **plantillas** (sin LLM), que es también el respaldo del agente.

## Resultados (14/11/2026)

| Métrica | Plantilla (baseline) | Ollama `qwen2.5:3b` |
|---|---|---|
| Exactitud de la intención (30 fijas) | 100 % | 100 % |
| Cifras esperadas que salen verificadas | 100 % | 97 % |
| Respuestas aprobadas por el juez | 100 % | 100 % |
| Bloqueo de preguntas adversas (10) | 100 % | 100 % |
| Educación con cita válida (6) | 100 % | 100 % |
| Respuestas por plantilla, sin llamar al LLM | 100 % | 74 % |
| Latencia p50 | 0,00 s | 2,26 s |
| Latencia p95 | 2,28 s | 17,40 s |

La latencia de Ollama es de una laptop sin GPU dedicada (Intel Core Ultra 7 155H). En la RTX 3050 de Michael, con el modelo cargado, las respuestas tardaron entre 1,0 y 4,0 s (ver `PROMPTS.md`). Falta repetir esta tabla allí.

Fuente citada en cada pregunta de educación:

| Pregunta | Fuente |
|---|---|
| ¿Qué es la TCEA? | Res. SBS 3274-2017, Reglamento de Gestión de Conducta de Mercado |
| ¿Cómo funciona la CTS? | Guía de Compensación por Tiempo de Servicios (MTPE) |
| ¿Qué es la gratificación? | Guía de gratificaciones por Fiestas Patrias y Navidad (MTPE) |
| ¿Qué es el fenómeno El Niño? | Comunicado Oficial ENFEN N.º 16-2026 |
| ¿Qué derechos tengo como consumidor? | Código de Protección y Defensa del Consumidor (Ley 29571) |
| ¿Para qué sirve un fondo de emergencia? | Su dinero, sus metas (CFPB), con aviso de que es una guía de EE. UU. |

## Cómo leerlo

- **Ninguna cifra inventada llegó al usuario** con ninguno de los dos proveedores. Con Ollama el juez rechazó las redacciones con cifras que no estaban en los datos, y en esos casos respondió la plantilla. Eso explica que el 26 % de las respuestas venga del LLM y el resto de plantillas.
- La única falla con Ollama fue una respuesta **incompleta, no falsa**: en «¿Cuánto me va a quedar de saldo?» el LLM dio una sola de las dos cifras de la banda.
- **Las plantillas igualan o superan al LLM en todas las métricas de exactitud.** El LLM aporta redacción más natural en pronóstico, salud y recomendaciones. Simulación, tipo de cambio, perfil y educación van siempre por plantilla (motivos en `PROMPTS.md`).
- Costo de la demo: S/ 0. Ollama corre local y el 74 % de las respuestas ni siquiera lo llama.

## Límites

- Las 30 preguntas las escribimos nosotros y el router se ajustó con ellas: la exactitud de la intención sobre preguntas nuevas puede ser menor.
- Los datos son los mocks del contrato, no los modelos de Diego: cuando la API use sus modelos (MG-06), hay que volver a correr la evaluación.
- 6 preguntas de educación son pocas para medir el RAG; la evaluación de recuperación (recall@4 0,94) es la de Diego en `models/metricas_rag.json`.
- El juez revisa cifras, unidades, signos, fechas, palabras clave y frases prohibidas, pero no todo el sentido de un texto libre.
