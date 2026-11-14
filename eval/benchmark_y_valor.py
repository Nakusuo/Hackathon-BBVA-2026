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

from src.agent.repositorio import Repositorio  # noqa: E402
from src.comun.rutas import MODELOS  # noqa: E402
from src.generador.contexto import cargar_yaml  # noqa: E402
from src.models import recomendador as REC  # noqa: E402

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
    parar[0] = True
    return {"clientes": n, "carga_modelos_y_datos_s": round(carga, 1), "contexto_por_cliente_ms": round(1000 * t_ctx / n, 2), "recomendaciones_por_cliente_ms": round(1000 * t_rec / n, 2),
            "recomendaciones_por_segundo": round(n / t_rec, 0), "pico_memoria_gb": round(pico[0] / 1e9, 2), "pronostico_30d_filas": len(repo.origen), "pronostico_30d_ms_por_cliente": round(1000 * t_pred / max(len(repo.origen), 1), 3)}


def valor() -> dict:
    imp = json.load(open(os.path.join(MODELOS, "metricas_impacto.json"), encoding="utf-8"))
    niv = cargar_yaml("niveles.yaml")["puntos"]
    d = imp["diferencias"]["lucas_vs_nada"]
    colchon = d["colchon_adicional_soles"]["media"]
    interes = d["intereses_evitados_soles_por_mes"]["media"]
    dias = d["dias_rojo_evitados_por_cliente_mes"]["media"]
    N = SUPUESTOS_VALOR["usuarios_activos_escenario_conservador"]
    margen = SUPUESTOS_VALOR["margen_anual_sobre_saldo_apartado"]
    ingreso_fondeo = N * colchon * margen
    costo_puntos = N * SUPUESTOS_VALOR["puntos_promedio_por_usuario_al_mes"] * 12 * niv["valor_por_punto_soles"]
    vpp = niv["valor_por_punto_soles"]
    margen_por_usuario = colchon * margen
    equilibrio_pts_mes = margen_por_usuario / (12 * vpp)
    sens = {f"{p} puntos por usuario al mes": {"costo_de_puntos_soles": N * p * 12 * vpp, "valor_neto_soles": ingreso_fondeo - N * p * 12 * vpp} for p in (20, 40, 60, 80, 120)}
    return {"punto_de_equilibrio": {"margen_por_usuario_al_anio_soles": margen_por_usuario, "puntos_por_usuario_al_mes_que_igualan_el_margen": equilibrio_pts_mes,
                                    "lectura": "si el usuario promedio gana mas puntos que este numero, el programa cuesta mas que el fondeo que genera; hay que bajar el valor del punto o premiar solo conductas que den ingreso"},
            "sensibilidad_costo_de_puntos": sens, "supuestos": SUPUESTOS_VALOR, "por_cliente": {"colchon_adicional_soles": colchon, "intereses_evitados_soles_por_mes": interes, "dias_en_rojo_evitados_por_mes": dias},
            "entidad_por_anio_escenario_conservador": {"usuarios": N, "margen_por_fondeo_de_lo_apartado_soles": ingreso_fondeo, "costo_de_puntos_soles": costo_puntos, "valor_neto_soles": ingreso_fondeo - costo_puntos,
                                                       "nota": "solo cuenta el fondeo de lo apartado; retencion, mora evitada y venta cruzada idonea no se valoran sin piloto"},
            "ahorro_del_cliente_por_anio_soles": interes * 12}


if __name__ == "__main__":
    e = medir()
    json.dump(e, open(os.path.join(MODELOS, "metricas_escala.json"), "w", encoding="utf-8"), indent=1)
    print(e)
    if os.path.isfile(os.path.join(MODELOS, "metricas_impacto.json")):
        v = valor()
        json.dump(v, open(os.path.join(MODELOS, "metricas_valor.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(json.dumps(v, indent=1, ensure_ascii=False))
