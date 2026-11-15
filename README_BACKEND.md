# Lucas — Backend FastAPI (MG-03)

**Responsable:** Miguel Allca · **Proyecto:** Hackathon BBVA 2026, Equipo 2  
**Estado:** unida a `develop` (PR #10 y #24), con datos fijos  
**Contrato de referencia:** `docs/api.md` (MG-01 versión 1.0, aprobada).

## Alcance

API REST para el MVP de Lucas. Expone 12 rutas de negocio con datos sintéticos y respuestas provisionales, además de una ruta de salud del servidor. **No utiliza cuentas bancarias reales, no mueve dinero y todavía no integra PostgreSQL, modelos analíticos ni agente IA.** Las operaciones POST de creación de metas y gastos no persisten registros.

**Cómo la usa el MVP.** El front lee esta API y valida cada respuesta, pero no toma de ella ninguna cifra visible: las rutas describen a `demo-001`, que no es la persona del motor del front. Si la API no responde, el front usa `data/sample/mocks/` y avisa «Sin conexión». `/chat` devuelve un mock sin verificar, así que el chat del front responde con sus plantillas. Detalle en `ARCHITECTURE.md`, sección 2.3.

## Tecnologías

Python, FastAPI, Pydantic, Uvicorn, Pytest y TestClient/httpx. El proyecto se ha trabajado en Windows con PowerShell.

## Puesta en marcha (Windows / PowerShell)

Desde la raíz del repositorio:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

No hay un `requirements.txt` propio de la API. Lo mínimo para correrla y probarla:

```powershell
python -m pip install fastapi uvicorn pydantic httpx pytest
```

Inicia el servidor:

```powershell
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

Accesos locales:

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json
- Salud del servidor: http://127.0.0.1:8000/api/v1/health

Para probar el mock:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/customers/demo-001/health'
```

El identificador `demo-001` es un cliente ficticio de demostración; no constituye un mecanismo de autenticación.

## Pruebas

```powershell
python -m pytest tests/api/ -v
```

**Último resultado:** 99 pruebas aprobadas en `develop` (2026-11-14).

## Organización conocida

```text
src/api/main.py              # Aplicación FastAPI y registro de routers
src/api/routers/             # Endpoints
src/api/schemas/             # Modelos Pydantic
tests/api/                   # Pruebas por endpoint
data/sample/mocks/           # Ejemplos de datos sintéticos del contrato
docs/api.md                  # Contrato MG-01
src/api/loader_pkl.py        # Carga los .pkl de models/; main.py todavía no lo usa
```

## Endpoints

Todos tienen prefijo `/api/v1`.

| Método | Ruta | Alcance actual |
|---|---|---|
| GET | `/customers/{customer_id}/health` | Salud financiera sintética |
| GET | `/customers/{customer_id}/forecast` | Pronóstico sintético, no modelo validado |
| GET | `/customers/{customer_id}/recommendations` | Recomendaciones de demostración |
| GET | `/customers/{customer_id}/events` | Eventos sintéticos |
| POST | `/simulations` | Escenarios hipotéticos, sin movimientos |
| GET | `/fx` | Tipo de cambio fallback, marcado como desactualizado |
| GET | `/customers/{customer_id}/goals` | Metas sintéticas |
| POST | `/customers/{customer_id}/goals` | Creación simulada, sin persistencia |
| GET | `/customers/{customer_id}/offers` | Ofertas genéricas ficticias |
| POST | `/customers/{customer_id}/expenses` | Registro simulado, sin persistencia |
| POST | `/chat` | Respuesta mock, sin agente real |
| POST | `/onboarding` | Validación de cinco respuestas; sin clasificación real |
| GET | `/health` | Estado del servidor |

Los esquemas completos, parámetros y ejemplos están en `/docs` al ejecutar el backend y en el contrato MG-01. El contrato prevalece como **propuesta**, no como especificación aprobada.

## Ejemplos de solicitud

**Crear meta** (mock, HTTP 201 esperado):

```json
{
  "name": "Comprar una laptop",
  "target_amount": 5000,
  "current_amount": 1500,
  "currency": "PEN",
  "target_date": "2027-06-30"
}
```

Ruta: `POST /api/v1/customers/demo-001/goals`. El progreso inicial esperado es 30 %. Se rechazan montos negativos, objetivos no positivos y ahorros iniciales mayores al objetivo.

**Onboarding** (mock):

```json
{
  "customer_id": "demo-001",
  "answers": {
    "monthly_income": 2500,
    "monthly_expenses": 1500,
    "current_savings": 3000,
    "monthly_debt_payment": 300,
    "income_stability": "stable"
  }
}
```

Ruta: `POST /api/v1/onboarding`. Mientras no se conecte el modelo de Diego, `profile` y `confidence` pueden ser `null` y `model` indica `pending-integration`. Los valores admitidos de `income_stability` son provisionales.

## Respuestas y límites

- `422`: errores de validación Pydantic.
- `404`: cliente no disponible en los escenarios mock.
- `201`: creación simulada de metas y gastos.
- Los valores derivados de modelos, probabilidades, cuadrantes y proyecciones **no son resultados verificados**.
- Las series con `sample_only: true` son ilustrativas y pueden no contener los 30 días del horizonte solicitado.
- El formato unificado de errores y el control de acceso siguen pendientes de aprobación.

## Seguridad

No utilizar esta versión con información financiera real. No asumir que conocer `customer_id` permite acceder a un cliente. Autenticación, autorización, secretos, conexión a BD y despliegue seguro están fuera del alcance actual de MG-03.
