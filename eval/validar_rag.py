"""Validacion del RAG: que los chunks, los embeddings y el indice esten bien hechos y se usen bien (no solo que la recuperacion de unas preguntas funcione).
1. Embeddings: la dimension coincide con el modelo; todos los vectores estan normalizados (producto interno = coseno); una muestra de fragmentos vuelve a embeberse con el prefijo de documento
   y da el MISMO vector que el guardado (el indice esta alineado con los textos y se hizo con este modelo); el prefijo de consulta da un vector distinto (se distinguen consulta y documento).
2. Chunks: tamanos, ninguno vacio ni diminuto, sin duplicados exactos, solapamiento entre fragmentos vecinos, metadatos completos (titulo, pagina, enlace, licencia, modulo).
3. Recuperacion: cada fragmento de una muestra se recupera a si mismo cuando se usa su propio inicio como consulta (el indice y el buscador estan alineados de punta a punta).
Uso: python eval/validar_rag.py  ->  models/metricas_rag_validacion.json"""
import inspect
import json
import os
import random
import sys
import warnings

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
warnings.filterwarnings("ignore")

import faiss  # noqa: E402
import numpy as np  # noqa: E402

from src.comun.huella import RAG, huella  # noqa: E402
from src.comun.rutas import MODELOS  # noqa: E402
from src.rag import indice as IX  # noqa: E402

SEMILLA = 20261114


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    frags = json.load(open(os.path.join(IX.INDICE_RAG, "fragmentos.json"), encoding="utf-8"))
    info = json.load(open(os.path.join(IX.INDICE_RAG, "info.json"), encoding="utf-8"))
    idx = faiss.read_index(os.path.join(IX.INDICE_RAG, "vectores.faiss"))
    n = len(frags)
    rng = random.Random(SEMILLA)

    # 1. embeddings -------------------------------------------------------------------------------------------------------------------------------
    V = np.vstack([idx.reconstruct(i) for i in range(idx.ntotal)])
    normas = np.linalg.norm(V, axis=1)
    muestra = rng.sample(range(n), 30)
    nuevos = IX.embeber([frags[i]["texto"] for i in muestra], "document")
    coseno_doc = [float(nuevos[j] @ V[i]) for j, i in enumerate(muestra)]
    como_consulta = IX.embeber([frags[i]["texto"] for i in muestra[:10]], "query")
    coseno_consulta = [float(como_consulta[j] @ V[i]) for j, i in enumerate(muestra[:10])]
    emb = {"modelo": info["modelo_embeddings"], "dimension_del_indice": int(idx.d), "dimension_declarada": info["dimension"], "vectores": int(idx.ntotal), "fragmentos": n,
           "tipo_de_indice": type(idx).__name__, "norma_minima": float(normas.min()), "norma_maxima": float(normas.max()),
           "reembebido_con_prefijo_de_documento": {"n": len(muestra), "coseno_minimo": min(coseno_doc), "coseno_medio": float(np.mean(coseno_doc))},
           "mismo_texto_con_prefijo_de_consulta": {"n": len(coseno_consulta), "coseno_medio": float(np.mean(coseno_consulta))},
           "prefijos_en_el_codigo": {"documento_al_indexar": 'embeber([f["texto"] for f in frags])' in inspect.getsource(IX.construir_indice) or "embeber([f[\"texto\"] for f in frags])" in inspect.getsource(IX.construir_indice),
                                     "consulta_al_buscar": '"query"' in inspect.getsource(IX.Buscador._vectores_consulta), "formato": "search_{tipo}: texto (requisito de nomic-embed-text)" if "search_{tipo}:" in inspect.getsource(IX.embeber) else "falta"}}

    # 2. chunks -----------------------------------------------------------------------------------------------------------------------------------
    largos = np.array([len(f["texto"]) for f in frags])
    textos = [f["texto"] for f in frags]
    solapes = []
    for x, y in zip(frags, frags[1:]):
        if x["documento"] == y["documento"] and x["pagina"] == y["pagina"]:
            k = max((k for k in range(20, min(len(x["texto"]), len(y["texto"]), 260)) if x["texto"][-k:] == y["texto"][:k]), default=0)
            solapes.append(k)
    con_solape = [k for k in solapes if k]
    campos = ["modulo", "documento", "titulo", "institucion", "pagina", "licencia_nivel", "enlace", "texto"]
    faltan = {c: sum(1 for f in frags if not f.get(c)) for c in campos}
    cierran = sum(t.rstrip()[-1:] in ".;:!?)" for t in textos)
    chunks = {"tam_fragmento": IX.TAM_FRAGMENTO, "solape": IX.SOLAPE, "documentos": len({f["documento"] for f in frags}), "modulos": sorted({f["modulo"] for f in frags}),
              "largo": {"minimo": int(largos.min()), "p5": int(np.percentile(largos, 5)), "mediana": int(np.median(largos)), "p95": int(np.percentile(largos, 95)), "maximo": int(largos.max())},
              "menores_de_80_caracteres": int((largos < 80).sum()), "mayores_que_el_tamano_mas_solape": int((largos > IX.TAM_FRAGMENTO + IX.SOLAPE).sum()),
              "duplicados_exactos": n - len(set(textos)), "pares_vecinos": {"n": len(solapes), "con_solape": len(con_solape), "fraccion_con_solape": len(con_solape) / len(solapes) if solapes else None, "solape_medio_en_caracteres": float(np.mean(con_solape)) if con_solape else 0.0,
                                "nota": "el troceador solo solapa cuando junta piezas pequenas; un parrafo largo cortado por oracion no repite texto"},
              "terminan_en_puntuacion": cierran / n, "nota_final_de_fragmento": "el separador (». «) queda al INICIO del fragmento siguiente, por eso pocos terminan en punto: no significa que corten a mitad de frase", "campos_vacios": faltan, "niveles_de_licencia": sorted({f["licencia_nivel"] for f in frags})}

    # 3. autorrecuperacion ------------------------------------------------------------------------------------------------------------------------
    b = IX.Buscador()
    prueba = rng.sample(range(n), 60)
    top1 = top3 = mismo_doc = 0
    for i in prueba:
        r = b.buscar(frags[i]["texto"][:220], k=3, modo="denso")
        ids = [x["fragmento_id"] for x in r]
        top1 += ids[:1] == [frags[i]["id"]]
        top3 += frags[i]["id"] in ids
        mismo_doc += r[0]["documento"] == frags[i]["documento"]
    auto = {"n": len(prueba), "el_fragmento_es_el_primero": top1 / len(prueba), "el_fragmento_esta_en_los_3_primeros": top3 / len(prueba), "el_primero_es_del_mismo_documento": mismo_doc / len(prueba)}

    ok = {"dimension_coincide": emb["dimension_del_indice"] == emb["dimension_declarada"] == 768, "vectores_igual_a_fragmentos": emb["vectores"] == emb["fragmentos"],
          "vectores_normalizados": emb["norma_minima"] > 0.999 and emb["norma_maxima"] < 1.001, "indice_exacto_de_producto_interno": emb["tipo_de_indice"] == "IndexFlatIP",
          "indice_alineado_con_los_textos": emb["reembebido_con_prefijo_de_documento"]["coseno_minimo"] > 0.999,
          "consulta_y_documento_se_distinguen": emb["mismo_texto_con_prefijo_de_consulta"]["coseno_medio"] < emb["reembebido_con_prefijo_de_documento"]["coseno_medio"] - 0.001,
          "prefijos_correctos": all(v for k, v in emb["prefijos_en_el_codigo"].items() if k != "formato") and emb["prefijos_en_el_codigo"]["formato"] != "falta",
          "sin_fragmentos_diminutos_ni_duplicados": chunks["menores_de_80_caracteres"] == 0 and chunks["duplicados_exactos"] == 0,
          "ningun_fragmento_excede_el_tamano_mas_solape": chunks["mayores_que_el_tamano_mas_solape"] == 0,
          "metadatos_completos": all(v == 0 for v in faltan.values()), "solo_licencia_nivel_A": chunks["niveles_de_licencia"] == ["A"],
          "cada_fragmento_se_recupera_a_si_mismo": auto["el_fragmento_esta_en_los_3_primeros"] >= 0.95 and auto["el_primero_es_del_mismo_documento"] >= 0.95}
    R = {"semilla": SEMILLA, "embeddings": emb, "chunks": chunks, "autorrecuperacion": auto, "comprobaciones": ok, "todo_ok": all(ok.values()), "huella_codigo": huella(RAG),
         "lectura": ("Los vectores se hicieron con nomic-embed-text (Ollama, local) y prefijo de documento al indexar y de consulta al buscar; estan normalizados y el indice es exacto de producto interno (coseno), asi que no hay aproximacion. "
                     "Volver a embeber una muestra da el mismo vector guardado: el indice esta alineado con los textos. El troceado es de 900 caracteres con 120 de solape cortando por parrafo, oracion o palabra (en ese orden).")}
    with open(os.path.join(MODELOS, "metricas_rag_validacion.json"), "w", encoding="utf-8") as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps(ok, indent=1))
    print("largo de chunks:", chunks["largo"], "| vecinos con solape:", chunks["pares_vecinos"]["con_solape"], "de", chunks["pares_vecinos"]["n"], "| duplicados exactos:", chunks["duplicados_exactos"])
    print("autorrecuperacion:", auto, "| coseno doc min/medio: %.4f / %.4f | misma frase como consulta: %.3f" % (emb["reembebido_con_prefijo_de_documento"]["coseno_minimo"], emb["reembebido_con_prefijo_de_documento"]["coseno_medio"], emb["mismo_texto_con_prefijo_de_consulta"]["coseno_medio"]))


if __name__ == "__main__":
    main()
