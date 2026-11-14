# Informe de avances — Lucas | Hackathon BBVA 2026

**Responsable:** Miguel Allca  
**Equipo:** Equipo 2  
**Área:** Backend / API REST  
**Proyecto:** Lucas, asistente financiero  
**Rama de trabajo:** `feature/backend-fastapi`  
**Fecha de corte:** 14 de noviembre de 2026  
**Alcance del informe:** trabajo realizado hasta antes de iniciar el paso 26.2 (preparación de integración).

## 1. Resumen ejecutivo

Se implementó la primera versión del backend de Lucas utilizando **FastAPI**, **Pydantic** y **datos sintéticos (mocks)**. Se desarrollaron las **12 rutas de negocio** previstas en el borrador del contrato MG-01, además de un endpoint de salud del servidor. Se incorporaron validaciones y pruebas automatizadas con **Pytest** y **TestClient**. El avance reportado al cierre fue de **94 pruebas aprobadas**.

Los cambios se confirmaron y subieron a la rama remota `feature/backend-fastapi`. **No se ha confirmado la creación, aprobación o fusión de un Pull Request.**

> **Alcance real:** los endpoints están disponibles como implementación inicial de demostración; no equivalen a un backend integrado con base de datos, modelos analíticos ni agente de IA. Los resultados financieros no son datos reales ni predicciones verificadas.

## 2. Trabajo completado

### 2.1. Estructura y herramientas

- Configuración de una aplicación FastAPI con Uvicorn.
- Organización de rutas en `src/api/routers/` y esquemas de validación en `src/api/schemas/`.
- Uso de Pydantic para validar solicitudes y respuestas.
- Configuración y ejecución de pruebas con Pytest y FastAPI TestClient.
- Disponibilidad de documentación interactiva mediante Swagger UI (`/docs`).
- Trabajo aislado en la rama Git `feature/backend-fastapi`.

### 2.2. Implementación de endpoints

Todas las rutas siguientes tienen el prefijo `/api/v1`.

| N.º | Método | Ruta | Estado / alcance |
|---:|---|---|---|
| 1 | GET | `/customers/{customer_id}/health` | Salud financiera sintética |
| 2 | GET | `/customers/{customer_id}/forecast` | Pronóstico financiero sintético |
| 3 | GET | `/customers/{customer_id}/recommendations` | Recomendaciones de demostración |
| 4 | GET | `/customers/{customer_id}/events` | Eventos financieros sintéticos |
| 5 | POST | `/simulations` | Simulaciones sin operaciones reales |
| 6 | GET | `/fx` | Tipo de cambio de respaldo, identificado como estimado/desactualizado |
| 7 | GET | `/customers/{customer_id}/goals` | Consulta de metas sintéticas |
| 8 | POST | `/customers/{customer_id}/goals` | Creación simulada, sin persistencia |
| 9 | GET | `/customers/{customer_id}/offers` | Ofertas genéricas ficticias |
| 10 | POST | `/customers/{customer_id}/expenses` | Registro simulado, sin persistencia |
| 11 | POST | `/chat` | Respuesta mock, sin agente conectado |
| 12 | POST | `/onboarding` | Recepción y validación de cinco respuestas; clasificación pendiente |

**Endpoint técnico adicional:** `GET /api/v1/health`.

### 2.3. Validaciones implementadas

- Verificación de campos obligatorios, tipos de datos y montos financieros.
- Rechazo de importes negativos o nulos donde el contrato requiere valores positivos.
- Respuestas HTTP de validación (422) y cliente no encontrado (404) en los escenarios cubiertos.
- Uso del cliente de demostración `demo-001` para los mocks.
- En onboarding, validación de ingreso, gastos, ahorros, pagos de deuda y estabilidad de ingresos; sin asignación arbitraria de perfil.
- En creación de metas, aceptación de `current_amount` opcional, cálculo del porcentaje inicial de progreso y rechazo de ahorros superiores al monto objetivo.
- En consulta de metas, incorporación de `currency` y campos provisionales de proyección (`suggested_biweekly_saving`, `projected_year_end_savings`, `completion_probability`) que pueden quedar en `null` mientras no estén disponibles los cálculos.

### 2.4. Pruebas y control de versiones

- Pruebas automatizadas por endpoint con Pytest y TestClient.
- **94 pruebas reportadas como aprobadas** tras corregir una validación de metas de ahorro.
- Corrección del caso en el que un ahorro inicial mayor al objetivo devolvía HTTP 201 en lugar de HTTP 422.
- Cambios subidos a GitHub en la rama `feature/backend-fastapi`.

## 3. Estado de los entregables

| Entregable | Estado |
|---|---|
| MG-01 — Contrato de API REST, versión 0.2 | Borrador técnico; pendiente de aprobación del equipo |
| MG-03 — Implementación inicial de endpoints FastAPI con mocks | Implementado y subido a rama remota |
| Validaciones Pydantic | Implementadas para los escenarios trabajados |
| Pruebas automatizadas | 94 aprobadas, según lo reportado |
| Pull Request | Creación y revisión no confirmadas |
| Fusión a rama principal | No confirmada |
| Persistencia PostgreSQL | Pendiente |
| Modelos financieros reales | Pendiente |
| Agente conversacional real | Pendiente |
| Integración frontend-backend | Pendiente |
| Autenticación/autorización por cliente | Pendiente |
| Despliegue del MVP | Pendiente |

## 4. Trabajo pendiente y dependencias

### Prioridad alta

1. **Revisar y aprobar MG-01:** confirmar campos, respuestas, códigos HTTP, perfiles y valores provisionales con los responsables del equipo.
2. **Preparar y revisar el Pull Request:** comparar `feature/backend-fastapi` con la rama de integración acordada, resolver observaciones y evitar fusionar cambios sin revisión.
3. **Integrar PostgreSQL con Michael:** conexión, modelos de datos, migraciones, consultas y persistencia de metas y gastos.
4. **Definir autenticación y autorización con Michael:** garantizar que cada cliente solo acceda a sus propios datos; el identificador en la URL no es autorización suficiente.
5. **Integrar analítica con Diego:** salud financiera, pronósticos, segmentación, recomendaciones, simulaciones, probabilidades y clasificación del onboarding.
6. **Integrar el agente IA con Jeffrey:** sustituir el mock de `/chat`, definir herramientas autorizadas y trazabilidad de respuestas.
7. **Conectar el frontend con Marcela:** acordar contratos definitivos, configuración de CORS y manejo de respuestas y errores.

### Prioridad media

8. Reemplazar progresivamente los mocks por datos y resultados procesados, conservando indicadores claros de simulación o estimación.
9. Agregar pruebas de integración y pruebas de extremo a extremo.
10. Revisar la consistencia de los formatos de error y los códigos HTTP frente al contrato aprobado.
11. Configurar variables de entorno, despliegue y controles operativos básicos.
12. Ejecutar una prueba integral del flujo de demostración de Lucas.

## 5. Orden sugerido para continuar

1. Confirmar el estado del Pull Request y obtener revisión del equipo.
2. Cerrar las observaciones y aprobar el contrato MG-01.
3. Coordinar persistencia y seguridad con Michael.
4. Integrar gradualmente los modelos de Diego y el agente de Jeffrey.
5. Conectar las pantallas de Marcela.
6. Ejecutar pruebas integrales y preparar el despliegue del MVP.

## 6. Consideraciones importantes

- Los datos usados hasta ahora son **sintéticos** y no representan información bancaria real.
- El backend **no realiza transferencias ni movimientos de dinero**.
- Las respuestas mock y los resultados provisionales **no deben presentarse como predicciones financieras validadas**.
- La implementación del onboarding devuelve una clasificación pendiente, no un perfil inferido arbitrariamente.
- El contrato MG-01 versión 0.2 sigue siendo un **borrador pendiente de aprobación**.
- Las pruebas existentes validan el comportamiento implementado; no sustituyen pruebas de integración ni una revisión exhaustiva del contrato.

---

**Elaborado para:** Miguel Allca  
**Corte de avance:** después de subir MG-03 a la rama remota y antes de iniciar el paso 26.2.
