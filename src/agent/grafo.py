"""Agente de Lucas con LangGraph. Dos modos sobre las mismas piezas:
 - agente_unico: una tuberia fija (contexto -> router -> herramientas -> RAG -> redaccion -> juez).
 - multiagente: un supervisor reparte el trabajo entre agentes especialistas que pueden pedirse datos entre si.
El LLM solo redacta; toda cifra sale de una herramienta y pasa por el juez. Si algo falla, responde una plantilla."""
import os
import re
import time
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.agent import proveedores as PV
from src.agent.juez_llm import juzgar
from src.agent.verificador import aplanar, numeros_de, verificar
from src.bcrp.cliente import ultimo_con_variacion
from src.comun.rutas import cargar_env
from src.generador.contexto import cargar_yaml
from src.models import niveles as N
from src.models import recomendador as REC
from src.models import riesgo_clima as RC
from src.models import salud as SA

UMBRAL_RELEVANCIA = 0.70   # filtro tipo CRAG, calibrado en src/rag/evaluar.py
MAX_INTENTOS = 2

REGLAS_INTENCION = [
    ("fuera_de_alcance", r"transfier|transferir|enviar (la )?(plata|dinero)|compra(r)? d[oó]lares|vende(r)? d[oó]lares|invierte en|invierto en|criptomoneda|bitcoin|compra(r)? acciones|en qu[eé] (acci[oó]n|empresa|cripto\w*)|ignora (tus|las) (reglas|instrucciones)|olvida (tus|las) instrucciones|tu prompt"),
    ("fen", r"ni[ñn]o|lluvia|huaico|inundaci|zona de riesgo|desastre|fen\b|prevenci"),
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
}
MODULOS_RAG = {"fen": ["fenomeno_el_nino"], "tasas": ["deudas", "derechos"], "educacion": None, "ofertas": ["deudas", "salud_financiera"]}


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


FINANZAS = r"plata|dinero|gast|ahorr|cuenta|saldo|sueldo|ingres|deuda|pago|banco|cuota|meta|financ|cr[eé]dito|tarjeta|tasa|nivel|puntos|beneficio|ni[ñn]o|lluvia|alcanza|cobro|rojo|presupuesto|reclam|derechos|datos personales|recomend"


def detectar_intencion(pregunta: str, evento: dict | None = None) -> str:
    if evento:
        return {"ingreso_extra": "ingreso_extra", "baja_de_tasa": "baja_de_tasa", "fen_comunicado": "fen", "riesgo_rojo": "riesgo_rojo"}.get(evento["tipo"], "general")
    for nombre, patron in REGLAS_INTENCION:
        if re.search(patron, pregunta, flags=re.I):
            return nombre
    return "general" if re.search(FINANZAS, pregunta, flags=re.I) else "fuera_de_alcance"


# ------------------------------------------------------------------ agentes especialistas (solo lectura)
def _a_pronostico(est, repo, **_):
    c = est["ctx"]
    d = {"pronostico_30_dias": {k: (round(v, 2) if isinstance(v, float) else v) for k, v in c["pronostico"].items()}, "saldo_actual": round(c["saldo_actual"], 0)}
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
    try:
        return {"tasas": ultimo_con_variacion("tasa_referencia")}
    except Exception as e:  # sin red ni cache el agente sigue sin esta herramienta
        return {"tasas": {"no_disponible": True, "motivo": type(e).__name__}}


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


AGENTES = {"pronostico": _a_pronostico, "salud": _a_salud, "clima": _a_clima, "tasas": _a_tasas, "recomendador": _a_recomendador, "educador": _a_educador}
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
    if intent == "fuera_de_alcance":
        return (f"{L[0]} Eso no lo hago: no muevo dinero, no compro ni vendo dolares y no te digo en que invertir. Lo que si puedo es mostrarte tu pronostico, tus recomendaciones y explicarte "
                "como funciona cada producto para que decidas con calma. Tu decides.")
    if "pronostico" in d:
        p = d["pronostico"]["pronostico_30_dias"]
        L.append(f"En 30 dias esperamos que tu saldo ronde S/ {p['saldo_esperado']:,.0f}, con un rango entre S/ {p['saldo_bajo']:,.0f} y S/ {p['saldo_alto']:,.0f}.")
        if p["p_rojo"] >= 0.15:
            L.append(f"Hay una probabilidad de {p['p_rojo']:.0%} de quedar en rojo{f' hacia el dia {int(p['dia_riesgo'])}' if p.get('dia_riesgo') else ''}.")
        m = d["pronostico"].get("proyeccion_mensual")
        if m:
            f0 = m[0]
            L.append(f"Para {f0['mes']} estimamos ingresos de S/ {f0['ingreso_esperado']:,.0f} (entre S/ {f0['ingreso_bajo']:,.0f} y S/ {f0['ingreso_alto']:,.0f}) y gastos de S/ {f0['gasto_esperado']:,.0f}.")
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

    def router(est):
        intent = detectar_intencion(est.get("pregunta", ""), est.get("evento"))
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
            if a in ("pronostico", "salud", "clima", "tasas") and a in e["datos"]:
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
        if est["intencion"] == "fuera_de_alcance":
            return {"usar_plantilla": True, "trazas": est["trazas"] + ["redactar:plantilla_por_alcance"]}
        cadena = PV.cadena()
        datos_txt = _datos_texto(est)
        tono = N.ficha(est["ctx"]["nivel"])["tono"]
        pregunta = est.get("pregunta") or f"Aviso proactivo: {est.get('evento')}"
        # un LLM externo solo ve datos sin identificadores: no se envia el id del cliente ni el departamento exacto
        for p in cadena:
            try:
                envio = datos_txt.replace(est["ctx"]["departamento"], "tu zona").replace(est["customer_id"], "el cliente") if p.nombre == "gemini" else datos_txt
                txt = p.redactar(pregunta, envio, tono, est.get("feedback"))
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
    g.add_node("router", router)
    g.add_node("redactar", redactar)
    g.add_node("juez", juez)
    g.add_node("plantilla", plantilla_nodo)
    g.add_node("finalizar", finalizar)
    g.add_edge(START, "cargar_contexto")
    g.add_edge("cargar_contexto", "router")
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
    g.add_edge("finalizar", END)
    app = g.compile()
    app.entidad = ent_nombre
    return app


def responder(app, customer_id: str, pregunta: str = "", evento: dict | None = None) -> dict:
    est = app.invoke({"customer_id": customer_id, "pregunta": pregunta, "evento": evento or {}, "modo_conversacion": "proactivo" if evento else "chat"})
    return {"respuesta": est["respuesta"], "intencion": est["intencion"], "proveedor": est["proveedor"], "citas": est["citas"], "cifras_verificadas": est["veredicto"].get("cifras_verificadas_final", 0),
            "cifras_sin_respaldo": est["veredicto"].get("cifras_sin_respaldo_final", []), "trazas": est["trazas"], "llamadas_llm": est["llamadas_llm"], "segundos": round(time.time() - est["t0"], 2),
            "recomendaciones": [{"id": r["id"], "accion": r["accion"], "impacto_soles": r["impacto_soles"], "confianza": r["confianza"]} for r in est.get("recos", [])], "rag_estado": est["rag_estado"]}


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
