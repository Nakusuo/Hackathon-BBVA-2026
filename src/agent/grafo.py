"""Grafo del agente: router → tools → redacción → juez → respuesta.

Si el juez rechaza, se redacta una vez más; si vuelve a fallar, responde la plantilla.
Las intenciones bloqueadas (operación, inyección) no pasan por tools ni por LLM.
"""

import logging
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from agent import plantillas, router
from agent.juez import juzgar
from agent.prompts import resumen_para_llm
from agent.providers import LLMProvider, TemplateProvider, redactar_con_respaldo
from agent.tools import Herramientas

log = logging.getLogger(__name__)

MAX_REDACCIONES = 2
_BLOQUEADAS = set(plantillas.RESPUESTAS_FIJAS)


class Estado(TypedDict, total=False):
    customer_id: str
    pregunta: str
    intencion: str
    monto: float | None
    datos: dict
    tools_usadas: list[str]
    borrador: str
    proveedor: str
    redacciones: int
    aprobado: bool
    cifras_verificadas: list[float]
    cifras_detalle: list[tuple[float, str]]
    respuesta: str


def construir(
    herramientas: Herramientas,
    cadena: list[LLMProvider],
    espera_s: float = 1.0,
    solo_plantilla: set[str] | None = None,
):
    """`solo_plantilla` cambia qué intenciones no pasan por el LLM (para probar CP-SIS-10)."""
    sin_llm = plantillas.INTENCIONES_SOLO_PLANTILLA if solo_plantilla is None else solo_plantilla

    def nodo_router(e: Estado) -> Estado:
        intencion, monto = router.clasificar(e["pregunta"])
        return {"intencion": intencion, "monto": monto, "redacciones": 0}

    def nodo_tools(e: Estado) -> Estado:
        cid = e["customer_id"]
        llamadas = {
            "get_health": lambda: herramientas.get_health(cid),
            "get_forecast": lambda: herramientas.get_forecast(cid),
            "get_recos": lambda: herramientas.get_recos(cid),
            "simulate": lambda: herramientas.simulate(cid, e["monto"]),
            "get_fx": herramientas.get_fx,
        }
        nombres = plantillas.TOOLS_POR_INTENCION[e["intencion"]]
        log.info("tools %s para intención %s", nombres, e["intencion"])
        return {"datos": {n: llamadas[n]() for n in nombres}, "tools_usadas": nombres}

    def nodo_redaccion(e: Estado) -> Estado:
        texto, proveedor = redactar_con_respaldo(cadena, e["intencion"], e["datos"], espera_s)
        return {"borrador": texto, "proveedor": proveedor, "redacciones": e["redacciones"] + 1}

    def nodo_juez(e: Estado) -> Estado:
        # El LLM solo vio el resumen: se le juzga contra eso, no contra la serie completa.
        vistos = (
            e["datos"]
            if e["proveedor"] == "plantilla"
            else resumen_para_llm(e["intencion"], e["datos"])
        )
        v = juzgar(e["borrador"], vistos, exigir_cifra=True)
        if not v.ok:
            log.warning("juez rechaza (%s): %s", e["proveedor"], v.cifras_no_verificadas)
        return {
            "aprobado": v.ok,
            "cifras_verificadas": v.cifras_verificadas,
            "cifras_detalle": v.detalle,
        }

    def nodo_plantilla(e: Estado) -> Estado:
        texto = TemplateProvider().redactar(e["intencion"], e.get("datos", {}))
        v = juzgar(texto, e.get("datos", {}), revisar_frases=False)
        return {
            "respuesta": texto,
            "proveedor": "plantilla",
            "aprobado": v.ok,
            "cifras_verificadas": v.cifras_verificadas,
            "cifras_detalle": v.detalle,
        }

    def nodo_respuesta(e: Estado) -> Estado:
        return {"respuesta": e["borrador"]}

    def tras_router(e: Estado) -> str:
        return "plantilla" if e["intencion"] in _BLOQUEADAS else "tools"

    def tras_tools(e: Estado) -> str:
        return "plantilla" if e["intencion"] in sin_llm else "redaccion"

    def tras_juez(e: Estado) -> str:
        if e["aprobado"]:
            return "respuesta"
        return "redaccion" if e["redacciones"] < MAX_REDACCIONES else "plantilla"

    g = StateGraph(Estado)
    g.add_node("router", nodo_router)
    g.add_node("tools", nodo_tools)
    g.add_node("redaccion", nodo_redaccion)
    g.add_node("juez", nodo_juez)
    g.add_node("plantilla", nodo_plantilla)
    g.add_node("respuesta", nodo_respuesta)
    g.add_edge(START, "router")
    g.add_conditional_edges("router", tras_router, ["tools", "plantilla"])
    g.add_conditional_edges("tools", tras_tools, ["redaccion", "plantilla"])
    g.add_edge("redaccion", "juez")
    g.add_conditional_edges("juez", tras_juez, ["respuesta", "redaccion", "plantilla"])
    g.add_edge("respuesta", END)
    g.add_edge("plantilla", END)
    return g.compile()


def preguntar(agente, customer_id: str, pregunta: str) -> Estado:
    return agente.invoke({"customer_id": customer_id, "pregunta": pregunta})
