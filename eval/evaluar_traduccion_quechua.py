"""Evidencia objetiva de la traduccion al quechua y desde el quechua, contra el benchmark publico FLORES-200 (quechua de Ayacucho, quy_Latn).
No reemplaza a un hablante nativo: mide cuanto se parece la salida del agente a traducciones humanas de referencia, con chrF (a nivel de caracteres, apto para lenguas con mucha morfologia),
y la compara con un piso (copiar el espanol sin traducir). Usa el mismo flujo del agente (traducir(): protege cifras y nombres, proveedor Gemini).
FLORES-200 (Meta AI, NLLB Team; CC BY-SA 4.0) se descarga aparte, fuera del repo: https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz (solo se leen lineas de texto).
Uso: python eval/evaluar_traduccion_quechua.py --flores RUTA/flores200_dataset [--n 60]  ->  models/metricas_quechua.json (solo metricas e indices de lineas, no el texto de FLORES)"""
import argparse
import json
import os
import random
import sys
import time
import warnings

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
warnings.filterwarnings("ignore")

import numpy as np  # noqa: E402
from sacrebleu.metrics import CHRF  # noqa: E402

from src.agente_analitico import traduccion as TR  # noqa: E402
from src.comun.rutas import MODELOS  # noqa: E402

SEMILLA = 20261114
PAUSA_S = 4.5   # el plan gratuito de Gemini limita las llamadas por minuto


def leer(ruta: str) -> list[str]:
    with open(ruta, encoding="utf-8") as f:
        return [x.rstrip("\n") for x in f]


def puntaje(hip: list[str], ref: list[str], palabras: int = 0) -> float:
    return CHRF(word_order=palabras).corpus_score(hip, [ref]).score


def intervalo(hip: list[str], ref: list[str], palabras: int = 0, rep: int = 1000) -> list[float]:
    """IC95 por remuestreo de oraciones (percentiles 2.5 y 97.5 del chrF del corpus)."""
    rng = np.random.default_rng(SEMILLA)
    n = len(hip)
    v = [puntaje([hip[i] for i in ix], [ref[i] for i in ix], palabras) for ix in (rng.integers(0, n, n) for _ in range(rep))]
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]


def direccion(origen: str, destino: str, fuente: list[str], ref: list[str]) -> dict:
    hip, cayo, prov = [], 0, {}
    for i, t in enumerate(fuente):
        r = TR.traducir(t, origen, destino)
        hip.append(r["texto"])
        cayo += not r["ok"]
        prov[r["proveedor"]] = prov.get(r["proveedor"], 0) + 1
        time.sleep(PAUSA_S)
        if (i + 1) % 10 == 0:
            print(f"  {origen}->{destino}: {i + 1}/{len(fuente)}", flush=True)
    sin_traducir = sum(h.strip().lower() == f.strip().lower() for h, f in zip(hip, fuente))
    return {"n": len(fuente), "chrf": puntaje(hip, ref), "chrf_mas_mas": puntaje(hip, ref, 2), "ic95_chrf": intervalo(hip, ref),
            "piso_copiar_el_origen_chrf": puntaje(fuente, ref), "piso_copiar_el_origen_chrf_mas_mas": puntaje(fuente, ref, 2),
            "oraciones_que_cayeron_al_texto_original": int(cayo), "oraciones_devueltas_sin_traducir": int(sin_traducir), "proveedores": prov}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--flores", required=True, help="carpeta flores200_dataset descargada")
    ap.add_argument("--n", type=int, default=60)
    a = ap.parse_args()
    es, qu = (leer(os.path.join(a.flores, "devtest", f"{c}_Latn.devtest")) for c in ("spa", "quy"))
    assert len(es) == len(qu) == 1012
    idx = sorted(random.Random(SEMILLA).sample(range(len(es)), a.n))
    es_m, qu_m = [es[i] for i in idx], [qu[i] for i in idx]
    os.environ.pop("GOOGLE_TRANSLATE_API_KEY", None)   # la clave de Gemini no se usa contra otras APIs de Google
    print(f"{a.n} oraciones de FLORES-200 devtest (semilla {SEMILLA})", flush=True)
    R = {"fuente": "FLORES-200 devtest, par spa_Latn / quy_Latn (quechua de Ayacucho); Meta AI, NLLB Team; CC BY-SA 4.0", "semilla": SEMILLA, "n": a.n, "indices_de_linea_devtest": idx,
         "metrica": "chrF de sacrebleu (caracteres, beta 2) y chrF++ (con bigramas de palabras)", "proveedor_evaluado": "Gemini via traduccion.traducir() (con proteccion de cifras y nombres)",
         "es_a_qu": direccion("es", "qu", es_m, qu_m), "qu_a_es": direccion("qu", "es", qu_m, es_m),
         "lectura": ("Un chrF por encima del piso de copiar el origen muestra que la salida se parece a una traduccion humana mas que el propio texto sin traducir; no demuestra que un hablante la entienda. "
                     "Las referencias de FLORES estan en la ortografia del quechua de Ayacucho: diferencias de escritura (por ejemplo entre variedades) bajan el chrF aunque la traduccion sea correcta."),
         "limite": "No hay hablante nativo que la revise. FLORES es texto de noticias y enciclopedia: no es el lenguaje de las finanzas personales. Quechua sureno (Cusco-Collao y Ayacucho-Chanka); el agente lo declara como no validado."}
    with open(os.path.join(MODELOS, "metricas_quechua.json"), "w", encoding="utf-8") as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    for k in ("es_a_qu", "qu_a_es"):
        d = R[k]
        print(f"{k}: chrF {d['chrf']:.1f} (IC95 {d['ic95_chrf'][0]:.1f} a {d['ic95_chrf'][1]:.1f}), chrF++ {d['chrf_mas_mas']:.1f}; piso copiar el origen {d['piso_copiar_el_origen_chrf']:.1f}; "
              f"cayeron al original {d['oraciones_que_cayeron_al_texto_original']}/{d['n']}; sin traducir {d['oraciones_devueltas_sin_traducir']}")


if __name__ == "__main__":
    main()
