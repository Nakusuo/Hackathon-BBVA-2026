"""Router por reglas: decide la intención y el monto sin LLM.

Va por reglas para que sea rápido, gratis, igual con o sin red, y para que un pedido de
operación o un intento de inyección se corte antes de llegar a cualquier modelo.
"""

import re
import unicodedata

_OPERACION = [
    r"\b(compr|vend)\w*\s+(\w+\s+)?dolar",
    # «cámbiame mis dólares» es operación; «el cambio del dólar» es consulta.
    r"\bcambi\w*\s+(?!del?\b)(\w+\s+)?dolar",
    r"\bcambi(a|ar|ame|en|amelos)\s+(\w+\s+){0,2}dolar",
    r"\btransf(iere|erir|erencia)",
    r"\b(yapea|plinea|envia(le)?\s+(plata|dinero))",
    r"\bmueve\s+(mi\s+)?(plata|dinero)",
    r"\b(donde|en que)\s+invierto\b",
]
_INYECCION = [
    r"\bignora\w*\b",
    r"\bolvida\w*\s+(tus|las)\s+(instrucciones|reglas)",
    r"\b(system|sistema)\s+prompt\b",
    r"\bprompt\b",
    r"\bactua\s+como\b",
    r"\bahora\s+eres\b",
    r"\bmodo\s+(desarrollador|dios|admin)",
    r"\bjailbreak\b",
    r"\brevela\w*\b",
]
_INTENCIONES = [
    (
        "simular",
        [
            r"\bsi\s+(gasto|compro|pago|me compro)\b",
            r"\b(puedo|podria)\s+(gastar|comprar|pagar)\b",
            r"\bsimula",
            r"\bque pasa si\b",
        ],
    ),
    (
        "pronostico",
        [
            r"\bfin de mes\b",
            r"\bllego\b",
            r"\balcanza",
            r"\bquincena\b",
            r"\ben rojo\b",
            r"\bpronostico\b",
            r"\bsaldo\b",
            r"\bque viene\b",
        ],
    ),
    ("salud", [r"\bsalud\b", r"\bpuntaje\b", r"\bcomo estoy\b", r"\bcomo voy\b"]),
    (
        "recos",
        [
            r"\bque (hago|me conviene|puedo hacer)\b",
            r"\brecomienda",
            r"\bconsejo",
            r"\bahorrar\b",
            r"\bconviene\b",
        ],
    ),
    ("segmento", [r"\bperfil\b", r"\bsegmento\b", r"\bque tipo de (?!cambio\b)"]),
    # Va después de las operaciones bloqueadas: «¿compro dólares?» nunca llega aquí.
    ("fx", [r"\btipo de cambio\b", r"\bdolar(es)?\b"]),
]
_MONTO = re.compile(r"(\d{1,3}(?:[ ,]\d{3})+|\d+)(\.\d{1,2})?")


def normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in sin_tildes if not unicodedata.combining(c))


def _alguna(patrones: list[str], texto: str) -> bool:
    return any(re.search(p, texto) for p in patrones)


def extraer_monto(texto: str) -> float | None:
    m = _MONTO.search(normalizar(texto))
    if not m:
        return None
    entero = m.group(1).replace(",", "").replace(" ", "")
    return float(entero + (m.group(2) or ""))


def clasificar(pregunta: str) -> tuple[str, float | None]:
    """Devuelve (intención, monto). Las intenciones bloqueadas van primero."""
    texto = normalizar(pregunta)
    if _alguna(_OPERACION, texto):
        return "operacion", None
    if _alguna(_INYECCION, texto):
        return "inyeccion", None
    for intencion, patrones in _INTENCIONES:
        if _alguna(patrones, texto):
            monto = extraer_monto(pregunta) if intencion == "simular" else None
            if intencion == "simular" and monto is None:
                return "pronostico", None
            return intencion, monto
    return "desconocido", None
