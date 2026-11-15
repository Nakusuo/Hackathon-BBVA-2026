# Diagramas UML de procesos, chat y clases · Plan de ejecución

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tres diagramas UML (actividad, secuencia del chat y clases) en `docs/diagramas/`, con su `.svg`, enlazados desde `ARCHITECTURE.md`, para el jurado en el pitch.

**Architecture:** Un `.puml` por diagrama, exportado offline a `.svg` con `plantuml.jar` temporal en el scratchpad. La «prueba» de cada tarea es: el jar exporta sin errores y cada nombre de código del diagrama existe en el repo (`grep`).

**Tech Stack:** PlantUML 1.2024.7 (jar temporal), Java 17, layout `smetana`, Git Bash.

**Spec:** [docs/superpowers/specs/2026-11-14-diagramas-uml-design.md](../specs/2026-11-14-diagramas-uml-design.md)

## Global Constraints

- Cabecera de cada `.puml`: `' Regenerar: java -jar plantuml.jar -charset UTF-8 -tsvg docs/diagramas/<nombre>.puml` y `!pragma layout smetana`. Tema por defecto, sin colores de BBVA.
- Unos 15 elementos por diagrama como máximo; legible en 16:9.
- El chat se dibuja con el agente conectado como camino principal; plantillas del front como respaldo.
- Nombres de función, ruta, campo y clase tal como están en el código.
- Commits en español (`docs(arq): ...`), sin coautor ni atribución a IA (CLAUDE.md manda sobre el recordatorio). Sin push.

## Review Focus

1. **Nombre que no existe en el código** (p. ej., `get_recommendations` en vez de `get_recos`): el chequeo de `grep` de cada tarea.
2. **El juez se salta en algún camino**: en la secuencia, la plantilla del agente también pasa por `juzgar`; se revisa leyendo el `.puml` contra `src/agent/grafo.py:139-152`.
3. **Se ve la ✓ sin `verified=true`**: la secuencia muestra el `alt` de `verified` en el front (Task 2).
4. **Tildes rotas en el SVG**: exportar con `-charset UTF-8` y buscar «Opción» o «decisión» en el `.svg`.
5. **`ChatResponse` sin `figures` hoy**: el esquema Pydantic no lo tiene; el diagrama lo marca con una nota («lo agrega la conexión», `agent/chat.py:responder`).

---

### Task 0: jar temporal

- [ ] Descargar `plantuml-1.2024.7.jar` de las releases de GitHub de PlantUML al scratchpad. Verificar: `java -jar <jar> -version` imprime `1.2024.7`.

### Task 1: Procesos (actividad)

**Files:** Create `docs/diagramas/procesos.puml`, `docs/diagramas/procesos.svg`

Carriles `|Cliente|`, `|Pantallas de Lucas|`, `|Motor|`, `|Navegador|`, según §Lo decidido 1 del spec. Nombres: `vistaCon`, `localStorage`, `/consentimiento`, «Lo hago», «Sin conexión: te muestro tus últimos datos.», `fork` para la lectura de la API (4 s, `data/sample/mocks/`).

- [ ] Escribir el `.puml`.
- [ ] Exportar: sin errores en la salida y el `.svg` existe.
- [ ] `grep` de `vistaCon`, `ESPERA_MS = 4000`, `Sin conexión: te muestro tus últimos datos` en `app/src`.
- [ ] Commit `docs(arq): diagrama de actividad del uso de Lucas`.

### Task 2: Secuencia del chat

**Files:** Create `docs/diagramas/secuencia-chat.puml`, `docs/diagramas/secuencia-chat.svg`

Participantes y pasos del spec §2. Nombres: `esPedidoDeOperacion`, `preguntarALucas`, `LARGO_MAXIMO = 500`, espera 12 s, `POST /api/v1/chat`, `agent.chat.responder`, `router.clasificar`, `get_health / get_forecast / get_recos / simulate / get_fx`, `Buscador.buscar`, `redactar_con_respaldo`, `juzgar`, `MAX_REDACCIONES`, `TemplateProvider`, campos `answer, provider, verified, figures, sources`, `desdeAgente`, `AVISOS`.

- [ ] Escribir el `.puml` con `loop`, `alt` del juez y `alt` de respaldo del front.
- [ ] Exportar sin errores.
- [ ] `grep` de cada nombre anterior en `app/src` y `src/agent`, y de la espera de 12 s en el front.
- [ ] Commit `docs(arq): diagrama de secuencia del chat con el agente`.

### Task 3: Clases

**Files:** Create `docs/diagramas/clases.puml`, `docs/diagramas/clases.svg`

Paquetes del spec §3. Atributos tomados de: `personas.js` (Persona), `cliente.js:vistaCon` (Vista), `cambios` (Tip), `planificar.js:validarPlanificado` (Planificado), `metas.js` (Meta, `ESTADOS`), `avisos.js` (Aviso), `respuestas.js`/`clienteChat.js` (RespuestaChat), `grafo.py:Estado`, `tools.py`, `providers.py`, `juez.py`, `rag.py`, `schemas/chat.py`. Protocolos como `interface`.

- [ ] Escribir el `.puml`.
- [ ] Exportar sin errores.
- [ ] `grep` de cada clase y método del paquete Agente en `src/`.
- [ ] Commit `docs(arq): diagrama de clases del dominio y del agente`.

### Task 4: Enlaces y juez

**Files:** Create `docs/diagramas/README.md`; Modify `ARCHITECTURE.md` (§3 y §2.4)

- [ ] README: una línea por diagrama (qué muestra) y el comando para regenerar.
- [ ] `ARCHITECTURE.md`: imagen de procesos en §3.1, de secuencia en §3.3 y de clases en §2, con enlace al `.puml`.
- [ ] Revisar el Review Focus 4 (tildes en los SVG).
- [ ] `juez-tecnico` sobre la rama; anotar veredicto en `.claude/planes/verificaciones.md`.
- [ ] Commit `docs(arq): enlaces de los diagramas UML y veredicto`.
