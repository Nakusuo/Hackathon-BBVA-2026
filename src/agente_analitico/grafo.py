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

from src.agente_analitico import proveedores as PV
from src.agente_analitico import traduccion as TR
from src.agente_analitico.juez_llm import juzgar
from src.agente_analitico.verificador import aplanar, numeros_de, verificar
from src.bcrp.cliente import ultimo_con_variacion
from src.comun.rutas import cargar_env, ruta
from src.generador.contexto import cargar_yaml
from src.models import niveles as N
from src.models import recomendador as REC
from src.models import riesgo_clima as RC
from src.models import salud as SA

UMBRAL_RELEVANCIA = 0.70   # filtro tipo CRAG, calibrado en src/rag/evaluar.py
MAX_INTENTOS = 2

REGLAS_INTENCION = [
    # seguridad: intentos de sacar instrucciones internas, claves o datos de otras personas, o de saltarse las reglas
    ("seguridad", r"system prompt|prompt del sistema|tu prompt|instrucciones (previas|anteriores|internas)|ignora (tus|las|todas|todo)|olvida (tus|las|todas|todo)|jailbreak|\bDAN\b|contrase[ñn]a|api[ _-]?key|clave de (api|acceso)|\btoken\b|hackea|inyecci[oó]n|exploit|vulnerabilidad|datos de (otro|otra|otros)|de otro cliente"),
    # fuera de tema: codigo, matematica y cultura general, que no son de este asistente
    ("fuera_de_tema", r"c[oó]digo|\bscript\b|python|javascript|typescript|\bsql\b|\bjava\b|algoritmo|ecuaci[oó]n|integral|derivada|teorema|demuestra|problema (de )?matem|resuelve (esta|este|el|la)|tarea de|compila|\bhtml\b|\bcss\b|\bbash\b|\bregex\b|receta|capital de|qui[eé]n gan[oó]|poema|chiste"),
    ("fuera_de_alcance", r"transfier|transferir|enviar (la )?(plata|dinero)|compra(r)? d[oó]lares|vende(r)? d[oó]lares|invierte en|invierto en|criptomoneda|bitcoin|compra(r)? acciones|en qu[eé] (acci[oó]n|empresa|cripto\w*)"),
    ("fen", r"ni[ñn]o|lluvia|huaico|inundaci|zona de riesgo|desastre|fen\b|prevenci"),
    ("calendario", r"\bcts\b|gratificaci[oó]n|compensaci[oó]n por tiempo|libre (disponibilidad|disposici[oó]n)|aguinaldo|cu[aá]ndo (me )?(cae|llega|llegan|depositan|pagan)"),
    ("tasas", r"\btasas?\b|inter[eé]s|tcea|refinanci|baj[oó] la tasa"),
    ("ofertas", r"pr[eé]stamo|cr[eé]dito|tarjeta|invertir|inversi[oó]n|dep[oó]sito|oferta"),
    ("salud_nivel", r"nivel|puntos|salud financiera|puntaje|campe[oó]n|maestro|aprendiz|luchador|canje|beneficio"),
    ("pronostico", r"alcanza|llego|fin de mes|saldo|rojo|cobro|pr[oó]ximo|pr[oó]ximos meses|cu[aá]nto (voy a|tendr|ganar|gastar)|proyecci|ingresos"),
    ("recomendaciones", r"recomiend|qu[eé] hago|consejo|ahorrar|meta|reducir|gasto"),
    ("educacion", r"qu[eé] es|c[oó]mo funciona|derechos?|reclam|datos personales|explica|c[oó]mo (armo|hago|llevo)"),
]
PLAN = {
    "pronostico": ["pronostico", "salud"], "recomendaciones": ["pronostico", "salud", "clima", "recomendador"], "salud_nivel": ["salud"], "fen": ["clima", "recomendador", "educador"],
    "tasas": ["tasas", "salud", "educador"], "ofertas": ["pronostico", "salud", "tasas", "recomendador"], "educacion": ["educador"], "ingreso_extra": ["salud", "recomendador"],
    "baja_de_tasa": ["tasas", "salud", "recomendador"], "riesgo_rojo": ["pronostico", "salud", "recomendador"], "general": ["pronostico", "salud", "recomendador"], "fuera_de_alcance": [],
    "fuera_de_tema": [], "seguridad": [], "calendario": ["calendario", "salud", "recomendador", "educador"], "gasto_atipico": ["pronostico", "salud", "recomendador"],
}
# Evento proactivo -> intencion. Un evento desconocido cae a 'general' (nunca rompe el agente).
EVENTO_A_INTENCION = {"ingreso_extra": "ingreso_extra", "baja_de_tasa": "baja_de_tasa", "fen_comunicado": "fen", "riesgo_rojo": "riesgo_rojo", "calendario_laboral": "calendario",
                      "libre_disposicion_por_vencer": "calendario", "gratificacion_pendiente": "calendario", "gasto_atipico": "gasto_atipico"}
SIN_LLM = ("fuera_de_alcance", "fuera_de_tema", "seguridad")   # se responden con plantilla: no gastan tokens ni dan pie a que el modelo se desvie
# Politica de ahorro de tokens (MVP): el LLM solo redacta lo que una plantilla no cubre bien. LLM_USO=siempre lo usa en todo (pruebas); LLM_USO=ahorro es el defecto.
INTENCIONES_CON_LLM = ("educacion", "general")
INTENCIONES_DE_SALDO = ("pronostico", "riesgo_rojo", "general")   # respuestas que hablan del saldo: ahi se aclara la fecha de los datos del cliente
AYUDO_EN = ("Si puedo ver si llegas a fin de mes y cuanto ingresaras y gastaras en los proximos meses, revisar tu salud financiera y tu nivel, darte recomendaciones para ahorrar o "
            "gastar mejor, avisarte de El Nino en tu zona y explicarte conceptos como la TCEA o tus derechos.")
MODULOS_RAG = {"fen": ["fenomeno_el_nino"], "tasas": ["deudas", "derechos"], "educacion": None, "ofertas": ["deudas", "salud_financiera"], "calendario": ["laboral"]}


class Estado(TypedDict, total=False):
    customer_id: str
    pregunta: str
    modo_conversacion: str
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


FINANZAS = r"plata|dinero|gast|ahorr|cuenta|saldo|sueldo|ingres|deuda|pago|banco|cuota|meta|financ|cr[eé]dito|tarjeta|tasa|nivel|puntos|beneficio|ni[ñn]o|lluvia|alcanza|cobro|rojo|presupuesto|reclam|derechos|datos personales|recomend"


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


def detectar_intencion(pregunta: str, evento: dict | None = None) -> str:
    if evento:
        return EVENTO_A_INTENCION.get(evento.get("tipo"), "general")
    for nombre, patron in REGLAS_INTENCION:
        if re.search(patron, pregunta, flags=re.I):
            return nombre
    return "general" if re.search(FINANZAS, pregunta, flags=re.I) else "fuera_de_tema"


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
    return {"salud": {"salud_financiera": c["salud"], "nivel": ficha["titulo"], "resumen_nivel": ficha["resumen"], "puntos": pts, "canjes_disponibles": [x["nombre"] for x in N.canjes_disponibles(pts)],
                      "lo_que_mas_resta": SA.explicar(f, 2), "para_subir": prog}}


def _a_clima(est, repo, **_):
    a = RC.alerta_fen(est["ctx"]["departamento"], est["ctx"]["hoy"])
    return {"clima": {"alerta": a} if a else {"sin_alerta": True, "exposicion": RC.exposicion_fen(est["ctx"]["departamento"])["nivel"]}}


def _a_tasas(est, repo, **_):
    """Tasa de referencia del BCRP en vivo (y el tipo de cambio si el cliente paga en dolares). Un dato desactualizado no se presenta como actual."""
    try:
        t = ultimo_con_variacion("tasa_referencia")
    except Exception as e:  # sin red ni cache el agente sigue sin esta herramienta
        return {"tasas": {"no_disponible": True, "motivo": type(e).__name__}}
    if not t["al_dia"]:
        return {"tasas": {"no_disponible": True, "motivo": "dato desactualizado", "ultimo_dato": {"fecha": t["fecha"], "valor": t["valor"], "origen": t["origen"]}}}
    if est["ctx"].get("paga_en_usd"):
        try:
            fx = ultimo_con_variacion("tipo_cambio_venta")
            if fx["al_dia"]:
                t = {**t, "tipo_cambio_venta": {"valor": round(fx["valor"], 3), "fecha": fx["fecha"], "variacion": round(fx["variacion"], 3)}}
        except Exception:  # el tipo de cambio es un extra: si falla, la tasa sigue valiendo
            pass
    return {"tasas": t}


def _a_calendario(est, repo, **_):
    """Calendario laboral del cliente (gratificacion, CTS y regla de retiro de la CTS). Ya viene calculado en su contexto con la fecha del reloj unico."""
    return {"calendario": est["ctx"]["calendario"]}


def _a_recomendador(est, repo, **_):
    c = dict(est["ctx"])
    c["tasa_ref"] = est["datos"].get("tasas", {}).get("valor", 4.5)
    c["baja_de_tasa"] = est["datos"].get("tasas", {}).get("variacion", 0) < 0
    if est.get("evento", {}).get("tipo") == "ingreso_extra":
        c["evento_ingreso"] = est["evento"]
    recs = REC.recomendar(c, 3)
    return {"recos": recs}


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


AGENTES = {"pronostico": _a_pronostico, "salud": _a_salud, "clima": _a_clima, "tasas": _a_tasas, "calendario": _a_calendario, "recomendador": _a_recomendador, "educador": _a_educador}
DEPENDENCIAS = {"recomendador": ["pronostico", "salud", "clima", "tasas"]}


# ------------------------------------------------------------------ redaccion y juez
def _datos_texto(est) -> str:
    L = []
    d = est["datos"]
    c = est["ctx"]
    L.append(f"Nivel: {d.get('salud', {}).get('nivel', N.ficha(c['nivel'])['titulo'])}. Tono: {N.ficha(c['nivel'])['tono']}.")
    for k, v in d.items():
        L.append(f"{k}: {v}")
    for i, r in enumerate(est.get("recos", [])[:3], 1):
        L.append(f"recomendacion {i}: {r['accion']} Impacto: {r['impacto_soles']}. Por que: {'; '.join(r['por_que'])}. Supuestos: {'; '.join(r['supuestos'])}. Confianza: {r['confianza']}.")
    for r in est.get("rag", [])[:3]:
        L.append(f"fuente [{r['titulo']}, pag. {r['pagina']}]: {r['texto'][:600]}")
    return "\n".join(L)


def _permitidos(est) -> set:
    p = aplanar(est["datos"]) | aplanar(est.get("recos", [])) | set(numeros_de(est.get("pregunta", "")))
    for r in est.get("rag", []):
        p |= aplanar(r["texto"]) | {float(r["pagina"])}
    if est.get("evento"):
        p |= aplanar(est["evento"])
    return p


def plantilla(est) -> str:
    c, d, intent = est["ctx"], est["datos"], est["intencion"]
    ficha = N.ficha(c["nivel"])
    L = [f"Hola, {ficha['titulo']}."]
    ev = est.get("evento") or {}
    if ev.get("tipo") == "ingreso_extra":
        L.append(f"Vemos que recibiste S/ {ev['monto']:,.0f} por {ev['origen']}.")
    elif ev.get("tipo") == "baja_de_tasa":
        L.append(f"La tasa de referencia del BCRP bajo de {ev['desde']:.2f}% a {ev['hasta']:.2f}%.")
    elif ev.get("tipo") == "fen_comunicado":
        L.append(f"El ENFEN publico el comunicado N.o {ev['numero']}.")
    elif ev.get("tipo") == "riesgo_rojo":
        L.append(f"Tu saldo podria quedar en rojo: la probabilidad es {ev['p_rojo']:.0%}.")
    elif ev.get("tipo") == "calendario_laboral":
        e = ev["evento"]
        L.append(f"Se acerca una fecha de tu calendario laboral: {e['nombre']} ({'hoy' if e['dias_para'] == 0 else f'en {e['dias_para']} dias'}).")
    elif ev.get("tipo") == "libre_disposicion_por_vencer":
        L.append(f"Te quedan {ev['dias_restantes']} dias para disponer del 100 % de tu CTS.")
    elif ev.get("tipo") == "gratificacion_pendiente":
        L.append(f"Aun no vemos tu {ev['nombre']}, que tu empleador debia pagar hasta el {ev['fecha_limite_texto']}.")
    elif ev.get("tipo") == "gasto_atipico":
        L.append(f"Registramos un gasto de S/ {ev['monto']:,.0f} en {ev['categoria']}: pesa {ev['fraccion_del_ingreso']:.0%} de tu ingreso mensual.")
    if intent in SIN_LLM:
        motivo = {"fuera_de_alcance": "Eso no lo hago: no muevo dinero, no compro ni vendo dolares y no te digo en que invertir.",
                  "fuera_de_tema": "De eso no puedo ayudarte: no resuelvo problemas de matematica, no escribo codigo ni respondo temas ajenos a tu plata.",
                  "seguridad": "Eso no lo puedo hacer: no comparto instrucciones internas, claves ni informacion de otras personas, y mis reglas no se pueden saltar."}[intent]
        return f"{L[0]} {motivo} {AYUDO_EN} Tu decides."
    if "pronostico" in d:
        p = d["pronostico"]["pronostico_30_dias"]
        mv = d["pronostico"].get("movimientos_recientes")
        if mv:
            L.append(f"Desde el {mv['desde']} entraron S/ {mv['ingresos']:,.0f} y salieron S/ {mv['gastos']:,.0f}; tu saldo de hoy ronda S/ {d['pronostico']['saldo_actual']:,.0f}.")
        L.append(f"En 30 dias esperamos que tu saldo ronde S/ {p['saldo_esperado']:,.0f}, con un rango entre S/ {p['saldo_bajo']:,.0f} y S/ {p['saldo_alto']:,.0f}.")
        if p["p_rojo"] >= 0.15:
            L.append(f"Hay una probabilidad de {p['p_rojo']:.0%} de quedar en rojo{f' hacia el dia {int(p['dia_riesgo'])}' if p.get('dia_riesgo') else ''}.")
        m = d["pronostico"].get("proyeccion_mensual")
        if m:
            f0 = m[0]
            L.append(f"Para {f0['mes']} estimamos ingresos de S/ {f0['ingreso_esperado']:,.0f} (entre S/ {f0['ingreso_bajo']:,.0f} y S/ {f0['ingreso_alto']:,.0f}) y gastos de S/ {f0['gasto_esperado']:,.0f}.")
        if d["pronostico"].get("aviso_datos"):
            L.append(d["pronostico"]["aviso_datos"])
    if "calendario" in d:
        cal = d["calendario"]
        if not cal.get("aplica"):
            L.append(cal["motivo"])
        else:
            for e in cal["eventos"][:2]:
                m = e["monto_estimado"]
                if e["tipo"] == "gratificacion":
                    L.append(f"{e['nombre']}: tu empleador la paga hasta el {e['fecha_limite_texto']} (en {e['dias_para']} dias). Estimamos S/ {m['gratificacion']:,.0f} mas S/ {m['bonificacion_extraordinaria']:,.0f} de bonificacion extraordinaria, en total S/ {m['total']:,.0f}.")
                else:
                    L.append(f"{e['nombre']}: tu empleador debe depositarla hasta el {e['fecha_limite_texto']}. Estimamos S/ {m['deposito_semestral']:,.0f}. Llega a tu cuenta de CTS, no a tu cuenta de sueldo.")
            L.append(f"Son estimaciones con {'tu ultima gratificacion' if cal['base_origen'] == 'historial' else 'tu ingreso medio (supuesto)'}: confirma el monto exacto con tu empleador.")
        ld = cal["libre_disposicion_cts"]
        if ld["regimen_transitorio_vigente"]:
            L.append(f"Sobre retirar tu CTS: hasta el {ld['vigente_hasta_texto']} puedes disponer del 100 % de lo depositado en entidades financieras ({ld['fuente']}); despues, solo hasta el 50 %. "
                     f"La CTS es una proteccion para cuando termina tu trabajo: retira solo lo que de verdad necesites. {ld['nota_proyectos']}")
        else:
            L.append(f"Sobre retirar tu CTS: hoy puedes disponer libremente de hasta el 50 % de lo depositado ({ld['fuente']}); con enfermedad terminal o cancer acreditados, del 100 %.")
        if cal.get("reglas_por_revisar"):
            L.append(f"Estas reglas se contrastaron con su fuente el {cal['reglas_verificadas_el']}: conviene volver a verificarlas.")
    if "salud" in d:
        s = d["salud"]
        L.append(f"Tu salud financiera es {s['salud_financiera']:.0f} de 100 y tu nivel es {s['nivel']}.")
        if s["lo_que_mas_resta"]:
            r0 = s["lo_que_mas_resta"][0]
            L.append(f"Lo que mas la baja es {r0['que_mide']}.")
        if s["para_subir"].get("faltantes"):
            fa = s["para_subir"]["faltantes"][0]
            L.append(f"Para subir a {s['para_subir']['siguiente']} te falta mejorar {fa['que']}: hoy tienes {fa['tienes']} y necesitas {fa['necesitas']}.")
        if s["puntos"]:
            L.append(f"Llevas {s['puntos']} puntos.")
    if "clima" in d and d["clima"].get("alerta"):
        a = d["clima"]["alerta"]
        L.append(f"Alerta: tu zona ({a['departamento']}) tiene exposicion {a['nivel']} a lluvias por El Nino segun el ENFEN. Acciones: {' '.join(a['acciones'][:3])}")
    if "tasas" in d and not d["tasas"].get("no_disponible"):
        t = d["tasas"]
        L.append(f"La tasa de referencia del BCRP esta en {t['valor']:.2f}% ({'bajo' if t['variacion'] < 0 else 'subio' if t['variacion'] > 0 else 'sin cambio'} {abs(t['variacion']):.2f} puntos frente al mes anterior).")
    for r in est.get("recos", [])[:3]:
        imp = f" Impacto estimado: S/ {r['impacto_soles']:,.0f}." if r.get("impacto_soles") else ""
        L.append(f"- {r['accion']}{imp} Por que: {r['por_que'][0]}.")
    if est.get("rag"):
        r0 = est["rag"][0]
        L.append(f"Segun {r0['titulo']} (pag. {r0['pagina']}): {r0['texto'][:320].strip()}...")
    elif est.get("rag_estado", "").startswith("sin_evidencia"):
        L.append("Sobre eso no encuentro informacion en las fuentes que tengo, asi que prefiero no inventarla.")
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
        cadena = PV.cadena()
        datos_txt = _datos_texto(est)
        tono = N.ficha(est["ctx"]["nivel"])["tono"]
        pregunta = est.get("pregunta") or f"Aviso proactivo: {est.get('evento')}"
        clave = hashlib.sha256(f"{PV.SISTEMA}|{pregunta}|{datos_txt}|{tono}|{est.get('feedback', '')}".encode()).hexdigest()[:24]
        cache = _cache_cargar()
        if clave in cache and cadena:  # misma pregunta con los mismos datos: no se vuelve a pagar
            return {"borrador": cache[clave], "proveedor": "cache", "usar_plantilla": False, "intentos": est["intentos"] + 1, "trazas": est["trazas"] + ["redactar:cache"]}
        # un LLM externo solo ve datos sin identificadores: no se envia el id del cliente ni el departamento exacto
        for p in cadena:
            try:
                envio = datos_txt.replace(est["ctx"]["departamento"], "tu zona").replace(est["customer_id"], "el cliente") if p.nombre == "gemini" else datos_txt
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
        citas = [{"titulo": r["titulo"], "pagina": r["pagina"], "documento": r["documento"], "enlace": r.get("enlace", ""), "licencia_nivel": r["licencia_nivel"]} for r in est.get("rag", [])]
        return {"respuesta": txt, "citas": citas, "veredicto": {**est.get("veredicto", {}), "cifras_verificadas_final": v["cifras_verificadas"], "cifras_sin_respaldo_final": v["cifras_sin_respaldo"]},
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
            "idioma": est.get("idioma", "es"), "respuesta_es": est.get("respuesta_es", est["respuesta"]), "traduccion": est.get("traduccion", {})}


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
