# Interfaz de Lucas

React + Recharts, empaquetado con Vite. Funciona sin internet: la tipografía viene instalada como paquete.

```bash
cd app
npm install
npm run dev      # abre http://localhost:5173
npm run build    # versión final en app/dist
npm run lint
```

Mientras no exista el contrato de la API (MG-01), las pantallas leen datos sintéticos de `src/mocks/`.

## Pruebas de la interfaz (Playwright)

Prueban las 3 pantallas en laptop clara (1366×768), laptop oscura y celular: que abran sin errores, sin scroll horizontal, con todo el texto de 16 px o más, y los flujos principales (aviso → Qué hacer, cambio de periodo, «¿Por qué?»). Dejan capturas en `app/capturas/`.

```bash
npx playwright install chromium   # solo la primera vez
npm run e2e
```

Si ya tienes un navegador basado en Chromium (Chrome, Brave), puedes usarlo sin descargar nada:

```bash
PW_CHROMIUM=/ruta/al/navegador npm run e2e
```
