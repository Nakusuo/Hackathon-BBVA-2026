"""Evaluacion del RAG por separado: recuperacion (recall@k, MRR y diversidad) para cada configuracion, con y sin filtro de modulo, separando preguntas simples
de compuestas, y filtro de relevancia tipo CRAG (rechazar lo que el indice no puede responder).
Configuraciones: denso, palabras (BM25), hibrido (RRF), hibrido + multiconsulta (descompone preguntas compuestas) y hibrido + multiconsulta + MMR."""
import numpy as np

from src.generador.contexto import cargar_yaml
from src.rag.indice import Buscador, descomponer

CONFIGURACIONES = {
    "denso": dict(modo="denso"),
    "bm25": dict(modo="bm25"),
    "hibrido": dict(modo="hibrido"),
    "hibrido + multiconsulta": dict(modo="hibrido", multiconsulta=True),
    "hibrido + multiconsulta + MMR": dict(modo="hibrido", multiconsulta=True, mmr=0.7),
}


def _docs(it: dict) -> list[str]:
    return it["doc"] if isinstance(it["doc"], list) else [it["doc"]]


def _posicion(it: dict, resultados: list[dict]):
    return next((i for i, x in enumerate(resultados) if any(d in x["documento"] for d in _docs(it))), None)


def evaluar_recuperacion(b: Buscador, k: int = 4) -> dict:
    items = cargar_yaml("preguntas_rag.yaml")["con_respuesta"]
    compuesta = [len(descomponer(it["q"])) > 1 for it in items]
    res = {}
    for nombre, cfg in CONFIGURACIONES.items():
        for filtrar in (False, True):
            hits, rr, docs_distintos = [], [], []
            for it in items:
                r = b.buscar(it["q"], k=k, modulo=it["modulo"] if filtrar else None, **cfg)
                pos = _posicion(it, r)
                hits.append(pos is not None)
                rr.append(1 / (pos + 1) if pos is not None else 0.0)
                docs_distintos.append(len({x["documento"] for x in r}))
            hits, rr, comp = np.array(hits), np.array(rr), np.array(compuesta)
            res[f"{nombre}{' + filtro de modulo' if filtrar else ''}"] = {
                f"recall@{k}": float(hits.mean()), "mrr": float(rr.mean()), "documentos_distintos_en_top": float(np.mean(docs_distintos)), "n": len(items),
                f"recall@{k}_simples": float(hits[~comp].mean()), f"recall@{k}_compuestas": float(hits[comp].mean()) if comp.any() else None, "n_compuestas": int(comp.sum())}
    return res


def calibrar_filtro_relevancia(b: Buscador, multiconsulta: bool = False) -> dict:
    """Busca el umbral de similitud del mejor fragmento que separa preguntas con respuesta de preguntas fuera del indice.
    Se calibra con las mismas preguntas con las que se reporta: la exactitud es optimista y se dice asi en el informe."""
    cfg = cargar_yaml("preguntas_rag.yaml")
    ok = np.array([b.buscar(it["q"], k=1, modo="denso", multiconsulta=multiconsulta)[0]["similitud"] for it in cfg["con_respuesta"]])
    fuera = np.array([b.buscar(q, k=1, modo="denso", multiconsulta=multiconsulta)[0]["similitud"] for q in cfg["fuera"]])
    mejor = (0.0, 0.0)
    for u in np.unique(np.concatenate([ok, fuera])):
        acc = (np.mean(ok >= u) + np.mean(fuera < u)) / 2
        if acc > mejor[0] or (acc == mejor[0] and u > mejor[1]):
            mejor = (float(acc), float(u))
    pares = [(o > f) for o in ok for f in fuera]
    return {"umbral": mejor[1], "exactitud_balanceada": mejor[0], "auc": float(np.mean(pares)), "similitud_con_respuesta": {"media": float(ok.mean()), "min": float(ok.min())},
            "similitud_fuera_del_indice": {"media": float(fuera.mean()), "max": float(fuera.max())}, "n_con_respuesta": len(ok), "n_fuera": len(fuera),
            "con_los_umbrales_actuales": {"umbral_en_uso": 0.70, "con_respuesta_aceptadas": float(np.mean(ok >= 0.70)), "fuera_rechazadas": float(np.mean(fuera < 0.70))}}
