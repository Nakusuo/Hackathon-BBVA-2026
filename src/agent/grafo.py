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
from agent.rag import Buscador, SinEmbeddings
from agent.tools import HerramientaNoDisponible, Herramientas

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
    citas: list[str]
    respuesta: str


def fragmentos_de(datos: dict) -> dict[str, str]:
    """{id: título y texto} de los fragmentos del RAG, para validar citas y cifras.

    Va el título porque la respuesta lo nombra y trae números («Res. SBS 3274-2017»).
    """
    fuentes = datos.get("buscar_fuentes", {}).get("fragmentos", [])
    return {f["id"]: f"{f['titulo']}. {f['texto']}" for f in fuentes}


def construir(
    herramientas: Herramientas,
    cadena: list[LLMProvider],
    espera_s: float = 1.0,
    solo_plantilla: set[str] | None = None,
    buscador: Buscador | None = None,
):
    """`solo_plantilla` cambia qué intenciones no pasan por el LLM (para probar CP-SIS-10).

    Sin `buscador` las preguntas de educación responden «no encontré una fuente».
    """
    sin_llm = plantillas.INTENCIONES_SOLO_PLANTILLA if solo_plantilla is None else solo_plantilla

    def buscar_fuentes(pregunta: str) -> dict | None:
        if buscador is None:
            return None
        modulos, temas = router.temas_rag(pregunta)
        try:
            fragmentos = buscador.buscar(pregunta, modulos)
        except SinEmbeddings as error:
            log.warning("RAG sin embeddings: %s", error)
            return None
        return {"tema": temas, "fragmentos": fragmentos} if fragmentos else None

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
        if e["intencion"] == "educacion":
            fuentes = buscar_fuentes(e["pregunta"])
            if fuentes is None:
                return {"intencion": "sin_fuente", "tools_usadas": nombres}
            return {"datos": {"buscar_fuentes": fuentes}, "tools_usadas": nombres}
        try:
            datos = {n: llamadas[n]() for n in nombres}
        except HerramientaNoDisponible as error:
            # Sin datos no hay cifras que verificar: se avisa sin inventar nada (CP-SIS-15).
            log.warning("tools no disponibles: %s", error)
            return {"intencion": "sin_datos", "tools_usadas": nombres}
        return {"datos": datos, "tools_usadas": nombres}

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
        educacion = e["intencion"] == "educacion"
        v = juzgar(
            e["borrador"],
            vistos,
            fragmentos=fragmentos_de(e["datos"]),
            exigir_cifra=not educacion,
            exigir_cita=educacion,
        )
        if not v.ok:
            log.warning("juez rechaza (%s): %s", e["proveedor"], v)
        return {
            "aprobado": v.ok,
            "cifras_verificadas": v.cifras_verificadas,
            "cifras_detalle": v.detalle,
            "citas": v.citas_validas,
        }

    def nodo_plantilla(e: Estado) -> Estado:
        datos = e.get("datos", {})
        texto = TemplateProvider().redactar(e["intencion"], datos)
        v = juzgar(texto, datos, fragmentos=fragmentos_de(datos), revisar_frases=False)
        return {
            "respuesta": texto,
            "proveedor": "plantilla",
            "aprobado": v.ok,
            "cifras_verificadas": v.cifras_verificadas,
            "cifras_detalle": v.detalle,
            "citas": v.citas_validas,
        }

    def nodo_respuesta(e: Estado) -> Estado:
        return {"respuesta": e["borrador"]}

    def tras_router(e: Estado) -> str:
        return "plantilla" if e["intencion"] in _BLOQUEADAS else "tools"

    def tras_tools(e: Estado) -> str:
        if e["intencion"] in sin_llm or e["intencion"] in _BLOQUEADAS:
            return "plantilla"
        return "redaccion"

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
