"""Vigilancia en tiempo real: detecta eventos que cambian la situacion del cliente y le avisa con recomendaciones segun su perfil.
Eventos: baja de la tasa del BCRP, ingreso que entra a la cuenta (CTS, bono, retiro, gratificacion, dinero extra), gasto atipico, fechas del calendario laboral
(gratificacion, deposito de CTS, fin de la libre disposicion de la CTS), gratificacion que no llego, nuevo comunicado del ENFEN para zonas expuestas y riesgo de rojo.
Reglas para no dar falsos positivos:
  * Cada hecho se avisa una sola vez (clave de deduplicacion) y como maximo 3 avisos por semana por cliente, empezando por lo mas urgente.
  * Un dato publico desactualizado (serie grabada o muy vieja) no genera avisos: no se presenta como noticia.
  * 'Gratificacion pendiente' solo se avisa a quien ya recibio una antes y si hay informacion reciente de sus movimientos.
  * Un gasto es atipico solo si pesa al menos 30 % del ingreso mensual y no es un pago recurrente esperado (alquiler, cuotas, servicios).
Las fuentes publicas se consultan con respaldo: API -> cache -> serie grabada."""
import os
import re
from datetime import date, datetime, timedelta

import requests

from src.agente_analitico import datos_vivos as DV
from src.agente_analitico import memoria
from src.agente_analitico.grafo import responder
from src.bcrp.cliente import ultimo_con_variacion
from src.comun import reloj
from src.comun.rutas import DOCS_RAG
from src.models import calendario_laboral as CL
from src.models import riesgo_clima as RC

CATEGORIAS_INGRESO_EXTRA = {"retiro_afp": "retiro de fondos de pensiones", "bono_estado": "bono del Estado", "gratificacion": "gratificacion", "cts": "CTS", "ingreso_extra": "ingreso extra"}
CATEGORIAS_GASTO_ESPERADO = {"alquiler", "cuota_prestamo", "colegio", "luz", "agua", "internet", "celular", "seguro", "suscripcion", "pago_credito_informal", "ahorro_programado"}
UMBRAL_BAJA_TASA = 0.10        # puntos porcentuales
GASTO_ATIPICO_FRACCION = 0.30  # fraccion del ingreso mensual
DIAS_AVISO_CALENDARIO = 7
VENTANA_INFORMACION_DIAS = 45  # sin movimientos recientes del cliente no se puede afirmar que algo "no llego"
PRIORIDAD = {"riesgo_rojo": 0, "gratificacion_pendiente": 1, "ingreso_extra": 2, "gasto_atipico": 3, "calendario_laboral": 4, "libre_disposicion_por_vencer": 5, "baja_de_tasa": 6, "fen_comunicado": 7}


def detectar_baja_de_tasa() -> dict | None:
    t = ultimo_con_variacion("tasa_referencia")
    if not t["al_dia"]:   # un dato viejo o grabado no es una noticia
        return None
    if t["variacion"] <= -UMBRAL_BAJA_TASA:
        return {"tipo": "baja_de_tasa", "desde": t["valor_previo"], "hasta": t["valor"], "variacion": t["variacion"], "fecha": t["fecha"], "origen_dato": t["origen"], "clave": f"tasa:{t['fecha']}"}
    return None


def detectar_ingreso_extra(movimientos: list[dict], ingreso_mensual: float, minimo_fraccion: float = 0.5) -> dict | None:
    """movimientos: [{'categoria','monto','tipo'}] nuevos en la cuenta. Es 'extra' si es de una categoria extraordinaria y pesa al menos la mitad de un ingreso mensual."""
    for m in movimientos:
        if m.get("tipo") == "ingreso" and m.get("categoria") in CATEGORIAS_INGRESO_EXTRA and m["monto"] >= minimo_fraccion * ingreso_mensual:
            return {"tipo": "ingreso_extra", "origen": CATEGORIAS_INGRESO_EXTRA[m["categoria"]], "monto": float(m["monto"]), "clave": f"mov:{m['id']}" if m.get("id") else None}
    return None


def detectar_gasto_atipico(movimientos: list[dict], ingreso_mensual: float) -> list[dict]:
    """Un gasto que pesa mucho frente al ingreso y que no es un pago recurrente esperado."""
    out = []
    for m in movimientos:
        if m.get("tipo") != "gasto" or m.get("categoria") in CATEGORIAS_GASTO_ESPERADO:
            continue
        frac = m["monto"] / max(ingreso_mensual, 1.0)
        if frac >= GASTO_ATIPICO_FRACCION:
            out.append({"tipo": "gasto_atipico", "monto": float(m["monto"]), "categoria": m.get("categoria", "otros"), "fraccion_del_ingreso": round(frac, 3), "clave": f"mov:{m['id']}" if m.get("id") else None})
    return out


def detectar_calendario(ctx: dict) -> list[dict]:
    """Fechas del calendario laboral que se acercan (7 dias o menos) y fin cercano de la libre disposicion del 100 % de la CTS. Solo para quien le corresponde."""
    cal = ctx.get("calendario") or {}
    if not cal.get("aplica"):
        return []
    out = [{"tipo": "calendario_laboral", "evento": e, "clave": f"cal:{e['tipo']}:{e['fecha_limite']}"} for e in cal["eventos"] if e["estado"] in ("proximo", "hoy") and e["dias_para"] <= DIAS_AVISO_CALENDARIO]
    ld = cal["libre_disposicion_cts"]
    if ld["regimen_transitorio_vigente"] and ld["por_vencer"]:
        tramo = 15 if ld["dias_restantes"] <= 15 else 60
        out.append({"tipo": "libre_disposicion_por_vencer", "dias_restantes": ld["dias_restantes"], "vigente_hasta": ld["vigente_hasta"], "clave": f"libre:{ld['vigente_hasta']}:{tramo}"})
    return out


def detectar_atraso_gratificacion(ctx: dict, hoy: date) -> dict | None:
    """La gratificacion no llego a tiempo. Solo si el cliente ya recibio una antes (base en su historial) y hay informacion reciente de sus movimientos."""
    cal = ctx.get("calendario") or {}
    if not cal.get("aplica") or cal.get("base_origen") != "historial":
        return None
    if not (ctx["movimientos_vivos"]["n"] > 0 or ctx["desfase_datos_dias"] <= VENTANA_INFORMACION_DIAS):
        return None
    tol = CL.cfg()["gratificacion"]["tolerancia_dias_para_avisar_atraso"]
    for e in CL.eventos(hoy, cal["base_mensual"], desde_dias=30, hasta_dias=0):
        if e["tipo"] != "gratificacion" or e["dias_para"] >= -tol:
            continue
        lim = date.fromisoformat(e["fecha_limite"])
        recibida = any(m["tipo"] == "ingreso" and m["categoria"] == "gratificacion" for m in DV.listar(ctx["customer_id"], despues_de=lim - timedelta(days=20)))
        if not recibida:
            return {"tipo": "gratificacion_pendiente", "nombre": e["nombre"], "fecha_limite": e["fecha_limite"], "fecha_limite_texto": e["fecha_limite_texto"], "clave": f"pend:{e['fecha_limite']}"}
    return None


def ultimo_comunicado_conocido() -> int:
    carpeta = os.path.join(DOCS_RAG, "fenomeno_el_nino")
    nums = [int(x.group(1)) for f in os.listdir(carpeta) if (x := re.search(r"comunicado_(\d+)_", f))] if os.path.isdir(carpeta) else []
    return max(nums, default=0)


def detectar_comunicado_enfen(timeout: int = 15) -> dict | None:
    """Consulta la pagina del ENFEN y avisa si hay un comunicado con numero mayor al ultimo que tiene el RAG."""
    try:
        r = requests.get("https://enfen.imarpe.gob.pe/", timeout=timeout, headers={"User-Agent": "analitica-hackathon/1.0"})
        r.raise_for_status()
        numeros = [int(n) for n in re.findall(r"(?i)comunicado\s+oficial\s+enfen\s+n\S*\s*(\d{1,3})\s*-\s*2026", r.text)]
    except requests.RequestException:
        return None
    ultimo = max(numeros, default=0)
    return {"tipo": "fen_comunicado", "numero": ultimo, "enlace": f"https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-{ultimo}-2026/", "clave": f"fen:{ultimo}"} if ultimo > ultimo_comunicado_conocido() else None


def detectar_riesgo_rojo(ctx: dict, umbral: float = 0.25) -> dict | None:
    p = ctx["pronostico"]
    return {"tipo": "riesgo_rojo", "p_rojo": p["p_rojo"], "dia_riesgo": p["dia_riesgo"], "clave": f"rojo:{ctx['hoy']}"} if p["p_rojo"] >= umbral else None


def eventos_para(ctx: dict, globales: list[dict], movimientos: list[dict] | None = None, hoy: date | None = None) -> list[dict]:
    """Eventos que aplican a un cliente, del mas urgente al menos urgente: los globales se filtran por su perfil (el del Nino, solo si vive en zona expuesta)."""
    hoy = hoy or reloj.hoy()
    ev = []
    for g in globales:
        if g["tipo"] == "fen_comunicado" and RC.alerta_fen(ctx["departamento"], ctx["hoy"]) is None:
            continue
        ev.append(g)
    ingreso = ctx["features"]["ingreso_medio"]
    if movimientos:
        e = detectar_ingreso_extra(movimientos, ingreso)
        if e:
            ev.append(e)
        ev += detectar_gasto_atipico(movimientos, ingreso)
    ev += detectar_calendario(ctx)
    for e in (detectar_atraso_gratificacion(ctx, hoy), detectar_riesgo_rojo(ctx)):
        if e:
            ev.append(e)
    return sorted(ev, key=lambda e: PRIORIDAD.get(e["tipo"], 99))


def avisar(app, repo, cid: str, eventos: list[dict], ahora: datetime | None = None) -> list[dict]:
    """Genera un aviso por evento con el agente (modo proactivo) respetando el tope semanal y sin repetir un hecho ya avisado. Devuelve los avisos enviados."""
    enviados = []
    for e in eventos:
        if e.get("clave") and memoria.ya_avisado(cid, e["clave"]):
            continue
        if not memoria.puede_avisar(cid, ahora):
            break
        r = responder(app, cid, "", e)
        memoria.registrar_aviso(cid, e["tipo"], ahora, e.get("clave"))
        enviados.append({"customer_id": cid, "evento": e, "mensaje": r["respuesta"], "proveedor": r["proveedor"], "cifras_verificadas": r["cifras_verificadas"], "llamadas_llm": r["llamadas_llm"]})
    return enviados


def ciclo(app, repo, clientes: list[str], movimientos_nuevos: dict | None = None, consultar_red: bool = True) -> list[dict]:
    """Una pasada de vigilancia. Con consultar_red=False solo usa lo que se le pase y los datos vivos guardados (util en pruebas y demos sin internet).
    Sin movimientos_nuevos se leen los datos vivos de los ultimos 3 dias; la clave de deduplicacion evita avisar dos veces lo mismo."""
    hoy = reloj.hoy()
    globales = []
    if consultar_red:
        for f in (detectar_baja_de_tasa, detectar_comunicado_enfen):
            try:
                e = f()
            except Exception:
                e = None
            if e:
                globales.append(e)
    salida = []
    for cid in clientes:
        ctx = repo.contexto(cid, hoy)
        movs = (movimientos_nuevos or {}).get(cid)
        if movs is None:
            movs = DV.listar(cid, despues_de=hoy - timedelta(days=3), hasta=hoy)
        salida += avisar(app, repo, cid, eventos_para(ctx, globales, movs, hoy))
    return salida
