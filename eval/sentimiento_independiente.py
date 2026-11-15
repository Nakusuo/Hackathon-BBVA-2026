"""Evaluacion del sentimiento con un set INDEPENDIENTE: ni el lexico ni las plantillas del generador ni las 24 frases a mano tuvieron que ver con el.
Procedencia: Gemini escribe mensajes de trabajadores peruanos para cada clase SIN ver el lexico ni las plantillas (generacion); en una segunda pasada ciega, otra llamada
etiqueta las mismas frases mezcladas SIN ver la clase pedida (etiquetado). Solo se evalua con las frases en que ambas pasadas coinciden (consenso) y se informa la coincidencia.
No es un set anotado por personas: es independiente del codigo y de las plantillas, pero no de un modelo de lenguaje. Se guarda para reproducir (la generacion no es determinista).
Uso: python eval/sentimiento_independiente.py [--regenerar]  ->  data/evaluacion/sentimiento_independiente.json y models/metricas_sentimiento_independiente.json"""
import argparse
import hashlib
import json
import os
import random
import sys
import time
import warnings

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
warnings.filterwarnings("ignore")

import joblib  # noqa: E402
import numpy as np  # noqa: E402
import requests  # noqa: E402
from sklearn.metrics import f1_score  # noqa: E402

from src.comun.rutas import MODELOS, cargar_env  # noqa: E402
from src.models import clasificacion as KL  # noqa: E402

CLASES = {
    "positivo": "alivio, un logro o una buena noticia sobre su plata (cobro, ahorro, deuda pagada, ventas buenas)",
    "neutro": "una consulta o un pedido informativo sobre sus movimientos, fechas o metas, sin carga emocional",
    "preocupado": "incertidumbre o inquietud por no llegar a cubrir sus gastos, sin desesperacion (todavia hay margen)",
    "negativo": "angustia, desesperacion, enojo o una crisis de plata que ya ocurrio (sin plata, sin trabajo, servicio cortado, deudas que ahogan)",
}
POR_CLASE = 35
RUTA_SET = os.path.join(RAIZ, "data", "evaluacion", "sentimiento_independiente.json")


def _gemini_json(sistema: str, usuario: str, temperatura: float) -> object:
    cargar_env()
    clave, modelo = os.environ["GEMINI_API_KEY"], os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
    for intento in range(4):
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent", headers={"x-goog-api-key": clave}, timeout=90,
                          json={"systemInstruction": {"parts": [{"text": sistema}]}, "contents": [{"role": "user", "parts": [{"text": usuario}]}],
                                "generationConfig": {"temperature": temperatura, "maxOutputTokens": 6000, "responseMimeType": "application/json"}})
        if r.status_code in (429, 500, 503) and intento < 3:
            time.sleep(8 * (intento + 1))
            continue
        r.raise_for_status()
        from src.agente_analitico.proveedores import texto_de_gemini
        return json.loads(texto_de_gemini(r.json())), modelo
    raise RuntimeError("Gemini no respondio")


def generar() -> dict:
    frases = []
    for clase, descr in CLASES.items():
        sistema = ("Eres redactor de mensajes cortos de trabajadores peruanos a una app de finanzas personales (oficios variados: bodeguero, mototaxista, empleada de comercio, albanil, vendedora ambulante, "
                   "docente, repartidor). Escribes como la gente escribe de verdad: coloquial, a veces sin tildes o con faltas leves, de 6 a 25 palabras, sin cifras exactas. Responde SOLO un arreglo JSON de cadenas.")
        usuario = f"Escribe {POR_CLASE} mensajes DISTINTOS entre si (no repitas estructuras) de alguien que expresa: {descr}."
        textos, modelo = _gemini_json(sistema, usuario, 0.9)
        frases += [{"texto": str(t).strip(), "clase_pedida": clase} for t in textos if str(t).strip()]
        time.sleep(5)
    vistos, unicos = set(), []
    for f in frases:   # sin duplicados exactos
        k = f["texto"].lower()
        if k not in vistos:
            vistos.add(k)
            unicos.append(f)
    ids = list(range(len(unicos)))
    random.Random(7).shuffle(ids)   # el etiquetador no ve el orden ni la clase pedida
    sistema = ("Clasificas mensajes de trabajadores peruanos a una app de finanzas personales en una de cuatro clases: " + "; ".join(f"{c} = {d}" for c, d in CLASES.items())
               + ". Responde SOLO un objeto JSON {\"<id>\": \"<clase>\"} con todas las ids.")
    etiquetas = {}
    for i in range(0, len(ids), 70):
        lote = ids[i:i + 70]
        usuario = "\n".join(f"{j}: {unicos[j]['texto']}" for j in lote)
        r, modelo = _gemini_json(sistema, usuario, 0.0)
        etiquetas.update({int(k): v for k, v in r.items()})
        time.sleep(5)
    for j, f in enumerate(unicos):
        f["clase_etiquetada_a_ciegas"] = etiquetas.get(j)
        f["consenso"] = f["clase_pedida"] == f["clase_etiquetada_a_ciegas"]
    return {"procedencia": {"modelo": modelo, "generado_el": time.strftime("%Y-%m-%d"), "por_clase_pedidas": POR_CLASE, "clases": CLASES,
                            "huella_de_las_instrucciones": hashlib.sha256(json.dumps(CLASES, sort_keys=True).encode()).hexdigest()[:12],
                            "nota": "Escrito por un modelo de lenguaje sin ver el lexico, las plantillas del generador ni las frases a mano; etiquetado en una pasada ciega aparte. No es un set anotado por personas."},
            "frases": unicos}


def f1_con_intervalo(y, p, rep: int = 1000) -> dict:
    rng = np.random.default_rng(3)
    n = len(y)
    v = [f1_score(y[ix], p[ix], average="macro") for ix in (rng.integers(0, n, n) for _ in range(rep))]
    return {"f1_macro": float(f1_score(y, p, average="macro")), "ic95": [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--regenerar", action="store_true")
    a = ap.parse_args()
    if a.regenerar or not os.path.isfile(RUTA_SET):
        os.makedirs(os.path.dirname(RUTA_SET), exist_ok=True)
        with open(RUTA_SET, "w", encoding="utf-8") as f:
            json.dump(generar(), f, ensure_ascii=False, indent=1)
    S = json.load(open(RUTA_SET, encoding="utf-8"))
    fr = S["frases"]
    cons = [f for f in fr if f["consenso"]]
    X, y = [f["texto"] for f in cons], np.array([f["clase_pedida"] for f in cons])
    modelo = joblib.load(os.path.join(MODELOS, "sentimiento.pkl"))["modelo"]
    p_lex, p_lr = KL.baseline_lexico(X), modelo.predict(X)
    azar = max(float((y == c).mean()) for c in CLASES)   # acertar siempre la clase mas frecuente
    por_clase = {c: {"n": int((y == c).sum()), "lexico_recall": float((p_lex[y == c] == c).mean()), "tfidf_lr_recall": float((p_lr[y == c] == c).mean())} for c in CLASES}
    R = {"procedencia": S["procedencia"], "frases_generadas": len(fr), "frases_con_consenso": len(cons), "coincidencia_generacion_vs_etiquetado_ciego": len(cons) / len(fr),
         "coincidencia_por_clase": {c: float(np.mean([f["consenso"] for f in fr if f["clase_pedida"] == c])) for c in CLASES},
         "lexico": f1_con_intervalo(y, p_lex), "tfidf_lr": f1_con_intervalo(y, p_lr), "exactitud_de_la_clase_mayoritaria": azar, "por_clase": por_clase,
         "lectura": ("Set independiente del codigo, de las plantillas y de las frases a mano. Decide cual de los dos modelos generaliza a frases nuevas; no esta anotado por personas. "
                     "El sentimiento no esta en produccion: el texto no mejora el pronostico (ver docs/EVALUACION_ANALITICA.md).")}
    with open(os.path.join(MODELOS, "metricas_sentimiento_independiente.json"), "w", encoding="utf-8") as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(f"{len(fr)} frases, {len(cons)} con consenso ({R['coincidencia_generacion_vs_etiquetado_ciego']:.0%}); F1 macro lexico {R['lexico']['f1_macro']:.3f} {R['lexico']['ic95'][0]:.2f}-{R['lexico']['ic95'][1]:.2f}, "
          f"TF-IDF+LR {R['tfidf_lr']['f1_macro']:.3f} {R['tfidf_lr']['ic95'][0]:.2f}-{R['tfidf_lr']['ic95'][1]:.2f}; clase mayoritaria {azar:.2f}")


if __name__ == "__main__":
    main()
