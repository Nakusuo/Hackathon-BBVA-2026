# Diagramas UML de Lucas

| Diagrama | Qué muestra |
|---|---|
| [casos-uso.puml](casos-uso.puml) | Quién usa Lucas y para qué (CU-01 a CU-10) |
| [procesos.puml](procesos.puml) | Actividad: del ingreso a «Lo hago», con el recálculo de todas las pantallas por `vistaCon` y el respaldo si la API no responde |
| [secuencia-chat.puml](secuencia-chat.puml) | Chat con el agente conectado: corte de operaciones, router, tools, LLM, juez de cifras y respaldo a plantillas |
| [clases.puml](clases.puml) | Clases del dominio del front (Persona, Vista, Tip, Meta…) y del agente (Herramientas, proveedores LLM, Veredicto, esquemas de `/chat`) |

`grafo_agente_unico.md` y `grafo_multiagente.md` son los grafos LangGraph que genera `draw_mermaid()`.

## Regenerar los SVG

Sin internet, con Java 17 y un `plantuml.jar` (1.2024.7) fuera del repo:

```bash
java -jar plantuml.jar -charset UTF-8 -tsvg docs/diagramas/*.puml
```
