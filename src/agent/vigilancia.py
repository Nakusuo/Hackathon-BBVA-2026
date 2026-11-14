"""Vigilancia en tiempo real: detecta eventos que cambian la situacion del cliente y le avisa con recomendaciones segun su perfil.
Eventos: baja de la tasa del BCRP, ingreso que entra a la cuenta (CTS, bono, retiro, dinero extra), nuevo comunicado del ENFEN para zonas expuestas y riesgo de rojo.
Maximo 3 avisos por semana por cliente. Las fuentes publicas se consultan con respaldo: API -> cache -> serie grabada."""
import os
import re
from datetime import datetime

import requests

from src.agent import memoria
from src.agent.grafo import responder
from src.bcrp.cliente import ultimo_con_variacion
from src.comun.rutas import DOCS_RAG
from src.models import riesgo_clima as RC

CATEGORIAS_INGRESO_EXTRA = {"retiro_afp": "retiro de fondos de pensiones", "bono_estado": "bono del Estado", "gratificacion": "gratificacion", "cts": "CTS", "ingreso_extra": "ingreso extra"}
UMBRAL_BAJA_TASA = 0.10  # puntos porcentuales


def detectar_baja_de_tasa() -> dict | None:
    t = ultimo_con_variacion("tasa_referencia")
    if t["variacion"] <= -UMBRAL_BAJA_TASA:
        return {"tipo": "baja_de_tasa", "desde": t["valor_previo"], "hasta": t["valor"], "variacion": t["variacion"], "fecha": t["fecha"], "origen_dato": t["origen"]}
    return None


def detectar_ingreso_extra(movimientos: list[dict], ingreso_mensual: float, minimo_fraccion: float = 0.5) -> dict | None:
    """movimientos: [{'categoria','monto','tipo'}] nuevos en la cuenta. Es 'extra' si es de una categoria extraordinaria y pesa al menos la mitad de un ingreso mensual."""
    for m in movimientos:
        if m.get("tipo") == "ingreso" and m.get("categoria") in CATEGORIAS_INGRESO_EXTRA and m["monto"] >= minimo_fraccion * ingreso_mensual:
            return {"tipo": "ingreso_extra", "origen": CATEGORIAS_INGRESO_EXTRA[m["categoria"]], "monto": float(m["monto"])}
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
    return {"tipo": "fen_comunicado", "numero": ultimo, "enlace": f"https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-{ultimo}-2026/"} if ultimo > ultimo_comunicado_conocido() else None


def detectar_riesgo_rojo(ctx: dict, umbral: float = 0.25) -> dict | None:
    p = ctx["pronostico"]
    return {"tipo": "riesgo_rojo", "p_rojo": p["p_rojo"], "dia_riesgo": p["dia_riesgo"]} if p["p_rojo"] >= umbral else None


def eventos_para(ctx: dict, globales: list[dict], movimientos: list[dict] | None = None) -> list[dict]:
    """Eventos que aplican a un cliente: los globales se filtran por su perfil (el del Nino, solo si vive en zona expuesta)."""
    ev = []
    for g in globales:
        if g["tipo"] == "fen_comunicado" and RC.alerta_fen(ctx["departamento"], ctx["hoy"]) is None:
            continue
        ev.append(g)
    if movimientos:
        e = detectar_ingreso_extra(movimientos, ctx["features"]["ingreso_medio"])
        if e:
            ev.append(e)
    r = detectar_riesgo_rojo(ctx)
    if r:
        ev.append(r)
    return ev


def avisar(app, repo, cid: str, eventos: list[dict], ahora: datetime | None = None) -> list[dict]:
    """Genera un aviso por evento con el agente (modo proactivo) respetando el tope semanal. Devuelve los avisos enviados."""
    enviados = []
    for e in eventos:
        if not memoria.puede_avisar(cid, ahora):
            break
        r = responder(app, cid, "", e)
        memoria.registrar_aviso(cid, e["tipo"], ahora)
        enviados.append({"customer_id": cid, "evento": e, "mensaje": r["respuesta"], "proveedor": r["proveedor"], "cifras_verificadas": r["cifras_verificadas"]})
    return enviados


def ciclo(app, repo, clientes: list[str], movimientos_nuevos: dict | None = None, consultar_red: bool = True) -> list[dict]:
    """Una pasada de vigilancia. Con consultar_red=False solo usa lo que se le pase (util en pruebas y demos sin internet)."""
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
        ctx = repo.contexto(cid)
        salida += avisar(app, repo, cid, eventos_para(ctx, globales, (movimientos_nuevos or {}).get(cid)))
    return salida
