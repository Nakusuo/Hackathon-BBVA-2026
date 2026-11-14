"""Puente entre `POST /api/v1/chat` (contrato MG-01) y el grafo del agente.

Miguel expone el endpoint en FastAPI y llama a `responder`; aquí se decide qué significa
cada campo de la respuesta.
"""

import uuid

from agent.formato import soles
from agent.grafo import preguntar

# Nombre que ve el usuario para cada campo de las tools (contrato) y del resumen del LLM.
ETIQUETAS = {
    "predicted_balance": "Saldo previsto",
    "saldo_previsto_final": "Saldo previsto",
    "lower_bound": "Saldo mínimo probable",
    "saldo_minimo_probable": "Saldo mínimo probable",
    "upper_bound": "Saldo máximo probable",
    "saldo_maximo_probable": "Saldo máximo probable",
    "confidence_level": "Confianza del pronóstico",
    "confianza": "Confianza del pronóstico",
    "score": "Puntaje de salud",
    "puntaje_de_salud": "Puntaje de salud",
    "puntaje_maximo": "Puntaje máximo",
    "emergency_fund_months": "Meses que cubre tu colchón",
    "meses_que_cubre_tu_ahorro_de_emergencia": "Meses que cubre tu colchón",
    "estimated_impact": "Efecto estimado al mes",
    "impacto_mensual_soles": "Efecto estimado al mes",
    "amount": "Gasto que consultas",
    "monto_del_gasto_que_preguntas": "Gasto que consultas",
    "final_balance": "Saldo final",
    "saldo_final_sin_el_gasto": "Saldo final sin el gasto",
    "saldo_final_con_el_gasto": "Saldo final con el gasto",
    "difference": "Diferencia",
    "rate": "Tipo de cambio (S/ por US$)",
    "horizon_days": "Días del pronóstico",
}
_SIN_SOLES = {
    "score",
    "puntaje_de_salud",
    "puntaje_maximo",
    "emergency_fund_months",
    "meses_que_cubre_tu_ahorro_de_emergencia",
    "confidence_level",
    "confianza",
    "horizon_days",
}


def cifras_con_etiqueta(detalle: list[tuple[float, str]]) -> list[dict]:
    """[{label, value, text}] sin repetir, para que la UI muestre cada cifra con su ✓."""
    vistas, cifras = set(), []
    for valor, campo in detalle:
        # Solo campos con etiqueta conocida: la página de una fuente no es una cifra del cliente.
        if (valor, campo) in vistas or campo not in ETIQUETAS:
            continue
        vistas.add((valor, campo))
        if campo in ("confidence_level", "confianza"):
            texto = f"{valor * 100 if abs(valor) <= 1 else valor:g} %"
        elif campo in _SIN_SOLES:
            texto = f"{valor:g}"
        elif campo == "rate":
            texto = f"S/ {valor}"
        else:
            texto = soles(valor)
        cifras.append({"label": ETIQUETAS.get(campo, campo), "value": valor, "text": texto})
    return cifras


def fuentes_citadas(estado: dict) -> list[dict]:
    """Solo los fragmentos que la respuesta cita, con lo que la UI necesita para mostrarlos."""
    fragmentos = estado.get("datos", {}).get("buscar_fuentes", {}).get("fragmentos", [])
    por_id = {f["id"]: f for f in fragmentos}
    return [
        {
            "id": cita,
            "title": por_id[cita]["titulo"],
            "institution": por_id[cita]["institucion"],
            "page": por_id[cita]["pagina"],
            "url": por_id[cita]["enlace"],
            # «EE. UU.» se muestra como etiqueta: la guía no habla de normas peruanas (CP-SIS-47).
            "context": por_id[cita]["contexto"],
        }
        for cita in estado.get("citas", [])
        if cita in por_id
    ]


def responder(agente, pedido: dict) -> dict:
    """`pedido` trae `customer_id`, `message` y opcionalmente `conversation_id`."""
    estado = preguntar(agente, pedido["customer_id"], pedido["message"])
    return {
        "conversation_id": pedido.get("conversation_id") or f"conv-{uuid.uuid4().hex[:12]}",
        "answer": estado["respuesta"],
        # ollama, gemini o plantilla: el que escribió la respuesta final.
        "provider": estado["proveedor"],
        # Veredicto del juez sobre la respuesta final, sea del LLM o de la plantilla.
        "verified": estado["aprobado"],
        # Cifras que la UI marca con ✓ (MC-06), tal como se escribieron.
        "verified_figures": estado.get("cifras_verificadas", []),
        # Las mismas, con etiqueta y el valor real de la tool (con su signo): Marcela las
        # muestra como «Saldo mínimo probable: -S/ 310». Campo nuevo, no cambia los demás.
        "figures": cifras_con_etiqueta(estado.get("cifras_detalle", [])),
        # Fragmentos del RAG que la respuesta cita y el juez validó (JF-05).
        "sources": fuentes_citadas(estado),
        "tools_used": estado.get("tools_usadas", []),
        "intent": estado["intencion"],
    }
