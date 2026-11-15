"""Semilla de preguntas frecuentes: respuestas de concepto armadas por plantilla (sin LLM, cero tokens) desde las fuentes oficiales del RAG, con sus citas.
Parte de las preguntas escritas a mano para evaluar el RAG (data/parametros/preguntas_rag.yaml) y se queda solo con las que el agente enruta a «educacion» (preguntas de concepto) y cuyo
mejor fragmento pasa el filtro de relevancia. Cada respuesta es la misma que daria la plantilla del agente: «Segun <fuente> (pag. N): <extracto>».
Salidas: data/faq/faq_semilla.json (la usa el agente) y docs/PREGUNTAS_FRECUENTES.md (contenido reutilizable para una pantalla de preguntas frecuentes de la app).
Hay que volver a correrlo si cambia el indice del RAG (la semilla guarda su huella).
Uso: python analitica/eval/generar_faq.py"""
import json
import os
import sys
import warnings

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "backend"))
warnings.filterwarnings("ignore")

import yaml  # noqa: E402

from src.agente_analitico import faq as FAQ  # noqa: E402
from src.agente_analitico.grafo import UMBRAL_RELEVANCIA, _aviso_de_origen, detectar_intencion, extracto  # noqa: E402
from src.rag.indice import Buscador  # noqa: E402


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    b = Buscador()
    P = yaml.safe_load(open(os.path.join(RAIZ, "data", "parametros", "preguntas_rag.yaml"), encoding="utf-8"))["con_respuesta"]
    entradas, descartadas = [], []
    for item in P:
        q = item["q"]
        if detectar_intencion(q) not in FAQ.INTENCIONES:
            descartadas.append((q, "el agente la enruta a otro tema (tiene su propia respuesta con datos del cliente o la fuente especifica)"))
            continue
        r = b.buscar(q, k=3, modulo=None, modo="denso")
        if not r or r[0]["similitud"] < UMBRAL_RELEVANCIA:
            descartadas.append((q, "no pasa el filtro de relevancia"))
            continue
        r0 = r[0]
        resp = f"Segun {r0['titulo']} (pag. {r0['pagina']}){_aviso_de_origen(r0)}: {extracto(r0['texto'], q)} Tu decides."
        entradas.append({"pregunta": q, "palabras": sorted(FAQ.normalizar(q)), "respuesta": resp, "huella_indice": FAQ.huella_indice(),
                         "fragmentos": [{k: x[k] for k in ("documento", "titulo", "pagina", "enlace", "licencia_nivel", "texto") if k in x} | {"similitud": x.get("similitud", 1.0)} for x in r]})
    os.makedirs(os.path.join(RAIZ, "data", "faq"), exist_ok=True)
    with open(os.path.join(RAIZ, "data", "faq", "faq_semilla.json"), "w", encoding="utf-8") as f:
        json.dump({"nota": "Respuestas de concepto armadas por plantilla desde las fuentes del RAG, sin LLM. Se vuelven a generar con analitica/eval/generar_faq.py si cambia el indice.", "huella_indice": FAQ.huella_indice(),
                   "entradas": entradas}, f, ensure_ascii=False, indent=1)
    L = ["# Preguntas frecuentes\n",
         "Contenido reutilizable para una pantalla de preguntas frecuentes de la app. Cada respuesta se arma **sin LLM** (cero tokens) con un extracto de una fuente oficial o de libre uso del RAG, con su cita, "
         "y es la misma que da el agente. Generado por `analitica/eval/generar_faq.py` desde `data/faq/faq_semilla.json`; no es asesoria legal ni financiera.\n"]
    for e in entradas:
        f0 = e["fragmentos"][0]
        L.append(f"## {e['pregunta']}\n\n{e['respuesta']}\n\n*Fuente:* [{f0['titulo']}]({f0.get('enlace', '')}), pagina {f0['pagina']} (nivel {f0['licencia_nivel']}).\n")
    L.append(f"\n<!-- huella_indice: {FAQ.huella_indice()} ({len(entradas)} preguntas; {len(descartadas)} se omiten porque el agente las responde por otro camino) -->\n")
    with open(os.path.join(RAIZ, "docs", "PREGUNTAS_FRECUENTES.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"{len(entradas)} preguntas en la semilla; {len(descartadas)} omitidas")
    for q, m in descartadas:
        print("  omitida:", q[:70], "->", m[:60])


if __name__ == "__main__":
    main()
