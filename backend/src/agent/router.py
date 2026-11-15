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
    # Casos de las frases naturales de Diego (backend/tests/agent/test_router_natural.py).
    r"\bpasa(le|me|les)?\s+(\w+\s+)?\d",
    r"\binvierte\b",
    r"\b(donde|en que)\s+(me\s+)?conviene\s+invertir\b",
    r"\b(compr|vend)\w*\s+(\w+\s+)?(acciones|bitcoin|cripto\w*)",
    r"\babre(me)?\s+(una\s+)?cuenta\b",
]
_INVERSION = [r"\binvert\w*", r"\binvier\w*", r"\baccion(es)?\b", r"\bbitcoin\b", r"\bcripto\w*"]
_INYECCION = [
    r"\bignora\w*\b",
    r"\bolvida\w*\s+(tus|las)\s+(instrucciones|reglas)",
    r"\bolvida\w*\s+(todo|lo anterior)",
    r"\bobedece\w*",
    r"\b(api key|apikey|clave secreta|contrasena|token)\b",
    r"\b(cuentas?|datos|saldo)\s+de\s+(otra persona|otro cliente|otros clientes|otras personas)",
    r"\b(system|sistema)\s+prompt\b",
    r"\bprompt\b",
    r"\bactua\s+como\b",
    r"\bahora\s+eres\b",
    r"\bmodo\s+(desarrollador|dios|admin)",
    r"\bjailbreak\b",
    r"\brevela\w*\b",
]
# Temas que siempre son de educación aunque la frase suene a pronóstico o a consejo:
# «¿qué hago con mi CTS?» o «me atrasé con la cuota, ¿qué hago?» no se responden con el
# saldo del cliente sino con la norma. Se revisan después de simular (que exige un monto).
_EDUCACION_FUERTE = [
    r"\b(cts|compensacion por tiempo|gratificacion|grati)\b",
    r"\b(tarjeta|credito|prestamo|deuda|cuota|interes|tasa|refinanci)\w*",
    r"\b(reclam|derecho|cobr)\w*",
    r"\b(atrase|atrasado|atraso|no pago)\b",
    r"\b(huaico|lluvia|llover|zona de riesgo|fenomeno|nino)\b",
    r"\b(deposito a plazo|oferta)\w*",
    # «¿Para qué sirve ahorrar?» pide una explicación, no una recomendación.
    r"\bpara que sirve",
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
            r"\bvoy a (tener|ganar|gastar)\b",
            r"\bproxim[oa]s (dias|semanas|meses)\b",
        ],
    ),
    ("salud", [r"\bsalud\b", r"\bpuntaje\b", r"\bcomo estoy\b", r"\bcomo voy\b", r"\bsana\b"]),
    (
        "recos",
        [
            r"\bgastando de mas\b",
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
    # Al final: «¿qué es mi perfil?» es segmento y «¿qué es el tipo de cambio?» es fx.
    (
        "educacion",
        [
            r"\bque (es|son|significa|significan)\b",
            r"\bpara que sirve",
            r"\bcomo funciona",
            r"\bque derechos\b",
            r"\b(tcea|tea|trea|cts|gratificacion|indecopi|reclamo|enfen)\b",
            r"\bfenomeno\b|\bel nino\b",
            r"\bdatos personales\b",
        ],
    ),
]

# Tema → módulo del índice de Diego. Es una lista cerrada: lo que llega al LLM como «tema»
# sale de aquí, nunca del texto libre del usuario (ISO 8.12).
_TEMAS_RAG = {
    "deudas": {
        "tcea": "TCEA",
        "tea": "TEA",
        "interes": "intereses",
        "credito": "crédito",
        "tarjeta": "tarjeta de crédito",
        "deuda": "deudas",
        "cuota": "cuotas",
        "mora": "mora",
        "atras": "pagos atrasados",
        "prestamo": "préstamos",
    },
    "derechos": {
        "reclam": "reclamos",
        "cobr": "cobros",
        "derecho": "derechos del usuario",
        "indecopi": "Indecopi",
        "consumidor": "protección al consumidor",
        "datos personales": "datos personales",
        "privacidad": "privacidad",
        "transparencia": "transparencia",
    },
    "salud_financiera": {
        "presupuesto": "presupuesto",
        "meta": "metas de ahorro",
        "emergencia": "fondo de emergencia",
        "colchon": "fondo de emergencia",
        "ahorro": "ahorro",
    },
    "laboral": {
        "cts": "CTS",
        "gratificacion": "gratificación",
        "grati": "gratificación",
        "bonificacion": "bonificación extraordinaria",
    },
    "fenomeno_el_nino": {
        "nino": "fenómeno El Niño",
        "fenomeno": "fenómeno El Niño",
        "enfen": "ENFEN",
        "lluvia": "lluvias",
        "huaico": "huaicos",
        "zona de riesgo": "zonas de riesgo",
    },
}


def temas_rag(pregunta: str) -> tuple[list[str] | None, list[str]]:
    """(módulos donde buscar, temas de la lista cerrada). Sin módulos se busca en todos."""
    texto = normalizar(pregunta)
    modulos, temas = [], []
    for modulo, palabras in _TEMAS_RAG.items():
        for palabra, tema in palabras.items():
            if re.search(rf"\b{palabra}", texto):
                if modulo not in modulos:
                    modulos.append(modulo)
                if tema not in temas:
                    temas.append(tema)
    return (modulos or None), temas


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
    bloqueada = (
        "operacion"
        if _alguna(_OPERACION, texto)
        else "inyeccion"
        if _alguna(_INYECCION, texto)
        else None
    )
    if bloqueada:
        # Un pedido de inversión bloqueado recibe una negativa que explica el porqué y
        # ofrece lo que sí se puede explicar con fuente (CP-SIS-12).
        return ("inversion" if _alguna(_INVERSION, texto) else bloqueada), None
    patrones = dict(_INTENCIONES)
    pide_simular = _alguna(patrones["simular"], texto)
    monto = extraer_monto(pregunta) if pide_simular else None
    if monto is not None:
        return "simular", monto
    if _alguna(patrones["pronostico"], texto):
        return "pronostico", None
    if _alguna(_EDUCACION_FUERTE, texto):
        return "educacion", None
    for intencion, lista in _INTENCIONES:
        if intencion not in ("simular", "pronostico") and _alguna(lista, texto):
            return intencion, None
    # «¿Qué pasa si…?» sin monto: lo más útil es el pronóstico.
    return ("pronostico" if pide_simular else "desconocido"), None
