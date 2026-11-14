# Registro de Marcela (Nakusuo) · Frontend

Rol: Frontend (código MC). Agente de apoyo: `frontend-ux`. Revisa mis PR: Dixon. Yo reviso los PR de Dixon.
Todo lo que subo lleva la firma «Nakusuo/Marcela».

## Lo que hice

| Fecha | Tarea | Rama | Qué quedó |
|---|---|---|---|
| 2026-11-14 | MC-01 Esqueleto de la UI | `feature/front-esqueleto` | App React + Recharts en `app/`. Pantallas Cómo estás, Qué viene (gráfico con banda y día de riesgo) y Qué hacer (tarjetas con «¿Por qué?»), aviso anticipado arriba. Datos sintéticos en `app/src/mocks/`. Probado en claro y oscuro, 1366×768 y celular (390 px). Sin push todavía |

## Lo que acordamos

| Fecha | Acuerdo | Por qué |
|---|---|---|
| 2026-11-14 | UI con React + Recharts (Vite) | Se ve como app real; el simulador y la banda que se mueve quedan fluidos; claro/oscuro y celular más fáciles |
| 2026-11-14 | Se hacen solo las pantallas necesarias, empezando por las principales (Cómo estás, Qué viene, Qué hacer) | Ver tipografía, diseño y colores antes de seguir |
| 2026-11-14 | Paleta celeste propia (acento `#0a6e9c` en claro, `#6cc4e8` en oscuro), sin logos ni códigos de color de BBVA | Las bases penalizan colores bancarios «como si fuera producto oficial»; celeste da confianza sin copiar |
| 2026-11-14 | Tipografía Atkinson Hyperlegible Next, instalada como paquete (funciona sin internet) | Hecha para leerse fácil; cifras alineadas; regla offline |
| 2026-11-14 | Rojo solo para riesgo y siempre con texto («Aviso», «podrías quedar en rojo») | No depender solo del color |

## Lo que falta

- [ ] Push de `feature/front-esqueleto` y PR a `develop` (revisa Dixon + `juez-tecnico`, y `juez-producto` porque se ve en la demo)
- [ ] MG-01: acordar con Miguel y Jeffrey el contrato de la API; cambiar `app/src/mocks/` por los JSON de `data/sample/mocks/`
- [ ] Juntar `npm run dev` con `make run` cuando Michael tenga el Makefile (MI-01)
- [ ] MC-02 completar Cómo estás y Qué viene con los datos del contrato
- [ ] MC-03 Avisos (bandeja) · MC-05 Simulador · MC-06 Chat · MC-11 Metas · MC-07 Evidencia
- [ ] Pantalla de consentimiento (datos sintéticos, qué se usa, se puede revocar)
- [ ] Botón «explícamelo fácil» (regla de negocio de la UI)
- [ ] Selector de persona (independiente / formal con quincena) para la demo
