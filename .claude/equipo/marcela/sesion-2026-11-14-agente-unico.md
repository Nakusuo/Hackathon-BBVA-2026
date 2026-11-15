# Sesión del 14-nov: agente único, demo local y metas desde el chat

Para retomar en una sesión nueva. Rama: `feature/ia-agente-unico` (local, **sin subir**, 20 commits sobre `develop` en `78e7d0c`).

## 1. Qué corre en esta PC y cómo levantarlo

| Pieza | Cómo | Dónde |
|---|---|---|
| Ollama 0.40.16 | se instaló con winget y arranca con Windows; modelos `qwen2.5:3b` y `nomic-embed-text` | `127.0.0.1:11434` |
| Postgres 16 + pgvector | `docker compose up -d` (contenedor `lucas-db`, volumen `lucas-db`) | `127.0.0.1:5432` |
| Datos en la base | una vez: `python eval/cargar_a_postgres.py --crear --rag` con el `.env` cargado (unos 3 min; 500 clientes, 3,26 M movimientos, 3 761 fragmentos del RAG) | esquema `lucas` |
| Backend FastAPI | `.venv/Scripts/python -m uvicorn src.api.main:app --port 8000` (carga el agente al arrancar) | `127.0.0.1:8000` |
| Front | `cd app && npm run dev` con `VITE_CHAT_AGENTE=si` en `app/.env` | `127.0.0.1:5173` |

- Python: `.venv` con Python 3.13 (en la PC no hay 3.11) y `pip install -r requirements.txt` (nuevo: une analítica, IA y API).
- `.env` (no se sube): `LLM_PROVIDER=ollama`, `LUCAS_FUENTE_DATOS=postgres`, `DATABASE_URL`, `POSTGRES_*`. Plantilla en `.env.example`.
- Pasos completos en [planes/comandos.md](../../planes/comandos.md), sección 9.

## 2. Qué se hizo en la rama

**Un solo agente.** `/api/v1/chat` ya no es un texto fijo: llama a `src/agente_analitico` (reglas de Diego) vía `src/api/agente.py`. `src/agent` (Jeffrey) quedó sin uso, sin borrar. Decisión anotada en `planes/estado.md`.

**Datos desde la base.** `src/models/datos.py` lee el esquema `lucas` si `LUCAS_FUENTE_DATOS=postgres`; las pruebas siempre usan los Parquet (`tests/conftest.py`).

**Intenciones nuevas del agente** (`src/agente_analitico/grafo.py`), todas por plantilla con cifras de herramientas:

| Intención | Ejemplo | Responde |
|---|---|---|
| `simular` | «¿puedo gastar 450 soles en un concierto?» | saldo a 30 días con y sin el gasto (vuelve a puntuar el pronóstico) |
| `meta` | «carro a fin de año, 12mil, ¿cuánto ahorro?» | plan en 4 bloques: punto de partida, qué hacer, convenio del banco, números |
| `compra` | «quiero comprar un carro» | pide precio y fecha |
| `ahorro` | «resumen de mis estadísticas de ahorro» | lo apartado en 6 meses, colchón, redondeo |
| `gastos` | «¿cuánto gasté este mes?» | total del mes por rubro y frente al mismo tramo del mes anterior |
| `ofertas` | «¿hay alguna oferta?» | catálogo con idoneidad; dice si un producto no existe (crédito vehicular) |
| `saludo` | «hola» | qué puede hacer Lucas, sin LLM |

- Montos con «12mil», «12k», «8 lucas»; plazos «a fin de año», «en 6 meses», «para julio».
- Memoria por conversación (en el proceso de la API): «sí», «¿y en 6 meses?», «¿y si son 8000?» siguen la pregunta anterior.
- Convenios: `data/catalogo_campanas.json` lo leen el front y el agente (`src/models/campanas.py`); los de pasajes nacionales no se ofrecen para Brasil.
- El juez además rechaza: respuesta casi vacía, mezcla de otro idioma, la ficha interna «Tono:», y no deja al LLM redactar si la fuente del RAG es extranjera.
- Respuestas cortas: cada pregunta cuenta solo lo que se preguntó; la API quita «Hola, Nivel.» y «Tu decides.» (el chat ya lo dice al pie).
- Tildes en las plantillas, recomendaciones, ofertas y calendario.

**Front.**
- Chat: animación de escritura, una burbuja por bloque (`## Título` y línea en blanco), cifras en negrita (`app/src/lucas/textoChat.js`), espera de 30 s al modelo local.
- Plan → meta: la API devuelve `goal_proposal` y el chat muestra «Crear meta» o «Actualizar meta» si ya existe con otro plazo o monto.
- Metas: botón «Editar» (nombre, monto, ya ahorré, fecha).
- Avisos: «Aparta S/ X para «meta»» en los 7 días antes del cobro y el mismo día; en la demo, Avisos → «Probar la regla en la demo» → «Día de cobro».

**Pruebas al cerrar.** Python 965 (1 saltada), front 213, Playwright 155 (1 saltada), lint y build sin errores.

## 3. Lo último del repo y cómo unirlo a develop

`develop` no cambió desde `78e7d0c`. Lo último que se subió es de **Diego**: `feature/ml-segmentos-pronostico`, 5 commits a las 23:28 (`eac3b6a`…`c825474`): chat conversacional (intenciones `conversacion` y `apoyo`, botones de opciones, bienvenida), rechazo de respuestas vacías y evasivas, QA ampliada, informe final.

**Orden recomendado:**

1. **Diego → develop primero.** Probado en una copia: dos conflictos y luego **1021 pruebas pasan**.
   - `data/generado/_manifiesto.json` (modificado por Diego, borrado en develop): **dejarlo borrado**; `data/generado` no entra al repo (S5).
   - `docs/EVALUACION_ANALITICA.md`: tomar de Diego las filas C9b y C10b y de develop la fila S5 en OK.
2. **Después, esta rama sobre develop.** Choca en `src/agente_analitico/grafo.py`, `proveedores.py`, `eval/qa_agente.py`, `tests/test_agente_llm.py`, `tests/test_proveedores.py` y `tests/test_router_natural.py` (más los dos de arriba). Hicimos lo mismo por caminos distintos:
   - Saludo: Diego `conversacion` (más completo: relleno, despedidas, «gracias») frente a nuestro `saludo`. Propuesta: quedarse con `conversacion` de Diego y borrar `saludo`.
   - Respuesta vacía: los dos la rechazan (`_es_respuesta_vacia` de Diego frente a nuestro `PALABRAS_MINIMAS`); quedarse con una.
   - Lo que no entiende: Diego lo manda a la IA con botones de opciones (`opciones`); conservarlo y exponerlo en `/chat` como campo nuevo para que el front pinte los botones.
   - Conservar lo nuestro: `simular`, `meta`, `compra`, `ahorro`, `gastos`, `con_contexto`, `propuesta`, plantillas por bloques y tildes.
   - Después de unir: correr pytest, `npm test`, Playwright y, si se toca el agente, `eval/qa_agente.py` (lo pide la puerta de calidad de Diego).
3. Pasar la rama por `juez-tecnico` y `juez-producto`, anotar en `planes/verificaciones.md` y abrir el PR (pedir permiso antes del push).

También sin unir: `origin/feature/backend-fastapi` (Miguel). Las demás rutas de la API (salud, pronóstico, recomendaciones) siguen con datos fijos.

## 4. Pendientes y decisiones abiertas

1. **Pantallas y chat hablan de clientes distintos** (lo más visible en la demo). El chat usa el cliente de la base (`independiente`→`C00016`, `formal`→`C00168`, cambiable con `LUCAS_CLIENTES_DEMO`); las pantallas usan `app/src/motor/personas.js`. Ejemplo: viaje a Cusco, chat «S/ 108 al mes, 26 meses» frente a Metas «S/ 430 al mes». Opciones: **A** las pantallas leen de la base vía API (recomendada, trabajo grande) o **B** el chat se ajusta a la persona del front. Falta que Marcela elija.
2. **Metas en el navegador** (localStorage): pasarlas a Postgres (`lucas.meta_ahorro`) para que el agente las vea y el aviso llegue con la app cerrada. Hoy no hay notificación push.
3. **Búsqueda web en el agente: descartada** por las reglas 3 (sin marcas reales) y 5 (offline). Los convenios salen del catálogo del banco.
4. La memoria de la conversación vive en el proceso de la API: se pierde al reiniciarla.
5. Leer de Postgres no da idéntico a los Parquet: el pronóstico cambia más de 0,1 % en 76 de 500 clientes (hasta 27 % en uno) por redondear a centavos. Que lo revise Diego.
6. Repo: `make check` no existe y `ruff` da 439 avisos (sobre todo en `eval/`); el `numpy` fijado difiere entre los requirements (se dejó 2.5.4).

## 5. Cosas que confunden

- Tras cambiar el prompt o las plantillas, borrar `data/generado/cache_llm.json` y `data/generado/faq/faq.db`: guardan respuestas viejas del LLM y las reutilizan.
- Tras cambiar código del agente o de la API, reiniciar uvicorn (no tiene `--reload`).
- Playwright regenera `demo/capturas/*.png`: devolverlas con `git checkout -- demo/capturas` si no se quieren cambiar.
- En el navegador, la persona se guarda en `localStorage['lucas-persona']` como texto plano (`formal`), no JSON.
- El modelo local tarda cerca de un minuto en la primera respuesta tras encender la PC.
