# Grafo del agente (agente_unico)

Generado con `app.get_graph().draw_mermaid()` de LangGraph.

```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	cargar_contexto(cargar_contexto)
	router(router)
	redactar(redactar)
	juez(juez)
	plantilla(plantilla)
	finalizar(finalizar)
	herramientas(herramientas)
	__end__([<p>__end__</p>]):::last
	__start__ --> cargar_contexto;
	cargar_contexto --> router;
	herramientas --> redactar;
	juez -.-> finalizar;
	juez -.-> plantilla;
	juez -.-> redactar;
	plantilla --> finalizar;
	redactar --> juez;
	router --> herramientas;
	finalizar --> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc

```
