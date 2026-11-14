"""Evalua el RAG (recuperacion por configuracion y filtro de relevancia tipo CRAG) y guarda models/metricas_rag.json.
Uso: python eval/evaluar_rag.py   (necesita Ollama con nomic-embed-text y el indice de docs/rag/indice)"""
import json
import os
import sys
import time
import warnings

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
warnings.filterwarnings("ignore")

from src.comun.huella import RAG, huella  # noqa: E402
from src.comun.rutas import INDICE_RAG, MODELOS  # noqa: E402
from src.rag import evaluar as E  # noqa: E402
from src.rag.indice import Buscador  # noqa: E402


def main():
    t0 = time.time()
    b = Buscador()
    out = {"recuperacion": E.evaluar_recuperacion(b), "filtro_relevancia": E.calibrar_filtro_relevancia(b), "filtro_relevancia_multiconsulta": E.calibrar_filtro_relevancia(b, multiconsulta=True),
           "indice": json.load(open(os.path.join(INDICE_RAG, "info.json"), encoding="utf-8")), "segundos": round(time.time() - t0, 1), "huella_codigo": huella(RAG)}
    json.dump(out, open(os.path.join(MODELOS, "metricas_rag.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cols = ["recall@4", "mrr", "documentos_distintos_en_top", "recall@4_simples", "recall@4_compuestas"]
    print(f"{'configuracion':52s}" + "".join(f"{c[:22]:>24s}" for c in cols))
    for nombre, m in out["recuperacion"].items():
        print(f"{nombre:52s}" + "".join(f"{(m[c] if m[c] is not None else float('nan')):24.3f}" for c in cols))
    n = next(iter(out["recuperacion"].values()))
    print(f"\npreguntas con respuesta: {n['n']} ({n['n_compuestas']} compuestas); fuera del indice: {out['filtro_relevancia']['n_fuera']}")
    for k in ("filtro_relevancia", "filtro_relevancia_multiconsulta"):
        f = out[k]
        print(k, {x: (round(f[x], 4) if isinstance(f[x], float) else f[x]) for x in ("umbral", "exactitud_balanceada", "auc")}, "| con el umbral 0.70 en uso:", {a: round(c, 3) for a, c in f["con_los_umbrales_actuales"].items()})
    print(f"{out['segundos']} s")


if __name__ == "__main__":
    main()
