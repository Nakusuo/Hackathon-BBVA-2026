# Estado del proyecto

Actualizar al terminar cada tarea y en cada checkpoint (10 min: qué está hecho, qué bloquea, qué se recorta).

## Equipo y roles

| Rol | Persona | Subagente |
|---|---|---|
| Datos | — | `datos` |
| ML / Analítica | — | `ml-analitica` |
| IA / Chat | — | `ia-chat` |
| Backend | — | `backend` |
| Frontend / UX | — | `frontend-ux` |
| PM / Pitch | — | `pitch-docs` |
| Investigación | — | `investigador` |
| Verificación | — | `juez-tecnico`, `juez-producto`, `juez-cumplimiento` |

## Decisiones tomadas

| Fecha | Decisión | Motivo |
|---|---|---|
| 2026-11-14 | Problema principal: liquidez a 30 días | Bases piden un problema y una población |
| 2026-11-14 | Datos: generador propio + DuckDB, calibrado con cifras públicas | No hay dataset peruano a nivel transacción |
| 2026-11-14 | LLM intercambiable: Ollama → API opcional → plantillas | BBVA no da claves; demo offline |
| 2026-11-14 | LLM local `qwen2.5:3b` 100 % en la RTX 3050 (4 GB), contexto 4096, flash attention, KV q8 y modelo siempre cargado | Cabe entero en VRAM y cumple < 8 s; el resto del pipeline va en CPU |
| 2026-11-14 | Lucas como compañero bancario: avisos anticipados y Sueldo Lucas pasan a DEBE; Lucas en 5 preguntas a DEBERÍA alta | Indicación del juez: fidelización, atracción, nada cosmético |
| 2026-11-14 | Gitflow simplificado y flujo investigador, codificador y jueces | Control del avance y verificación |
| — | UI: Streamlit o React + Recharts (decidir en la 1.ª hora y no cambiar) | — |

## Respuestas de la organización

| Pregunta | Respuesta |
|---|---|
| LLM externo con clave propia | — |
| Dataset común | — |
| APIs públicas en la demo | — |
| Formato de entrega y hora de cierre | — |
| Prueba de evolución | — |
| Modelos/dependencias descargados de antemano | — |

## Avance del MVP

### DEBE
- [ ] D1 Generador de datos sintéticos (calendario PE + escenarios difíciles)
- [ ] D2 Motor: categorías, fijo/variable, gasto hormiga, recurrentes
- [ ] D3 Salud financiera 0–100 con componentes
- [ ] D4 Pronóstico 30 días + banda + «día de riesgo»
- [ ] D5 Recomendador híbrido (3 acciones con impacto, por qué, límites, confianza)
- [ ] D6 Simulador «qué pasaría si»
- [ ] D7 Chat con tools + verificador + fallback
- [ ] D8 Panel Evidencia (baseline vs modelo, cobertura, % verificado)
- [ ] F1 Avisos anticipados del día de riesgo (fidelización)
- [ ] F2 Sueldo Lucas: monto quincenal estable para ingresos irregulares (fidelización)

### DEBERÍA
- [ ] A1 Lucas en 5 preguntas: pronóstico sin historial (atracción, prioridad alta)
- [ ] A2 Plata del negocio y plata de la casa (atracción)
- [ ] F4 Resumen de la quincena con cambios del puntaje
- [ ] Perfiles K-Prototypes
- [ ] Detector de suscripciones duplicadas
- [ ] Formulario «agrega un gasto o meta» con recálculo en vivo
- [ ] Tipo de cambio BCRP con caché y respaldo
- [ ] Pantalla de consentimiento + «explícamelo fácil»

### PODRÍA
- [ ] F3 Plan de grati y CTS
- [ ] Explicación contrafactual
- [ ] Alerta de movimiento atípico
- [ ] Prueba de equipo rojo en vivo

## Hitos del cronograma

| Hito | Cuándo | Estado |
|---|---|---|
| Repo con estructura, `.env.example`, esquema acordado | Sáb, 1.ª hora | — |
| `make data` funciona; UI navega las 5 pantallas | Sáb mañana | — |
| Primer flujo de punta a punta | Sáb tarde | — |
| Demo completa (aunque fea) | Sáb noche | — |
| EVALUATION.md con números reales | Dom temprano | — |
| Congelamiento de código | Dom mediodía | — |
| 3 ensayos del pitch (10:00 min) | Dom tarde | — |

**Regla de recorte:** si a mitad del día 1 el flujo de punta a punta no funciona, se recorta todo lo «Debería».

## Bloqueos y recortes

| Fecha | Qué | Acción |
|---|---|---|
| — | — | — |
