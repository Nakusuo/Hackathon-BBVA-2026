# Registro de Marcela (Nakusuo) · Frontend

Rol: Frontend (código MC). Agente de apoyo: `frontend-ux`. Revisa mis PR: Dixon. Yo reviso los PR de Dixon.
Todo lo que subo lleva la firma «Nakusuo/Marcela».

## Lo que hice

| Fecha | Tarea | Rama | Qué quedó |
|---|---|---|---|
| 2026-11-14 | MC-01 Esqueleto de la UI | `feature/front-esqueleto` | App React + Recharts en `app/`. Pantallas Cómo estás, Qué viene (gráfico con banda y día de riesgo) y Qué hacer (tarjetas con «¿Por qué?»), aviso anticipado arriba. Datos sintéticos en `app/src/mocks/`. Probado en claro y oscuro, 1366×768 y celular (390 px). Sin push todavía |
| 2026-11-14 | MC-01 Rediseño con referencias + Playwright | `feature/front-esqueleto` | Barra lateral oscura con píldora activa (abajo y flotante en celular), tarjeta principal «Puedes gastar S/ 34 al día», aviso de Lucas, anillo de salud por componentes, filas con iniciales, selector «Hasta mi ingreso / 30 días», lista de pagos que vienen, montos destacados en Qué hacer. 21 pruebas de Playwright en verde (claro, oscuro, celular) |

| 2026-11-14 | Correcciones de los jueces | `feature/front-esqueleto` | Motor único de cifras (`app/src/mocks/motor.js`): gasto seguro S/ 26 al día, riesgo 28–29 con peor caso −S/ 60, cada recomendación con su efecto real y juntas dejan +S/ 12 sin días en rojo. Salud = promedio real (54). Cada pantalla cabe en 1366×768 (lo vigila una prueba). Paleta con ámbar. 14 pruebas de funciones (`npm test`) y 21 de Playwright en verde |
| 2026-11-14 | Segunda revisión de jueces | `feature/front-esqueleto` | juez-tecnico APRUEBA, juez-producto APRUEBA (~61/100, antes ~46), juez-cumplimiento CUMPLE. Se aplicaron también dos opcionales: % de deudas calculado de los pagos (45 %, salud 52) y resumen del gráfico para lectores de pantalla |
| 2026-11-14 | Push y PR #3 | `feature/front-esqueleto` | Rama subida y PR a `develop` abierto: https://github.com/MaickolO/Hackathon-BBVA-2026-Equipo-2/pull/3 (revisa Dixon) |
| 2026-11-14 | Investigación de UI bancaria | — | Informe `.claude/investigacion/ui-banca.md` (agente investigador): ocultar saldo es estándar en Perú, categorías comparadas con el promedio, entrada al asistente con tarjeta proactiva + acceso fijo, guía corta (estudio NN/g) |
| 2026-11-14 | Banca + Lucas v2 | `feature/front-banca-lucas` | Ingreso visual de Mi Banca, inicio con saldo ocultable, cuentas, accesos, tarjeta «Lucas te avisa» y Lucas al centro de la barra; espacio Lucas con Resumen (gasto diario, aviso, lo que aprendí con «¿Es correcto?», tips con efecto, apartado comprobado, salud), Gastos (7 categorías frente al promedio), Qué viene y Chat (respuestas con cifras verificadas y límites de asesoría); guía de 3 pasos. 19 pruebas de funciones y 28 de Playwright en verde |
| 2026-11-14 | Revisión y corrección de errores + estructura de referencias | `feature/front-banca-lucas` | Corregidos: aviso «solo Lucas» que se borraba antes de tiempo, foco que escapaba de la guía y no volvía al «?», selector partido en celular, «No» de lo aprendido que no hacía nada visible, lector de pantalla que no leía el aviso de la tarjeta de Lucas, leyenda del gráfico con color equivocado. Nueva estructura (referencias de apps financieras, en azules): cabecera azul profunda con saldo, tarjeta de crédito visual, accesos en bloque blanco, pagos programados deslizables, movimientos por día; Resumen con dos recuadros; Gastos y Qué viene con panel azul y hoja blanca. 19 pruebas de funciones y 36 de Playwright en verde |
| 2026-11-14 | Correcciones de los 3 jueces + mejoras de producto | `feature/front-banca-lucas` | Banco ficticio «Banco Vértice» con rótulo visible. Animaciones (de otra sesión) revisadas, con motion fijo y respetando «reducir movimiento». Guía: paso 2 ya no se aplasta y «?» funciona en todas las pestañas. Chat: no dice «Puedes» ante gastos imposibles, lee «S/ 1.500» y no confunde días, responde «¿Puedo ahorrar X?», usa los tips activos y dice «Calculado con tus datos». Botón «Lo hago» en cada tip: el aviso, el gráfico, la banca y el chat se recalculan en vivo (−S/ 60 → −S/ 29 → −S/ 7 → +S/ 12) y se recuerda. Persona coherente: cuenta de ahorros, 2 clientes con cobros que varían, tarjeta como pago total, apartado calculado (S/ 40 sin tips, S/ 150 con los 3). 28 pruebas de funciones y 44 de Playwright en verde |
| 2026-11-14 | Segunda ronda de jueces y actualización con develop | `feature/front-banca-lucas` | Rama rebasada sobre `develop` (contrato de API de Miguel y docs de Dixon) sin conflictos. juez-tecnico APRUEBA, juez-producto APRUEBA (~63/100), juez-cumplimiento CUMPLE CON RIESGOS (favicon en el límite de marca). 28 pruebas de funciones y 44 de Playwright en verde |
| 2026-11-14 | Traer novedades del repo | `feature/front-rediseno-movil` | `git fetch` del remoto. `develop` sin cambios nuevos (sigue en el PR #6, ya incluido en esta rama). Ramas nuevas de otros, aún sin unir a `develop`: `feature/ia-jeffrey-actividades` (Jeffrey: chat de consola, respuesta de `/chat` y `/fx` según el contrato MG-01, servicio BCRP), `feature/datos-diagramas-v2` (Dixon: `docs/arquitectura-datos.md`), `feature/backend-contrato` y `feature/backend-fastapi` (ya dentro de `develop`). No se unió nada a la rama del front. Nakusuo/Marcela |
| 2026-11-14 | Revisión de choques entre ramas | `feature/front-rediseno-movil` | Se simuló la unión de `feature/front-rediseno-movil`, `feature/ia-jeffrey-actividades` y `feature/datos-diagramas-v2` con `develop` y entre ellas: sin conflictos (no comparten archivos). Con las tres juntas en una copia aparte: 29/29 pruebas del front, build OK, 149/149 pruebas de Python y ruff sin errores. `feature/datos-diagramas-v2` va 25 commits detrás de `develop`, pero se une sin choques. Nakusuo/Marcela |
| 2026-11-14 | Push de la rama del front | `feature/front-rediseno-movil` | Rama subida a GitHub (sin PR todavía). Solo lo que estaba en commits; los cambios sin guardar de otra sesión en `app/` quedaron en la laptop. Nakusuo/Marcela |
| 2026-11-14 | Jueces técnicos de las ramas de los demás | — | Dixon `feature/datos-diagramas-v2`: CAMBIOS, no unir (el doc ya está idéntico en `develop` por un commit directo; el diagrama mermaid no compila, el ERD contradice ARCHITECTURE). Jeffrey PR #5: CAMBIOS (el juez de cifras ignoraba el signo). Miguel `feature/backend-fastapi`: CAMBIOS (signo de `expense` contra el mock, simulador sin tope, al forecast le faltan `first_risk_date`/`model`/`sample_only`, cifras escritas en el código, `rate` como texto). Los jueces de mi rama y de Diego se cortaron sin veredicto. Nakusuo/Marcela |
| 2026-11-14 | Arreglos en la rama de Jeffrey (con su PR #5) | `feature/ia-jeffrey-actividades` | Commits `ed58864` y `6c35ff4`, **solo locales, sin subir**: el juez rechaza «S/ 310 a favor» con saldo −310, redondeo solo a decena (≥100) o centena (≥1 000), prohibidas «préstamo», sugerir crédito y «sin riesgo», router manda «tipo de cambio» y «cambio del dólar» a fx, versiones fijas de `ollama` y `google-genai`, licencia del Banco Mundial corregida. 173/173 pytest y ruff limpio. Nakusuo/Marcela |
| 2026-11-14 | Ramas nuevas revisadas | — | Diego subió `feature/ml-segmentos-pronostico` (152 archivos, ~24 500 líneas: ML, agente propio en `src/agente_analitico`, RAG, BCRP, puntos). No choca con `develop`, front ni backend, **sí con Jeffrey** (`.gitignore` y `docs/rag/fuentes.csv`) y duplica su trabajo: mismos PDFs con otros nombres, dos catálogos de fuentes, dos agentes con juez, dos `src/bcrp/`. Las historias de usuario que mencionó un compañero ya estaban en `develop` (commit de Michael a las 13:42). Nakusuo/Marcela |

## Lo que acordamos

| Fecha | Acuerdo | Por qué |
|---|---|---|
| 2026-11-14 | UI con React + Recharts (Vite) | Se ve como app real; el simulador y la banda que se mueve quedan fluidos; claro/oscuro y celular más fáciles |
| 2026-11-14 | Se hacen solo las pantallas necesarias, empezando por las principales (Cómo estás, Qué viene, Qué hacer) | Ver tipografía, diseño y colores antes de seguir |
| 2026-11-14 | Paleta final: tinta `#1b2433`, datos en petróleo `#1f6b8a`, celeste `#dcebf7` para la tarjeta principal y **ámbar `#e8a33d` como color propio de Lucas** (texto ámbar `#9a5b0c`). Reemplaza a `#0a6e9c` y luego a `#0e1e3d`/`#1d63b8` | El juez-cumplimiento vio `#0e1e3d` ≈ `#072146` y `#1d63b8` ≈ `#1973B8` de BBVA; el ámbar hace que se lea como marca propia |
| 2026-11-14 | Tipografías: Source Serif 4 para títulos y cifras grandes, Plus Jakarta Sans para el texto, ambas instaladas como paquete. Se quitó Atkinson | Estilo editorial y empático como la banca moderna, sin usar fuentes de BBVA; funciona sin internet |
| 2026-11-14 | Estilo tomado de referencias de apps financieras: tarjetas redondeadas, píldoras, navegación oscura, anillo de puntaje. Fuera: degradados, fotos de personas, logos de marcas, emojis | Se ve como app real sin caer en AI slop |
| 2026-11-14 | Todo texto ≥ 16 px, verificado por una prueba de Playwright | Regla de accesibilidad de negocio.md |
| 2026-11-14 | Playwright para probar la UI; puede usar un navegador ya instalado con `PW_CHROMIUM` | Pruebas de sistema ISTQB y capturas para la demo |
| 2026-11-14 | Todas las cifras de las pantallas salen de un solo motor, nunca escritas a mano en textos | Los jueces encontraron contradicciones (S/ 34 al día frente a rojo; 80 por quincena = 240) |
| 2026-11-14 | Límite de marca (juez-cumplimiento): ningún azul a menos de ~20 puntos por canal de `#004481`, `#072146`, `#1464A5`, `#1973B8`, `#5BBEFF`, `#2DCCCD`; sin tipografías de BBVA; el ámbar es la firma de Lucas; en el pitch «podría integrarse» | Que el front se sienta bancario sin aparentar producto oficial |
| 2026-11-14 | Sin modo oscuro: solo blancos y azules. Paleta: blanco, azul petróleo `#1b6378` (ajuste de Venice Blue `#16587B`, que quedaba a ≤ 22 puntos del azul `#004481` de BBVA), azul claro `#84b3ce` solo para fondos, crema Merino `#f5eedd` como superficie propia de Lucas. Reemplaza el ámbar | Pedido de Marcela; límite de marca del juez-cumplimiento |
| 2026-11-14 | Nueva estructura: ingreso (formulario visual con datos ficticios) → «Mi Banca» genérica (banca de siempre) → botón de Lucas → espacio Lucas (lo que aprendió de ti, tips, gastos por categoría, qué viene) → chat que responde con lo aprendido y predicciones → guía la primera vez | Mostrar a Lucas integrado en una banca, como lo usaría un cliente |
| 2026-11-14 | «Mi Banca» es una banca genérica, no la app de BBVA | Las bases prohíben interfaces bancarias como si fueran oficiales; en el pitch: «se integra en la app de cualquier banco» |
| 2026-11-14 | Íconos: Phosphor Icons (`@phosphor-icons/react`) en vez de Lucide | Pedido de Marcela |
| 2026-11-14 | Lucas entra por la tarjeta de aviso en el inicio y por un botón destacado al centro de la barra inferior, no por burbuja flotante | Investigación: la burbuja tapa contenido y se ignora; la tarjeta muestra valor antes de abrir |
| 2026-11-14 | Guía de primera vez: 3 pasos en contexto, con «Saltar» y botón «?» para volver a verla | Estudio NN/g: los tutoriales largos no mejoran el uso |
| 2026-11-14 | Texto en gris tinta `#1f2a30` (antes `#14303f`, a ≤ 15 puntos del marino `#072146` de BBVA) y cabeceras en azul profundo `#134e5e` | Mantener el límite de marca del juez-cumplimiento |
| 2026-11-14 | Estructura tomada de referencias de apps financieras, siempre en azules: número grande sobre azul, hoja blanca con la lista, recuadros de presupuesto, botón central | Pedido de Marcela |
| 2026-11-14 | Banco ficticio: «Banco Vértice» (búsqueda web sin coincidencias; falta revisar registro SBS). «Mi Banca» descartado por parecerse a Mibanco | Que funcione para cualquier banco sin imitar a uno real |
| 2026-11-14 | Los tips se activan con «Lo hago» y todo se recalcula con el mismo motor; el chat dice «Calculado con tus datos» hasta que exista el verificador (JF-04) | Momento memorable de la demo y honestidad con las cifras |
| 2026-11-14 | Rojo solo para riesgo y siempre con texto («Aviso», «podrías quedar en rojo») | No depender solo del color |
| 2026-11-14 | Normas de diseño v2: modo oscuro con fondo carbón neutro (no azul marino) y un solo acento azul eléctrico con brillo, siempre a más de 20 puntos por canal de los azules de BBVA. Reemplaza «Sin modo oscuro: solo blancos y azules» | Las pantallas se veían planas; referencias de apps financieras oscuras |
| 2026-11-14 | Vidrio esmerilado y brillo azul solo en la tarjeta protagonista de cada pantalla (login, panel de Resumen); sin morado ni rosa | Que destaque una cosa por pantalla sin caer en AI slop (regla 8 de la nota de diseño) |
| 2026-11-14 | Celular primero: cada pantalla principal cabe en 1.5 pantallas de celular; el detalle va en pantallas u hojas aparte, sin sobrecargar | Pedido de Marcela: que el usuario no se abrume |
| 2026-11-14 | Gráficas según ui-ux-pro-max: etiquetas y porcentajes visibles, nunca solo color; dona solo hasta 6 partes; pronóstico con línea punteada y banda | Accesibilidad y lectura rápida en celular |
| 2026-11-14 | Tipografía: Manrope para títulos, cifras y texto, instalada como paquete con versión fija. Reemplaza a Source Serif 4 + Plus Jakarta Sans | La serifa se veía antigua sobre fondo oscuro; comparación de 4 opciones (Manrope, Sora + Inter, Space Grotesk + Inter, Plus Jakarta) y eligió Marcela |

## Para retomar en otra laptop (2026-11-14)

1. `git fetch --all --prune` y `git switch feature/front-rediseno-movil` → `git pull`.
2. Los arreglos de Jeffrey **solo existen en la laptop anterior** hasta que se suban (`git push origin feature/ia-jeffrey-actividades` desde allí). Si no se subieron, rehacerlos según la fila «Arreglos en la rama de Jeffrey».
3. Volver a pasar `juez-tecnico` por `feature/front-rediseno-movil` y por `feature/ml-segmentos-pronostico` (se cortaron).
4. Juntar a `develop` con PR + squash (`gh pr merge <n> --squash --delete-branch`) solo lo aprobado: mi rama y el PR #5 de Jeffrey con los arreglos.
5. No juntar todavía: Dixon (no aporta nada; corregir el doc en rama nueva), Miguel (5 bloqueantes), Diego (decidir con Jeffrey qué agente, qué catálogo RAG y qué `src/bcrp` se quedan).
6. Decidir con Miguel y Diego qué significa `expense` en el simulador (gasto nuevo o recorte).

## Lo que falta

- [x] Segunda ronda de jueces sobre `feature/front-banca-lucas`: APRUEBA, APRUEBA (~63) y CUMPLE CON RIESGOS. Nakusuo/Marcela
- [x] Push de `feature/front-banca-lucas` y PR #6 unido a `develop`; PR #3 cerrado porque su contenido entró con el #6. Nakusuo/Marcela
- [ ] PR de `feature/front-rediseno-movil` a `develop` tras su juez
- [ ] Subir los arreglos de Jeffrey y unir el PR #5
- [ ] Avisar a Dixon, Miguel y Diego de sus veredictos
- [ ] Guion de demo de 60 s en `demo/` (banca → aviso → «Lo hago» → el rojo desaparece → apartar S/ 150)
- [ ] Revisar «Banco Vértice» en el registro de la SBS antes del pitch
- [ ] Conectar el chat al agente real (JF-02/JF-03) y el pronóstico al modelo de Diego (DI-06)

- [ ] Firecrawl: conectar en claude.ai (Settings → Connectors) para investigación web
- [ ] Mejoras del juez-producto: apartado S/ 150 calculado por el motor (entrada a Sueldo Lucas); explicar «peor caso» con palabras simples y mostrar «evitas 2 días en rojo»; enlazar MusiKa (Suscripciones) y la salud a acciones
- [ ] Con la API: «veces este mes» como ritmo diario, explicaciones de salud desde el modelo (DI-07)
- [ ] Lugar para la marca ✓ de cifra verificada cuando exista la API
- [ ] Push de `feature/front-esqueleto` y PR a `develop` (revisa Dixon + `juez-tecnico`, y `juez-producto` porque se ve en la demo)
- [ ] MG-01: acordar con Miguel y Jeffrey el contrato de la API; cambiar `app/src/mocks/` por los JSON de `data/sample/mocks/`
- [ ] Juntar `npm run dev` con `make run` cuando Michael tenga el Makefile (MI-01)
- [ ] MC-02 completar Cómo estás y Qué viene con los datos del contrato
- [ ] MC-03 Avisos (bandeja) · MC-05 Simulador · MC-06 Chat · MC-11 Metas · MC-07 Evidencia
- [ ] Pantalla de consentimiento (datos sintéticos, qué se usa, se puede revocar)
- [ ] Botón «explícamelo fácil» (regla de negocio de la UI)
- [ ] Selector de persona (independiente / formal con quincena) para la demo
