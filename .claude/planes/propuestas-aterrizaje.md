# Propuestas de aterrizaje: lo prometido vs. lo que la app hace

Fecha: 2026-11-15. Base: rama `integracion/diego-presentacion-final`, commit `d32063d`.
Fuentes de lo prometido: lámina 7 y 8 de `docs/presentacion/final/plantilla.html`, `docs/demo/GUION.md`, `.claude/planes/estado.md`. Solo se anota lo que se ve o se dice en la demo.

## 1. Promesa → Estado hoy → Evidencia

| Promesa | Estado | Evidencia |
|---|---|---|
| Guion de 60 s: banca → «Lucas lo ve venir» → «Lo hago» ×3 → rojo desaparece → apartar al cobrar | Hecho (con el motor del front) | `docs/demo/GUION.md`; prueba `frontend/e2e/guion-demo.spec.js` |
| Avisos: lo urgente primero, una vez, máx. 3 por semana | Hecho (en el front) | `frontend/src/lucas/avisos.js:2,138-166` |
| Cada aviso dice por qué, supuesto y qué tan seguro | Hecho | `frontend/src/lucas/Avisos.jsx:42,141-146` |
| Si el servidor no responde, Lucas lo dice y sigue | Hecho | `frontend/src/api/lucas.js:25-33` (`conRespaldo`), `GUION.md` plan B |
| Pronóstico a 30 días con banda del modelo («Saldo con banda») | A medias: el front usa el motor local; la API devuelve una recta inventada | `backend/src/api/routers/forecast.py:25-40` (1500 − 10/día, «Todavía no existe un modelo predictivo conectado»). El contrato real ya está hecho y sin usar: `backend/src/agente_analitico/contrato.py:20` (`pronostico_contrato`) |
| Lámina 7: «Cada ingreso o gasto que se registra actualiza el saldo y el riesgo al instante, sin duplicados» | Falta en la app | `POST /expenses` no guarda nada (`backend/src/api/routers/expenses.py:30-33`). La función real existe y es idempotente (`datos_vivos.registrar`, `backend/src/agente_analitico/datos_vivos.py:90`) pero ninguna ruta ni pantalla la llama. No hay pantalla para registrar un movimiento (búsqueda en `frontend/src`) |
| Lámina 7: «Tipo de cambio con caché, último valor y serie grabada; un dato viejo no se presenta como actual» | A medias: el servicio existe, la ruta no lo usa | `backend/src/bcrp/servicio.py:81-150` (`ServicioBCRP`, `fx_contrato`); `backend/src/api/routers/fx.py:30-40` devuelve 3.75 fijo y `backend/tests/api/test_fx.py` exige ese 3.75. Ninguna pantalla lo muestra (`estado.md`, bloqueos) |
| Lámina 8: «Chat con botones», cifras con ✓ | A medias: por defecto responde con plantillas; el agente solo con `VITE_CHAT_AGENTE=si` | `frontend/src/lucas/Chat.jsx:14`; `GUION.md` plan B. `POST /chat` sí usa el agente real (`backend/src/api/routers/chat.py`) |
| Simulador «qué pasaría si» | A medias: el endpoint existe, ninguna pantalla lo muestra | `estado.md` (bloqueos); `frontend/src/api/lucas.js:49` (`simularCambios` sin uso en `.jsx`) |
| Lámina 8 «Abrir la demo» | A medias: depende de pasar `--demo-url` al compilar | `analitica/eval/construir_presentacion_final.py:162` |
| Pronóstico y salud de la API coinciden con lo que ve la persona | Falta: `demo-001` en la API es otra persona que el motor | `estado.md` (decisión «motor manda, API detrás»); `backend/src/api/routers/financial_health.py:13` (clientes escritos a mano) |
| «Sin duplicados» en datos vivos, sin guardar el texto del movimiento | Hecho en el módulo | `backend/tests/test_datos_vivos.py` |
| Video de respaldo y 3 ensayos cronometrados | Falta (no es código) | `GUION.md` «Pendiente»; `tareas.md` MC-10, TODOS-04 |

## 2. Propuestas priorizadas

### P1 [auto] `/forecast` devuelve el pronóstico real con respaldo al mock
- Qué: en `get_forecast`, llamar a `pronostico_contrato(repo, cid, dias)` con el cliente alias (`demo-001` → `C00016`); si faltan los modelos (devuelve `None`) o el repo no carga, responder el mock de hoy. Aceptar `days` (1 a 30) y devolver los campos extra (`first_risk_date`, `model`, `risk_probability`, `synthetic_data`, `sample_only`).
- Por qué: es la promesa «saldo con banda» y cierra el bloqueo 3 del PR #10 (faltaban `first_risk_date`, `model`, `sample_only`). El jurado técnico mira si la API usa el modelo o una recta.
- Archivos: `backend/src/api/routers/forecast.py`, `backend/src/api/schemas/forecast.py` (campos opcionales), `backend/tests/api/test_forecast.py`.
- Tamaño: M. Riesgo: bajo (el respaldo conserva el comportamiento actual y el front valida el contrato en `frontend/src/api/contrato.js`).
- Probar: `pytest backend/tests/api/test_forecast.py backend/tests/test_serie_diaria.py`; caso con modelos (skip si faltan) y caso sin modelos que devuelve el mock; `days=0` y `days=31` dan 422.
- Choca con: regla 1 (toda cifra sale de una tool) si el mock se presenta como real: el campo `sample_only` debe ser `true` cuando se usa el respaldo.

### P2 [auto] `POST /expenses` guarda el movimiento con `datos_vivos.registrar`
- Qué: la ruta llama a `registrar` (tipo `gasto`), acepta un `id` opcional del cliente para que repetir el envío no duplique, y devuelve el registro. Sin base de datos: usa el archivo de datos vivos que ya existe.
- Por qué: es la mitad de la promesa «registrar actualiza el saldo y el riesgo, sin duplicados». Hoy la ruta es un simulacro y la prueba solo comprueba el eco.
- Archivos: `backend/src/api/routers/expenses.py`, `backend/src/api/schemas/expenses.py`, `backend/tests/api/test_expenses.py`.
- Tamaño: S. Riesgo: bajo (escribe un archivo; la prueba debe apuntar a una carpeta temporal con `carpeta()`).
- Probar: dos envíos con el mismo id devuelven `duplicado=true` y una sola línea guardada; monto negativo o fecha a más de 1 día futura da 422; después de registrar, `GET /forecast` de P1 cambia el primer día de riesgo o el saldo (prueba de metamórfica).
- Choca con: regla 3 y privacidad (`reglas/negocio.md`): no guardar la descripción libre. `registrar` ya la descarta; la prueba debe comprobarlo.

### P3 [auto] `/fx` lee el servicio BCRP con la cadena caché → último valor → serie grabada
- Qué: la ruta llama a `ServicioBCRP().obtener("tipo_cambio")` y lo pasa por `fx_contrato`. Sin red usa la serie grabada y marca `is_fallback` e `is_stale` en `true`. Actualizar la prueba que exige 3.75.
- Por qué: la lámina 7 lo promete con esas palabras y hoy `/fx` devuelve un valor fijo etiquetado `synthetic_demo`.
- Archivos: `backend/src/api/routers/fx.py`, `backend/tests/api/test_fx.py`.
- Tamaño: S. Riesgo: bajo (las pruebas no deben llamar a la red: inyectar un servicio falso o forzar el respaldo con una variable).
- Probar: con servicio de red caído devuelve la serie grabada con `is_stale=true`; con valor fresco devuelve `is_stale=false`; `base`/`quote` distintos dan 422.
- Choca con: regla 5 (offline; el BCRP tiene serie grabada de respaldo) a favor; ningún choque.

### P4 [auto] El front muestra la fecha y el origen del tipo de cambio en Evidencia
- Qué: usar la lectura `tipoCambio` que ya se carga para mostrar una línea «Dólar: S/ X · fecha · fuente» y «dato anterior» cuando `is_stale`, en la sección de fuentes de Evidencia. Sin gráficos nuevos.
- Por qué: hoy se pide y se valida pero no se ve; la lámina dice que un dato viejo no se presenta como actual. Marcela prefiere pocos textos (una línea).
- Archivos: `frontend/src/evidencia/Evidencia.jsx`, `frontend/src/evidencia/secciones.js`, prueba en `frontend/pruebas/`.
- Tamaño: S. Riesgo: bajo.
- Probar: `npm test` en `frontend` con respuesta `is_stale=true` y `false`; `frontend/e2e/pantallas.spec.js` sigue verde (no mover nada de la demo de 60 s).
- Choca con: regla 4 (sin marca de BBVA): solo mostrar «BCRP» como fuente, sin logos. Depende de P3 para que el dato sea real.

### P5 Pantalla «Registrar un movimiento» (ingreso o gasto) en Lucas
- Qué: un formulario corto (monto, tipo, categoría, fecha) en el espacio Lucas que llama a `POST /expenses` y actualiza el saldo y el aviso. El motor del front debe tomar el neto de los movimientos nuevos.
- Por qué: es la parte visible de «Tus movimientos» (lámina 7); sin ella la promesa no se puede demostrar en vivo. Es lo más cercano al «compañero que se adelanta».
- Archivos: `frontend/src/lucas/` (pantalla nueva), `frontend/src/motor/motor.js`, `frontend/src/api/lucas.js`, `frontend/e2e/`.
- Tamaño: L. Riesgo: alto: toca el motor del que salen las cifras del guion; un error rompe la prueba `guion-demo.spec.js`.
- Probar: nueva prueba e2e que registre un gasto grande y compruebe que baja el saldo y aparece el aviso; el guion de 60 s debe seguir dando las mismas cifras.
- Choca con: regla 7 (MoSCoW: núcleo primero) y la decisión «motor manda, API detrás»; requiere decidir si el movimiento nuevo vive solo en el navegador o en la API. No es [auto] por esa decisión abierta.

### P6 Alinear `demo-001` de la API con la persona del motor del front
- Qué: que `/health`, `/events` y `/recommendations` de `demo-001` salgan del mismo cliente que el motor (independiente con recibo por honorarios), o que el front lea de la API las cifras que hoy calcula solo.
- Por qué: mientras no coincidan, mostrar la API contradice la pantalla; es el motivo por el que el front la ignora para las cifras.
- Archivos: `backend/src/api/routers/financial_health.py`, `events.py`, `recommendations.py`; `frontend/src/api/respaldo.js`; `data/sample/mocks/`.
- Tamaño: L. Riesgo: alto (decisión de producto: cuál es la fuente de verdad).
- Probar: prueba de contrato que compare las cifras del guion con la respuesta de la API.
- Choca con: regla 1 si se dejan cifras escritas a mano en el código de la API.

### P7 Activar el chat con agente en el ensayo y decidir el valor por defecto
- Qué: probar el recorrido de las preguntas fijas con `VITE_CHAT_AGENTE=si` en la laptop de la demo, medir la latencia y decidir si la demo de 75 s lo usa. Si no se usa, decir en el pitch «chat con plantillas verificadas».
- Por qué: la lámina 8 muestra «Chat con botones» y el jurado lo va a probar; hoy depende de una variable que nadie sabe si está puesta.
- Archivos: `frontend/.env.example`, `docs/demo/GUION.md`.
- Tamaño: S. Riesgo: medio (el LLM local tarda hasta 14 s; hay respaldo a plantillas).
- Probar: ensayo manual con cronómetro; `frontend/e2e/pantallas.spec.js` en ambos modos.
- Choca con: regla 5 (Gemini apagado por defecto, sin datos personales). No es [auto] porque necesita ejecutar el LLM en la máquina de la demo.

### P8 Conectar «Abrir la demo» y cerrar el material de respaldo
- Qué: compilar la presentación con `--demo-url` real, y dejar grabado el video de respaldo y los 3 ensayos cronometrados.
- Por qué: las bases piden el video y los ensayos; ya están como pendientes en `GUION.md` y `tareas.md`.
- Archivos: `analitica/eval/construir_presentacion_final.py` (solo se ejecuta), `docs/demo/`.
- Tamaño: M. Riesgo: bajo. Probar: abrir `docs/presentacion/final/index.html` y comprobar el enlace.
- Choca con: nada. No es código: lo hace una persona.

## 3. Rama `origin/feature/backend-fastapi` (Miguel): qué portar

Resultado: no unirla y no portar su código. Un solo commit (`0cba5ab`) que reescribe 12 routers con SQL directo.

- Su pronóstico es una recta (`balance_projection`, comentada «NO es un modelo predictivo entrenado») con una banda de ±10 % ilustrativa y `confidence_level` 0.5. Eso es peor que lo que ya hay en `develop`: el pronóstico con banda al 80 % medida (`pronostico_contrato`). Rompe la regla 2 (cada técnica se mide contra su baseline) y la lámina de la banda.
- Obliga a tener Postgres y `DB_USER`, `DB_PASSWORD`, `DB_NAME` para que arranque cualquier ruta; rompe las pruebas offline (regla 5). `develop` ya lee Postgres de forma opcional con `LUCAS_FUENTE_DATOS=postgres` (`backend/src/models/datos.py`).
- Lee `app.onboarding_financiero` y `app.movimientos_usuario`, que no tienen carga en `develop`.
- Se puede rescatar solo la idea: `customer_scope` (poner `app.customer_id` para la política de filas) si se activa RLS (`MI-03`, `MI-06`). Queda fuera de esta noche porque no hay conexión a la base en el flujo de la demo.

## 4. Lo que NO se propone

- Unir `origin/feature/backend-fastapi`: ver sección 3.
- «Lucas en 5 preguntas», Sueldo Lucas, grati/CTS en la app, ofertas, cuadrante y RAG en la app: `estado.md` los sacó del MVP; la lámina 7 solo menciona la CTS como norma, no como función.
- Conectar Postgres a la demo: la demo corre offline y la regla 5 prioriza eso.
- Mostrar el simulador `POST /simulations` en pantalla: el signo de `expense` y los topes siguen sin resolver (bloqueo 1 y 2 del PR #10) y no está en el guion.
- Cifras de retención o mora «de Lucas»: con datos sintéticos no se pueden probar (regla 13).
- Cambiar colores, tipografías o textos de marca: la identidad de Lucas ya está cerrada y sin marca de BBVA.
- Aprendizaje por respuestas, memoria y metas nuevas: son de ola 2 (regla 14) y el guion de 60 s no las usa.
