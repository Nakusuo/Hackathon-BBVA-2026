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
| 2026-11-14 | Rojo solo para riesgo y siempre con texto («Aviso», «podrías quedar en rojo») | No depender solo del color |

## Lo que falta

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
