"""Evidencia de escalabilidad (tiempos y memoria medidos) y calculadora de valor para la entidad con supuestos visibles.
Uso: python eval/benchmark_y_valor.py   ->  models/metricas_escala.json y models/metricas_valor.json"""
import json
import os
import sys
import threading
import time
import warnings

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
warnings.filterwarnings("ignore")
os.environ["LLM_PROVIDER"] = "plantillas"

import psutil  # noqa: E402

from src.agente_analitico.repositorio import Repositorio  # noqa: E402
from src.comun.rutas import MODELOS  # noqa: E402
from src.models import programa_puntos as PP, recomendador as REC  # noqa: E402

# Supuestos del equipo, todos visibles. La entidad que integre Lucas los reemplaza por los suyos.
SUPUESTOS_VALOR = {
    "margen_anual_sobre_saldo_apartado": 0.03,     # margen financiero del banco por cada sol que el cliente aparta (supuesto)
    "usuarios_activos_escenario_conservador": 100_000,
    "puntos_promedio_por_usuario_al_mes": 120,     # supuesto: cerca de dos conductas sanas por mes
    "aceptacion_de_la_recomendacion": "ya incluida: el impacto se simulo con la probabilidad de aceptacion de cada cliente",
    "retencion_y_mora": "no se asigna valor: no hay evidencia publica causal; lo mediria un piloto con grupo de control",
}


def medir() -> dict:
    pico = [0]
    parar = [False]

    def vigilar():
        p = psutil.Process(os.getpid())
        while not parar[0]:
            pico[0] = max(pico[0], p.memory_info().rss)
            time.sleep(0.05)
    threading.Thread(target=vigilar, daemon=True).start()
    t = time.time()
    repo = Repositorio()
    carga = time.time() - t
    ids = list(repo.clientes.index)
    t = time.time()
    ctxs = [repo.contexto(c) for c in ids]
    t_ctx = time.time() - t
    t = time.time()
    for c in ctxs:
        REC.recomendar(c, 3)
    t_rec = time.time() - t
    n = len(ids)
    pron = repo.pron["modelo"]
    t = time.time()
    pron.predecir(repo.origen)
    t_pred = time.time() - t
    t = time.time()
    repo.serie["modelo"].predecir(repo.origen)   # los 30 dias de un cliente (saldo esperado y banda al 80 % de cada dia)
    t_ser = time.time() - t
    parar[0] = True
    return {"clientes": n, "serie_diaria_30_dias_ms_por_cliente": round(1000 * t_ser / max(len(repo.origen), 1), 3), "carga_modelos_y_datos_s": round(carga, 1), "contexto_por_cliente_ms": round(1000 * t_ctx / n, 2), "recomendaciones_por_cliente_ms": round(1000 * t_rec / n, 2),
            "recomendaciones_por_segundo": round(n / t_rec, 0), "pico_memoria_gb": round(pico[0] / 1e9, 2), "pronostico_30d_filas": len(repo.origen), "pronostico_30d_ms_por_cliente": round(1000 * t_pred / max(len(repo.origen), 1), 3)}


def valor() -> dict:
    """Valor para la entidad en dos lecturas. Bruta: la comision del consumo y el margen de lo apartado financian los puntos (atribuye todo al programa).
    Conservadora: solo cuenta lo que Lucas genera de mas (el colchon adicional medido) y calcula cuanto debe crecer el consumo para que el programa se pague solo."""
    imp = json.load(open(os.path.join(MODELOS, "metricas_impacto.json"), encoding="utf-8"))
    pp = json.load(open(os.path.join(MODELOS, "metricas_programa_puntos.json"), encoding="utf-8"))
    d = imp["diferencias"]["lucas_vs_nada"]
    colchon = d["colchon_adicional_soles"]["media"]
    margen = pp["supuestos"]["margen_anual_sobre_saldo_apartado"]
    N = SUPUESTOS_VALOR["usuarios_activos_escenario_conservador"]
    t = pp["total"]
    fondeo_lucas = colchon * margen
    consumo_elegible = t["comision_anual"] / pp["supuestos"]["comision_por_consumo"]
    comision_por_sol = pp["supuestos"]["comision_por_consumo"]
    uplift_necesario = max((t["costo_anual"] - fondeo_lucas) / (consumo_elegible * comision_por_sol), 0.0) if consumo_elegible else None
    sens = {f"{round(u * 100)} % mas de consumo": {"valor_neto_por_usuario_anual": fondeo_lucas + u * consumo_elegible * comision_por_sol - t["costo_anual"],
                                                  "valor_neto_escenario": N * (fondeo_lucas + u * consumo_elegible * comision_por_sol - t["costo_anual"])} for u in (0.0, 0.05, 0.10, 0.15, 0.20)}
    return {"supuestos": {**SUPUESTOS_VALOR, **pp["supuestos"], "valor_por_punto_soles": pp["valor_por_punto"]},
            "por_cliente_lucas": {"colchon_adicional_soles": colchon, "dias_en_rojo_evitados_por_mes": d["dias_rojo_evitados_por_cliente_mes"]["media"], "intereses_evitados_soles_por_mes": d["intereses_evitados_soles_por_mes"]["media"]},
            "programa_de_puntos": {"puntos_por_usuario_al_mes": t["puntos_por_usuario_al_mes"], "costo_por_usuario_al_anio": t["costo_anual"], "consumo_elegible_por_usuario_al_anio": consumo_elegible,
                                   "costo_sobre_ingreso_bruto": t["costo_sobre_ingreso"], "tope_de_reinversion": pp["supuestos"]["reinversion_maxima_de_la_comision"], "topes_por_nivel": pp["topes_de_reinversion"],
                                   "por_nivel": pp["por_nivel"]},
            "lectura_bruta": {"ingreso_por_usuario_al_anio": t["ingreso_anual"], "neto_por_usuario_al_anio": t["neto_bruto_por_usuario_anual"], "neto_escenario": t["neto_bruto_anual_escenario"],
                              "aviso": "atribuye al programa toda la comision del consumo y todo el margen de lo apartado: es un techo, no una prediccion"},
            "lectura_conservadora": {"fondeo_adicional_por_usuario_al_anio": fondeo_lucas, "costo_de_puntos_por_usuario_al_anio": t["costo_anual"],
                                     "neto_por_usuario_sin_mas_consumo": fondeo_lucas - t["costo_anual"], "mas_consumo_necesario_para_pagarse": uplift_necesario, "sensibilidad": sens,
                                     "nota": "retencion, mora evitada y venta cruzada idonea no se valoran sin un piloto con grupo de control"},
            "proyeccion_a_futuro": PP.proyeccion_multianual(t, fondeo_lucas)}


if __name__ == "__main__":
    e = medir()
    json.dump(e, open(os.path.join(MODELOS, "metricas_escala.json"), "w", encoding="utf-8"), indent=1)
    print(e)
    if os.path.isfile(os.path.join(MODELOS, "metricas_impacto.json")):
        v = valor()
        json.dump(v, open(os.path.join(MODELOS, "metricas_valor.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(json.dumps(v, indent=1, ensure_ascii=False))
