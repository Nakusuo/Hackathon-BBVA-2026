"""Respuestas por plantilla: siempre funcionan, sin red ni LLM, y son el baseline del agente.

Solo usan cifras que vienen en `datos` (campos del contrato `docs/api.md`), así el juez
siempre las aprueba.
"""

from agent.formato import fecha_larga, soles

CIERRE = "Es una simulación para orientarte, no una asesoría. Tú decides."

RESPUESTAS_FIJAS = {
    "operacion": (
        "No puedo hacer operaciones ni decirte si comprar o vender dólares. "
        "Sí puedo mostrarte cómo te queda el mes o simular un gasto."
    ),
    "inyeccion": (
        "Solo puedo ayudarte con tu plata: cómo estás, qué viene, qué te conviene "
        "y simular un gasto."
    ),
    "desconocido": (
        "No te entendí bien. Puedes preguntarme si llegas a fin de mes, cómo está tu salud "
        "financiera, qué te conviene hacer o qué pasa si gastas un monto."
    ),
}

_IMPACTO = {"expense_reduction": "dejas de gastar", "savings_allocation": "apartas"}
_PERIODO = {"monthly": "al mes", "weekly": "a la semana", "once": "una vez"}


def _salud(d: dict) -> str:
    h = d["get_health"]
    return (
        f"Tu salud financiera está en {h['score']} puntos ({h['status']}). "
        f"Tu colchón te alcanza para {h['emergency_fund_months']} meses de gastos."
    )


def _pronostico(d: dict) -> str:
    f = d["get_forecast"]
    ultimo = f["forecast"][-1]
    texto = (
        f"Hacia el {fecha_larga(ultimo['date'])} tu saldo estaría entre "
        f"{soles(ultimo['lower_bound'])} y {soles(ultimo['upper_bound'])}, "
        f"con {f['confidence_level']:.0%} de confianza."
    )
    if f.get("first_risk_date"):
        texto += f" El {fecha_larga(f['first_risk_date'])} podrías quedar en rojo."
    return texto


def _recos(d: dict) -> str:
    lineas = []
    for r in d["get_recos"]["recommendations"]:
        verbo = _IMPACTO.get(r.get("impact_type"), "mejoras")
        periodo = _PERIODO.get(r.get("impact_period"), "")
        lineas.append(
            f"- {r['action']}: {verbo} unos {soles(r['estimated_impact'])} {periodo} "
            f"(confianza {r['confidence']})."
        )
    return "Lo que más te conviene ahora:\n" + "\n".join(lineas)


def _simular(d: dict) -> str:
    s = d["simulate"]
    gasto = soles(s["request"]["changes"][0]["amount"])
    final = s["simulated"]["final_balance"]
    if final < 0:
        return f"Si gastas {gasto}, terminarías el periodo en rojo: {soles(final)}."
    return f"Si gastas {gasto}, terminarías el periodo con {soles(final)}."


def _segmento(d: dict) -> str:
    h = d["get_health"]
    return (
        f"Por ahora tu perfil figura como «{h['quadrant']}» y tu situación como "
        f"«{h['status']}». El nombre definitivo del perfil lo da el modelo de segmentos."
    )


def _fx(d: dict) -> str:
    fx = d["get_fx"]
    texto = (
        f"El tipo de cambio de referencia al {fecha_larga(fx['date'])} es "
        f"S/ {fx['rate']} por dólar."
    )
    if fx.get("is_fallback") or fx.get("is_stale"):
        texto += " Es un dato guardado, puede no ser el de hoy."
    return texto + " Es solo referencia, no una recomendación para comprar o vender."


_POR_INTENCION = {
    "salud": _salud,
    "pronostico": _pronostico,
    "recos": _recos,
    "simular": _simular,
    "segmento": _segmento,
    "fx": _fx,
}

# Qué tool alimenta cada intención; el grafo las llama en este orden.
TOOLS_POR_INTENCION = {
    "salud": ["get_health"],
    "pronostico": ["get_forecast"],
    "recos": ["get_recos"],
    "simular": ["simulate"],
    "segmento": ["get_health"],
    "fx": ["get_fx"],
}


# Donde la plantilla ya responde bien no se llama al LLM (regla de costo). En la prueba con
# qwen2.5:3b el LLM invirtió la unidad del tipo de cambio («USD/PEN»), llamó «actual» a un
# dato guardado y en la simulación le quitó el signo al saldo («S/ 50 te sobraron» por -50),
# un error de sentido que el juez de cifras no puede ver.
INTENCIONES_SOLO_PLANTILLA = {"fx", "segmento", "simular"}


def responder(intencion: str, datos: dict) -> str:
    if intencion in RESPUESTAS_FIJAS:
        return RESPUESTAS_FIJAS[intencion]
    return f"{_POR_INTENCION[intencion](datos)}\n\n{CIERRE}"
