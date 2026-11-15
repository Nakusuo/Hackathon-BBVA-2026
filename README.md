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
- **El agente del chat** (`backend/src/agente_analitico/`, LangGraph con supervisor, 12 agentes especializados y juez de cifras) responde en `/chat`. La app lo usa con `VITE_CHAT_AGENTE=si`; sin esa variable, el chat responde con plantillas.
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

## Uso de IA

**Borrador: falta la confirmación del equipo. Las marcas [pendiente] se resuelven antes de entregar.**

**Herramientas.** Claude Code, con los modelos `claude-opus-5-5`, `claude-fable-5-2`, `claude-sonnet-5-5` y `claude-haiku-5-5` [medido: inventario de 20 sesiones de esta máquina, 75 pedidos humanos]. Los subagentes de `.claude/agents/` (investigador, codificador, uno por área, tester y tres jueces) se usaron para investigar, programar, probar y revisar. Las sesiones de los demás integrantes no están contadas [pendiente].

**Cronología** (14–15 nov, hora de Perú): planificación y primer chat por plantillas; integración del front con la API y 6 rondas de jueces sobre el chat; agente único; escritorio web y registro de movimientos.

**Qué hizo la IA y qué el equipo.** La IA escribió la mayor parte del código, las pruebas y la documentación a pedido de cada persona. El equipo definió problema, arquitectura y alcance, y decidió qué se unía (`.claude/planes/estado.md`, «Decisiones»).

**Cómo se verificó.** Cada revisión del juez técnico corre pruebas, lint, build y Gitflow. Si la pantalla se ve en la demo, también pasa por el juez de producto y el de cumplimiento. Hay 69 veredictos en `.claude/planes/verificaciones.md`. Última medición de pytest: 1116 aprobadas y 1 omitida [medido].

**Errores de la IA y correcciones** (de `verificaciones.md`):
- El verificador de cifras aceptaba «S/ 290» con un saldo de -290. El juez técnico lo bloqueó y se corrigió.
- Con gasto seguro 0, el front decía «puedes gastar hasta S/ 0 al día sin quedar en rojo». Se corrigió en la ronda siguiente.
- Algunas recomendaciones del mock tenían cifras falsas. Se corrigieron antes de unir.
- Un commit llevaba una línea de coautoría de IA. El juez técnico pidió quitarla.
- Con el modelo de 1.500 millones de parámetros, el LLM inventó cifras en 2 de 5 preguntas. Por eso se usa el de 3.000 millones (`PROMPTS.md`).

**IA dentro del producto.** El chat usa `qwen2.5:3b` con Ollama, en local. Solo redacta con los datos que le pasan las herramientas. Gemini está apagado por defecto. Hoy el código envía al proveedor el texto que escribe la persona, y eso no debe pasar con un proveedor externo: queda pendiente y no se activa hasta resolverlo. Detalle en [PROMPTS.md](PROMPTS.md).

**Medido en el chat** [medido, `models/metricas_chat_ollama.json`, 46 preguntas]: cifras verificadas 96,7 %, adversas bloqueadas 100 %, 73,9 % por plantilla. Latencia p95 17,4 s frente al objetivo de 8 s [pendiente de resolver]. Las plantillas dan 100 % de cifras verificadas sin llamar al LLM.

**Código y fuentes reutilizados.** Dependencias de `backend/requirements*.txt` y `analitica/requirements-analitica.txt`, con licencias [pendiente]. Ningún fragmento copiado confirmado [pendiente]. El RAG cita normas públicas (SBS, ENFEN, guías del Estado). Los datos son sintéticos.

## Límites

- No mueve dinero, no ejecuta operaciones y no recomienda comprar dólares ni invertir. Es orientación, no asesoría: la persona decide.
- Banco Vértice es ficticio; Lucas no es un producto de BBVA.
- En la demo cualquiera puede elegir cualquier persona; el inicio de sesión real lo pondría el banco.
