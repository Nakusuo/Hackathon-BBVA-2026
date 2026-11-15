"""Mapa de decision de una consulta y ahorro de tokens, con un ejemplo REAL: un parrafo de siete consultas pasa por el router de verdad (detectar_intencion), la pregunta nueva de concepto recupera los
fragmentos que devuelve el RAG de verdad (chunks ya embebidos, busqueda densa) y los tokens salen de lo medido en la QA con Gemini real. Nada de esto se escribe a mano.
Camino de cada consulta con la politica `LLM_USO=ahorro`:
  - seguridad, fuera de alcance o fuera de tema -> plantilla fija (0 tokens)
  - un tema conocido (pronostico, calendario, tipo de cambio, nivel, tasas, El Nino, ofertas...) -> los modelos y herramientas calculan y una plantilla redacta (0 tokens)
  - pregunta de concepto -> si ya se respondio y verifico para ese nivel, preguntas frecuentes (0 tokens); si es nueva, RAG (chunks -> embeddings -> top-3) y el LLM redacta, y se guarda
Ahorro en porcentajes y en soles: los tokens medidos por llamada (mensaje enviado, fuentes leidas por el RAG y respuesta) se multiplican por el precio publicado del modelo y por el tipo de cambio del BCRP.
Salida: docs/presentacion/mapa_de_consultas.json (lo usan el diagrama, las graficas en porcentaje y el informe)."""
import importlib.util
import json
import os
import sys
import warnings

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "backend"))
warnings.filterwarnings("ignore")

CONSULTAS = ["¿Llego a fin de mes con mi plata?", "¿Cuándo me cae la CTS y puedo retirarla?", "¿Cuánto está el dólar hoy?", "Pásale 200 soles a mi hermano",
             "¿Qué es la TCEA?", "que es la tcea", "Cuéntame un chiste"]
DESTINO = os.path.join(RAIZ, "docs", "presentacion", "mapa_de_consultas.json")
# Precio del modelo que usa el agente (nivel Standard de pago, texto; la salida incluye el razonamiento interno, que este modelo no cobra aparte: se comprobo en usageMetadata, total = entrada + salida).
PRECIO = {"modelo": "gemini-3.5-flash-lite", "usd_por_millon_de_entrada": 0.30, "usd_por_millon_de_salida": 2.50, "fuente": "https://aistudio.google.com/docs/pricing", "consultado": "2026-11-14",
          "nota": "El plan gratuito no cobra: esto es lo que costaria en produccion con el plan de pago. Sin descuentos por cache de contexto ni por lotes."}
ESCALA = 100_000   # consultas, para expresar el ahorro en soles; es un volumen de ejemplo, no un pronostico de uso


def _tipo_de_cambio() -> dict:
    """Ultimo tipo de cambio interbancario (venta) de la serie del BCRP que ya usa el proyecto. Se lee de la cache para que el resultado sea el mismo en cada corrida."""
    try:
        with open(os.path.join(RAIZ, "data", "generado", "cache_bcrp", "tc_interbancario_venta_diario.json"), encoding="utf-8") as f:
            per = json.load(f)["periods"]
        obs = [(p["name"], float(p["values"][0])) for p in per if p.get("values") and str(p["values"][0]).replace(".", "", 1).isdigit()]
        return {"valor": round(obs[-1][1], 4), "fecha": obs[-1][0], "fuente": "BCRP, tipo de cambio interbancario venta (S/ por US$), serie en data/generado/cache_bcrp"}
    except (OSError, ValueError, KeyError, IndexError):
        return {"valor": 3.40, "fecha": "referencial", "fuente": "valor de referencia: no se encontro la serie del BCRP en la cache"}


def _mezcla_de_evaluacion() -> dict:
    """Que parte de las preguntas de evaluacion iria a la IA con la politica de ahorro: un ejemplo de mezcla mas amplio que el parrafo de siete consultas (son preguntas escritas por el equipo, no trafico real)."""
    from src.agente_analitico.grafo import INTENCIONES_CON_LLM, SIN_LLM, detectar_intencion
    spec = importlib.util.spec_from_file_location("evaluar_agente", os.path.join(RAIZ, "analitica", "eval", "evaluar_agente.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    its = [detectar_intencion(q) for q, _ in mod.PREGUNTAS]
    ia, fija = sum(i in INTENCIONES_CON_LLM for i in its), sum(i in SIN_LLM for i in its)
    return {"preguntas": len(its), "van_a_la_ia": ia, "plantilla_fija": fija, "herramientas_y_plantilla": len(its) - ia - fija, "proporcion_ia": ia / len(its)}


def _costos(entrada: float, salida: float, lectura: int, corpus: int, parrafo_n: int, parrafo_ia: int, mezcla: dict) -> dict:
    """Soles y porcentajes. Una llamada al LLM = mensaje enviado (instrucciones, datos y pregunta) + lectura de las fuentes que trae el RAG + respuesta. La entrada y la salida se cobran distinto."""
    tc = _tipo_de_cambio()
    pe, ps = PRECIO["usd_por_millon_de_entrada"] / 1e6 * tc["valor"], PRECIO["usd_por_millon_de_salida"] / 1e6 * tc["valor"]   # soles por token
    tok = {"mensaje": max(entrada - lectura, 0), "lectura_de_fuentes": lectura, "respuesta": salida}
    sol = {"mensaje": tok["mensaje"] * pe, "lectura_de_fuentes": lectura * pe, "respuesta": salida * ps}
    por_llamada, tot_tok = sum(sol.values()), sum(tok.values())
    mensaje_sin_fuentes = tok["mensaje"] * pe + salida * ps
    corpus_soles = corpus * pe + mensaje_sin_fuentes   # hipotesis: el LLM recibe TODO el corpus en cada pregunta de concepto (cabe en su ventana, pero cuesta)

    def esc(p_ia: float) -> dict:
        sin, con = ESCALA * por_llamada, ESCALA * p_ia * por_llamada
        return {"proporcion_que_llega_a_la_ia": p_ia, "sin_ruteo_soles": sin, "con_ruteo_soles": con, "ahorro_soles": sin - con, "ahorro_pct": 1 - p_ia}
    return {"precio": PRECIO, "tipo_de_cambio": tc, "escala_consultas": ESCALA,
            "por_llamada": {"tokens": tok, "soles": {**sol, "total": por_llamada}, "pct_de_los_tokens": {k: v / tot_tok for k, v in tok.items()}, "pct_del_costo": {k: v / por_llamada for k, v in sol.items()}},
            "parrafo_de_ejemplo": esc(parrafo_ia / parrafo_n) | {"consultas": parrafo_n, "llamadas": parrafo_ia},
            "mezcla_de_evaluacion": esc(mezcla["proporcion_ia"]) | {"detalle": mezcla},
            "lectura_del_corpus": {"tokens_corpus": corpus, "tokens_con_rag": lectura, "reduccion_pct": 1 - lectura / corpus, "soles_por_consulta_leyendo_todo": corpus_soles, "soles_por_consulta_con_rag": por_llamada,
                                   "soles_por_escala_leyendo_todo": ESCALA * corpus_soles, "soles_por_escala_con_rag": ESCALA * por_llamada, "ahorro_pct": 1 - por_llamada / corpus_soles},
            "nota": ("Estimacion: tokens medidos en la QA con Gemini real x precio publicado x tipo de cambio del BCRP. El mensaje es el promedio de las llamadas medidas (incluye las cortas); la lectura de fuentes se estima con 4 caracteres por token. "
                     "Los soles de ahorro por ruteo dependen de la mezcla de consultas: el parrafo de ejemplo y las preguntas de evaluacion son dos casos, no trafico real.")}


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
    R["costos"] = _costos(entrada, salida, R["tokens_de_los_3_fragmentos"], R["tokens_del_corpus_completo"], len(filas), con_llm, _mezcla_de_evaluacion())
    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    with open(DESTINO, "w", encoding="utf-8") as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    return R
