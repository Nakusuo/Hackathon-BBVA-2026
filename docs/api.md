# Lucas — Contrato de API REST

**Versión:** 1.0 — aprobada (MG-01)  
**Responsable:** Miguel — Backend  
**Revisión funcional:** Marcela (Frontend), Jeffrey (Agente IA)  
**Validación de modelos:** Diego (Analítica)  
**Validación de seguridad y persistencia:** Michael (Arquitectura)  
**Estado:** APROBADO el 2026-11-14 por Marcela, Jeffrey, Diego y Michael (acuerdo fuera de GitHub, registrado por Marcela).

## 1. Alcance y convenciones

Lucas expone información financiera derivada de **datos sintéticos** y permite simulaciones; **no mueve dinero**. La API propuesta utiliza FastAPI, JSON y prefijo `/api/v1`. La moneda principal es `PEN`; identificadores de cliente `customer_id`; fechas `YYYY-MM-DD` y marcas temporales ISO 8601 con zona horaria.

- GET para consultas, POST para operaciones de registro o simulación. Un POST de simulación no persiste cambios financieros.
- Montos de gastos, ingresos, metas y cambios de simulación: números positivos donde corresponda; no usar flotantes binarios para cálculos monetarios de producción (usar `Decimal`).
- Los datos financieros deben aislarse por cliente mediante autenticación/autorización por definir con Michael. **No asumir que un `customer_id` en la ruta concede acceso**.
- Los valores `confidence`, `quadrant`, `segment` y probabilidades requieren validación de los modelos de Diego.
- Los archivos en `data/sample/mocks/` son ejemplos ilustrativos, **no datos reales ni resultados validados de modelos**.
- `demo-001` es la persona del motor del front: sus respuestas de `health`, `forecast`, `recommendations` y `events` salen de `data/sample/demo-001/`, que genera `frontend/scripts/exportar-persona-demo.mjs`. Si cambia el motor hay que regenerarlas (`node scripts/exportar-persona-demo.mjs` desde `frontend/`); `frontend/pruebas/demo001.test.js` falla si no se hizo. El chat de `demo-001` también cita esos JSON (pronóstico, salud, tips y simulación de un gasto); lo que no está en ellos lo contesta como «sin datos». Los ids de la base (`C000xx`) usan el modelo en `forecast` y no tienen las otras tres rutas.
- El campo `sample_only: true` en pronóstico y simulación significa que la serie está truncada intencionalmente; en producción el horizonte de 30 días deberá contener los días previstos conforme al contrato aprobado.

## 2. Inventario de endpoints propuestos

| Método | Ruta | Mock respuesta | Mock solicitud |
|---|---|---|---|
| GET | `/api/v1/customers/{customer_id}/health` | `health.json` | — |
| GET | `/api/v1/customers/{customer_id}/forecast` | `forecast.json` | — |
| GET | `/api/v1/customers/{customer_id}/recommendations` | `recommendations.json` | — |
| GET | `/api/v1/customers/{customer_id}/events` | `events.json` | — |
| POST | `/api/v1/simulations` | `simulation.json` | `simulation-request.json` |
| GET | `/api/v1/fx` | `fx.json` | — |
| GET | `/api/v1/customers/{customer_id}/goals` | `goals.json` | — |
| POST | `/api/v1/customers/{customer_id}/goals` | `goal-created.json` | `goal-request.json` |
| GET | `/api/v1/customers/{customer_id}/offers` | `offers.json` | — |
| POST | `/api/v1/customers/{customer_id}/expenses` | `expense.json` | `expense-request.json` |
| POST | `/api/v1/chat` | `chat.json` | `chat-request.json` |
| POST | `/api/v1/onboarding` | `onboarding.json` | `onboarding-request.json` |

**Estado de las rutas:** aprobadas con la versión 1.0 del contrato. La tabla incluye onboarding y ofertas, ausentes del inventario inicial.

## 3. Salud financiera

**GET** `/api/v1/customers/{customer_id}/health` — Respuesta 200: `health.json`.

Campos actuales: `customer_id` (string), `score` (number), `status` (string), `quadrant` (string), `emergency_fund_months` (number), `currency` (`PEN`). Los rangos y vocabularios de score, status y quadrant deben acordarse con Diego. **No asumir** que `Q2` es un cuadrante oficial.

## 4. Pronóstico financiero

**GET** `/api/v1/customers/{customer_id}/forecast`

Devuelve el pronóstico de saldo para los próximos 30 días,
incluyendo bandas de incertidumbre al 80 % y el primer día
de riesgo de saldo negativo.

### Parámetros

- `customer_id` (string, obligatorio): identificador del cliente.
- `days` (integer, opcional): horizonte de pronóstico. Por defecto 30.

### Respuesta HTTP 200

El objeto contiene:

- `customer_id`: identificador del cliente.
- `currency`: moneda del saldo.
- `horizon_days`: horizonte solicitado.
- `confidence_level`: nivel de la banda de predicción.
- `forecast`: serie diaria de saldos previstos.
- `first_risk_date`: primer día de riesgo, o null.
- `model`: identificador del modelo utilizado.

### Reglas

- El pronóstico no representa un saldo garantizado.
- Las bandas inferior y superior expresan incertidumbre.
- El cálculo debe provenir del modelo de Diego.
- Los datos simulados deben identificarse como tales.
- La respuesta debe permitir dibujar el gráfico de saldo.

**Mock:** `forecast.json` contiene solo cuatro días ilustrativos y `sample_only: true`; no debe interpretarse como un pronóstico completo de 30 días. `first_risk_date` es demostrativo. La banda al 80 % requiere confirmación con Diego.

## 5. Motor de recomendaciones

**GET** `/api/v1/customers/{customer_id}/recommendations`

Devuelve hasta tres recomendaciones financieras personalizadas
según la situación económica del cliente.

### Parámetros

- `customer_id` (string, obligatorio): identificador del cliente.

### Respuesta HTTP 200

- `customer_id`: identificador del cliente.
- `currency`: moneda del impacto económico.
- `recommendations`: lista de cero a tres recomendaciones.

Cada recomendación contiene:

- `id`: identificador de la recomendación.
- `action`: acción sugerida.
- `estimated_impact`: impacto estimado en soles.
- `impact_period`: periodo del impacto.
- `reason`: justificación basada en los datos.
- `data_used`: datos utilizados.
- `assumptions`: supuestos del cálculo.
- `confidence`: alta, media o baja.
- `disclaimer`: mensaje de orientación y decisión del usuario.

### Reglas de negocio

1. Devolver como máximo tres recomendaciones.
2. Generar candidatos mediante reglas financieras.
3. Puntuar por impacto económico y facilidad.
4. Ajustar la puntuación según el segmento financiero.
5. Aplicar filtros de seguridad antes de seleccionar el top 3.
6. No recomendar crédito con colchón inferior a un mes
   o deuda alta.
7. No recomendar productos de inversión o ahorro a plazo
   con colchón inferior a tres meses o deuda cara.
8. No recomendar comprar ni vender dólares.
9. No prometer rentabilidades.
10. Toda recomendación debe incluir "tú decides".

### Dependencias

- DI-05: segmentación de clientes.
- DI-07: modelo de salud financiera.
- MG-04: implementación del recomendador.

**Mock:** `recommendations.json`. Se añade `impact_type` para distinguir `expense_reduction` (gasto evitado) de `savings_allocation` (dinero apartado; no es ganancia). Valores y taxonomía por aprobar. `estimated_impact` conserva el valor original y se interpreta según `impact_type`.

## 6. Eventos y alertas financieras

**GET** `/api/v1/customers/{customer_id}/events`

Devuelve los eventos financieros relevantes del cliente,
incluyendo alertas preventivas y recordatorios.

### Parámetros

- `customer_id` (string, obligatorio): identificador del cliente.

### Respuesta HTTP 200

- `customer_id`: identificador del cliente.
- `events`: lista de eventos financieros.
- `weekly_notifications_remaining`: avisos disponibles esta semana.

Cada evento contiene:

- `id`: identificador del evento.
- `type`: tipo de evento financiero.
- `title`: título del aviso.
- `message`: descripción del evento.
- `event_date`: fecha del evento.
- `priority`: low, medium o high.
- `estimated_impact`: impacto económico estimado en PEN.
- `notified`: indica si se envió una notificación.

### Tipos de eventos

- `income`: ingreso de dinero.
- `gratification`: gratificación.
- `cts`: depósito de CTS.
- `recurring_expense`: gasto recurrente.
- `negative_balance_risk`: riesgo de saldo negativo.

### Reglas de negocio

1. Máximo tres avisos por semana por cliente.
2. Priorizar los eventos de mayor relevancia.
3. Evitar notificaciones duplicadas.
4. No generar avisos alarmistas.
5. Utilizar los resultados del pronóstico financiero.
6. No realizar movimientos de dinero.

### Dependencias

- DI-06: pronóstico financiero.
- MG-05: motor de eventos y avisos.

## 7. Simulador financiero y Sueldo Lucas

**POST** `/api/v1/simulations`

Permite comparar el pronóstico financiero original
con un escenario hipotético de cambios en ingresos
o gastos, sin modificar los datos originales.

### Request

- `customer_id`: identificador del cliente.
- `horizon_days`: horizonte de simulación (30 por defecto).
- `changes`: lista de cambios hipotéticos.

Cada cambio contiene:

- `type`: income o expense.
- `amount`: monto positivo en PEN.
- `frequency`: once o monthly.
- `description`: descripción del cambio.

### Response HTTP 200

- `customer_id`: identificador del cliente.
- `currency`: PEN.
- `horizon_days`: horizonte calculado.
- `baseline`: escenario original.
- `simulated`: escenario modificado.
- `difference`: diferencia de saldo final.
- `disclaimer`: advertencia de simulación.

Cada escenario contiene:

- `final_balance`: saldo al final del horizonte.
- `negative_balance_days`: días con saldo negativo.
- `forecast`: serie diaria de saldos previstos.

### Reglas

1. No modificar transacciones reales.
2. No realizar transferencias ni movimientos de dinero.
3. Utilizar el modelo de pronóstico de Diego.
4. Mostrar el escenario original y el simulado.
5. Identificar los resultados como simulaciones.
6. Validar los montos y tipos de cambio.
7. No prometer resultados financieros.

### Pendientes

- Definir el contrato específico de Sueldo Lucas.
- Confirmar la representación de ingresos recurrentes.
- Confirmar con Diego cómo se recalcula el pronóstico.
- Confirmar con Marcela los controles del simulador.

### Dependencias

- DI-06: pronóstico financiero.
- MG-07: implementación del simulador.
- MC-05: interfaz del simulador.

**Mocks:** `simulation-request.json` (solicitud) y `simulation.json` (respuesta). La respuesta es parcial (`sample_only: true`); no demuestra que el modelo calcule 30 registros. La regla temporal exacta para `frequency: monthly` y el contrato de Sueldo Lucas requieren acuerdo con Diego.

## 8. Metas de ahorro

**GET** `/api/v1/customers/{customer_id}/goals`

Devuelve las metas de ahorro del cliente y su progreso.

**POST** `/api/v1/customers/{customer_id}/goals`

Registra una nueva meta de ahorro.

### Request POST

- `name`: nombre de la meta.
- `target_amount`: monto objetivo en PEN.
- `target_date`: fecha límite.
- `current_amount`: monto ahorrado inicialmente.

### Response HTTP 200 (GET)

- `customer_id`: identificador del cliente.
- `currency`: PEN.
- `goals`: lista de metas.

Cada meta contiene:

- `id`: identificador de la meta.
- `name`: nombre.
- `target_amount`: monto objetivo.
- `current_amount`: monto acumulado.
- `target_date`: fecha límite.
- `progress_percentage`: porcentaje completado.
- `suggested_biweekly_saving`: ahorro quincenal sugerido.
- `projected_year_end_savings`: ahorro proyectado a fin de año.
- `completion_probability`: probabilidad estimada de cumplir la meta.

### Reglas de negocio

1. El ahorro sugerido no debe provocar saldo negativo
   en el escenario proyectado.
2. Utilizar el pronóstico financiero de Diego.
3. Validar que los montos sean positivos.
4. No prometer el cumplimiento de una meta.
5. Expresar las proyecciones como estimaciones.
6. No mover dinero automáticamente.

### Dependencias

- DI-06: pronóstico financiero.
- MG-11: implementación de metas.

**Mocks:** `goals.json` (GET), `goal-request.json` (POST) y `goal-created.json` (respuesta ilustrativa POST). Para creación se **propone** HTTP 201, sujeto a acuerdo. `completion_probability` y la proyección anual son valores ficticios.

## 9. Ofertas responsables

**GET** `/api/v1/customers/{customer_id}/offers`

Devuelve hasta tres ofertas ficticias o genéricas
seleccionadas según el perfil financiero del cliente.

### Parámetros

- `customer_id` (string, obligatorio).

### Respuesta HTTP 200

- `customer_id`: identificador del cliente.
- `currency`: PEN.
- `offers`: lista de ofertas elegibles.

Cada oferta contiene:

- `id`: identificador.
- `name`: nombre genérico.
- `category`: categoría.
- `description`: descripción.
- `reason`: justificación personalizada.
- `estimated_benefit`: beneficio estimado.
- `eligible`: indica si cumple las reglas.
- `disclaimer`: advertencia informativa.

### Reglas de negocio

1. Usar exclusivamente ofertas ficticias o genéricas.
2. No utilizar nombres ni promociones reales de bancos.
3. Seleccionar por necesidad, cuadrante e idoneidad.
4. No recomendar crédito si el cliente incumple
   las reglas de seguridad financiera.
5. Ofrecer ahorro a plazo o educación sobre inversión
   solo con colchón >= 3 meses y sin deuda cara.
6. No prometer rentabilidades.
7. Comparar precision@3 contra ofertas populares.
8. Ninguna oferta ejecuta operaciones financieras.

### Dependencias

- MG-08: catálogo y motor de ofertas.
- DI-05: segmentación financiera.
- DI-07: salud financiera.

## 10. Registro de gastos

**POST** `/api/v1/customers/{customer_id}/expenses`

Registra un gasto del cliente para su posterior análisis.

### Parámetros

- `customer_id` (string, obligatorio): identificador del cliente.

### Request JSON

- `amount`: monto del gasto, mayor que cero.
- `currency`: moneda, PEN para el MVP.
- `category`: categoría del gasto.
- `description`: descripción opcional.
- `date`: fecha del gasto en formato ISO 8601.

### Response HTTP 201

- `id`: identificador generado para el gasto.
- `customer_id`: identificador del cliente.
- `amount`: monto registrado.
- `currency`: moneda.
- `category`: categoría.
- `description`: descripción.
- `date`: fecha del gasto.
- `created_at`: fecha y hora de registro.

### Reglas

1. Validar el monto con Pydantic.
2. Rechazar montos iguales o inferiores a cero.
3. Validar la fecha y la categoría.
4. No permitir registrar gastos de otro cliente.
5. No realizar movimientos bancarios reales.
6. Devolver errores controlados.
7. Persistir los registros cuando esté implementada
   la integración con PostgreSQL.

### Dependencias

- MG-03: API FastAPI.
- MI-03: estructura y permisos de PostgreSQL.
- MC-05: formulario de ingresos y gastos.

### Pendientes

- Confirmar las categorías admitidas.
- Confirmar el esquema de persistencia con Michael.
- Confirmar si el frontend necesita registrar ingresos
mediante otro endpoint.

## 11. Servicio de tipo de cambio (FX)

**GET** `/api/v1/fx`

Devuelve el tipo de cambio de referencia entre USD y PEN.

### Parámetros

- `base` (string, opcional): moneda base, USD por defecto.
- `quote` (string, opcional): moneda destino, PEN por defecto.

### Response HTTP 200

- `base`: moneda base.
- `quote`: moneda destino.
- `rate`: tipo de cambio de referencia.
- `date`: fecha del dato.
- `source`: fuente del valor.
- `is_fallback`: indica si se utilizó un respaldo.
- `is_stale`: indica si el dato está desactualizado.

### Reglas

1. Consultar primero la fuente BCRP.
2. Utilizar caché cuando la fuente no responda.
3. Recurrir al último valor conocido si es necesario.
4. Utilizar una serie grabada para la demo como último recurso.
5. Identificar claramente los datos de respaldo.
6. No recomendar comprar ni vender dólares.
7. No ejecutar conversiones ni operaciones bancarias reales.
8. No presentar el valor como una cotización comercial garantizada.

### Dependencias

- Servicio de consulta BCRP.
- Configuración de caché y respaldos.
- MG-03: implementación de FastAPI.

## 12. Chat de Lucas

**POST** `/api/v1/chat`

Recibe un mensaje del usuario y devuelve una respuesta
generada por el agente conversacional.

### Request JSON

- `customer_id`: identificador del cliente.
- `message`: mensaje del usuario.
- `conversation_id`: identificador opcional de conversación.

### Response HTTP 200

- `conversation_id`: identificador de conversación.
- `answer`: respuesta del agente.
- `provider`: proveedor utilizado.
- `verified`: indica si las cifras fueron verificadas.
- `sources`: fuentes utilizadas para la respuesta.
- `tools_used`: herramientas consultadas.

### Reglas

1. El agente utiliza herramientas de solo lectura.
2. Las cifras financieras deben verificarse contra
   las salidas de las herramientas.
3. Ante un error del proveedor, se utiliza el mecanismo
   de reintento y respuesta por plantilla.
4. No ejecutar transferencias ni operaciones bancarias.
5. No revelar información financiera de otros clientes.
6. No exponer claves ni datos internos del servidor.
7. Las respuestas deben distinguir estimaciones
   de información confirmada.

### Dependencias

- JF-02: grafo del agente.
- JF-03: herramientas del agente.
- JF-04: verificador de cifras.
- MC-06: interfaz del chat.

### Pendientes

- Dueño del endpoint: propuesta, Miguel lo expone y llama a `agent.chat.responder` de Jeffrey.
- Campos que el front ya consume (PR #16): `figures` `[{label, value, unit, text}]` con `unit` en `PEN`, `percent`, `months`, `days` o `score`, y `sources` `[{id, title, url}]` (acepta también `titulo` y `enlace`). Con `verified` distinto de `true` el front no muestra `answer` y responde con su plantilla.
- Unificar `provider`: el mock dice `template` y el agente `plantilla`.
- Confirmar que el texto libre del usuario nunca se envía a Gemini (ISO 27001, 8.12).
- Definir autenticación y permisos con Michael.

**Mocks:** `chat-request.json`, `chat.json`. `verified: true` en el ejemplo no demuestra verificación real; Jeffrey debe definir el criterio, la procedencia de `sources` y el comportamiento ante error del proveedor. También debe acordarse quién implementa `/chat`.

## 13. Lucas en 5 preguntas — Onboarding

**POST** `/api/v1/onboarding`

Recibe cinco respuestas de un usuario nuevo y devuelve
una asignación inicial de perfil financiero.

### Request JSON

- `customer_id`: identificador del cliente.
- `answers`: objeto con cinco respuestas.

Campos provisionales de answers:

- `monthly_income`: ingreso mensual estimado.
- `monthly_expenses`: gastos mensuales estimados.
- `current_savings`: ahorros disponibles.
- `monthly_debt_payment`: pago mensual de deudas.
- `income_stability`: estabilidad de ingresos.

### Response HTTP 200

- `customer_id`: identificador del cliente.
- `profile`: perfil financiero asignado.
- `confidence`: confianza estimada del modelo, si está disponible.
- `model`: identificador del modelo utilizado.
- `is_estimate`: indica que es una evaluación inicial.

### Reglas

1. Validar las cinco respuestas con Pydantic.
2. Rechazar montos negativos.
3. No asignar un perfil mediante valores arbitrarios.
4. Utilizar el modelo de asignación de Diego.
5. Identificar los resultados como estimaciones.
6. No ejecutar operaciones financieras.
7. No almacenar información sensible innecesaria.

### Dependencias

- DI-12: modelo de asignación (Diego).
- MG-10: endpoint FastAPI (Miguel).
- MC-08: pantalla de onboarding (Marcela).

### Pendientes

- Confirmar las cinco preguntas definitivas con Diego.
- Confirmar los nombres y tipos de las respuestas.
- Confirmar los perfiles que devuelve el modelo.
- Confirmar el contrato con Marcela.

**Mocks:** `onboarding-request.json` y `onboarding.json`. Las cinco preguntas son provisionales; el resultado usa `pending_model_assignment`, no una clasificación real. Requiere validación DI-12.

## 14. Errores HTTP y validación

| Código | Significado |
|---|---|
| 400 | Solicitud inválida por regla de negocio |
| 401 | Falta autenticación |
| 403 | Acceso no autorizado al cliente |
| 404 | Cliente o recurso no encontrado |
| 422 | Error de validación Pydantic |
| 500 | Error interno controlado, sin detalles sensibles |
| 503 | Dependencia externa no disponible |

Ejemplo **propuesto** de error (confirmar compatibilidad con el manejador FastAPI/Pydantic):

```json
{"error":{"code":"CUSTOMER_NOT_FOUND","message":"No se encontró el cliente solicitado"}}
```

**Nota:** FastAPI devuelve por defecto errores de validación con `detail`; si se adopta el esquema anterior, deberá implementarse un manejador de excepciones y documentarse explícitamente. El formato aún no está aprobado.

## 15. Matriz de decisiones pendientes de aprobación

| Decisión | Quién valida | Estado |
|---|---|---|
| Rutas, parámetros, paginación y campos requeridos por las pantallas | Marcela + Miguel | Aprobado |
| Contrato `/chat`, `conversation_id`, `verified`, `sources` y dueño del endpoint | Jeffrey + Miguel | Aprobada la base; quedan los pendientes de la sección 12 |
| Contratos de score, cuadrantes, segmentos y confianza | Diego + Miguel | Aprobado |
| Serie diaria de 30 días, bandas y definición de riesgo | Diego + Miguel | Aprobado |
| Reglas de simulación, recurrencia y Sueldo Lucas | Diego + Marcela + Miguel | Aprobado |
| Cinco preguntas definitivas y salida DI-12 | Diego + Marcela + Miguel | Aprobado |
| Autenticación, autorización, esquemas y permisos PostgreSQL | Michael + Miguel | Aprobado |
| Propietario de integración BCRP, caché y endpoint FX | Jeffrey + Miguel | Aprobado |
| Categorías de gastos, ingreso manual y persistencia | Marcela + Michael + Miguel | Aprobado |
| Tipos de impacto, elegibilidad, ofertas y cálculo precision@3 | Diego + Miguel | Aprobado |
| Probabilidad de metas y proyección de ahorro | Diego + Miguel | Aprobado |
| Códigos HTTP y formato uniforme de errores | Michael + Miguel | Aprobado |

## 16. Criterio de cierre de MG-01

- [x] Documentación inicial de los endpoints propuestos.
- [x] Mocks JSON sintácticamente válidos, incluidos request y response para los POST documentados.
- [x] Duplicación de recomendaciones eliminada; inventario y numeración revisados.
- [x] Confirmación de contratos con Marcela y Jeffrey.
- [x] Validación de campos derivados de modelos con Diego.
- [x] Aprobación de seguridad/autorización con Michael.
- [x] Registrar acuerdos y actualizar este documento a versión aprobada.

Aprobado el 2026-11-14 por Marcela, Jeffrey, Diego y Michael, fuera de GitHub (el PR #4 se unió sin revisiones); lo registra Marcela. Los cambios al contrato desde ahora van por PR con revisión de los afectados.
