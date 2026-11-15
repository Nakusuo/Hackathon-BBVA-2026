"""Mapa de decision de una consulta y ahorro de tokens, con un ejemplo REAL: un parrafo de siete consultas pasa por el router de verdad (detectar_intencion), la pregunta nueva de concepto recupera los
fragmentos que devuelve el RAG de verdad (chunks ya embebidos, busqueda densa) y los tokens salen de lo medido en la QA con Gemini real. Nada de esto se escribe a mano.
Camino de cada consulta con la politica `LLM_USO=ahorro`:
  - seguridad, fuera de alcance o fuera de tema -> plantilla fija (0 tokens)
  - un tema conocido (pronostico, calendario, tipo de cambio, nivel, tasas, El Nino, ofertas...) -> los modelos y herramientas calculan y una plantilla redacta (0 tokens)
  - pregunta de concepto -> si ya se respondio y verifico para ese nivel, preguntas frecuentes (0 tokens); si es nueva, RAG (chunks -> embeddings -> top-3) y el LLM redacta, y se guarda
Salida: docs/presentacion/mapa_de_consultas.json (lo usan el diagrama y el informe)."""
import json
import os
import sys
import warnings

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
warnings.filterwarnings("ignore")

CONSULTAS = ["¿Llego a fin de mes con mi plata?", "¿Cuándo me cae la CTS y puedo retirarla?", "¿Cuánto está el dólar hoy?", "Pásale 200 soles a mi hermano",
             "¿Qué es la TCEA?", "que es la tcea", "Cuéntame un chiste"]
DESTINO = os.path.join(RAIZ, "docs", "presentacion", "mapa_de_consultas.json")


def generar(buscador) -> dict:
    from src.agente_analitico import faq as FQ
    from src.agente_analitico.grafo import INTENCIONES_CON_LLM, SIN_LLM, UMBRAL_RELEVANCIA, detectar_intencion
    qa = json.load(open(os.path.join(RAIZ, "models", "metricas_qa_agente.json"), encoding="utf-8"))["resumen"]["tokens_gemini"]
    entrada, salida = qa["entrada"] / qa["llamadas"], qa["salida"] / qa["llamadas"]
    frags = json.load(open(os.path.join(RAIZ, "docs", "rag", "indice", "fragmentos.json"), encoding="utf-8"))
    chars = sum(len(f["texto"]) for f in frags)
    filas, vistos, rag = [], set(), None
    for i, q in enumerate(CONSULTAS, 1):
        it = detectar_intencion(q)
        if it in SIN_LLM:
            ruta, llm = "plantilla_fija", False
        elif it not in INTENCIONES_CON_LLM:
            ruta, llm = "herramientas_y_plantilla", False
        elif FQ.normalizar(q) in vistos:
            ruta, llm = "preguntas_frecuentes", False
        else:
            vistos.add(FQ.normalizar(q))
            ruta, llm = "rag_y_ia", True
            if rag is None:
                r = buscador.buscar(q, k=3, modulo=None, modo="denso")
                rag = {"pregunta": q, "umbral_de_relevancia": UMBRAL_RELEVANCIA, "pasa_el_filtro": bool(r) and r[0]["similitud"] >= UMBRAL_RELEVANCIA,
                       "fragmentos": [{"titulo": x["titulo"], "pagina": x["pagina"], "similitud": x["similitud"], "caracteres": len(x["texto"]), "tokens_estimados": round(len(x["texto"]) / 4)} for x in r]}
        filas.append({"n": i, "consulta": q, "intencion": it, "camino": ruta, "usa_llm": llm, "tokens_de_entrada": round(entrada) if llm else 0, "tokens_de_salida": round(salida) if llm else 0})
    con_llm = sum(f["usa_llm"] for f in filas)
    sin_ruteo = len(filas) * (entrada + salida)
    con_ruteo = con_llm * (entrada + salida)
    R = {"consultas": filas, "rag": rag, "tokens_por_llamada_medidos_en_la_qa": {"entrada": round(entrada), "salida": round(salida), "llamadas_medidas": qa["llamadas"]},
         "todo_al_llm": round(sin_ruteo), "con_ruteo": round(con_ruteo), "ahorro": 1 - con_ruteo / sin_ruteo if sin_ruteo else 0.0,
         "tokens_del_corpus_completo": round(chars / 4), "tokens_de_los_3_fragmentos": sum(f["tokens_estimados"] for f in (rag or {"fragmentos": []})["fragmentos"]),
         "nota": "Tokens estimados con 4 caracteres por token; los tokens por llamada son el promedio medido en la QA con Gemini real (incluye llamadas cortas de traduccion). Politica LLM_USO=ahorro."}
    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    with open(DESTINO, "w", encoding="utf-8") as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    return R
