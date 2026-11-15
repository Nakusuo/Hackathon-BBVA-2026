"""Prueba con OTRA muestra del generador: los modelos se entrenaron con la semilla 2026; aqui se generan 500 clientes nuevos con otra semilla (mismos parametros, otro azar)
y se evaluan SIN reentrenar. Si el pronostico solo hubiera aprendido el ruido de una muestra, aqui se caeria; si cubre y gana a los baselines tambien en una muestra nueva,
generaliza al proceso que simula el generador (no demuestra nada sobre datos reales). Los datos nuevos se escriben fuera del repo (carpeta temporal) y no se versionan.
Uso: python eval/evaluar_otra_semilla.py [--semilla 2027] [--salida RUTA]  ->  models/metricas_otra_semilla.json"""
import argparse
import json
import os
import sys
import tempfile
import time
import warnings

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
warnings.filterwarnings("ignore")

import joblib  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.metrics import adjusted_rand_score  # noqa: E402

from src.comun.rutas import MODELOS  # noqa: E402
from src.generador.pipeline import generar  # noqa: E402
from src.models import datos, pronostico as P, segmentacion as S, serie_diaria as SD  # noqa: E402

CORTES = {"entrena_hasta": "2023-06-30", "calibra_desde": "2023-10-01", "prueba_desde": "2024-01-01"}


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--semilla", type=int, default=2027)
    ap.add_argument("--salida", default=os.path.join(tempfile.gettempdir(), "lucas_otra_semilla"))
    a = ap.parse_args()
    if not os.path.isfile(os.path.join(a.salida, "meta.json")):
        log(f"generando 500 clientes con la semilla {a.semilla} en {a.salida}")
        generar(clientes=500, inicio="2019-01-01", fin="2025-12-31", semilla=a.semilla, salida=a.salida, lote=50, verbose=False)
    seg = joblib.load(os.path.join(MODELOS, "segmentacion.pkl"))
    pk = joblib.load(os.path.join(MODELOS, "pronostico.pkl"))
    sd = joblib.load(os.path.join(MODELOS, "serie_diaria.pkl"))
    meta_entrenamiento = json.load(open(os.path.join(MODELOS, "metricas.json"), encoding="utf-8"))
    s, cl, ctx = datos.cargar_series(a.salida), datos.cargar_clientes(a.salida), datos.cargar_contexto(a.salida)
    f = S.features_cliente(a.salida, "2024-01-01")   # el segmento se asigna con datos anteriores a la ventana de prueba
    lab = S.asignar(seg, f)
    seg_map = dict(zip(f.index, lab.tolist()))
    ari = float(adjusted_rand_score(cl.loc[f.index, "arquetipo"], lab))
    df = P.construir_origenes(s, cl, ctx, seg_map)
    C = P.cortes(df, CORTES)
    te, cal = C["prueba"], C["calibra"]
    log(f"origenes de prueba de la muestra nueva: {len(te):,}")
    pred = pk["modelo"].predecir(te)
    ma3 = P.baseline_ma3(te, P.cuantiles_residuo(cal, "net_ma3"))
    est = P.baseline_estructural(te, P.cuantiles_residuo(cal, "st_net"))
    sal = {"lightgbm": P.metricas(te, pred), "ma3": P.metricas(te, ma3), "perfil_estructural": P.metricas(te, est)}
    rojo = {"tasa_positivos": float(te["rojo30"].mean()), **P.metricas_rojo(te["rojo30"].to_numpy(), pred["p_rojo"].to_numpy())}
    tab = SD.metricas_por_dia(te, sd["modelo"].predecir(te))
    ref = meta_entrenamiento["pronostico"]["saldo_30d"]["lightgbm_optimizado"]
    ref_rojo = meta_entrenamiento["pronostico"]["rojo_30d_anticipacion"]["lightgbm_calibrado"]
    ari_ref = meta_entrenamiento["segmentacion"]["ari_vs_etiquetas"]["kprototypes"]["arquetipo"]
    R = {"semilla_de_entrenamiento": 2026, "semilla_de_la_muestra_nueva": a.semilla, "clientes": int(len(cl)), "origenes_de_prueba": int(len(te)), "sin_reentrenar": True,
         "saldo_30d_en_la_muestra_nueva": sal, "saldo_30d_en_la_muestra_de_entrenamiento": {"cobertura_80": ref["cobertura_80"], "mae_rel_ingreso": ref["mae_rel_ingreso"]},
         "rojo_30d_en_la_muestra_nueva": rojo, "rojo_30d_en_la_muestra_de_entrenamiento": {"pr_auc": ref_rojo["pr_auc"], "roc_auc": ref_rojo["roc_auc"]},
         "serie_diaria_en_la_muestra_nueva": {"cobertura_media": float(tab["cobertura_80"].mean()), "cobertura_minima": float(tab["cobertura_80"].min()), "cobertura_maxima": float(tab["cobertura_80"].max()),
                                              "mae_rel_medio": float(tab["mae_rel_ingreso"].mean())},
         "segmentacion": {"ari_con_los_arquetipos_en_la_muestra_nueva": ari, "ari_en_la_muestra_de_entrenamiento": ari_ref, "segmentos_asignados": {str(k): int(v) for k, v in zip(*np.unique(lab, return_counts=True))}},
         "lectura": ("Los modelos se entrenaron con la semilla 2026 y aqui se prueban en 500 clientes nuevos (otra semilla, mismos parametros): miden si generalizan al proceso del generador, no a datos reales. "
                     "La muestra nueva comparte los supuestos del generador, asi que no corrige un sesgo del diseno del generador.")}
    with open(os.path.join(MODELOS, "metricas_otra_semilla.json"), "w", encoding="utf-8") as fh:
        json.dump(R, fh, ensure_ascii=False, indent=1)
    log(f"saldo a 30 dias: cobertura {sal['lightgbm']['cobertura_80']:.3f} (entrenamiento {ref['cobertura_80']:.3f}), error {sal['lightgbm']['mae_rel_ingreso']:.3f} vs ma3 {sal['ma3']['mae_rel_ingreso']:.3f} "
        f"y estructural {sal['perfil_estructural']['mae_rel_ingreso']:.3f}; rojo PR-AUC {rojo['pr_auc']:.3f} (entrenamiento {ref_rojo['pr_auc']:.3f}); serie diaria cobertura "
        f"{R['serie_diaria_en_la_muestra_nueva']['cobertura_minima']:.3f} a {R['serie_diaria_en_la_muestra_nueva']['cobertura_maxima']:.3f}; ARI arquetipos {ari:.3f} (entrenamiento {ari_ref:.3f})")


if __name__ == "__main__":
    main()
