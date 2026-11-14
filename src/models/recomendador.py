"""Recomendador hibrido: reglas candidatas -> impacto x facilidad -> ajuste por nivel -> filtros de seguridad -> top 3.
Cada recomendacion trae accion, impacto en S/, por que, supuestos, confianza y deja la decision al usuario."""
import json


from src.comun.rutas import ruta
from src.models import niveles as N
from src.models import riesgo_clima as RC

TCEA_DEUDA_CARA = 0.45


def catalogo() -> dict:
    with open(ruta("data", "catalogo_ofertas.json"), encoding="utf-8") as f:
        return {o["id"]: o for o in json.load(f)["ofertas"]}


def cuota_mensual(monto: float, tea: float, meses: int) -> float:
    i = (1 + tea) ** (1 / 12) - 1
    return float(monto * i / (1 - (1 + i) ** -meses)) if i > 0 else float(monto / meses)


def confianza(ancho_rel: float | None) -> str:
    if ancho_rel is None:
        return "media"
    return "alta" if ancho_rel < 1.2 else "media" if ancho_rel < 1.8 else "baja"


def _gasto_mensual(f: dict) -> float:
    return float(f["gasto_sobre_ingreso"] * f["ingreso_medio"])


def idoneo_para_credito(f: dict, p_rojo: float, cuota_nueva: float = 0.0) -> tuple[bool, list[str]]:
    """Reglas de seguridad: nada de credito con colchon bajo, cuotas altas, dias en rojo recientes o riesgo de rojo alto."""
    razones = []
    if f["colchon_observado"] < 1.0:
        razones.append("tu colchon es menor a un mes de ingreso")
    if f["cuota_sobre_ingreso"] + cuota_nueva / max(f["ingreso_medio"], 1) > 0.30:
        razones.append("tus cuotas pasarian del 30 % de tu ingreso")
    if f["dias_rojo_3m"] > 0:
        razones.append("tuviste dias en rojo en los ultimos 3 meses")
    if p_rojo > 0.30:
        razones.append("hay una probabilidad alta de quedar en rojo en 30 dias")
    return (not razones), razones


def candidatos(c: dict) -> list[dict]:
    """c: features observables, pronostico, salud, nivel, departamento, tipo_trabajo, tcea y, si existen, duplicadas, evento_ingreso y tasa_ref."""
    f, pr = c["features"], c.get("pronostico", {})
    ingreso, gasto = f["ingreso_medio"], _gasto_mensual(f)
    p_rojo = float(pr.get("p_rojo", 0.0))
    conf = confianza(pr.get("ancho_rel"))
    out = []

    if p_rojo >= 0.25:
        dia = pr.get("dia_riesgo")
        out.append({"id": "aviso_dia_de_riesgo", "accion": f"Tu saldo podria quedar en rojo{f' hacia el dia {int(dia)}' if dia else ''}: mueve un gasto grande para despues de tu cobro o aparta lo que puedas hoy.",
                    "impacto_soles": round(min(gasto * 0.25, max(0.0, -float(pr.get("saldo_bajo", 0.0)))) or gasto * 0.15, 0), "urgencia": 1.0, "facilidad": 0.8,
                    "por_que": [f"probabilidad de quedar en rojo en 30 dias: {p_rojo:.0%}", f"saldo esperado: S/ {pr.get('saldo_esperado', 0):,.0f}"], "supuestos": ["el pronostico usa tu historial y el calendario de pagos"],
                    "confianza": conf})
    if c.get("duplicadas"):
        monto = float(c.get("monto_duplicada", 30.0))
        out.append({"id": "cancelar_suscripcion_duplicada", "accion": "Cancela la suscripcion que pagas dos veces.", "impacto_soles": round(monto * 12, 0), "urgencia": 0.6, "facilidad": 0.95,
                    "por_que": ["tienes dos cobros del mismo servicio cada mes"], "supuestos": ["el monto mensual del duplicado es el ultimo cobro"], "confianza": "alta", "puntos": "cancelar_suscripcion_duplicada"})
    if f["pct_hormiga"] > 0.07:
        out.append({"id": "reducir_gasto_hormiga", "accion": "Baja un 20 % tus gastos pequenos de delivery y antojos.", "impacto_soles": round(0.2 * f["pct_hormiga"] * gasto * 12, 0), "urgencia": 0.4,
                    "facilidad": 0.6, "por_que": [f"los gastos hormiga son {f['pct_hormiga']:.0%} de tu gasto"], "supuestos": ["recortas el 20 % sin cambiar el resto"], "confianza": "media"})
    if f["cv_ingreso"] > 0.40:
        reserva = ingreso * f["cv_ingreso"]
        out.append({"id": "sueldo_lucas", "accion": f"Activa tu Sueldo Lucas: guarda lo que te sobre en meses buenos y usa un monto fijo de unos S/ {max(ingreso - reserva / 6, 0) / 2:,.0f} por quincena.", "impacto_soles": round(reserva, 0),
                    "urgencia": 0.7, "facilidad": 0.55, "por_que": [f"tu ingreso varia mucho de un mes a otro (variacion {f['cv_ingreso']:.0%})"],
                    "supuestos": ["la reserva objetivo es un mes malo tipico: ingreso medio x variacion", "el monto fijo reparte esa reserva en 6 meses"], "confianza": "media"})
    if f["colchon_observado"] < 1.0:
        meta = gasto
        out.append({"id": "meta_colchon", "accion": f"Arma un colchon de un mes de gastos (S/ {meta:,.0f}) con S/ {meta / 12:,.0f} por quincena.", "impacto_soles": round(meta, 0), "urgencia": 0.65, "facilidad": 0.5,
                    "por_que": [f"hoy tu colchon alcanza para {f['colchon_observado']:.1f} meses de ingreso"], "supuestos": ["aporte fijo durante 12 quincenas"], "confianza": "media", "puntos": "aporte_a_meta_de_ahorro"})
    ev = c.get("evento_ingreso")
    if ev:
        monto = float(ev["monto"])
        a_colchon = min(monto, max(gasto * 3 - f["colchon_observado"] * ingreso, 0)) if f["colchon_observado"] < 3 else 0.0
        a_deuda = 0.0
        if c.get("tcea", 0) > TCEA_DEUDA_CARA and c.get("deuda", 0) > 0:
            a_deuda = min(monto - a_colchon, c["deuda"] * 0.5)
        resto = max(monto - a_colchon - a_deuda, 0)
        out.append({"id": "plan_ingreso_extra", "accion": f"Entraron S/ {monto:,.0f} ({ev['origen']}): propon repartirlos asi: colchon S/ {a_colchon:,.0f}, deuda cara S/ {a_deuda:,.0f}, meta o gusto S/ {resto:,.0f}.",
                    "impacto_soles": round(a_colchon + a_deuda, 0), "urgencia": 0.9, "facilidad": 0.85, "por_que": [f"recibiste un ingreso extra por {ev['origen']}", "primero se cubre el colchon y la deuda mas cara"],
                    "supuestos": ["colchon objetivo: 3 meses de gastos", "se destina hasta el 50 % de la deuda cara"], "confianza": "alta"})
    dep = c.get("departamento")
    alerta = RC.alerta_fen(dep, c.get("hoy")) if dep else None
    if alerta:
        fondo = gasto * (2 if alerta["nivel"] == "alta" else 1)
        out.append({"id": "prevencion_fen", "accion": f"Vives en {dep}, zona con exposicion {alerta['nivel']} a lluvias por El Nino: prepara tu hogar y un fondo de S/ {fondo:,.0f}.",
                    "impacto_soles": round(fondo, 0), "urgencia": 1.0 if alerta["nivel"] == "alta" else 0.8, "facilidad": 0.5, "alerta": alerta,
                    "por_que": ["el ENFEN mantiene la alerta de El Nino costero", alerta["motivo"]], "supuestos": ["el fondo cubre 1 o 2 meses de gastos segun la exposicion"], "confianza": "media",
                    "puntos": "accion_de_prevencion_ante_el_nino"})
        cat = catalogo()["mejora_vivienda_prevencion"]
        tea = (c.get("tasa_ref", 4.5) + cat["supuestos"]["tea_sobre_tasa_referencia_pp"] - cat["supuestos"]["descuento_preferencial_pp"]) / 100
        monto = 4000.0
        cuota = cuota_mensual(monto, tea, 18)
        ok, razones = idoneo_para_credito(f, p_rojo, cuota)
        if ok:
            out.append({"id": "oferta_mejora_vivienda", "accion": f"Podrias mejorar tu vivienda con un credito de unos S/ {monto:,.0f} a 18 meses (cuota estimada S/ {cuota:,.0f}).", "impacto_soles": None, "urgencia": 0.75,
                        "facilidad": 0.4, "tipo_producto": cat["tipo_producto"], "por_que": ["estas en zona expuesta", "pasas las reglas de idoneidad: colchon, cuotas y dias en rojo"],
                        "supuestos": [f"tasa efectiva anual de {tea:.1%} (tasa de referencia del BCRP + margen supuesto - descuento preferencial supuesto)", "simulacion; no es una oferta real"], "confianza": "media"})
    if c.get("baja_de_tasa") and c.get("tcea", 0) > TCEA_DEUDA_CARA and c.get("deuda", 0) > 0:
        out.append({"id": "comparar_tasas", "accion": "Bajaron las tasas: compara el costo de tu deuda actual con otras opciones antes de decidir.", "impacto_soles": None, "urgencia": 0.6, "facilidad": 0.7,
                    "por_que": [f"tu deuda cuesta {c['tcea']:.0%} al ano y la tasa de referencia bajo"], "supuestos": ["es una comparacion educativa, no una oferta"], "confianza": "media"})
    from src.models import ofertas as O  # import tardio: ofertas usa funciones de este modulo
    out += O.ofertas_por_perfil(c, c.get("top_categorias"))
    return out


def filtrar_seguridad(recs: list[dict], c: dict) -> list[dict]:
    f, p_rojo = c["features"], float(c.get("pronostico", {}).get("p_rojo", 0.0))
    seguras = []
    for r in recs:
        if r["id"] in ("oferta_mejora_vivienda",) and not idoneo_para_credito(f, p_rojo)[0]:
            continue
        if r["id"] == "comparar_tasas" and f["colchon_observado"] < 1.0 and f["dias_rojo_3m"] > 0:
            r = {**r, "accion": "Antes de mirar tasas, prioriza cubrir tus dias en rojo; luego compara con calma."}
        r.setdefault("tu_decides", True)
        seguras.append(r)
    return seguras


def recomendar(c: dict, n: int = 3) -> list[dict]:
    """Top n por urgencia x facilidad x peso del nivel (los niveles bajos reciben primero lo urgente y simple)."""
    nivel = c.get("nivel", "aprendiz")
    esc = N._cfg()["escalera"]
    peso_facil = 1.0 + 0.5 * (len(esc) - 1 - esc.index(nivel)) / max(len(esc) - 1, 1)
    rechazadas = {k for k, v in c.get("memoria", {}).get("respuestas_reco", {}).items() if v == "no_me_sirve"}
    recs = [r for r in filtrar_seguridad(candidatos(c), c) if r["id"] not in rechazadas]
    ingreso = max(c["features"]["ingreso_medio"], 1.0)
    for r in recs:
        imp = (r["impacto_soles"] or 0) / ingreso
        r["puntaje"] = round(r["urgencia"] * (r["facilidad"] ** peso_facil) * (1 + min(imp, 1.0)), 4)
        if r.get("puntos"):
            r["puntos_que_ganas"] = N.puntos_por(r["puntos"], nivel)
    return sorted(recs, key=lambda r: r["puntaje"], reverse=True)[:n]
