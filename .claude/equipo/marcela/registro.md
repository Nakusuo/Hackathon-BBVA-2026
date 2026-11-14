# Registro de Marcela (Nakusuo) · Frontend

Rol: Frontend (código MC). Agente de apoyo: `frontend-ux`. Revisa mis PR: Dixon. Yo reviso los PR de Dixon.
Todo lo que subo lleva la firma «Nakusuo/Marcela».

## Lo que hice

| Fecha | Tarea | Rama | Qué quedó |
|---|---|---|---|
| 2026-11-14 | MC-01 Esqueleto de la UI | `feature/front-esqueleto` | App React + Recharts en `app/`. Pantallas Cómo estás, Qué viene (gráfico con banda y día de riesgo) y Qué hacer (tarjetas con «¿Por qué?»), aviso anticipado arriba. Datos sintéticos en `app/src/mocks/`. Probado en claro y oscuro, 1366×768 y celular (390 px). Sin push todavía |
| 2026-11-14 | MC-01 Rediseño con referencias + Playwright | `feature/front-esqueleto` | Barra lateral oscura con píldora activa (abajo y flotante en celular), tarjeta principal «Puedes gastar S/ 34 al día», aviso de Lucas, anillo de salud por componentes, filas con iniciales, selector «Hasta mi ingreso / 30 días», lista de pagos que vienen, montos destacados en Qué hacer. 21 pruebas de Playwright en verde (claro, oscuro, celular) |

## Lo que acordamos

| Fecha | Acuerdo | Por qué |
|---|---|---|
| 2026-11-14 | UI con React + Recharts (Vite) | Se ve como app real; el simulador y la banda que se mueve quedan fluidos; claro/oscuro y celular más fáciles |
| 2026-11-14 | Se hacen solo las pantallas necesarias, empezando por las principales (Cómo estás, Qué viene, Qué hacer) | Ver tipografía, diseño y colores antes de seguir |
| 2026-11-14 | Paleta celeste propia (acento `#0a6e9c` en claro, `#6cc4e8` en oscuro), sin logos ni códigos de color de BBVA | Las bases penalizan colores bancarios «como si fuera producto oficial»; celeste da confianza sin copiar |
| 2026-11-14 | Tipografía Plus Jakarta Sans, instalada como paquete (funciona sin internet). Reemplaza a Atkinson Hyperlegible | Más cercana a las referencias de apps financieras; cifras alineadas; regla offline |
| 2026-11-14 | Estilo tomado de referencias de apps financieras: tarjetas redondeadas, píldoras, navegación oscura, anillo de puntaje. Fuera: degradados, fotos de personas, logos de marcas, emojis | Se ve como app real sin caer en AI slop |
| 2026-11-14 | Todo texto ≥ 16 px, verificado por una prueba de Playwright | Regla de accesibilidad de negocio.md |
| 2026-11-14 | Playwright para probar la UI; puede usar un navegador ya instalado con `PW_CHROMIUM` | Pruebas de sistema ISTQB y capturas para la demo |
| 2026-11-14 | Rojo solo para riesgo y siempre con texto («Aviso», «podrías quedar en rojo») | No depender solo del color |

## Lo que falta

- [ ] Firecrawl: conectar en claude.ai (Settings → Connectors) para investigación web
- [ ] Pasar la rama por `juez-tecnico` y `juez-producto`
- [ ] Push de `feature/front-esqueleto` y PR a `develop` (revisa Dixon + `juez-tecnico`, y `juez-producto` porque se ve en la demo)
- [ ] MG-01: acordar con Miguel y Jeffrey el contrato de la API; cambiar `app/src/mocks/` por los JSON de `data/sample/mocks/`
- [ ] Juntar `npm run dev` con `make run` cuando Michael tenga el Makefile (MI-01)
- [ ] MC-02 completar Cómo estás y Qué viene con los datos del contrato
- [ ] MC-03 Avisos (bandeja) · MC-05 Simulador · MC-06 Chat · MC-11 Metas · MC-07 Evidencia
- [ ] Pantalla de consentimiento (datos sintéticos, qué se usa, se puede revocar)
- [ ] Botón «explícamelo fácil» (regla de negocio de la UI)
- [ ] Selector de persona (independiente / formal con quincena) para la demo
