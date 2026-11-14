"""Nodo juez: cada cifra de la respuesta debe salir de una tool y cada cita debe existir."""

import re
from dataclasses import dataclass, field
from datetime import date

# Acepta «1 680», «1,680.50», «1.680,50», «85,5» y «0.25». El separador de miles
# puede ser espacio normal o fino porque así formatean montos las plantillas.
_NUMERO = re.compile(
    r"(?<![\w.,])-?\d{1,3}(?:[  .,]\d{3})+(?:[.,]\d+)?(?![\w])|(?<![\w.,])-?\d+(?:[.,]\d+)?(?![\w])"
)
_CITA = re.compile(r"\[fuente:\s*([^\]]+?)\s*\]")
# «1.» o «2)» al inicio de línea numeran una lista, no son cifras.
_VINETA = re.compile(r"^\s*\d{1,2}[.)]\s", re.MULTILINE)
_FECHA_ISO = re.compile(r"^\d{4}-\d{2}(-\d{2})?$|^\d{4}-\d{2}-\d{2}T")

# Al hablar se redondea a la decena desde 100 y a la centena desde 1 000; nada intermedio.
_REDONDEOS = ((100, -1), (1000, -2))


@dataclass
class Veredicto:
    ok: bool
    cifras_verificadas: list[float] = field(default_factory=list)
    cifras_no_verificadas: list[float] = field(default_factory=list)
    cifras_mal_descritas: list[float] = field(default_factory=list)
    citas_invalidas: list[str] = field(default_factory=list)
    fechas_incorrectas: list[str] = field(default_factory=list)
    frases_prohibidas: list[str] = field(default_factory=list)
    # (valor de la tool, campo del que salió) de cada cifra verificada que no es una fecha:
    # la UI la muestra con su etiqueta y con el signo real, aunque el texto lo haya omitido.
    detalle: list[tuple[float, str]] = field(default_factory=list)


def interpretar_numero(texto: str) -> tuple[float, int]:
    """Convierte un número escrito a la peruana o a la inglesa en (valor, decimales escritos)."""
    limpio = texto.replace(" ", "").replace(" ", "")
    ultimo_punto, ultima_coma = limpio.rfind("."), limpio.rfind(",")
    if ultimo_punto >= 0 and ultima_coma >= 0:
        decimal = "." if ultimo_punto > ultima_coma else ","
        miles = "," if decimal == "." else "."
        limpio = limpio.replace(miles, "").replace(decimal, ".")
    elif ultima_coma >= 0 or ultimo_punto >= 0:
        sep = "," if ultima_coma >= 0 else "."
        partes = limpio.split(sep)
        # Un solo separador seguido de 3 dígitos es de miles («1,680»); si no, es decimal («85,5»).
        if all(len(p) == 3 for p in partes[1:]) and (len(partes) > 2 or sep == ","):
            limpio = limpio.replace(sep, "")
        else:
            limpio = limpio.replace(sep, ".")
    decimales = len(limpio.split(".")[1]) if "." in limpio else 0
    return float(limpio), decimales


_CORTE = re.compile(r"[.!?;:,\n](?:\s|$)")
_FIN_DE_FRASE = re.compile(r"[.!?;\n](?:\s|$)")


def _frase(texto: str, inicio: int, fin: int) -> str:
    previos = [m.end() for m in _FIN_DE_FRASE.finditer(texto, 0, inicio)]
    siguiente = _FIN_DE_FRASE.search(texto, fin)
    return texto[previos[-1] if previos else 0 : siguiente.start() if siguiente else len(texto)]


def _alrededor(texto: str, numeros: list[re.Match], i: int) -> tuple[str, str, str]:
    """Lo escrito justo antes y justo después del número, y la frase entera que lo contiene."""
    m = numeros[i]
    desde = max(m.start() - 30, numeros[i - 1].end() if i else 0)
    hasta = min(m.end() + 25, numeros[i + 1].start() if i + 1 < len(numeros) else len(texto))
    antes, despues = texto[desde : m.start()], texto[m.end() : hasta]
    cortes = list(_CORTE.finditer(antes))
    antes = antes[cortes[-1].end() :] if cortes else antes
    corte = _CORTE.search(despues)
    despues = despues[: corte.start()] if corte else despues
    return antes.lower(), despues.lower(), _frase(texto, m.start(), m.end()).lower()


def extraer_numeros(texto: str) -> list[tuple[float, int, bool, tuple[str, str, str]]]:
    """(valor, decimales, escrito_como_soles, (antes, después, frase)) de cada número."""
    limpio = _VINETA.sub("", _CITA.sub("", texto))
    encontrados = list(_NUMERO.finditer(limpio))
    numeros = []
    for i, m in enumerate(encontrados):
        antes, despues = limpio[max(0, m.start() - 4) : m.start()], limpio[m.end() : m.end() + 3]
        en_soles = "S/" in antes or despues.lstrip().startswith("S/")
        valor, decimales = interpretar_numero(m.group())
        # «-S/ 200» es negativo aunque el signo quede antes del símbolo.
        if "-S/" in antes:
            valor = -abs(valor)
        numeros.append((valor, decimales, en_soles, _alrededor(limpio, encontrados, i)))
    return numeros


# Un campo es de dinero si su nombre lo dice. Así «S/ 72» no pasa cuando 72 es el puntaje.
_CLAVES_DINERO = re.compile(
    r"saldo|gasto|impacto|soles|monto|balance|bound|amount|impact|difference|rate|benefit|saving"
)


@dataclass
class Permitidos:
    cifras: set[float] = field(default_factory=set)
    soles: set[float] = field(default_factory=set)
    partes_fecha: set[float] = field(default_factory=set)
    fechas: list[date] = field(default_factory=list)
    campo: dict[float, str] = field(default_factory=dict)

    @property
    def todos(self) -> set[float]:
        return self.cifras | self.partes_fecha


def valores_permitidos(datos) -> Permitidos:
    """Junta cada número de las tools (aparte los de dinero) y día, mes y año de sus fechas."""
    p = Permitidos()

    def visitar(x, clave: str = ""):
        if isinstance(x, bool):
            return
        if isinstance(x, (int, float)):
            p.cifras.add(float(x))
            p.campo.setdefault(float(x), clave)
            if _CLAVES_DINERO.search(clave):
                p.soles.add(float(x))
            if 0 < abs(x) <= 1:
                p.cifras.add(round(float(x) * 100, 6))
                p.campo.setdefault(round(float(x) * 100, 6), clave)
        elif isinstance(x, str) and _FECHA_ISO.match(x):
            # Un periodo mensual («2026-10») aporta mes y año; una fecha, también el día.
            p.partes_fecha.update({float(x[:4]), float(x[5:7])})
            if len(x) >= 10:
                d = date.fromisoformat(x[:10])
                p.partes_fecha.add(float(d.day))
                p.fechas.append(d)
        elif isinstance(x, dict):
            for k, v in x.items():
                visitar(v, str(k).lower())
        elif isinstance(x, (list, tuple)):
            for v in x:
                visitar(v, clave)

    visitar(datos)
    return p


# Un LLM chico a veces «aconseja» aunque el prompt lo prohíba; aquí se corta.
# Si el RAG de inversión (JF-05) necesita explicar qué es invertir, va por plantilla con cita.
_PROHIBIDAS = [
    r"\binvert\w*",
    r"\binvier\w*",
    r"\b(compr|vend)\w*\s+(\w+\s+)?d[oó]lar",
    r"\btransfi?er\w*",
    r"\brentabilidad (asegurada|garantizada)",
    r"\bte garantiz\w*",
    r"\bpr[eé]stamo\w*",
    # «Tu tarjeta de crédito» describe; «pide un crédito» sugiere (negocio.md, regla 1).
    r"\b(un|otro|nuevo|l[ií]nea de) cr[eé]dito\b",
    r"\bsin (ning[uú]n )?riesgo\b",
    r"\b(ganancia|rentabilidad|ganar[aá]s) segur\w*",
]


def frases_prohibidas(texto: str) -> list[str]:
    bajo = texto.lower()
    return [m.group() for patron in _PROHIBIDAS for m in re.finditer(patron, bajo)]


_DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
_DIA_Y_NUMERO = re.compile(
    r"\b(lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\s+(\d{1,2})\b"
)


def fechas_incorrectas(texto: str, fechas: list[date]) -> list[str]:
    """«jueves 18» cuando el 18 de los datos cae miércoles: el LLM no sabe calendarios."""
    errores = []
    for m in _DIA_Y_NUMERO.finditer(texto.lower()):
        dia_semana = _DIAS.index(m.group(1).replace("é", "e").replace("á", "a"))
        mismas = [f for f in fechas if f.day == int(m.group(2))]
        if mismas and all(f.weekday() != dia_semana for f in mismas):
            errores.append(m.group())
    return errores


def _redondea_a(valor: float, decimales: int, p: float) -> bool:
    if abs(abs(valor) - abs(p)) <= 0.5 * 10**-decimales:
        return True
    # Quien escribe decimales afirma precisión: ahí solo vale el redondeo de lo escrito.
    if decimales:
        return False
    return any(abs(p) >= desde and abs(valor) == round(abs(p), a) for desde, a in _REDONDEOS)


def buscar(valor: float, decimales: int, permitidos: set[float]) -> float | None:
    """El valor permitido del que `valor` es una forma escrita (exacto o redondeado), o None."""
    cerca = [p for p in permitidos if _redondea_a(valor, decimales, p)]
    # Ante un empate (+150 del gasto y -150 de la diferencia) gana el del mismo signo.
    return (
        min(cerca, key=lambda p: (abs(abs(valor) - abs(p)), (p < 0) != (valor < 0), p))
        if cerca
        else None
    )


def coincide(valor: float, decimales: int, permitidos: set[float]) -> bool:
    return buscar(valor, decimales, permitidos) is not None


# Un saldo negativo escrito sin «-» solo vale si la marca de rojo va pegada a la cifra
# («en rojo por S/ 310», «te faltarían S/ 310», «S/ 310 en rojo») y la frase no niega nada:
# «No vas a quedar en rojo por S/ 310» dice lo contrario. Ante la duda responde la plantilla.
_ROJO_ANTES = re.compile(
    r"(en rojo|en negativo|falta\w*|faltar\w*|d[eé]ficit|deuda|sobregir\w*|corto|debajo)"
    r"\s+(?:(?:por|de|en|con|unos|unas|cerca de)\s+)*(?:s/\s*)?$"
)
_ROJO_DESPUES = re.compile(
    r"^\s*(?:de\s+)?(en rojo|en negativo|abajo|bajo cero|de deuda|negativo"
    # «S/ 200 te faltaron» sí; en «S/ 150 te faltarían S/ 200» lo que falta es el 200.
    r"|(?:te |me )?falta\w*(?!.*s/))"
)
_NEGACION = re.compile(r"\b(no|sin|ni|nada|nunca|jam[aá]s|ning[uú]n\w*|tampoco|lejos de)\b")
_A_FAVOR = re.compile(r"a favor|te sobra|sobran|de sobra|positiv|ganancia|tranquil")


def _marca_rojo(antes: str, despues: str) -> bool:
    return bool(_ROJO_DESPUES.search(despues) or _ROJO_ANTES.search(antes))


def signo_contradice(valor: float, origen: float, alrededor: tuple[str, str, str]) -> bool:
    """«S/ 310 a favor» cuando el dato es -310: la cifra existe pero dice lo contrario."""
    antes, despues, frase = alrededor
    if origen < 0 <= valor:
        return (
            bool(_A_FAVOR.search(antes + " " + despues))
            or bool(_NEGACION.search(frase))
            or not _marca_rojo(antes, despues)
        )
    # «En rojo por S/ 210» cuando el dato es +210 también es falso, aunque asuste.
    return origen > 0 and (valor < 0 or _marca_rojo(antes, despues))


# Lo vio Michael en la RTX 3050: «Tu saldo actual es S/ 120» con 120 = ahorro en delivery,
# y el 3b llamó «saldo actual» al saldo final de la simulación.
_CAMPOS_SALDO = re.compile(r"saldo|balance|bound")
_CAMPOS_FUTUROS = re.compile(r"final|bound|predicted|previsto|probable")
_DICE_HOY = re.compile(r"\b(actual|hoy|ahora)\b")


def cifra_mal_descrita(campo: str, antes: str) -> bool:
    """La cifra existe, pero el texto la llama como otra cosa."""
    if "saldo" in antes and not _CAMPOS_SALDO.search(campo):
        return True
    return bool(_DICE_HOY.search(antes) and _CAMPOS_FUTUROS.search(campo))


def juzgar(
    texto: str,
    datos,
    fuentes_validas: set[str] | None = None,
    exigir_cifra: bool = False,
    revisar_frases: bool = True,
) -> Veredicto:
    """Aprueba la respuesta solo si todas sus cifras y citas tienen respaldo.

    Con `exigir_cifra`, si las tools trajeron números la respuesta debe usar al menos uno
    que no sea parte de una fecha: un texto sin montos no es error, pero no ayuda a decidir.
    """
    p = valores_permitidos(datos)
    verificadas, no_verificadas, detalle, mal_descritas = [], [], [], []
    for valor, decimales, en_soles, alrededor in extraer_numeros(texto):
        respaldo = buscar(valor, decimales, p.soles if en_soles else p.todos)
        if respaldo is None or signo_contradice(valor, respaldo, alrededor):
            no_verificadas.append(valor)
            continue
        origen = buscar(valor, decimales, p.soles if en_soles else p.cifras)
        if origen is not None and cifra_mal_descrita(p.campo[origen], alrededor[0]):
            mal_descritas.append(valor)
            continue
        verificadas.append(valor)
        if origen is not None:
            detalle.append((origen, p.campo[origen]))
    montos = len(detalle)
    citas_invalidas = [c for c in _CITA.findall(texto) if c not in (fuentes_validas or set())]
    fechas_mal = fechas_incorrectas(texto, p.fechas)
    # Las plantillas las escribe el equipo y algunas niegan a propósito («no puedo comprar dólares»).
    prohibidas = frases_prohibidas(texto) if revisar_frases else []
    sin_cifras = exigir_cifra and bool(p.cifras) and not montos
    return Veredicto(
        ok=not (no_verificadas or mal_descritas or citas_invalidas or fechas_mal or prohibidas)
        and not sin_cifras,
        cifras_verificadas=verificadas,
        cifras_no_verificadas=no_verificadas,
        cifras_mal_descritas=mal_descritas,
        citas_invalidas=citas_invalidas,
        fechas_incorrectas=fechas_mal,
        frases_prohibidas=prohibidas,
        detalle=detalle,
    )
