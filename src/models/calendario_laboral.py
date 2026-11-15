"""Calendario laboral del dependiente: cuando le toca la gratificación y la CTS, cuanto se estima y que regla de retiro de la CTS rige hoy.
Es determinista y no usa red ni LLM: las reglas viven en data/parametros/normas_laborales.yaml con su evidencia en los documentos oficiales del RAG,
y aquí solo se aplican. Todo monto es una estimación con su supuesto a la vista."""
from datetime import date, timedelta

from src.generador.contexto import cargar_yaml

_CFG = None
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "setiembre", "octubre", "noviembre", "diciembre"]


def cfg() -> dict:
    global _CFG
    if _CFG is None:
        _CFG = cargar_yaml("normas_laborales.yaml")
    return _CFG


def texto_fecha(d: date) -> str:
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]} de {d.year}"


def dia_habil_siguiente(d: date) -> date:
    """Sabado y domingo son inhabiles. (El 15 de mayo, julio, noviembre y diciembre no es feriado nacional.)"""
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def fecha_limite(tipo: str, anio: int, mes: int) -> date:
    """La CTS pasa al primer día habil siguiente si el 15 es inhabil (TUO art. 22). La gratificación se paga 'en la primera quincena': su limite es el 15."""
    d = date(anio, mes, cfg()[tipo]["dia_limite"])
    return dia_habil_siguiente(d) if tipo == "cts" else d


def monto_gratificacion(base_mensual: float) -> dict:
    g = cfg()["gratificacion"]
    pct = g["bonificacion_extraordinaria"][g["supuesto_afiliacion"]]
    bruta = base_mensual * g["veces_la_remuneracion"]
    return {"gratificacion": round(bruta, 0), "bonificacion_extraordinaria": round(bruta * pct, 0), "total": round(bruta * (1 + pct), 0), "porcentaje_bonificacion": pct}


def monto_cts(base_mensual: float) -> dict:
    """Dozavos de la remuneracion computable por los meses completos del semestre (aquí, 6). La computable suma un sexto de la gratificación del semestre."""
    c, g = cfg()["cts"], cfg()["gratificacion"]
    computable = base_mensual + base_mensual * g["veces_la_remuneracion"] * c["fraccion_de_gratificacion_en_la_remuneracion_computable"]
    return {"remuneracion_computable": round(computable, 0), "deposito_semestral": round(computable / 12 * c["meses_del_semestre"], 0)}


def eventos(hoy: date, base_mensual: float, desde_dias: int = 30, hasta_dias: int = 200) -> list[dict]:
    """Eventos cuya fecha limite cae entre (hoy - desde_dias) y (hoy + hasta_dias), ordenados por fecha."""
    c = cfg()
    out = []
    for anio in (hoy.year - 1, hoy.year, hoy.year + 1):
        for tipo, meses in (("gratificacion", c["gratificacion"]["meses"]), ("cts", c["cts"]["meses_deposito"])):
            for mes in meses:
                lim = fecha_limite(tipo, anio, mes)
                dias = (lim - hoy).days
                if not -desde_dias <= dias <= hasta_dias:
                    continue
                ev = {"tipo": tipo, "fecha_limite": lim.isoformat(), "fecha_limite_texto": texto_fecha(lim), "dia_limite_legal": c[tipo]["dia_limite"], "dias_para": dias,
                      "estado": "pasado" if dias < 0 else "hoy" if dias == 0 else "proximo"}
                if tipo == "gratificacion":
                    ev.update(nombre=c["gratificacion"]["nombre"][mes], semestre=c["gratificacion"]["semestre"][mes], monto_estimado=monto_gratificacion(base_mensual))
                else:
                    ev.update(nombre=f"Deposito de CTS (periodo {c['cts']['periodo'][mes]})", monto_estimado=monto_cts(base_mensual), se_deposita_en=c["cts"]["se_deposita_en"])
                out.append(ev)
    return sorted(out, key=lambda e: e["fecha_limite"])


def libre_disposicion(hoy: date) -> dict:
    """Regla de retiro de la CTS que rige hoy (Ley 32322). Los proyectos de ley no cuentan hasta que sean ley."""
    c = cfg()["libre_disposicion"]
    fin = date.fromisoformat(c["vigente_hasta"])
    vigente = hoy <= fin
    dias = (fin - hoy).days if vigente else 0
    return {"porcentaje_libre_hoy": c["porcentaje_transitorio"] if vigente else c["porcentaje_permanente"], "porcentaje_permanente": c["porcentaje_permanente"],
            "regimen_transitorio_vigente": vigente, "vigente_hasta": fin.isoformat(), "vigente_hasta_texto": texto_fecha(fin), "dias_restantes": dias,
            "por_vencer": vigente and dias <= c["dias_para_avisar_vencimiento"], "enfermedad_terminal_o_cancer": c["enfermedad_terminal_o_cancer"],
            "nota_proyectos": c["nota_proyectos"], "proyecto_en_evaluacion": c.get("proyecto_en_evaluacion"), "finalidad_de_la_cts": cfg()["cts"]["finalidad"], "fuente": "Ley 32322 (El Peruano, 9 de mayo de 2025)"}


def reglas_por_revisar(hoy: date) -> bool:
    """Las reglas se contrastaron con su fuente en fecha_verificacion: pasado el plazo, el agente debe decir que conviene volver a verificarlas."""
    return (hoy - date.fromisoformat(cfg()["fecha_verificacion"])).days > cfg()["dias_para_revisar"]


def calendario(hoy: date, tipo_trabajo: str, base_mensual: float | None, origen_base: str = "ingreso_medio", n: int = 3) -> dict:
    """Lo que el agente ve del calendario laboral de un cliente. origen_base: 'historial' (su última gratificación) o 'ingreso_medio' (supuesto)."""
    a = cfg()["alcance"]
    base = {"hoy": hoy.isoformat(), "reglas_verificadas_el": cfg()["fecha_verificacion"], "reglas_por_revisar": reglas_por_revisar(hoy), "libre_disposicion_cts": libre_disposicion(hoy)}
    if tipo_trabajo in a["no_aplica_a"] or not base_mensual or base_mensual <= 0:
        return {**base, "aplica": False, "motivo": "Eres independiente: la CTS y las gratificaciones son beneficios de quienes trabajan en planilla, así que no te corresponden."
                if tipo_trabajo in a["no_aplica_a"] else "No hay un ingreso fijo en planilla con el cual estimar la CTS ni la gratificación."}
    prox = [e for e in eventos(hoy, base_mensual) if e["estado"] != "pasado"][:n]
    return {**base, "aplica": True, "base_mensual": round(base_mensual, 0), "base_origen": origen_base, "confianza": "alta" if origen_base == "historial" else "media",
            "supuestos": [a["supuesto_del_equipo"], "la base es tu última gratificación (equivale a una remuneracion)" if origen_base == "historial" else "la base es tu ingreso medio mensual (supuesto: no hay una gratificación anterior)"],
            "eventos": prox}
