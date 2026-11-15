"""Respuestas por plantilla: siempre funcionan, sin red ni LLM, y son el baseline del agente.

Solo usan cifras que vienen en `datos` (campos del contrato `docs/api.md`), así el juez
siempre las aprueba.
"""

import unicodedata

from .formato import fecha_larga, soles
from .rag import ACRONIMOS

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
    "sin_datos": (
        "Ahora no puedo ver tus datos, así que prefiero no darte cifras. "
        "Prueba de nuevo en un momento."
    ),
    # Sin números: es una respuesta fija y el juez no tiene datos contra qué comprobarlos.
    "inversion": (
        "No puedo decirte en qué invertir: para recomendar una inversión la norma de la "
        "Superintendencia del Mercado de Valores exige evaluar antes tu perfil de riesgo, y "
        "Lucas no es un asesor. Sí puedo explicarte qué es un depósito a plazo, cómo armar tu "
        "fondo de emergencia antes de pensar en invertir o simular cuánto puedes apartar."
    ),
    "sin_fuente": (
        "No encontré una fuente oficial que responda eso, así que prefiero no inventarlo. "
        "Puedo explicarte la TCEA, tus derechos como usuario, la CTS, la gratificación "
        "o cómo armar un fondo de emergencia."
    ),
}

CIERRE_EDUCACION = "Es información general con su fuente, no una asesoría. Tú decides."
LARGO_EXTRACTO = 320


def _sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def extracto(texto: str, claves: list[str] = (), largo: int = LARGO_EXTRACTO) -> str:
    """Frases completas desde la primera que menciona el tema, o desde el inicio.

    El corte del PDF deja restos al borde del fragmento («. 12.2 Si la tasa…»): se limpian.
    """
    texto = texto.strip().lstrip(".,;: ")
    bajo = _sin_tildes(texto.lower())
    posiciones = [bajo.find(_sin_tildes(c.lower())) for c in claves]
    encontradas = [p for p in posiciones if p > 0]
    if encontradas:
        tema = min(encontradas)
        # Si no hay un punto cerca antes del tema, lo anterior suele ser el membrete del PDF.
        inicio = texto.rfind(". ", max(0, tema - 200), tema)
        if inicio >= 0:
            texto = texto[inicio + 2 :]
        else:
            # Dos palabras antes del tema, para que se lea «…La CTS es» y no «…CTS es».
            desde = texto.rfind(" ", 0, max(0, texto.rfind(" ", 0, tema - 1)))
            texto = "…" + texto[desde + 1 :]
    if len(texto) <= largo:
        return texto
    corte = texto.rfind(". ", 0, largo)
    return texto[: corte + 1] if corte > largo // 3 else texto[:largo] + "…"


def _educacion(d: dict) -> str:
    fuentes = d["buscar_fuentes"]
    f = fuentes["fragmentos"][0]
    claves = [*fuentes["tema"], *(ACRONIMOS.get(t, "") for t in fuentes["tema"])]
    texto = (
        f"Según {f['titulo']} ({f['institucion']}, página {f['pagina']}): "
        f"«{extracto(f['texto'], [c for c in claves if c])}» [fuente: {f['id']}]"
    )
    if f["contexto"] != "Peru":
        texto += (
            f"\nOjo: esta guía es de {f['contexto']}; las normas peruanas pueden ser distintas."
        )
    return texto


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
    "educacion": _educacion,
}

# Qué tool alimenta cada intención; el grafo las llama en este orden.
TOOLS_POR_INTENCION = {
    "salud": ["get_health"],
    "pronostico": ["get_forecast"],
    "recos": ["get_recos"],
    "simular": ["simulate"],
    "segmento": ["get_health"],
    "fx": ["get_fx"],
    "educacion": ["buscar_fuentes"],
}


# Donde la plantilla ya responde bien no se llama al LLM (regla de costo). En la prueba con
# qwen2.5:3b el LLM invirtió la unidad del tipo de cambio («USD/PEN»), llamó «actual» a un
# dato guardado y en la simulación le quitó el signo al saldo («S/ 50 te sobraron» por -50),
# un error de sentido que el juez de cifras no puede ver. En educación (RAG) no citó la fuente
# y metió cifras ajenas al fragmento en 4 de 4 intentos: la plantilla cita textual.
INTENCIONES_SOLO_PLANTILLA = {"fx", "segmento", "simular", "educacion"}


def responder(intencion: str, datos: dict) -> str:
    if intencion in RESPUESTAS_FIJAS:
        return RESPUESTAS_FIJAS[intencion]
    cierre = CIERRE_EDUCACION if intencion == "educacion" else CIERRE
    return f"{_POR_INTENCION[intencion](datos)}\n\n{cierre}"
