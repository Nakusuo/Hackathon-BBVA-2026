# Interfaz de Lucas

React + Recharts, empaquetado con Vite. Funciona sin internet: la tipografía viene instalada como paquete.

```bash
cd app
npm install
npm run dev      # abre http://localhost:5173
npm run build    # versión final en app/dist
npm run lint
npm test         # pruebas de funciones: montos, fechas, eje, coherencia de cifras y respuestas del chat
```

Recorrido: `/ingresar` (Banco Vértice, banco ficticio con datos de prueba ya cargados) → `/banca` (inicio con la tarjeta de aviso de Lucas y Lucas al centro de la barra) → `/lucas/resumen`, `/lucas/gastos`, `/lucas/que-viene` y `/lucas/chat`. La primera vez que se entra a Lucas aparece una guía de 3 pasos; se vuelve a ver con el botón «?».

Las cifras que se recalculan con «Lo hago» (saldo, pronóstico, peor día, gasto diario, tips y apartado) salen de `src/motor/`: una persona sintética y un sustituto simple del pronóstico y del recomendador, para que ninguna pantalla contradiga a otra. La API de hoy describe a otra persona (`demo-001`), así que todavía no reemplaza esas cifras.

La API de FastAPI (`src/api/` en la raíz) se lee solo desde `src/api/lucas.js`: valida cada respuesta y, si la API no responde en 4 s, devuelve error o trae otro formato, usa los JSON de `data/sample/mocks/` y Lucas lo avisa. Para levantarla junto al front:

```bash
# desde la raíz del repo, con fastapi y uvicorn instalados
uvicorn src.api.main:app --host 127.0.0.1 --port 8000
# en app/: Vite pasa /api al puerto 8000 (la API no tiene CORS); otra dirección con LUCAS_API
npm run dev
```

## Pruebas de la interfaz (Playwright)

Prueban cada pantalla en laptop (1366×768) y celular: que abran sin errores, sin scroll horizontal y con todo el texto de 16 px o más; que el aviso y el gasto diario se vean sin bajar; y los flujos principales (ingreso → banca → Lucas, guía de primera vez, ocultar montos, confirmar lo aprendido, chat con cifras verificadas y sin asesoría). Dejan capturas en `app/capturas/`.

```bash
npx playwright install chromium   # solo la primera vez
npm run e2e
```

Si ya tienes un navegador basado en Chromium (Chrome, Brave), puedes usarlo sin descargar nada:

```bash
PW_CHROMIUM=/ruta/al/navegador npm run e2e
# si otra copia del repo ya usa el puerto 5174:
PW_PUERTO=5181 npm run e2e
```
