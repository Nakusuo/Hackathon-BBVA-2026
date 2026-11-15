# Lucas, copiloto de plata

Hackathon BBVA 2026 · Equipo 2

Lucas responde una pregunta para quien trabaja en el sector privado en Perú:

> «¿Cuánto puedo gastar o ahorrar este mes sin quedarme en rojo antes de mi próximo ingreso, y qué cambio me conviene más?»

Es un compañero bancario, no un chatbot: ve venir el rojo antes del cobro, propone cambios con su efecto en S/ y deja que la persona decida. Lucas es marca propia; podría integrarse en la app de cualquier banco. Todos los datos son sintéticos.

## Qué hace el MVP

La demo muestra a Lucas dentro de **Banco Vértice**, una banca ficticia, con dos personas: una independiente que cobra por recibo por honorarios y una formal con sueldo por quincena.

| Pantalla | Qué ve la persona |
|---|---|
| Banca | Su banca de siempre, con la tarjeta «Lucas te avisa» o «Lucas lo ve venir» |
| Consentimiento | Qué datos usa Lucas antes de activarlo, y cómo retirarlo |
| Resumen | Cuánto gasta al día, el aviso de su peor día, tips con «Lo hago» y cuánto puede apartar al cobrar |
| Qué viene | Su saldo hasta el cobro con banda y peor caso, y un simulador de gastos o ingresos que vienen |
| Gastos | En qué se le va la plata, frente a su promedio, y sus suscripciones |
| Avisos | Hasta 3 avisos por semana, con «¿Por qué?» y «útil / no me sirve» |
| Metas | Cuánto apartar en cada cobro para llegar a una meta sin quedar en rojo |
| Salud | Puntaje de 0 a 100 y qué parte mejorar |
| Chat | «¿Me alcanza?», «¿llego a mi cobro?» y metas, con cifras calculadas con sus datos; nunca asesoría |
| Evidencia | Para el jurado: impacto en S/ por cliente y cada técnica frente a su baseline |

Al pulsar «Lo hago» en un tip, se recalculan juntos el aviso, el gráfico, la banca, la salud y el chat. El guion de 60 s está en [docs/demo/GUION.md](docs/demo/GUION.md).

## Qué está conectado y qué no

- **Las cifras de las pantallas** salen del motor del front (`frontend/src/motor/`), en el navegador. Funcionan sin internet y sin servidor.
- **La API** (`backend/src/api/`, FastAPI) responde las 12 rutas del contrato con datos fijos de otra persona. El front la lee y la valida, pero no toma de ella ninguna cifra visible. Si se cae, Lucas lo dice y sigue igual.
- **El agente del chat** (`backend/src/agent/`, LangGraph con juez de cifras) funciona por consola y con sus pruebas, pero la API todavía no lo llama. En la app, el chat responde con plantillas.
- **La analítica** (`backend/src/models/`, `analitica/eval/`) entrena y mide los modelos sobre 500 clientes sintéticos. Sus resultados llegan a la app solo por el panel Evidencia.
- **PostgreSQL**: el esquema está en `db/init.sql`, pero nada se conecta a la base en el MVP.

## Cómo se corre

Front (Node 20 o más):

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
npm test           # pruebas de funciones
npm run e2e        # Playwright (la primera vez: npx playwright install chromium)
```

API, en otra terminal y desde la raíz (Python 3.11 o más, con `fastapi`, `uvicorn` y `pydantic`):

```bash
python -m uvicorn --app-dir backend src.api.main:app --host 127.0.0.1 --port 8000
python -m pytest backend/tests/api
```

Vite pasa `/api` al puerto 8000. Sin la API, la app funciona igual y avisa «Sin conexión».

Agente y analítica: ver la sección 5 de [ARCHITECTURE.md](ARCHITECTURE.md). Sus dependencias van en `backend/requirements-ia.txt` y `analitica/requirements-analitica.txt`.

## Documentación

| Documento | Contenido |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Componentes, flujos, datos y cómo se corre |
| [docs/casos-uso.md](docs/casos-uso.md) | Casos de uso UML con su diagrama y la matriz de trazabilidad |
| [.claude/planes/historias.md](.claude/planes/historias.md) | Historias de usuario con criterios y pruebas |
| [docs/arquitectura-datos.md](docs/arquitectura-datos.md) | Datos sintéticos, qué guarda el navegador y clasificación |
| [docs/api.md](docs/api.md) y [README_BACKEND.md](docs/README_BACKEND.md) | Contrato y estado de la API |
| [PROMPTS.md](PROMPTS.md) | Modelos, prompts y medición del agente |
| [docs/EVALUACION_ANALITICA.md](docs/EVALUACION_ANALITICA.md) | Cifras de cada modelo frente a su baseline |
| [frontend/README.md](frontend/README.md) | Detalle del front y sus pruebas |

## Límites

- No mueve dinero, no ejecuta operaciones y no recomienda comprar dólares ni invertir. Es orientación, no asesoría: la persona decide.
- Banco Vértice es ficticio; Lucas no es un producto de BBVA.
- En la demo cualquiera puede elegir cualquier persona; el inicio de sesión real lo pondría el banco.
