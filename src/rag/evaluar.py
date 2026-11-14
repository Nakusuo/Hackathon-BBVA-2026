"""Evaluacion del RAG por separado: recuperacion (recall@k y MRR, denso frente a palabras frente a hibrido, con y sin filtro de modulo)
y filtro de relevancia tipo CRAG (rechazar lo que el indice no puede responder)."""
import numpy as np

from src.generador.contexto import cargar_yaml
from src.rag.indice import Buscador


def evaluar_recuperacion(b: Buscador, k: int = 4) -> dict:
    cfg = cargar_yaml("preguntas_rag.yaml")["con_respuesta"]
    res = {}
    for modo in ("denso", "bm25", "hibrido"):
        for filtrar in (False, True):
            hits, rr = [], []
            for it in cfg:
                r = b.buscar(it["q"], k=k, modulo=it["modulo"] if filtrar else None, modo=modo)
                pos = next((i for i, x in enumerate(r) if it["doc"] in x["documento"]), None)
                hits.append(pos is not None)
                rr.append(1 / (pos + 1) if pos is not None else 0.0)
            res[f"{modo}{' + filtro de modulo' if filtrar else ''}"] = {f"recall@{k}": float(np.mean(hits)), "mrr": float(np.mean(rr)), "n": len(cfg)}
    return res


def calibrar_filtro_relevancia(b: Buscador) -> dict:
    """Busca el umbral de similitud del mejor fragmento que separa preguntas con respuesta de preguntas fuera del indice."""
    cfg = cargar_yaml("preguntas_rag.yaml")
    ok = np.array([b.buscar(it["q"], k=1, modo="denso")[0]["similitud"] for it in cfg["con_respuesta"]])
    fuera = np.array([b.buscar(q, k=1, modo="denso")[0]["similitud"] for q in cfg["fuera"]])
    mejor = (0.0, 0.0)
    for u in np.unique(np.concatenate([ok, fuera])):
        acc = (np.mean(ok >= u) + np.mean(fuera < u)) / 2
        if acc > mejor[0] or (acc == mejor[0] and u > mejor[1]):
            mejor = (float(acc), float(u))
    pares = [(o > f) for o in ok for f in fuera]
    return {"umbral": mejor[1], "exactitud_balanceada": mejor[0], "auc": float(np.mean(pares)), "similitud_con_respuesta": {"media": float(ok.mean()), "min": float(ok.min())},
            "similitud_fuera_del_indice": {"media": float(fuera.mean()), "max": float(fuera.max())}, "n_con_respuesta": len(ok), "n_fuera": len(fuera)}
