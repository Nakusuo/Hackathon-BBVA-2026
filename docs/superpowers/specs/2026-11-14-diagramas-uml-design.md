# Diseño: diagramas UML de procesos, chat y clases

Fecha: 2026-11-14 · Rama: `feature/docs-mvp` · Autor: Michael (arquitectura)

## Intención

Tres diagramas UML para el **jurado en el pitch**, junto al de casos de uso ya existente. Tienen que mostrar en segundos las dos ideas que sostienen a Lucas: cada cifra sale de un solo motor, y el LLM explica pero no calcula (un juez verifica cada número).

## Objetivos, no objetivos y antiobjetivos

- **Objetivos:** diagrama de actividad del uso de Lucas, secuencia del chat con el agente conectado y diagrama de clases del dominio y del agente.
- **No objetivos:** documentar cada función, la analítica (`src/models/`) o el generador de datos.
- **Antiobjetivos:** diagramas que contradigan el código; cifras inventadas; un flujo donde Lucas mueva dinero o asesore; marca o colores de BBVA.

## Restricciones

- Igual que [casos-uso.puml](../../diagramas/casos-uso.puml): PlantUML con `!pragma layout smetana`, tema por defecto, SVG generado offline con `plantuml.jar` temporal y Java 17 (el jar no se sube).
- Legible en una diapositiva: unos 15 elementos por diagrama como máximo.
- Español, sin AI-slop ([calidad-codigo.md](../../../.claude/reglas/calidad-codigo.md)).

## Enfoques considerados

| Enfoque | A favor | En contra | Elegido |
|---|---|---|---|
| Solo lo que corre hoy, con el agente como «preparado» | Cero riesgo de exagerar | Esconde la pieza más fuerte del pitch | No: la conexión API → agente ya se está haciendo (decisión de Michael) |
| **Agente conectado como camino principal, plantillas como respaldo** | Muestra el juez de cifras y el respaldo sin red | El diagrama va un paso delante del código | **Sí** |
| Clases del código Python solamente | Muy técnico | Ruido para el jurado; deja fuera el front | No |
| **Clases: dominio del front + agente del chat** | Une las dos mitades de la historia | Dos paquetes en un diagrama | **Sí** (mi elección, Michael no la fijó) |

## Lo decidido

### Archivos

```
docs/diagramas/procesos.puml       + procesos.svg
docs/diagramas/secuencia-chat.puml + secuencia-chat.svg
docs/diagramas/clases.puml         + clases.svg
docs/diagramas/README.md           qué muestra cada diagrama y cómo regenerarlos
ARCHITECTURE.md                    enlaza los tres en §3 (Flujos) y §2
```

### 1. Procesos (actividad UML con carriles)

Carriles: Cliente · Banca Vértice / Lucas (pantallas) · Motor (`vistaCon`) · Navegador (`localStorage`).

Ingresar → ¿hay permiso? (no → consentimiento) → banca → abrir Lucas → `vistaCon` arma la vista → pantallas pintan → el cliente decide: «Lo hago», planificar un gasto, crear una meta o preguntar en el chat → se guarda en el navegador → vuelve a `vistaCon` (todas las pantallas cambian juntas). Rama paralela: lectura de la API con espera de 4 s; si falla, mocks y aviso «Sin conexión», sin cambiar cifras. Retirar el permiso borra lo de esa persona.

### 2. Secuencia del chat

Participantes: Cliente · Chat (`clienteChat.js`) · API `POST /api/v1/chat` · Agente (grafo LangGraph) · Router · Tools · LLM (Ollama / Gemini) · Juez.

1. El cliente escribe; el front corta operaciones, dólares e inversión (`esPedidoDeOperacion`) sin salir a la red.
2. Front → API (espera 12 s, 500 caracteres) → `agent.chat.responder`.
3. Router clasifica sin LLM; intenciones bloqueadas → plantilla.
4. Tools de solo lectura traen los datos (educación → RAG).
5. `loop` máx. 2 redacciones: LLM redacta solo con la salida de las tools → juez revisa cifras, signo y citas.
6. `alt`: aprobado → respuesta del LLM; rechazado dos veces → plantilla (también juzgada).
7. API devuelve `answer`, `verified`, `figures`, `sources`; el front pone ✓ solo si `verified`.
8. `alt` de respaldo: sin red, demora, formato ilegible o `verified=false` → plantillas del front con el motor y el aviso correspondiente.

### 3. Clases

- Paquete **Dominio (front)**: Persona, Vista, Tip (cambio), Planificado, Meta, Aviso, RespuestaChat. Cada clase con estereotipo del módulo que la implementa (`<<personas.js>>`, `<<cliente.js>>`, `<<metas.js>>`…). Relación clave: Vista se arma desde Persona + Tips elegidos + Planificados.
- Paquete **Agente (Python)**: Estado, `Herramientas` ← `HerramientasAPI` / `HerramientasMock`, `LLMProvider` ← `ProveedorChat` / `TemplateProvider`, `Veredicto`, `Permitidos`, `Buscador`, y `ChatRequest` / `ChatResponse` de la API.
- Unión entre paquetes: RespuestaChat se arma desde ChatResponse.

## Lo que queda al constructor

- Atributos exactos de cada clase, tomados del código (solo los que se entienden en una diapositiva).
- Disposición de cada diagrama mientras quepa en 16:9.

## Verificación

- Los tres `.puml` regeneran su `.svg` sin errores.
- Cada nombre de función, ruta, campo o clase del diagrama existe en el código (`grep`).
- `juez-tecnico` antes de unir a `develop`; veredicto en [verificaciones.md](../../../.claude/planes/verificaciones.md).
