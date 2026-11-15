"""El chat de `demo-001` habla de la misma persona que las pantallas: las cifras salen de los JSON del motor del front
(persona_demo), no del cliente de la base al que apunta el alias. Cada texto pasa por el verificador igual que el del agente.
Lo que no está en esos JSON (gastos por rubro, metas, ofertas, calendario) no se responde con otra persona: se dice que no hay dato."""

import re
from datetime import date

from src.agente_analitico.verificador import aplanar, verificar
from src.api import persona_demo

# Preguntas sin cifras de la persona: el agente las contesta igual para cualquier cliente.
INTENCIONES_DEL_AGENTE = (
    "educacion",
    "fuera_de_tema",
    "fuera_de_alcance",
    "seguridad",
    "compra",
    "conversacion",
    "tipo_de_cambio",
)
INTENCIONES_DE_PRONOSTICO = ("pronostico", "riesgo_rojo", "general", "apoyo")
SIN_DATO = (
    "De eso todavía no tengo datos en esta cuenta de demostración. Sí puedo decirte si llegas a tu cobro, "
    "cómo está tu salud financiera, si puedes hacer un gasto y qué tips te convienen. Tú decides."
)


def _fecha(texto: str) -> str:
    from src.agente_analitico.grafo import MESES_DEL_ANO

    d = date.fromisoformat(texto)
    return f"{d.day} de {MESES_DEL_ANO[d.month - 1]}"


def _mismo_dia(fecha: str, anterior: str) -> str:
    return "ese mismo día" if fecha == anterior else f"el {_fecha(fecha)}"


def _soles(valor: float) -> str:
    signo = "−" if valor < 0 else ""
    return f"{signo}S/ {abs(valor):,.0f}"


def _tramo_hasta_el_cobro(dias: list[dict]) -> list[dict]:
    """Los días anteriores al primer día en que el saldo sube: el pronóstico solo sube cuando entra un ingreso."""
    for i in range(1, len(dias)):
        if dias[i]["predicted_balance"] > dias[i - 1]["predicted_balance"]:
            return dias[:i]
    return dias


def _hasta_el_cobro() -> tuple[list[dict], str | None]:
    dias = persona_demo.respuesta("forecast.json")["forecast"]
    tramo = _tramo_hasta_el_cobro(dias)
    return tramo, dias[len(tramo)]["date"] if len(tramo) < len(dias) else None


def get_forecast() -> dict:
    tramo, cobro = _hasta_el_cobro()
    peor_esperado = min(tramo, key=lambda d: d["predicted_balance"])
    peor_caso = min(tramo, key=lambda d: d["lower_bound"])
    return {
        "primer_dia": tramo[0],
        "cobro": cobro,
        "peor_esperado": peor_esperado,
        "peor_caso": peor_caso,
        "primer_rojo": persona_demo.respuesta("forecast.json")["first_risk_date"],
    }


def simulate(gasto: float) -> dict:
    """Restar el gasto al pronóstico es una resta, no una predicción: el motor del front hace lo mismo al simular un cambio."""
    f = get_forecast()
    esperado, caso = (
        f["peor_esperado"]["predicted_balance"] - gasto,
        f["peor_caso"]["lower_bound"] - gasto,
    )
    return {
        "gasto": gasto,
        "cobro": f["cobro"],
        "fecha_esperado": f["peor_esperado"]["date"],
        "saldo_esperado_con_gasto": esperado,
        "fecha_peor_caso": f["peor_caso"]["date"],
        "saldo_peor_caso_con_gasto": caso,
    }


def _cierre(f: dict) -> str:
    return f" Tu cobro llega el {_fecha(f['cobro'])}." if f["cobro"] else ""


def _texto_pronostico() -> tuple[str, dict]:
    f = get_forecast()
    esperado, caso = f["peor_esperado"], f["peor_caso"]
    if caso["lower_bound"] >= 0:
        veredicto = "Sí llegas a tu cobro, incluso en el peor caso."
    elif esperado["predicted_balance"] >= 0:
        veredicto = "Llegas a tu cobro, pero justo: en el peor caso te quedas en rojo antes."
    else:
        veredicto = "Con lo esperado no llegas a tu cobro sin quedar en rojo."
    texto = (
        f"{veredicto} Tu saldo esperado más bajo antes de cobrar es {_soles(esperado['predicted_balance'])} el {_fecha(esperado['date'])}, "
        f"y en el peor caso baja a {_soles(caso['lower_bound'])} {_mismo_dia(caso['date'], esperado['date'])}.{_cierre(f)} Tú decides."
    )
    return texto, f


def _texto_salud() -> tuple[str, dict]:
    h = persona_demo.respuesta("health.json")
    texto = (
        f"Tu salud financiera es {h['score']} de 100 («{h['status']}»). Tu colchón cubre unos {h['emergency_fund_months']} meses de gasto, "
        "así que cualquier imprevisto te aprieta. Tú decides."
    )
    return texto, h


def _texto_simulacion(gasto: float) -> tuple[str, dict]:
    s = simulate(gasto)
    if s["saldo_peor_caso_con_gasto"] >= 0:
        veredicto = f"Sí puedes gastar {_soles(gasto)}: incluso en el peor caso llegas a tu cobro sin quedar en rojo."
    elif s["saldo_esperado_con_gasto"] >= 0:
        veredicto = f"Con {_soles(gasto)} llegas a tu cobro en lo esperado, pero en el peor caso quedarías en rojo."
    else:
        veredicto = f"Gastar {_soles(gasto)} te deja en rojo antes de cobrar."
    texto = (
        f"{veredicto} Tu saldo esperado más bajo pasaría a {_soles(s['saldo_esperado_con_gasto'])} el {_fecha(s['fecha_esperado'])} "
        f"y el peor caso a {_soles(s['saldo_peor_caso_con_gasto'])} {_mismo_dia(s['fecha_peor_caso'], s['fecha_esperado'])}. Tú decides."
    )
    return texto, s


def get_recos() -> list[dict]:
    return persona_demo.respuesta("recommendations.json")["recommendations"]


def _texto_recomendaciones() -> tuple[str, list[dict]]:
    recos = get_recos()
    lineas = [f"{r['action']} (ahorras unos {_soles(r['estimated_impact'])})." for r in recos]
    return "Estos cambios te ayudan a llegar mejor a tu cobro: " + " ".join(
        lineas
    ) + " Tú decides.", recos


def _respuesta(
    texto: str, datos, herramientas: list[str], intencion: str, extra: set | None = None
) -> dict:
    v = verificar(texto, aplanar(datos) | (extra or set()))
    return {
        "answer": texto,
        "provider": "plantilla",
        "verified": v["ok"],
        "sources": [],
        "tools_used": herramientas,
        "intent": intencion,
        "goal_proposal": None,
        "options": [],
    }


def responder(mensaje: str) -> dict | None:
    """None si la pregunta no depende de las cifras de la persona y puede contestarla el agente."""
    from src.agente_analitico.grafo import detectar_intencion, monto_de

    intencion = detectar_intencion(mensaje)
    if intencion in INTENCIONES_DEL_AGENTE:
        return None
    if intencion == "general" and re.search(r"\bsalud\b", mensaje, flags=re.IGNORECASE):
        intencion = "salud_nivel"
    if intencion == "simular":
        texto, datos = _texto_simulacion(monto_de(mensaje))
        return _respuesta(texto, datos, ["simulate"], intencion)
    if intencion in INTENCIONES_DE_PRONOSTICO:
        texto, datos = _texto_pronostico()
        return _respuesta(texto, datos, ["get_forecast"], intencion)
    if intencion == "salud_nivel":
        texto, datos = _texto_salud()
        return _respuesta(texto, datos, ["get_health"], intencion)
    if intencion == "recomendaciones":
        texto, datos = _texto_recomendaciones()
        return _respuesta(texto, datos, ["get_recos"], intencion)
    return {**_respuesta(SIN_DATO, {}, [], intencion), "verified": True}
