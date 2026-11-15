"""Agente de Lucas con LangGraph. Dos modos sobre las mismas piezas:
 - agente_unico: una tuberia fija (contexto -> router -> herramientas -> RAG -> redaccion -> juez).
 - multiagente: un supervisor reparte el trabajo entre agentes especialistas que pueden pedirse datos entre si.
El LLM solo redacta; toda cifra sale de una herramienta y pasa por el juez. Si algo falla, responde una plantilla."""
import hashlib
import json
import os
import re
import time
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.agente_analitico import faq as FAQ
from src.agente_analitico import proveedores as PV
from src.agente_analitico import traduccion as TR
from src.agente_analitico.juez_llm import juzgar
from src.agente_analitico.repositorio import VENTANA_RECALCULO_DIAS as VENTANA_DATOS_DIAS
from src.agente_analitico.verificador import aplanar, numeros_de, verificar
from src.bcrp.cliente import ultimo_con_variacion
from src.comun import reloj
from src.comun.rutas import cargar_env, ruta
from src.generador.contexto import cargar_yaml
from src.models import calendario_laboral as CL
from src.models import campanas as CA
from src.models import niveles as N
from src.models import ofertas as O
from src.models import programa_puntos as PP
from src.models import recomendador as REC
from src.models import riesgo_clima as RC
from src.models import salud as SA

UMBRAL_RELEVANCIA = 0.70   # filtro tipo CRAG, calibrado en src/rag/evaluar.py
MAX_INTENTOS = 2

# Pregunta de concepto: «que es una cosa» (no «que es lo que me conviene» ni «que es mi nivel»), «como funciona», «para que sirve»...
CONCEPTO = r"qu[eé] es (?!lo\b|mi\b|mis\b|tu\b|tus\b)\w|qu[eé] significa|c[oó]mo funciona|c[oó]mo se (?:calcula|cobra|paga)|explica|en qu[eé] consiste|para qu[eé] sirve"
# Si la pregunta de concepto es del programa de puntos y niveles de Lucas, la respuesta esta en los datos del cliente, no en las fuentes
PROGRAMA = r"puntos|nivel|canje|beneficios|insignia"
# Pista de tiempo o de monto: si la pregunta de CTS o gratificacion la trae, quiere el calendario; si solo es de concepto, quiere la explicacion
PISTA_DE_CALENDARIO = r"cu[aá]ndo|cu[aá]nto|retir|dispon|deposit|monto|fecha|\bcae\b|llega|pagan|\bpaga\b"

# Las operaciones y los consejos de inversion no se hacen: se cortan antes de cualquier herramienta o LLM
OPERACION = (r"transfier|transferir|p[aá]sa(?:le|me|selo)\b|yapea|plinea|c[aá]mbiame|abre(?:me)? (?:una|un) (?:cuenta|dep[oó]sito)|m[aá]nda(?:le|me)? (?:plata|dinero|s/|\d)|env[ií]a(?:le|me)? (?:plata|dinero|s/|\d)|enviar (?:la )?(?:plata|dinero)|"
             r"compr[oa]r? d[oó]lares|vend[oe]r? d[oó]lares|invierte en|invierto en|d[oó]nde (?:me conviene )?(?:invierto|invertir)|en qu[eé] (?:me conviene )?invertir|criptomoneda|bitcoin|compra(?:r)? acciones|en qu[eé] (?:acci[oó]n|empresa|cripto\w*)")
# Mora y reclamos: es una pregunta de derechos, aunque nombre una tarjeta, un cobro o un prestamo
MORA_Y_RECLAMOS = r"derechos?|reclam|atras[eéo]|\bmora\b|no pago|dej[eé] de pagar|me cobran de m[aá]s|no reconozco|datos personales"

# «¿Y si gasto S/ 450?»: solo es una simulacion si la frase trae un monto (lo comprueba detectar_intencion); sin monto sigue su camino normal
SIMULAR = r"\bsi (?:me )?(?:gasto|compro|pago)\b|(?:puedo|podr[ií]a|quiero|quisiera|voy a|pienso|planeo) (?:gastar|comprar(?:me)?|pagar)|\bsimula|qu[eé] pasa(?:r[ií]a)? si"
# «¿Cuanto debo ahorrar para comprar X?»: es una meta de ahorro, no un gasto de hoy. Va antes que simular porque la frase suele traer «quiero comprar»
META = (r"cu[aá]nto (?:debo|deber[ií]a|tengo que|necesito|me falta|hay que) (?:ir )?(?:ahorr|apart|junt|guard)\w*|(?:ahorrar|juntar|apartar|guardar) (?:\S+ ){0,3}para (?:poder |compr|un|una|mi|el|la|ir|viaj)\w*|"
        r"para poder (?:comprar|irme|viajar|pagar)|plan (?:de|para) (?:ahorr|junt)\w*|(?:convenio|descuento)s? (?:con|del|de) (?:el |mi |nuestro )?banco")
# Quiere comprar algo y no dijo cuanto cuesta: se le pide el precio en vez de tratarlo como un tema ajeno
COMPRA = r"(?:quiero|quisiera|voy a|pienso|planeo|me gustar[ií]a) comprar(?:me)?\b"
# Lo que ya se gasto: «¿cuanto gaste este mes?», «¿en que se me va la plata?». «¿En que estoy gastando de mas?» sigue siendo una recomendacion
GASTOS = (r"cu[aá]nto (?:gast[eé]|he gastado|llevo gastado|gastamos)|en qu[eé] (?:gast[eé]|se me (?:va|fue|van))|(?:resumen|detalle|total) de (?:mis |los )?gastos|"
          r"mis gastos (?:de|del) (?:este |el )?mes|gastos? (?:de|del) (?:este )?mes\b")
# Balance de lo que la persona ya aparto; «como ahorro mas» sigue siendo una recomendacion
AHORRO = r"(?:resum\w+|estad[ií]stic\w+|c[oó]mo va[n]?|cu[aá]nto (?:he|llevo|tengo)).{0,40}ahorr|cu[aá]nto ahorro\b"
# Productos que el catalogo de demostracion no tiene: se dice, en vez de ofrecer otra cosa como si respondiera
SIN_PRODUCTO = {"un crédito vehicular": r"camioneta|\bauto\b|autom[oó]vil|carro|veh[ií]cul|\bmoto\b", "un crédito hipotecario": r"hipotec|\bcasa\b|departamento|\bdepa\b|terreno"}
# Conversacion natural: una persona suele empezar con «hola», «oye» o «ayudame», o contar como se siente, sin una pregunta concreta. Eso no se rechaza: se acoge y se ofrecen opciones.
SALUDO = (r"hola+|holi+|ola+|al[oó]|wenas?|buen[ao]s(?: d[ií]as| tardes| noches)?|buen d[ií]a|hey|ey|epa|oye|oiga|disculpa|disculpe|saludos|qu[eé] tal|qu[eé] onda|"
          r"hello|hi|howdy|greetings|good (?:morning|afternoon|evening|night)")
RELLENO = (r"por favor|porfa|una consulta|tengo una consulta|tengo una duda|quiero preguntar|quiero consultar|necesito ayuda|necesito apoyo|me puedes ayudar|puedes ayudarme|me ayudas|ay[uú]dame|ay[uú]denme|ayuda|"
           r"auxilio|gracias|muchas gracias|ok|okey|listo|vale|dale|chau|adi[oó]s|hasta luego|nos vemos|c[oó]mo est[aá]s|c[oó]mo te va|c[oó]mo andas|qui[eé]n eres|qu[eé] eres|qu[eé] puedes hacer|en qu[eé] me ayudas|"
           r"qu[eé] haces|no s[eé]|no entiendo|nada|cualquier cosa|lo que sea|una cosita|una cosa|algo|un favor|bien|todo bien|m[aá]s o menos|ah|eh|mm+|jaja+|"
           # se le habla al agente por su nombre o de forma coloquial; respuestas sueltas; presentaciones y preguntas sobre quien es
           r"lucas|amig[oa]|bot|asistente|copiloto|compa|hermano|hermana|bro|s[ií]|no|claro|exacto|tal vez|quiz[aá]s?|pues|bueno|entonces|ya|aj[aá]|uhm+|hmm+|xd+|jeje+|jiji+|lol|haha+|"
           r"tengo una pregunta|una pregunta|quisiera (?:saber|preguntar|consultar)(?: algo)?|quiero (?:saber|preguntar|consultar)(?: algo)?|puedo preguntar(?:te)?(?: algo)?|puedo hacerte una pregunta|necesito saber algo|"
           r"c[oó]mo te llamas|c[oó]mo te dicen|tu nombre|eres (?:un )?(?:bot|robot|ia|humano|persona)|thanks|thank you|gracias por todo|"
           r"there|everyone|friend|please|help|help me|i need help|need help|can you help me|i have a question|a question|question")
CONVERSACION = rf"^[\W_]*(?:(?:{SALUDO}|{RELLENO})\b[\s,.!?¿¡:;-]*)+$"   # el mensaje entero es saludo o relleno: nada concreto que responder todavia
DESPEDIDA = r"chau|adi[oó]s|hasta luego|nos vemos"
# Emociones o una situacion dificil contada con palabras propias: se responde con empatia y se ofrece por donde empezar
EMOCIONAL = (r"preocup|angusti|agobi|estres|ahog|desespera|miedo|ansios|triste|p[eé]sim|cansad|harto|no puedo m[aá]s|no s[eé] qu[eé] hacer|no s[eé] c[oó]mo|me siento|"
             r"estoy (muy |bien |re )?(mal|apurad|complicad|ajustad|fregad|asustad)|problemas? (de|con) (mi )?(plata|dinero|deudas?)|estoy sin (plata|dinero|trabajo)|me qued[eé] sin|perd[ií] mi trabajo|me despidieron|"
             r"no tengo (plata|dinero|con qu[eé])|me cuesta (llegar|pagar)")
# Mensaje abierto: pide ayuda o habla de si mismo sin decir de que (no es un tema ajeno como una receta o una pregunta de cultura general)
ABIERTO = r"ayud|problema|duda|consulta|necesito|no s[eé]|no entiendo|hablar con|conversar|contarte|desahog|apoyo|orient|quiero (algo|saber algo|preguntar)|tengo (algo|una cosa|un tema)"
# Una pregunta sobre el mundo («¿que hora es?», «¿cuanto cuesta un iPhone?») no trae nada de la persona: eso si se rechaza con amabilidad. Si trae algo suyo («mi casa», «me falta», «puedo»), lo entiende la IA.
PREGUNTA_DEL_MUNDO = r"^[\s¿¡]*(?:qu[eé]|cu[aá]l(?:es)?|cu[aá]nt[oa]s?|qui[eé]n(?:es)?|d[oó]nde|c[oó]mo|cu[aá]ndo|por qu[eé]|en qu[eé]|a qu[eé]|de qu[eé]|para qu[eé])\b"
PERSONAL = r"\b(?:mi|mis|m[ií]o|m[ií]a|me|conmigo|tengo|debo|puedo|quiero|necesito|estoy|soy|tuve|ten[ií]a|pagar|pago|pagu[eé])\b"
INTENCIONES_ABIERTAS = ("conversacion", "apoyo", "general", "fuera_de_tema", "fuera_de_alcance")   # las respuestas que llevan opciones (botones)

REGLAS_INTENCION = [
    # seguridad: intentos de sacar instrucciones internas, claves o datos de otras personas, o de saltarse las reglas
    ("seguridad", r"system prompt|prompt del sistema|tu prompt|tus instrucciones|instrucciones (previas|anteriores|internas)|revela|ignora (tus|las|todas|todo)|olvida (tus|las|todas|todo)|jailbreak|\bDAN\b|contrase[ñn]a|api[ _-]?key|clave de (api|acceso)|\btoken\b|hackea|inyecci[oó]n|exploit|vulnerabilidad|"
                  r"ignore (?:your|all|the|any|previous)|disregard (?:your|all|the|previous)|your (?:system )?(?:prompt|instructions)|reveal your|you are now|pretend (?:to be|you)|developer mode|api key|other (?:customer|person|user)|"
                  r"datos de (otro|otra|otros)|de otro cliente|de otra persona|de otra gente|de terceros|cuentas? de (otro|otra|otros|otras)|act[uú]a como|ahora eres|modo (desarrollador|dios|admin)|sin (reglas|filtros|restricciones|l[ií]mites)"),
    # saludos y ayuda: se contestan con lo que si hace Lucas, no como un tema ajeno
    ("conversacion", CONVERSACION),
    # fuera de tema: codigo, matematica y cultura general, que no son de este asistente
    ("fuera_de_tema", r"c[oó]digo|\bscript\b|python|javascript|typescript|\bsql\b|\bjava\b|algoritmo|ecuaci[oó]n|integral|derivada|teorema|demuestra|problema (de )?matem|resuelve (esta|este|el|la)|tarea de|compila|\bhtml\b|\bcss\b|\bbash\b|\bregex\b|receta|capital de|qui[eé]n gan[oó]|poema|chiste"),
    ("fuera_de_alcance", OPERACION),
    ("meta", META),
    ("simular", SIMULAR),
    ("ahorro", AHORRO),
    ("gastos", GASTOS),
    ("fen", r"ni[ñn]o|lluvia|llov|huaico|inundaci|zona de riesgo|desastre|fen\b|fen[oó]meno|prevenci"),
    ("calendario", r"\bcts\b|gratificaci[oó]n|compensaci[oó]n por tiempo|libre (disponibilidad|disposici[oó]n)|aguinaldo|cu[aá]ndo (me )?(cae|llega|llegan|depositan|pagan)"),
    # una pregunta de concepto ("que es la TCEA", "como funciona el credito") se explica con las fuentes: va antes de tasas y ofertas, que serian para pedir un producto o ver la tasa
    ("educacion", CONCEPTO),
    ("educacion", MORA_Y_RECLAMOS),
    ("tipo_de_cambio", r"d[oó]lar|tipo de cambio"),
    ("tasas", r"\btasas?\b|inter[eé]s|tcea|refinanci|baj[oó] la tasa"),
    ("ofertas", r"pr[eé]stamo|cr[eé]dito|tarjeta|invertir|inversi[oó]n|dep[oó]sito|oferta"),
    ("salud_nivel", r"nivel|puntos|salud financiera|puntaje|campe[oó]n|maestro|aprendiz|luchador|canje|beneficio"),
    ("pronostico", r"alcanza|llego|fin de mes|saldo|rojo|cobro|pr[oó]ximo|pr[oó]ximos meses|cu[aá]nto (voy a|tendr|ganar|gastar)|proyecci|ingresos|me quedo sin (plata|dinero)|quedarme sin (plata|dinero)|c[oó]mo (voy|ando|me va|me est[aá] yendo)( (este|en este|con este|el|en el))? ?mes|c[oó]mo (voy|ando)\W*$"),
    ("recomendaciones", r"recomiend|qu[eé] hago|consejo|ahorrar|meta|reducir|gast"),
    ("educacion", r"c[oó]mo (armo|hago|llevo)"),
]
PLAN = {
    "pronostico": ["pronostico", "salud"], "recomendaciones": ["pronostico", "salud", "clima", "recomendador"], "salud_nivel": ["salud"], "fen": ["clima", "recomendador", "educador"],
    "tasas": ["tasas", "salud", "educador"], "ofertas": ["tasas", "ofertas"], "simular": ["simulador"], "ahorro": ["ahorro"], "meta": ["meta"], "compra": [], "gastos": ["gastos"], "educacion": ["educador"], "ingreso_extra": ["salud", "recomendador"],
    "baja_de_tasa": ["tasas", "salud", "recomendador"], "riesgo_rojo": ["pronostico", "salud", "recomendador"], "general": ["pronostico", "salud", "recomendador"], "fuera_de_alcance": [],
    "fuera_de_tema": [], "seguridad": [], "conversacion": [], "apoyo": ["pronostico", "salud", "recomendador"], "calendario": ["calendario", "salud", "recomendador", "educador"], "gasto_atipico": ["pronostico", "salud", "recomendador"], "tipo_de_cambio": ["tasas"],
}
# Evento proactivo -> intencion. Un evento desconocido cae a 'general' (nunca rompe el agente).
EVENTO_A_INTENCION = {"ingreso_extra": "ingreso_extra", "baja_de_tasa": "baja_de_tasa", "fen_comunicado": "fen", "riesgo_rojo": "riesgo_rojo", "calendario_laboral": "calendario",
                      "libre_disposicion_por_vencer": "calendario", "gratificacion_pendiente": "calendario", "gasto_atipico": "gasto_atipico"}
SIN_LLM = ("fuera_de_alcance", "fuera_de_tema", "seguridad", "compra")   # se responden con plantilla: no gastan tokens ni dan pie a que el modelo se desvie
# Politica de ahorro de tokens (MVP): el LLM solo redacta lo que una plantilla no cubre bien. LLM_USO=siempre lo usa en todo (pruebas); LLM_USO=ahorro es el defecto.
INTENCIONES_CON_LLM = ("educacion", "general", "apoyo")   # lo nuevo, lo abierto y lo emocional van a la IA; un saludo se contesta con plantilla (0 tokens)
INTENCIONES_DE_SALDO = ("pronostico", "riesgo_rojo", "general", "apoyo")   # respuestas que hablan del saldo: ahi se aclara la fecha de los datos del cliente
AYUDO_EN = "Sí puedo ver si llegas a fin de mes, simular un gasto, calcular cuánto apartar para una meta, resumir tu ahorro y mostrarte ofertas para tu perfil."
MODULOS_RAG = {"fen": ["fenomeno_el_nino"], "tasas": ["deudas", "derechos"], "educacion": None, "ofertas": ["deudas", "salud_financiera"], "calendario": ["laboral"]}


class Estado(TypedDict, total=False):
    customer_id: str
    pregunta: str
    modo_conversacion: str
    opciones: list
    evento: dict
    ctx: dict
    intencion: str
    pendientes: list
    siguiente: str
    datos: dict
    recos: list
    rag: list
    rag_estado: str
    borrador: str
    proveedor: str
    intentos: int
    feedback: str
    veredicto: dict
    juez_llm: dict
    respuesta: str
    citas: list
    trazas: list
    llamadas_llm: int
    usar_plantilla: bool
    t0: float
    idioma: str
    pregunta_original: str
    respuesta_es: str
    traduccion: dict


FINANZAS = r"plata|dinero|gast|ahorr|cuenta|saldo|sueldo|ingres|deuda|pago|banco|cuota|meta|financ|econom|colch|cr[eé]dito|tarjeta|tasa|nivel|puntos|beneficio|ni[ñn]o|lluvia|alcanza|cobro|rojo|presupuesto|reclam|derechos|datos personales|recomend"


def _termina_en_oracion_completa(txt: str) -> bool:
    """Un texto del LLM debe cerrar con puntuacion final. Un corte por el tope de tokens deja la última palabra a medias («...que eleg»)."""
    return txt.rstrip()[-1:] in tuple(".!?…)»\"”*")


def _es_respuesta_vacia(txt: str) -> bool:
    """Un borrador que solo trae el cierre («Tu decides.») o una frase suelta no responde nada: se rechaza como una cifra inventada (fallo real de la QA: un modelo local contesto solo «Tu decides.»)."""
    cuerpo = re.sub(r"(?i)tu decides\.?", "", txt).strip(" \n\t.*-")
    return len(cuerpo) < 40


# Intenciones donde los datos DE LA PERSONA contestan la pregunta (su saldo, su nivel, sus recomendaciones, su calendario): ahi una negativa del LLM («no tengo esa informacion, pregunta a un asesor») es una evasiva.
# No se incluyen fen, tasas, ofertas ni tipo de cambio: ahi se puede preguntar por un documento o un dato externo que no esta («el comunicado 35 del ENFEN», «la tasa de otro banco») y decir que no se tiene es lo honesto.
INTENCIONES_CON_DATOS = ("pronostico", "salud_nivel", "recomendaciones", "calendario", "riesgo_rojo", "ingreso_extra", "gasto_atipico")


def _es_evasiva(txt: str) -> bool:
    """El LLM se nego a responder («No tengo esa informacion a la mano, te sugiero preguntar a un asesor») cuando las herramientas SI traian los datos. Fallo real de la QA con Gemini: en 4 de 6 intentos
    contesto asi sobre el programa de puntos teniendolo en los datos. Se detecta por la frase con la que abre el borrador."""
    inicio = re.sub(r"^\W*(?:¡?hola\W+)?", "", txt.strip(), flags=re.I)[:90].lower()
    return re.match(r"(?:lo siento\W+)?no (?:tengo|cuento con|dispongo de|manejo) ", inicio) is not None


def _filtra_el_prompt(txt: str) -> bool:
    """El LLM nunca debe nombrar la seccion interna del prompt (en mayusculas, como la recibe): «lo que dicen los DATOS» revela como esta armado el agente."""
    # «Tono: practico; propone metas medibles» es la ficha interna del nivel, que el modelo local a veces copia tal cual
    return re.search(r"\bDATOS\b|\bTono:", txt) is not None


# Palabras que existen en portugues y no en espanol: el modelo local a veces se pasa de idioma a mitad de la respuesta
OTRO_IDIOMA = re.compile(r"\b(?:voc[eê]s?|n[aã]o|tamb[eé]m|ent[aã]o|ainda|al[eé]m|voc[eê]|seus?|suas?|uma|pelo|pela|isso|est[aá] sendo|the|and|your)\b", flags=re.I)


def _mezcla_otro_idioma(txt: str) -> bool:
    return len(OTRO_IDIOMA.findall(txt)) >= 3


def _ruta_cache() -> str:
    return ruta("data", "generado", "cache_llm.json")


def _cache_cargar() -> dict:
    try:
        with open(_ruta_cache(), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _cache_guardar(clave: str, texto: str) -> None:
    c = _cache_cargar()
    c[clave] = texto
    os.makedirs(os.path.dirname(_ruta_cache()), exist_ok=True)
    with open(_ruta_cache(), "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False)


MILES = r"(?:\s*(mil|k|lucas?)\b)?"
NO_ES_MONTO = r"(?!\s*(?:%|por ciento|(?:d[ií]as?|semanas?|mes(?:es)?|a[ñn]os?|cuotas?|horas?)\b))"


def monto_de(pregunta: str) -> float | None:
    """El monto en soles de la frase: el que va con «S/» o «soles» y, si no hay, el primer número que no sea un plazo («en 2 semanas») ni un porcentaje.
    «12mil», «12 mil», «12k» y «12 lucas» son doce mil."""
    hallado = (re.search(rf"s/\.?\s*(\d[\d.,]*){MILES}", pregunta, flags=re.I) or re.search(rf"(\d[\d.,]*){MILES}\s*(?:de )?soles\b", pregunta, flags=re.I)
               or re.search(rf"(\d[\d.,]*)(?![\d.,])(?:\s*(mil|k|lucas?)\b|{NO_ES_MONTO})", pregunta, flags=re.I))
    if not hallado:
        return None
    n = next(iter(numeros_de(hallado.group(1).rstrip(".,"))), None)
    if not n or n <= 0:
        return None
    return n * 1000 if hallado.group(2) else n


MESES_DEL_ANO = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def plazo_de(pregunta: str, hoy) -> tuple[int, str] | None:
    """Meses que faltan para la fecha que nombra la frase y como decirla: «a fin de año», «en 8 meses», «para julio». Sin plazo en la frase devuelve None."""
    t = pregunta.lower()
    m = re.search(r"en (\d+|un|dos|tres|seis) (mes(?:es)?|a[ñn]os?)", t)
    if m:
        n = {"un": 1, "dos": 2, "tres": 3, "seis": 6}.get(m.group(1)) or int(m.group(1))
        n = n * 12 if m.group(2).startswith("a") else n
        return (n, f"en {n} meses") if n > 0 else None
    if re.search(r"fin(?:es)? de a[ñn]o|navidad|a[ñn]o nuevo", t):
        return max(1, 12 - hoy.month + (1 if hoy.day <= 15 else 0)), "a fin de año"
    for i, nombre in enumerate(MESES_DEL_ANO, 1):
        if re.search(rf"\b(?:para|en|hasta|a) {nombre}\b", t) or (nombre == "septiembre" and "setiembre" in t):
            return (i - hoy.month) % 12 or 12, f"para {nombre}"
    return None


# Respuestas que solo se entienden con la pregunta anterior: «sí», «¿y en 6 meses?», «cuesta 12 mil», «para julio»
SEGUIMIENTO = r"^\W*(?:y|s[ií]|ok|okey|dale|ya|bueno|entonces|pero|o sea|osea)\b"
SIN_TEMA = ("general", "fuera_de_tema", "conversacion")   # «sí», «ok», «dale» son conversacion: solos no dicen de que
PALABRAS_DE_UN_DATO = 4


def con_contexto(pregunta: str, previa: str | None) -> str:
    """Si la pregunta es un seguimiento y por si sola no tiene tema, se le pega la anterior DETRAS: así el monto y el plazo nuevos se leen primero
    («¿y si son 8000?» cambia el precio) y el tema sale de la anterior. Una pregunta con tema propio se responde tal cual."""
    if not previa or detectar_intencion(pregunta) not in SIN_TEMA:
        return pregunta
    trae_un_dato = len(pregunta.split()) <= PALABRAS_DE_UN_DATO and (re.search(r"\d", pregunta) or re.search("|".join(MESES_DEL_ANO) + r"|a[ñn]o", pregunta, flags=re.I))
    if re.search(SEGUIMIENTO, pregunta, flags=re.I) or trae_un_dato:
        return f"{pregunta.strip()} {previa.strip()}"
    return pregunta


def detectar_intencion(pregunta: str, evento: dict | None = None) -> str:
    if evento:
        return EVENTO_A_INTENCION.get(evento.get("tipo"), "general")
    for nombre, patron in REGLAS_INTENCION:
        if nombre == "calendario" and re.search(CONCEPTO, pregunta, flags=re.I) and not re.search(PISTA_DE_CALENDARIO, pregunta, flags=re.I):
            continue   # «para que sirve la CTS»: se explica con las fuentes, no con fechas y montos
        if patron == CONCEPTO and re.search(PROGRAMA, pregunta, flags=re.I):
            continue   # «como funciona el programa de puntos»: lo responden los datos del cliente (salud_nivel)
        if nombre == "simular" and monto_de(pregunta) is None:
            continue
        if nombre == "simular" and plazo_de(pregunta, reloj.hoy()) is not None:
            return "meta"
        if re.search(patron, pregunta, flags=re.I):
            return nombre
    if re.search(COMPRA, pregunta, flags=re.I):
        return "compra"
    if re.search(EMOCIONAL, pregunta, flags=re.I):
        return "apoyo"   # solo si ninguna regla de tema aplico: «me preocupa el Nino» sigue siendo una pregunta de El Nino
    if re.search(FINANZAS, pregunta, flags=re.I):
        return "general"
    if re.search(ABIERTO, pregunta, flags=re.I):
        return "conversacion"   # lo vago se acoge con opciones
    if re.search(PREGUNTA_DEL_MUNDO, pregunta, flags=re.I) and not re.search(PERSONAL, pregunta, flags=re.I):
        return "fuera_de_tema"   # una pregunta de cultura general, sin nada de la persona: rechazo amable con opciones
    return "general"   # lo que las reglas no reconocen lo interpreta la IA (si falla o no hay, la plantilla pide aclarar y ofrece opciones): reglas e IA se apoyan, nunca se rechaza por no entender


# ------------------------------------------------------------------ agentes especialistas (solo lectura)
def _a_pronostico(est, repo, **_):
    c = est["ctx"]
    d = {"pronostico_30_dias": {k: (round(v, 2) if isinstance(v, float) else v) for k, v in c["pronostico"].items()}, "saldo_actual": round(c["saldo_actual"], 0)}
    if c["movimientos_vivos"]["n"]:   # lo que entro al aplicativo despues del ultimo cierre de datos
        d["movimientos_recientes"] = {k: c["movimientos_vivos"][k] for k in ("desde", "hasta", "n", "ingresos", "gastos", "neto", "ingresos_por_categoria", "gastos_por_categoria")}
        d["pronostico_reestimado_con_movimientos"] = c["pronostico_reestimado"]
    if c.get("aviso_datos") and est["intencion"] in INTENCIONES_DE_SALDO:   # el aviso solo importa cuando la respuesta habla del saldo; en las demas seria ruido
        d["aviso_datos"] = c["aviso_datos"]
    m = repo.proyeccion_mensual(c["customer_id"]) if hasattr(repo, "proyeccion_mensual") else None
    if m is not None:
        d["proyeccion_mensual"] = m
    return {"pronostico": d}


def _a_salud(est, repo, **_):
    c = est["ctx"]
    f = repo.features.loc[c["customer_id"]]
    ficha = N.ficha(c["nivel"])
    prog = N.progreso(c["nivel"], f, c["salud"])
    pts = c["memoria"]["puntos"]
    programa = {**PP.resumen_para_usuario(c["nivel"]), "por_cada_soles_de_consumo": 10, "por_cada_soles_apartados": 100,   # los dos montos viajan en los datos: toda cifra del texto se puede rastrear
                "como_funciona": "Ganas puntos por conductas sanas: por consumo (con tarjeta o QR, cuando tu caja esta ordenada) y por lo que apartas para ahorrar; no se premia gastar mas. "
                                 "Con tus puntos puedes hacer canjes cuando alcanzas lo necesario para cada uno, y subes de nivel cuando mejoran tu salud financiera y tu colchon."}
    return {"salud": {"salud_financiera": c["salud"], "nivel": ficha["titulo"], "resumen_nivel": ficha["resumen"], "puntos": pts, "canjes_disponibles": [x["nombre"] for x in N.canjes_disponibles(pts)],
                      "lo_que_mas_resta": SA.explicar(f, 2), "para_subir": prog, "programa_de_puntos": programa}}


def _a_clima(est, repo, **_):
    a = RC.alerta_fen(est["ctx"]["departamento"], est["ctx"]["hoy"])
    return {"clima": {"alerta": a} if a else {"sin_alerta": True, "exposicion": RC.exposicion_fen(est["ctx"]["departamento"])["nivel"]}}


def _a_tasas(est, repo, **_):
    """Tasa de referencia del BCRP en vivo (y el tipo de cambio si el cliente paga en dólares). Un dato desactualizado no se presenta como actual."""
    pide_dolar = bool(est["ctx"].get("paga_en_usd")) or bool(re.search(r"d[oó]lar|tipo de cambio", est.get("pregunta", ""), flags=re.I))
    try:
        t = ultimo_con_variacion("tasa_referencia")
        out = dict(t) if t["al_dia"] else {"no_disponible": True, "motivo": "dato desactualizado", "ultimo_dato": {"fecha": t["fecha"], "valor": t["valor"], "origen": t["origen"]}}
    except Exception as e:  # sin red ni cache el agente sigue sin esta herramienta
        out = {"no_disponible": True, "motivo": type(e).__name__}
    if pide_dolar:
        try:
            fx = ultimo_con_variacion("tipo_cambio_venta")
            out["tipo_cambio_venta"] = ({"valor": round(fx["valor"], 3), "fecha": fx["fecha"], "variacion": round(fx["variacion"], 3), "origen": fx["origen"]} if fx["al_dia"]
                                        else {"no_disponible": True, "motivo": "dato desactualizado", "ultimo_dato": {"fecha": fx["fecha"], "valor": round(fx["valor"], 3), "origen": fx["origen"]}})
        except Exception as e:
            out["tipo_cambio_venta"] = {"no_disponible": True, "motivo": type(e).__name__}
    return {"tasas": out}


def _a_calendario(est, repo, **_):
    """Calendario laboral del cliente (gratificación, CTS y regla de retiro de la CTS). Ya viene calculado en su contexto con la fecha del reloj único."""
    return {"calendario": est["ctx"]["calendario"]}


def _a_recomendador(est, repo, **_):
    c = dict(est["ctx"])
    c["tasa_ref"] = est["datos"].get("tasas", {}).get("valor", 4.5)
    c["baja_de_tasa"] = est["datos"].get("tasas", {}).get("variacion", 0) < 0
    if est.get("evento", {}).get("tipo") == "ingreso_extra":
        c["evento_ingreso"] = est["evento"]
    recs = REC.recomendar(c, 3)
    return {"recos": recs}


def _a_simulador(est, repo, **_):
    """Vuelve a puntuar el pronóstico a 30 días con el saldo de hoy menos el gasto que la persona consulta. La cuenta la hace el modelo, nunca el redactor."""
    c = est["ctx"]
    monto = monto_de(est.get("pregunta", ""))
    sin = c["pronostico"]
    vivo = c["movimientos_vivos"]["neto"] if c["pronostico_reestimado"] else 0.0
    con = repo._pronostico(repo.fila_de(c["customer_id"]), vivo - monto)
    return {"simulacion": {"gasto": round(monto, 2), "saldo_esperado_sin_gasto": round(sin["saldo_esperado"], 0), "saldo_esperado_con_gasto": round(con["saldo_esperado"], 0),
                           "saldo_bajo_con_gasto": round(con["saldo_bajo"], 0), "prob_rojo_sin_gasto": round(sin["p_rojo"], 2), "prob_rojo_con_gasto": round(con["p_rojo"], 2),
                           "porcentaje_del_ingreso_mensual": round(100 * monto / max(c["features"]["ingreso_medio"], 1.0), 0), "horizonte_dias": 30}}


def _a_ahorro(est, repo, **_):
    c = est["ctx"]
    f = c["features"]
    meta_colchon = 4.5 if c["tipo_trabajo"] in ("independiente", "mixto") else 3.0
    d = {**repo.ahorro_reciente(c["customer_id"]), "porcentaje_del_ingreso_que_ahorras": round(100 * f["ahorro_pct"], 0), "colchon_en_meses_de_ingreso": round(f["colchon_observado"], 1),
         "colchon_recomendado_en_meses": meta_colchon, "ahorro_por_redondeo_mensual": c["ahorro_redondeo_mensual"]}
    meta = float(repo.clientes.loc[c["customer_id"], "meta_ahorro"])
    if meta > 0:
        d["meta_de_ahorro"] = round(meta, 0)
    return {"ahorro": d}


RUBROS_A_LA_VISTA = 4
LARGO_NOMBRE_META = 40   # el mismo tope que la pantalla Metas
NO_SON_NOMBRE = {"meta", "plan", "mes", "ano", "año", "viaje", "monto", "precio"}


def nombre_de_meta(pregunta: str) -> str:
    """Nombre corto para guardar la meta: «Viaje a Brasil», «Carro», «Laptop». Sale de la frase; si no se reconoce, «Mi meta»."""
    viaje = re.search(r"viaj\w*\s+(?:a|al|por)\s+([A-Za-zÁÉÍÓÚÑáéíóúñ]+)", pregunta)
    if viaje:
        lugar = viaje.group(1)
        return f"Viaje a {lugar[0].upper()}{lugar[1:]}"[:LARGO_NOMBRE_META]
    cosa = re.search(r"(?:comprar(?:me|lo)?|pagar(?:me)?|para)\s+(?:un|una|el|la|mi|mis)\s+([a-záéíóúñ]+)", pregunta, flags=re.I)
    if cosa and cosa.group(1).lower() not in NO_SON_NOMBRE:
        return cosa.group(1).capitalize()[:LARGO_NOMBRE_META]
    return "Viaje" if re.search(r"viaj", pregunta, flags=re.I) else "Mi meta"


def _sumar_meses(d, meses: int):
    import calendar
    from datetime import date

    anio, mes = divmod(d.month - 1 + meses, 12)
    anio += d.year
    return date(anio, mes + 1, min(d.day, calendar.monthrange(anio, mes + 1)[1]))


def _a_gastos(est, repo, **_):
    c = est["ctx"]
    g = repo.gastos_del_mes(c["customer_id"])
    d, h = g["desde"], g["hasta"]
    rubros = g["por_rubro"][:RUBROS_A_LA_VISTA]
    resto = round(sum(r["soles"] for r in g["por_rubro"][RUBROS_A_LA_VISTA:]), 0)
    return {"gastos": {"periodo": f"del {d.day} al {h.day} de {MESES_DEL_ANO[h.month - 1]} de {h.year}", "total": g["total"], "movimientos": g["movimientos"], "rubros": rubros,
                       "resto": resto, "mismo_tramo_mes_anterior": g["mismo_tramo_mes_anterior"], "diferencia": round(g["total"] - g["mismo_tramo_mes_anterior"], 0),
                       "apartado": g["apartado"], "datos_de_otra_fecha": c["desfase_datos_dias"] > VENTANA_DATOS_DIAS}}


RECORTE_HORMIGA = 0.5   # supuesto visible del plan: bajar a la mitad los gastos pequenos (delivery, antojos)


def _a_meta(est, repo, **_):
    """Plan para una meta: de donde parte la persona, que ajustes le suman, que convenio del banco aplica y los números finales.
    Todas las cuentas se hacen aquí con sus datos; el redactor solo las cuenta."""
    from datetime import date

    c, pregunta = est["ctx"], est.get("pregunta", "")
    f, hoy = c["features"], date.fromisoformat(c["hoy"])
    gasto = round(f["gasto_sobre_ingreso"] * f["ingreso_medio"], 0)
    aparta = repo.ahorro_reciente(c["customer_id"])["apartado_promedio_mensual"]
    ajustes = [{"que": "Bajar a la mitad tus gastos hormiga (delivery y antojos)", "soles_al_mes": round(RECORTE_HORMIGA * f["pct_hormiga"] * gasto, 0)},
               {"que": "Cancelar la suscripción que pagas dos veces", "soles_al_mes": round(c["monto_duplicada"], 0) if c["duplicadas"] else 0.0},
               {"que": "Activar el redondeo de tus gastos", "soles_al_mes": float(c["ahorro_redondeo_mensual"])}]
    ajustes = [a for a in ajustes if a["soles_al_mes"] >= 10]
    capacidad = aparta + sum(a["soles_al_mes"] for a in ajustes)
    d = {"ingreso_mensual": round(f["ingreso_medio"], 0), "gasto_mensual": gasto, "apartas_hoy_por_mes": aparta, "ajustes": ajustes, "podrias_apartar_por_mes": capacidad, "convenio": None}
    conv = CA.campana_para(pregunta, hoy)
    if conv:
        d["convenio"] = {"aliado": conv["aliado"], "beneficio": CA.beneficio(conv), "rubro": conv["rubro"], "condicion": conv["condicion"], "aplica": conv["aplica"], "motivo": conv["motivo"],
                         "vigente_hasta": CL.texto_fecha(date.fromisoformat(conv["hasta"]))}
    monto = monto_de(pregunta)
    if monto:
        rebaja = CA.descuento(conv, monto) if conv else 0.0
        a_juntar = monto - rebaja
        meses, cuando = plazo_de(pregunta, hoy) or (None, None)
        d["numeros"] = {"precio": round(monto, 0), "descuento": rebaja, "a_juntar": a_juntar, "meses_pedidos": meses, "cuando": cuando, "por_mes_pedido": float(-(-a_juntar // meses)) if meses else None,
                        "meses_con_el_plan": int(-(-a_juntar // capacidad)) if capacidad > 0 else None}
        # Lo que la app guarda si la persona acepta: el monto a juntar y la fecha. El aporte de cada cobro lo recalcula la app con su propio pronostico.
        plazo_meses = meses or d["numeros"]["meses_con_el_plan"]
        if plazo_meses:
            fecha = date(hoy.year, 12, 31) if cuando == "a fin de año" else _sumar_meses(hoy, plazo_meses)
            d["propuesta"] = {"nombre": nombre_de_meta(pregunta), "objetivo": a_juntar, "fecha": fecha.isoformat()}
    else:
        d["numeros"] = {"precio": None, "juntarias_en_6_meses": capacidad * 6, "juntarias_en_12_meses": capacidad * 12}
    return {"meta": d}


def _a_ofertas(est, repo, **_):
    """Ofertas del catálogo de demostración con su idoneidad. Lo que no es idoneo se muestra con su razón, no se esconde."""
    c = dict(est["ctx"])
    c["tasa_ref"] = est["datos"].get("tasas", {}).get("valor", 4.5)
    ofertas = [o for o in O.ofertas_por_perfil(c, c.get("top_categorias")) if o["familia"] != "consumir"]
    sin = next((nombre for nombre, patron in SIN_PRODUCTO.items() if re.search(patron, est.get("pregunta", ""), flags=re.I)), None)
    return {"ofertas": {"no_hay_en_el_catalogo": sin, "idoneas": [{"producto": o.get("tipo_producto", o["familia"]), "accion": o["accion"], "por_que": o["por_que"][0]} for o in ofertas if o["idoneo"]],
                        "todavia_no": [{"producto": o.get("tipo_producto", o["familia"]), "accion": o["accion"], "por_que": o["razones_no_idoneo"][0]} for o in ofertas if not o["idoneo"]]}}


def _a_educador(est, repo, buscador=None, **_):
    if buscador is None:
        return {"rag": [], "rag_estado": "sin_indice"}
    modulo = MODULOS_RAG.get(est["intencion"])
    r = buscador.buscar(est["pregunta"], k=3, modulo=modulo, modo="denso")
    mejor = r[0]["similitud"] if r else 0.0
    # filtro tipo CRAG: si ni el mejor fragmento es relevante, no se le pasa nada al redactor
    if mejor < UMBRAL_RELEVANCIA:
        return {"rag": [], "rag_estado": f"sin_evidencia (mejor similitud {mejor:.2f})"}
    return {"rag": r, "rag_estado": "correcto"}


AGENTES = {"pronostico": _a_pronostico, "salud": _a_salud, "clima": _a_clima, "tasas": _a_tasas, "calendario": _a_calendario, "recomendador": _a_recomendador, "educador": _a_educador, "simulador": _a_simulador, "ahorro": _a_ahorro, "ofertas": _a_ofertas, "meta": _a_meta, "gastos": _a_gastos}
DEPENDENCIAS = {"recomendador": ["pronostico", "salud", "clima", "tasas"], "ofertas": ["tasas"]}


# ------------------------------------------------------------------ redaccion y juez
def _aviso_de_origen(r: dict, mayus: bool = False) -> str:
    """Una fuente de otro pais es una guia orientativa, no la norma peruana: se avisa en el dato para el LLM y en la plantilla."""
    ctx = r.get("contexto", "Peru")
    if ctx == "Peru":
        return ""
    quien = "internacional" if ctx == "internacional" else f"de {ctx}"
    return f" GUIA {quien.upper()} (orientativa, no es norma peruana)" if mayus else f" [guia {quien}, orientativa: no es norma peruana]"


def _datos_texto(est) -> str:
    L = []
    d = est["datos"]
    c = est["ctx"]
    L.append(f"Nivel: {d.get('salud', {}).get('nivel', N.ficha(c['nivel'])['titulo'])}. Tono: {N.ficha(c['nivel'])['tono']}.")
    for k, v in d.items():
        L.append(f"{k}: {v}")
    for i, r in enumerate(est.get("recos", [])[:3], 1):
        L.append(f"recomendación {i}: {r['accion']} Impacto: {r['impacto_soles']}. Por que: {'; '.join(r['por_que'])}. Supuestos: {'; '.join(r['supuestos'])}. Confianza: {r['confianza']}.")
    for r in est.get("rag", [])[:3]:
        L.append(f"fuente [{r['titulo']}, pag. {r['pagina']}]{_aviso_de_origen(r, mayus=True)}: {r['texto'][:600]}")
    return "\n".join(L)


def _permitidos(est) -> set:
    p = aplanar(est["datos"]) | aplanar(est.get("recos", [])) | set(numeros_de(est.get("pregunta", "")))
    for r in est.get("rag", []):
        p |= aplanar(r["texto"]) | {float(r["pagina"])} | aplanar(r.get("titulo", ""))   # el titulo citado (p. ej. «Ley 29571») tambien se le muestra a la persona
    if est.get("evento"):
        p |= aplanar(est["evento"])
    return p


PALABRAS_VACIAS = {"cual", "cuales", "como", "cuando", "donde", "puedo", "tengo", "para", "sobre", "tiene", "hacer", "mismo", "esto", "esta", "este", "unos", "unas", "algo", "quien", "porque", "entre"}


def extracto(texto: str, pregunta: str, limite: int = 360) -> str:
    """Frases completas del fragmento, empezando por la qué más se parece a la pregunta (comparte una sigla o una palabra de más de 3 letras). Nunca empieza a mitad de frase ni corta una cifra."""
    frases = [f.strip(" .;:-") for f in re.split(r"(?<=[.;:])\s+", re.sub(r"\s+", " ", texto))]
    frases = [f for f in frases if len(f) > 25]
    if not frases:
        return re.sub(r"\s+", " ", texto)[:limite].rsplit(" ", 1)[0].strip()
    claves = {p for p in re.findall(r"\w+", pregunta.lower()) if len(p) > 3 and p not in PALABRAS_VACIAS}
    puntaje = [sum(c in f.lower() for c in claves) for f in frases]
    inicio = max(range(len(frases)), key=lambda i: (puntaje[i], -i))
    salida = ""
    for f in frases[inicio:]:
        if salida and len(salida) + len(f) > limite:
            break
        salida = f"{salida}. {f}" if salida else f
    if len(salida) > limite:   # una sola frase muy larga: se corta en una palabra, nunca dentro de un numero
        salida = salida[:limite].rsplit(" ", 1)[0].rstrip(" ,;:(") + "..."
    return salida if salida.endswith("...") else salida + "."


def _soles(v: float) -> str:
    return f"{'-' if v < 0 else ''}S/ {abs(v):,.0f}"


def _lineas_simulacion(s: dict) -> list[str]:
    L = [f"Con ese gasto de {_soles(s['gasto'])}, en {s['horizonte_dias']} días tu saldo rondaría {_soles(s['saldo_esperado_con_gasto'])} en vez de {_soles(s['saldo_esperado_sin_gasto'])}.",
         f"En un mes malo podría bajar hasta {_soles(s['saldo_bajo_con_gasto'])}."]
    if s["prob_rojo_con_gasto"] >= 0.15:
        L.append(f"Riesgo de quedar en rojo: {s['prob_rojo_con_gasto']:.0%}. Conviene esperar a tu próximo ingreso o bajar el monto.")
    elif s["saldo_bajo_con_gasto"] < 0:
        L.append("El riesgo de quedar en rojo es bajo, pero en un mes malo sí quedarías en negativo.")
    else:
        L.append("El pronóstico no marca riesgo de quedar en rojo.")
    return L


def _lineas_gastos(g: dict) -> list[str]:
    periodo = g["periodo"][0].upper() + g["periodo"][1:]
    L = ["## Este mes", f"{periodo} gastaste {_soles(g['total'])} en {g['movimientos']} movimientos."]
    if g["mismo_tramo_mes_anterior"] and abs(g["diferencia"]) >= 1:
        L.append(f"Son {_soles(abs(g['diferencia']))} {'más' if g['diferencia'] > 0 else 'menos'} que a esta altura del mes pasado ({_soles(g['mismo_tramo_mes_anterior'])}).")
    if g["apartado"]:
        L.append(f"Además apartaste {_soles(g['apartado'])} para ahorrar, que no cuenta como gasto.")
    if g["datos_de_otra_fecha"]:
        L.append("Tus movimientos de demostración llegan hasta esa fecha.")
    if g["rubros"]:
        L += ["", "## En qué se fue", *[f"- {r['rubro']}: {_soles(r['soles'])}" for r in g["rubros"]]]
        if g["resto"]:
            L.append(f"- Lo demás: {_soles(g['resto'])}")
    return L


def _lineas_meta(m: dict) -> list[str]:
    """Cuatro bloques separados por una línea en blanco (el chat pinta cada uno en su propio mensaje): punto de partida, que hacer, convenio y números."""
    L = ["## Tu punto de partida", f"Ganas unos {_soles(m['ingreso_mensual'])} al mes y gastas {_soles(m['gasto_mensual'])}.",
         f"Hoy apartas {_soles(m['apartas_hoy_por_mes'])} al mes." if m["apartas_hoy_por_mes"] > 0 else "En los últimos meses no apartaste nada."]
    if m["ajustes"]:
        L += ["", "## Lo que puedes hacer", *[f"- {a['que']}: +{_soles(a['soles_al_mes'])} al mes" for a in m["ajustes"]], f"Con eso apartarías {_soles(m['podrias_apartar_por_mes'])} al mes."]
    cv = m["convenio"]
    if cv:
        L += ["", "## Convenio del banco", f"{cv['aliado']}: {cv['beneficio']} en {cv['rubro']}, {cv['condicion']}."]
        L.append(f"Vale hasta el {cv['vigente_hasta']}." if cv["aplica"] else f"Para lo que buscas no aplica: {cv['motivo']}.")
        L.append("Es un convenio de ejemplo.")
    n = m["numeros"]
    L += ["", "## Los números"]
    if n["precio"] is None:
        if m["podrias_apartar_por_mes"] > 0:
            L.append(f"A ese ritmo juntarías {_soles(n['juntarias_en_6_meses'])} en 6 meses y {_soles(n['juntarias_en_12_meses'])} en 12 meses.")
        L.append("Dime cuánto cuesta y para cuándo, y cierro los números.")
        return L
    L.append(f"- Precio: {_soles(n['precio'])}")
    if n["descuento"]:
        L += [f"- Descuento con {cv['aliado']}: -{_soles(n['descuento'])}", f"- Te toca juntar: {_soles(n['a_juntar'])}"]
    if n["meses_pedidos"]:
        alcanza = m["podrias_apartar_por_mes"] >= n["por_mes_pedido"]
        L.append(f"Para tenerlo {n['cuando']} necesitas {_soles(n['por_mes_pedido'])} al mes: {'con el plan sí llegas' if alcanza else 'con el plan no alcanza'}.")
        if alcanza:
            return L
    if n["meses_con_el_plan"]:
        L.append(f"Apartando {_soles(m['podrias_apartar_por_mes'])} al mes llegas en {n['meses_con_el_plan']} meses.")
    else:
        L.append("Hoy no te queda margen para apartar: primero hay que bajar gastos.")
    return L


def _lineas_ahorro(a: dict) -> list[str]:
    if not a["meses"]:
        return ["Todavía no tengo meses completos de tus movimientos para resumir tu ahorro."]
    L = [f"En los últimos {a['meses']} meses apartaste {_soles(a['apartado_total'])}, unos {_soles(a['apartado_promedio_mensual'])} al mes." if a["apartado_total"] > 0
         else f"En los últimos {a['meses']} meses no apartaste nada."]
    falta = a["colchon_en_meses_de_ingreso"] < a["colchon_recomendado_en_meses"]
    L.append(f"- Colchón: {a['colchon_en_meses_de_ingreso']:.1f} meses de ingreso ({'te falta para' if falta else 'ya pasaste'} los {a['colchon_recomendado_en_meses']:.1f} recomendados).")
    if a.get("meta_de_ahorro"):
        L.append(f"- Meta registrada: {_soles(a['meta_de_ahorro'])}.")
    if a["ahorro_por_redondeo_mensual"]:
        L.append(f"- Con el redondeo de tus gastos sumarías unos {_soles(a['ahorro_por_redondeo_mensual'])} al mes.")
    return L


MAX_OFERTAS = 2


def _lineas_ofertas(o: dict) -> list[str]:
    L = []
    if o["no_hay_en_el_catalogo"]:
        L.append(f"En el catálogo de demostración no hay {o['no_hay_en_el_catalogo']}.")
    if o["idoneas"]:
        L.append("Lo que hoy sí calza con tu perfil:")
        L += [f"- {x['accion']}" for x in o["idoneas"][:MAX_OFERTAS]]
    if o["todavia_no"]:
        L.append("Todavía no te conviene:")
        L += [f"- {x['accion']}" for x in o["todavia_no"][:1]]
    if not o["idoneas"] and not o["todavia_no"]:
        L.append("Hoy no tengo una oferta del catálogo que calce con tu perfil.")
    return L


# Que partes de lo que se sabe del cliente contesta cada pregunta. Sin esto la plantilla contaba todo (clima, tasa, salud) en cualquier respuesta.
SECCIONES = {"pronostico": {"pronostico"}, "calendario": {"calendario"}, "salud_nivel": {"salud"}, "recomendaciones": {"recos"}, "general": {"pronostico", "recos"}, "fen": {"clima", "recos", "rag"},
             "tasas": {"tasas", "rag"}, "tipo_de_cambio": {"tasas"}, "educacion": {"rag"}}
RECOS_POR_INTENCION = {"recomendaciones": 3, "general": 2, "fen": 1}
PIDE_PROYECCION = r"ingres|ganar|gastar|meses|mes que viene"
def _opciones(est) -> list:
    """Opciones de respuesta rapida (botones) segun el contexto de la persona: lo que mas le conviene mirar primero. Cada una trae la pregunta que se envia si la toca."""
    c = est["ctx"]
    ops = []

    def add(id_, texto, pregunta):
        ops.append({"id": id_, "texto": texto, "pregunta": pregunta})
    if c["pronostico"]["p_rojo"] >= 0.15:
        add("riesgo_rojo", "Mi riesgo de quedar en rojo", "¿Voy a quedar en rojo este mes?")
    else:
        add("pronostico", "¿Llego a fin de mes?", "¿Llego a fin de mes con mi plata?")
    cal = c.get("calendario") or {}
    if cal.get("aplica") and cal.get("eventos") and cal["eventos"][0].get("dias_para", 99) <= 45:
        add("calendario", "Mi CTS y mi gratificación", "¿Cuándo me cae la CTS y puedo retirarla?")
    add("recomendaciones", "Ideas para ahorrar y gastar mejor", "¿Qué me recomiendas hacer con mi plata este mes?")
    add("salud_nivel", "Mi salud financiera y mi nivel", "¿En qué nivel estoy y cómo está mi salud financiera?")
    if RC.alerta_fen(c["departamento"], c["hoy"]):
        add("fen", "El Niño en mi zona", "¿Estoy en riesgo por el Fenómeno El Niño y qué hago para prepararme?")
    add("educacion", "Entender mis derechos y mis deudas", "¿Qué derechos tengo si me atraso en un pago?")
    return ops[:4]


def _menu(ops: list) -> str:
    return " • ".join(o["texto"] for o in ops)   # sin numeros: el verificador de cifras los tomaria por montos


def _plantilla_conversacional(est, intent: str) -> str:
    """Saludo, mensaje abierto, emocion o algo que no se entendio: se acoge con calidez y se ofrecen opciones en vez de rechazar. Sin cifras; sin LLM."""
    titulo = N.ficha(est["ctx"]["nivel"])["titulo"]
    texto = (est.get("pregunta") or "").lower()
    menu = _menu(_opciones(est))
    if intent == "apoyo":
        return (f"Siento que estes pasando por eso, {titulo}, y gracias por contarmelo: aqui estoy para ayudarte paso a paso y sin juzgarte. "
                f"Para ayudarte mejor, ¿con cual de estas quieres empezar? {menu} O cuentame un poco mas con tus palabras. Tu decides.")
    if re.search(DESPEDIDA, texto):
        return f"¡Hasta pronto, {titulo}! Cuando quieras volver a revisar tu plata, aqui estare. Tu decides."
    if "gracias" in texto:
        return f"¡Con gusto, {titulo}! ¿Quieres revisar algo mas? {menu} Tu decides."
    if intent == "general":
        return (f"Quiero ayudarte, {titulo}, pero no estoy seguro de haber entendido bien lo que necesitas. ¿Es alguna de estas? {menu} "
                f"O cuentame con otras palabras y lo vemos juntos. Tu decides.")
    return (f"¡Hola, {titulo}! Soy Lucas, tu copiloto de plata. Cuentame con confianza que te gustaria revisar o que te preocupa; si prefieres, elige una opcion: {menu} "
            f"¿Por donde empezamos? Tu decides.")


def plantilla(est) -> str:
    c, d, intent = est["ctx"], est["datos"], est["intencion"]
    ficha = N.ficha(c["nivel"])
    L = [f"Hola, {ficha['titulo']}."]
    ev = est.get("evento") or {}
    if ev.get("tipo") == "ingreso_extra":
        L.append(f"Vemos que recibiste S/ {ev['monto']:,.0f} por {ev['origen']}.")
    elif ev.get("tipo") == "baja_de_tasa":
        L.append(f"La tasa de referencia del BCRP bajó de {ev['desde']:.2f}% a {ev['hasta']:.2f}%.")
    elif ev.get("tipo") == "fen_comunicado":
        L.append(f"El ENFEN público el comunicado N.o {ev['numero']}.")
    elif ev.get("tipo") == "riesgo_rojo":
        L.append(f"Tu saldo podría quedar en rojo: la probabilidad es {ev['p_rojo']:.0%}.")
    elif ev.get("tipo") == "calendario_laboral":
        e = ev["evento"]
        L.append(f"Se acerca una fecha de tu calendario laboral: {e['nombre']} ({'hoy' if e['dias_para'] == 0 else f'en {e['dias_para']} días'}).")
    elif ev.get("tipo") == "libre_disposicion_por_vencer":
        L.append(f"Te quedan {ev['dias_restantes']} días para disponer del 100 % de tu CTS.")
    elif ev.get("tipo") == "gratificacion_pendiente":
        L.append(f"Aún no vemos tu {ev['nombre']}, que tu empleador debia pagar hasta el {ev['fecha_limite_texto']}.")
    elif ev.get("tipo") == "gasto_atipico":
        L.append(f"Registramos un gasto de S/ {ev['monto']:,.0f} en {ev['categoria']}: pesa {ev['fraccion_del_ingreso']:.0%} de tu ingreso mensual.")
    if intent in SIN_LLM:
        motivo = {"fuera_de_alcance": "Eso no lo hago: no muevo dinero, no compro ni vendo dólares y no te digo en qué invertir.",
                  "fuera_de_tema": "De eso no puedo ayudarte: solo veo temas de tu plata.",
                  "seguridad": "Eso no lo puedo hacer: no comparto instrucciones internas, claves ni información de otras personas, y mis reglas no se pueden saltar."}.get(intent)
        if intent == "compra":
            return f"{L[0]}\n¿Cuánto cuesta y para cuándo lo quieres?\nCon el precio te digo cómo quedaría tu saldo o cuánto apartar al mes para llegar. Tu decides."
        extra = "" if intent == "seguridad" else f" Si prefieres, elige una opcion: {_menu(_opciones(est))}"
        return f"{L[0]} {motivo}\n{AYUDO_EN}{extra} Tu decides."
    if intent in ("conversacion", "apoyo") or (intent == "general" and est.get("pregunta") and not est.get("evento")):
        return _plantilla_conversacional(est, intent)
    if intent == "simular":
        return "\n".join([L[0], *_lineas_simulacion(d["simulacion"]), "Es una simulación, no una asesoría. Tu decides."])
    if intent == "gastos":
        return "\n".join([L[0], *_lineas_gastos(d["gastos"]), "Tu decides."])
    if intent == "meta":
        guardar = ["", "¿La guardo en tus metas? Así te recuerdo cuánto apartar cada vez que cobres."] if d["meta"].get("propuesta") else []
        return "\n".join([L[0], *_lineas_meta(d["meta"]), *guardar, "Tu decides."])
    if intent == "ahorro":
        return "\n".join([L[0], *_lineas_ahorro(d["ahorro"]), "Tu decides."])
    if intent == "ofertas":
        return "\n".join([L[0], *_lineas_ofertas(d["ofertas"]), "Es un catálogo de demostración, no una oferta real. Tu decides."])
    ver = None if ev else SECCIONES.get(intent)   # un aviso proactivo conserva todo su contexto

    def muestra(seccion: str) -> bool:
        return ver is None or seccion in ver

    if "pronostico" in d and muestra("pronostico"):
        p = d["pronostico"]["pronostico_30_dias"]
        mv = d["pronostico"].get("movimientos_recientes")
        if mv:
            L.append(f"Desde el {mv['desde']} entraron S/ {mv['ingresos']:,.0f} y salieron S/ {mv['gastos']:,.0f}; tu saldo de hoy ronda S/ {d['pronostico']['saldo_actual']:,.0f}.")
        L.append(f"En 30 días esperamos que tu saldo ronde S/ {p['saldo_esperado']:,.0f}, con un rango entre S/ {p['saldo_bajo']:,.0f} y S/ {p['saldo_alto']:,.0f}.")
        if p["p_rojo"] >= 0.15:
            L.append(f"Hay una probabilidad de {p['p_rojo']:.0%} de quedar en rojo{f' hacia el día {int(p['dia_riesgo'])}' if p.get('dia_riesgo') else ''}.")
        m = d["pronostico"].get("proyeccion_mensual")
        if m and (ver is None or re.search(PIDE_PROYECCION, est.get("pregunta", ""), flags=re.I)):
            f0 = m[0]
            L.append(f"Para {f0['mes']} estimamos ingresos de S/ {f0['ingreso_esperado']:,.0f} (entre S/ {f0['ingreso_bajo']:,.0f} y S/ {f0['ingreso_alto']:,.0f}) y gastos de S/ {f0['gasto_esperado']:,.0f}.")
        if d["pronostico"].get("aviso_datos"):
            L.append(d["pronostico"]["aviso_datos"])
    if "calendario" in d and muestra("calendario"):
        cal = d["calendario"]
        if not cal.get("aplica"):
            L.append(cal["motivo"])
        else:
            for e in cal["eventos"][:2]:
                m = e["monto_estimado"]
                if e["tipo"] == "gratificacion":
                    L.append(f"{e['nombre']}: tu empleador la paga hasta el {e['fecha_limite_texto']} (en {e['dias_para']} días). Estimamos S/ {m['gratificacion']:,.0f} más S/ {m['bonificacion_extraordinaria']:,.0f} de bonificación extraordinaria, en total S/ {m['total']:,.0f}.")
                else:
                    L.append(f"{e['nombre']}: tu empleador debe depositarla hasta el {e['fecha_limite_texto']}. Estimamos S/ {m['deposito_semestral']:,.0f}. Llega a tu cuenta de CTS, no a tu cuenta de sueldo.")
            L.append(f"Son estimaciones con {'tu última gratificación' if cal['base_origen'] == 'historial' else 'tu ingreso medio (supuesto)'}: confirma el monto exacto con tu empleador.")
        ld = cal["libre_disposicion_cts"]
        if ld["regimen_transitorio_vigente"]:
            L.append(f"Sobre retirar tu CTS: hasta el {ld['vigente_hasta_texto']} puedes disponer del 100 % de lo depositado en entidades financieras ({ld['fuente']}); después, solo hasta el 50 %. "
                     f"La CTS es una protección para cuando termina tu trabajo: retira solo lo que de verdad necesites. {ld['nota_proyectos']}")
        else:
            L.append(f"Sobre retirar tu CTS: hoy puedes disponer libremente de hasta el 50 % de lo depositado ({ld['fuente']}); con enfermedad terminal o cáncer acreditados, del 100 %.")
        if cal.get("reglas_por_revisar"):
            L.append(f"Estas reglas se contrastaron con su fuente el {cal['reglas_verificadas_el']}: conviene volver a verificarlas.")
    if "salud" in d and muestra("salud"):
        s = d["salud"]
        L.append(f"Tu salud financiera es {s['salud_financiera']:.0f} de 100 y tu nivel es {s['nivel']}.")
        if s["lo_que_mas_resta"]:
            r0 = s["lo_que_mas_resta"][0]
            L.append(f"Lo que más la baja es {r0['que_mide']}.")
        if s["para_subir"].get("faltantes"):
            fa = s["para_subir"]["faltantes"][0]
            L.append(f"Para subir a {s['para_subir']['siguiente']} te falta mejorar {fa['que']}: hoy tienes {fa['tienes']} y necesitas {fa['necesitas']}.")
        if s["puntos"]:
            L.append(f"Llevas {s['puntos']} puntos.")
        pg = s.get("programa_de_puntos")
        if pg and intent == "salud_nivel":   # la pregunta es del programa: se explica como funciona en SU nivel, con las reglas del catalogo
            consumo = (f" y {pg['puntos_por_cada_10_soles_de_consumo']:g} por cada S/ {pg['por_cada_soles_de_consumo']} de consumo con tarjeta o QR, siempre que tu caja este ordenada." if pg["el_consumo_suma_puntos"] else f". {pg['nota']}")
            L.append(f"En tu nivel ganas {pg['puntos_por_cada_100_soles_apartados']:g} puntos por cada S/ {pg['por_cada_soles_apartados']} que apartas{consumo}")
            L.append("Beneficios de tu nivel: " + "; ".join(pg["beneficios"]) + ".")
    if "clima" in d and d["clima"].get("alerta") and muestra("clima"):
        a = d["clima"]["alerta"]
        L.append(f"Alerta: tu zona ({a['departamento']}) tiene exposición {a['nivel']} a lluvias por El Niño según el ENFEN. Acciones: {' '.join(a['acciones'][:3])}")
    if "tasas" in d and muestra("tasas"):
        t = d["tasas"]
        if not t.get("no_disponible") and "valor" in t and intent != "tipo_de_cambio":
            L.append(f"La tasa de referencia del BCRP está en {t['valor']:.2f}% ({'bajo' if t['variacion'] < 0 else 'subio' if t['variacion'] > 0 else 'sin cambio'} {abs(t['variacion']):.2f} puntos frente al mes anterior).")
        fx = t.get("tipo_cambio_venta")
        if fx and not fx.get("no_disponible"):
            L.append(f"El tipo de cambio interbancario (venta) del BCRP es S/ {fx['valor']:.3f} por dólar al {fx['fecha']} ({'bajo' if fx['variacion'] < 0 else 'subio' if fx['variacion'] > 0 else 'sin cambio'} S/ {abs(fx['variacion']):.3f} frente al día anterior). "
                     f"Es solo un dato de referencia, no una recomendación de operar con dólares.")
        elif fx:
            L.append("No pude traer el tipo de cambio actualizado del BCRP, así que prefiero no darte un dato viejo.")
    for r in est.get("recos", [])[:3 if ver is None else RECOS_POR_INTENCION.get(intent, 0)]:
        imp = f" Impacto estimado: S/ {r['impacto_soles']:,.0f}." if r.get("impacto_soles") else ""
        L.append(f"- {r['accion']}{imp} Por que: {r['por_que'][0]}.")
    if est.get("rag"):
        r0 = est["rag"][0]
        ex = extracto(r0["texto"], est.get("pregunta", ""))
        claves = {w for w in re.findall(r"[a-zñáéíóú]{4,}", (est.get("pregunta") or "").lower()) if w not in PALABRAS_VACIAS}
        comunes = claves & set(re.findall(r"[a-zñáéíóú]{4,}", ex.lower()))   # palabras de la pregunta que de verdad aparecen en la frase que se cita
        if r0.get("similitud", 1.0) >= 0.75 or len(comunes) >= 2:
            L.append(f"Segun {r0['titulo']} (pag. {r0['pagina']}){_aviso_de_origen(r0)}: {ex}")
        else:   # la fuente se parece pero no responde con claridad: mejor decirlo que citar una frase suelta
            L.append(f"Encontre una fuente relacionada ({r0['titulo']}, pag. {r0['pagina']}), pero no responde con claridad a tu pregunta, asi que prefiero no inventar una respuesta.")
    elif est.get("rag_estado", "").startswith("sin_evidencia") and muestra("rag"):
        L.append("Sobre eso no encuentro información en las fuentes que tengo, así que prefiero no inventarla.")
    L.append("Tu decides.")
    return " ".join(L) if len(L) < 3 else "\n".join(L)


def construir_grafo(repo, buscador=None, modo: str = "agente_unico", usar_juez_llm: bool | None = None):
    cargar_env()
    if usar_juez_llm is None:
        usar_juez_llm = os.environ.get("JUEZ_LLM", "0") == "1"
    ent_nombre = cargar_yaml("entidad.yaml")["entidad"]["nombre"]

    def cargar(est):
        ctx = repo.contexto(est["customer_id"])
        return {"ctx": ctx, "datos": {}, "recos": [], "rag": [], "rag_estado": "no_aplica", "trazas": ["cargar_contexto"], "intentos": 0, "llamadas_llm": 0, "t0": time.time()}

    def traducir_entrada(est):
        """Detecta el idioma del usuario (o usa el elegido) y lleva la pregunta al espanol, que es el idioma del router y del RAG."""
        pref = est["ctx"]["memoria"].get("preferencias", {}).get("idioma")
        idioma = est.get("idioma") or pref or (TR.detectar_idioma(est["pregunta"]) if est.get("pregunta") else "es")
        if idioma == "es" or not est.get("pregunta"):
            return {"idioma": idioma, "trazas": est["trazas"] + [f"idioma:{idioma}"]}
        r = TR.traducir(est["pregunta"], idioma, "es")
        upd = {"idioma": idioma, "traduccion": {"entrada": r}, "trazas": est["trazas"] + [f"idioma:{idioma}->es:{'ok' if r['ok'] else 'fallo'}({r['proveedor']})"]}
        if r["ok"]:
            upd.update({"pregunta_original": est["pregunta"], "pregunta": r["texto"]})
        return upd

    def traducir_salida(est):
        idioma = est.get("idioma", "es")
        if idioma == "es":
            return {}
        r = TR.traducir(est["respuesta"], "es", idioma)
        texto = (r["texto"] + chr(10) + TR.AVISO.get(idioma, "")) if r["ok"] else (est["respuesta"] + chr(10) + TR.NOTA_FALLO.get(idioma, ""))
        return {"respuesta_es": est["respuesta"], "respuesta": texto, "traduccion": {**est.get("traduccion", {}), "salida": r},
                "trazas": est["trazas"] + [f"es->{idioma}:{'ok' if r['ok'] else 'fallo'}({r['proveedor']})"]}

    def router(est):
        intent = detectar_intencion(est.get("pregunta", ""), est.get("evento"))
        ajenos = [i for i in re.findall(r"\bC\d{5}\b", est.get("pregunta", "")) if i != est["customer_id"]]
        if ajenos:  # el agente solo habla de la informacion de quien pregunta
            intent = "seguridad"
        return {"intencion": intent, "pendientes": list(PLAN[intent]), "trazas": est["trazas"] + [f"router:{intent}"]}

    def herramientas(est):  # modo agente unico: ejecuta el plan en orden, resolviendo dependencias sin conversacion entre agentes
        e = dict(est)
        orden = []
        for a in est["pendientes"]:
            for dep in DEPENDENCIAS.get(a, []):
                if dep not in orden:
                    orden.append(dep)
            if a not in orden:
                orden.append(a)
        trazas = list(est["trazas"])
        for a in orden:
            if a in ("pronostico", "salud", "clima", "tasas", "calendario") and a in e["datos"]:
                continue
            upd = AGENTES[a](e, repo, buscador=buscador)
            for k, v in upd.items():
                if k in ("recos", "rag", "rag_estado"):
                    e[k] = v
                else:
                    e["datos"] = {**e["datos"], k: v}
            trazas.append(f"agente:{a}")
        return {"datos": e["datos"], "recos": e.get("recos", []), "rag": e.get("rag", []), "rag_estado": e.get("rag_estado", "no_aplica"), "trazas": trazas, "pendientes": []}

    def supervisor(est):
        pend = list(est["pendientes"])
        sig = pend.pop(0) if pend else "redactar"
        return {"pendientes": pend, "siguiente": sig, "trazas": est["trazas"] + [f"supervisor->{sig}"]}

    def agente_nodo(nombre):
        def nodo(est):
            faltan = [a for a in DEPENDENCIAS.get(nombre, []) if a not in est["datos"]]
            if faltan:  # el agente pide datos a sus pares (por medio del supervisor) y vuelve despues
                return {"pendientes": faltan + [nombre] + est["pendientes"], "trazas": est["trazas"] + [f"{nombre} solicita a {','.join(faltan)}"]}
            upd = AGENTES[nombre](est, repo, buscador=buscador)
            out = {"trazas": est["trazas"] + [f"agente:{nombre}"]}
            for k, v in upd.items():
                if k in ("recos", "rag", "rag_estado"):
                    out[k] = v
                else:
                    out["datos"] = {**est["datos"], **out.get("datos", {}), k: v}
            return out
        return nodo

    def redactar(est):
        if est["intencion"] in SIN_LLM:
            return {"usar_plantilla": True, "trazas": est["trazas"] + ["redactar:plantilla_por_alcance"]}
        if os.environ.get("LLM_USO", "ahorro") == "ahorro" and est["intencion"] not in INTENCIONES_CON_LLM:
            return {"usar_plantilla": True, "trazas": est["trazas"] + ["redactar:plantilla_por_ahorro"]}
        if any(r.get("contexto", "Peru") != "Peru" for r in est.get("rag", [])[:1]):
            # la mejor fuente es una guia de otro pais: la plantilla la cita con su aviso «no es norma peruana», que el redactor suele omitir
            return {"usar_plantilla": True, "trazas": est["trazas"] + ["redactar:plantilla_por_fuente_extranjera"]}
        cadena = PV.cadena()
        datos_txt = _datos_texto(est)
        tono = N.ficha(est["ctx"]["nivel"])["tono"]
        pregunta = est.get("pregunta") or f"Aviso proactivo: {est.get('evento')}"
        if cadena and est["intencion"] in FAQ.INTENCIONES and est.get("rag_estado") == "correcto":   # pregunta de concepto ya respondida y verificada: se reutiliza sin gastar tokens
            hit = FAQ.buscar(est["pregunta"], est["ctx"]["nivel"])
            if hit:
                return {"borrador": hit["respuesta"], "rag": hit["fragmentos"], "proveedor": "faq", "usar_plantilla": False, "intentos": est["intentos"] + 1,
                        "trazas": est["trazas"] + [f"redactar:faq({hit['origen']})"]}
        clave = hashlib.sha256(f"{PV.SISTEMA}|{pregunta}|{datos_txt}|{tono}|{est.get('feedback', '')}".encode()).hexdigest()[:24]
        cache = _cache_cargar()
        if clave in cache and cadena:  # misma pregunta con los mismos datos: no se vuelve a pagar
            return {"borrador": cache[clave], "proveedor": "cache", "usar_plantilla": False, "intentos": est["intentos"] + 1, "trazas": est["trazas"] + ["redactar:cache"]}
        # un LLM externo solo ve datos sin identificadores: no se envia el id del cliente ni el departamento exacto
        for p in cadena:
            try:
                envio = datos_txt.replace(est["ctx"]["departamento"], "tu zona").replace(est["customer_id"], "el cliente") if getattr(p, "externo", True) else datos_txt   # todo proveedor externo recibe los datos sin id ni zona
                txt = p.redactar(pregunta, envio, tono, est.get("feedback"))
                if "```" not in txt:
                    _cache_guardar(clave, txt)
                return {"borrador": txt, "proveedor": p.nombre, "llamadas_llm": est["llamadas_llm"] + 1, "usar_plantilla": False, "intentos": est["intentos"] + 1,
                        "trazas": est["trazas"] + [f"redactar:{p.nombre}"]}
            except PV.ErrorProveedor as e:
                est = {**est, "trazas": est["trazas"] + [f"redactar:{p.nombre}_fallo({str(e)[:40]})"]}
        return {"usar_plantilla": True, "trazas": est["trazas"] + ["redactar:sin_proveedor"]}

    def juez(est):
        if est.get("usar_plantilla"):
            return {"veredicto": {"ok": True, "nota": "plantilla"}, "trazas": est["trazas"]}
        txt = est["borrador"]
        v = verificar(txt, _permitidos(est))
        if v["ok"] and not _termina_en_oracion_completa(txt):   # un borrador cortado a la mitad se rechaza igual que uno con una cifra inventada
            v = {**v, "ok": False, "prohibidos": v["prohibidos"] + ["respuesta cortada: no termina en una oracion completa"]}
        if v["ok"] and _es_respuesta_vacia(txt):
            v = {**v, "ok": False, "prohibidos": v["prohibidos"] + ["respuesta vacia: casi no dice nada"]}
        if v["ok"] and _mezcla_otro_idioma(txt):
            v = {**v, "ok": False, "prohibidos": v["prohibidos"] + ["no esta escrita en espanol"]}
        if v["ok"] and _filtra_el_prompt(txt):
            v = {**v, "ok": False, "prohibidos": v["prohibidos"] + ["filtra el nombre interno de la seccion de datos del prompt"]}
        if v["ok"] and est["intencion"] in INTENCIONES_CON_DATOS and _es_evasiva(txt):   # si se niega pero los datos estaban, se reintenta y, si insiste, responde la plantilla (que si usa los datos)
            v = {**v, "ok": False, "prohibidos": v["prohibidos"] + ["respuesta evasiva: los datos si traian la informacion, respondela con ellos"]}
        jl = {}
        if v["ok"] and usar_juez_llm:
            jl = juzgar(_datos_texto(est), txt, usar_gemini=est.get("proveedor") == "gemini")
            if not jl["fundamentado"]:
                v = {**v, "ok": False, "prohibidos": v["prohibidos"] + [f"juez LLM: {'; '.join(jl['problemas'])[:120]}"]}
        fb = ""
        if not v["ok"]:
            fb = f"cifras sin respaldo: {v['cifras_sin_respaldo']}; problemas: {v['prohibidos']}"
        return {"veredicto": v, "juez_llm": jl, "feedback": fb, "trazas": est["trazas"] + [f"juez:{'ok' if v['ok'] else 'rechaza'}"]}

    def tras_juez(est):
        if est.get("usar_plantilla") or est["veredicto"]["ok"]:
            return "finalizar" if not est.get("usar_plantilla") else "plantilla"
        return "redactar" if est["intentos"] < MAX_INTENTOS else "plantilla"

    def plantilla_nodo(est):
        return {"borrador": plantilla(est), "proveedor": "plantilla", "trazas": est["trazas"] + ["plantilla"]}

    def finalizar(est):
        txt = est["borrador"].strip()
        if "tu decides" not in txt.lower():
            txt += " Tu decides."
        v = verificar(txt, _permitidos(est))
        FAQ.registrar(est, txt)   # cuenta la consulta y, si la respuesta es de concepto y reutilizable, la guarda para la proxima persona
        citas = [{"titulo": r["titulo"], "pagina": r["pagina"], "documento": r["documento"], "enlace": r.get("enlace", ""), "licencia_nivel": r["licencia_nivel"]} for r in est.get("rag", [])]
        return {"opciones": _opciones(est) if est["intencion"] in INTENCIONES_ABIERTAS and est.get("modo_conversacion") != "proactivo" else [],
                "respuesta": txt, "citas": citas, "veredicto": {**est.get("veredicto", {}), "cifras_verificadas_final": v["cifras_verificadas"], "cifras_sin_respaldo_final": v["cifras_sin_respaldo"]},
                "trazas": est["trazas"] + ["finalizar"]}

    g = StateGraph(Estado)
    g.add_node("cargar_contexto", cargar)
    g.add_node("traducir_entrada", traducir_entrada)
    g.add_node("traducir_salida", traducir_salida)
    g.add_node("router", router)
    g.add_node("redactar", redactar)
    g.add_node("juez", juez)
    g.add_node("plantilla", plantilla_nodo)
    g.add_node("finalizar", finalizar)
    g.add_edge(START, "cargar_contexto")
    g.add_edge("cargar_contexto", "traducir_entrada")
    g.add_edge("traducir_entrada", "router")
    if modo == "multiagente":
        g.add_node("supervisor", supervisor)
        for a in AGENTES:
            g.add_node(f"agente_{a}", agente_nodo(a))
            g.add_edge(f"agente_{a}", "supervisor")
        g.add_edge("router", "supervisor")
        g.add_conditional_edges("supervisor", lambda e: e["siguiente"], {**{a: f"agente_{a}" for a in AGENTES}, "redactar": "redactar"})
    else:
        g.add_node("herramientas", herramientas)
        g.add_edge("router", "herramientas")
        g.add_edge("herramientas", "redactar")
    g.add_edge("redactar", "juez")
    g.add_conditional_edges("juez", tras_juez, {"finalizar": "finalizar", "redactar": "redactar", "plantilla": "plantilla"})
    g.add_edge("plantilla", "finalizar")
    g.add_edge("finalizar", "traducir_salida")
    g.add_edge("traducir_salida", END)
    app = g.compile()
    app.entidad = ent_nombre
    return app


def responder(app, customer_id: str, pregunta: str = "", evento: dict | None = None, idioma: str | None = None) -> dict:
    est = app.invoke({"customer_id": customer_id, "pregunta": pregunta, "evento": evento or {}, "modo_conversacion": "proactivo" if evento else "chat", "idioma": idioma})
    return {"respuesta": est["respuesta"], "intencion": est["intencion"], "proveedor": est["proveedor"], "citas": est["citas"], "cifras_verificadas": est["veredicto"].get("cifras_verificadas_final", 0),
            "cifras_sin_respaldo": est["veredicto"].get("cifras_sin_respaldo_final", []), "trazas": est["trazas"], "llamadas_llm": est["llamadas_llm"], "segundos": round(time.time() - est["t0"], 2),
            "recomendaciones": [{"id": r["id"], "accion": r["accion"], "impacto_soles": r["impacto_soles"], "confianza": r["confianza"]} for r in est.get("recos", [])], "rag_estado": est["rag_estado"],
            "idioma": est.get("idioma", "es"), "respuesta_es": est.get("respuesta_es", est["respuesta"]), "traduccion": est.get("traduccion", {}),
            "propuesta_meta": est["datos"].get("meta", {}).get("propuesta"), "opciones": est.get("opciones", [])}


def bienvenida(app, customer_id: str, idioma: str | None = None) -> dict:
    """Mensaje con el que el chat puede ABRIR la conversacion antes de que la persona escriba nada: saludo de plantilla (cero tokens) con opciones segun su perfil.
    Si la persona responde con algo distinto, ese mensaje entra por `responder` y el agente lo entiende, contesta si sabe, o dice con honestidad que no puede y vuelve a ofrecer opciones."""
    return responder(app, customer_id, "hola", idioma=idioma)


def exportar_diagramas(carpeta: str, repo, buscador=None) -> dict:
    os.makedirs(carpeta, exist_ok=True)
    out = {}
    for modo in ("agente_unico", "multiagente"):
        app = construir_grafo(repo, buscador, modo)
        mer = app.get_graph().draw_mermaid()
        ruta = os.path.join(carpeta, f"grafo_{modo}.md")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(f"# Grafo del agente ({modo})\n\nGenerado con `app.get_graph().draw_mermaid()` de LangGraph.\n\n```mermaid\n{mer}\n```\n")
        out[modo] = ruta
    return out
