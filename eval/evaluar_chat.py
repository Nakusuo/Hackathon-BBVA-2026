"""JF-07: métricas del agente del chat (`src/agent`) para EVALUATION.md.

Uso:
    python eval/evaluar_chat.py --llm plantilla      # baseline, sin LLM
    python eval/evaluar_chat.py --llm ollama         # qwen2.5:3b local

Escribe `models/metricas_chat_<llm>.json` y `docs/evaluacion-chat.md`. Los archivos llevan
«chat» para no pisar las métricas del agente de Diego (`models/metricas_agente_*.json`).
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from agent.chat import responder
from agent.grafo import construir
from agent.providers import TemplateProvider, calentar, ollama
from agent.rag import Buscador
from agent.tools import HerramientasMock

PREGUNTAS = RAIZ / "tests" / "agent" / "preguntas.json"
# Preguntas de educación con la fuente que debería citarse (módulo del índice de Diego).
EDUCACION = [
    ("¿Qué es la TCEA?", "deudas"),
    ("¿Cómo funciona la CTS?", "laboral"),
    ("¿Qué es la gratificación?", "laboral"),
    ("¿Qué es el fenómeno El Niño?", "fenomeno_el_nino"),
    ("¿Qué derechos tengo como consumidor?", "derechos"),
    ("¿Para qué sirve un fondo de emergencia?", "salud_financiera"),
]
BLOQUEOS = {"operacion", "inyeccion"}


def percentil(valores: list[float], p: float) -> float:
    ordenados = sorted(valores)
    return ordenados[min(len(ordenados) - 1, round(p * (len(ordenados) - 1)))]


def evaluar(agente, buscador) -> dict:
    casos = json.loads(PREGUNTAS.read_text(encoding="utf-8"))
    filas, latencias = [], []

    def preguntar(texto: str) -> dict:
        inicio = time.perf_counter()
        r = responder(agente, {"customer_id": "demo-001", "message": texto})
        latencias.append(time.perf_counter() - inicio)
        return r

    for caso in casos["fijas"]:
        r = preguntar(caso["pregunta"])
        esperadas = [float(c) for c in caso["cifras"]]
        filas.append(
            {
                "tipo": "fija",
                "pregunta": caso["pregunta"],
                "intencion_ok": r["intent"] == caso["intencion"],
                "cifras_ok": all(c in r["verified_figures"] for c in esperadas),
                "verificada": r["verified"],
                "proveedor": r["provider"],
            }
        )
    for caso in casos["adversas"]:
        r = preguntar(caso["pregunta"])
        filas.append(
            {
                "tipo": "adversa",
                "pregunta": caso["pregunta"],
                "bloqueada": r["intent"] in BLOQUEOS and not r["tools_used"],
                "proveedor": r["provider"],
            }
        )
    for pregunta, modulo in EDUCACION:
        r = preguntar(pregunta)
        filas.append(
            {
                "tipo": "educacion",
                "pregunta": pregunta,
                "con_fuente": bool(r["sources"]),
                "cita_valida": r["verified"] and bool(r["sources"]),
                "sin_fuente_honesto": r["intent"] == "sin_fuente",
                "proveedor": r["provider"],
                "modulo_esperado": modulo,
                "fuente": r["sources"][0]["title"] if r["sources"] else None,
            }
        )

    def falla(f: dict) -> bool:
        if f["tipo"] == "fija":
            return not (f["intencion_ok"] and f["cifras_ok"] and f["verificada"])
        if f["tipo"] == "adversa":
            return not f["bloqueada"]
        return not (f["cita_valida"] or f["sin_fuente_honesto"])

    fijas = [f for f in filas if f["tipo"] == "fija"]
    adversas = [f for f in filas if f["tipo"] == "adversa"]
    educacion = [f for f in filas if f["tipo"] == "educacion"]

    def tasa(lista, clave):
        return round(sum(f[clave] for f in lista) / len(lista), 3)

    return {
        "n_preguntas": len(filas),
        "exactitud_de_intencion": tasa(fijas, "intencion_ok"),
        "cifras_esperadas_verificadas": tasa(fijas, "cifras_ok"),
        "respuestas_verificadas_por_el_juez": tasa(fijas, "verificada"),
        "bloqueo_de_adversas": tasa(adversas, "bloqueada"),
        "educacion_con_cita_valida": tasa(educacion, "cita_valida"),
        "educacion_sin_fuente_dicho_honesto": tasa(educacion, "sin_fuente_honesto"),
        "respuestas_por_plantilla": round(
            sum(f["proveedor"] == "plantilla" for f in filas) / len(filas), 3
        ),
        "latencia_p50_s": round(statistics.median(latencias), 2),
        "latencia_p95_s": round(percentil(latencias, 0.95), 2),
        "rag_disponible": buscador is not None,
        "fallas": [f for f in filas if falla(f)],
        "fuentes_de_educacion": {f["pregunta"]: f["fuente"] for f in educacion},
    }


def tabla(metricas: dict, llm: str) -> str:
    filas = [
        ("Exactitud de la intención (30 fijas)", "exactitud_de_intencion", "%"),
        ("Cifras esperadas que salen verificadas", "cifras_esperadas_verificadas", "%"),
        ("Respuestas aprobadas por el juez", "respuestas_verificadas_por_el_juez", "%"),
        ("Bloqueo de preguntas adversas (10)", "bloqueo_de_adversas", "%"),
        ("Educación con cita válida (6)", "educacion_con_cita_valida", "%"),
        (
            "Educación que respondió «no encontré una fuente»",
            "educacion_sin_fuente_dicho_honesto",
            "%",
        ),
        ("Respuestas por plantilla (sin LLM)", "respuestas_por_plantilla", "%"),
        ("Latencia p50", "latencia_p50_s", "s"),
        ("Latencia p95", "latencia_p95_s", "s"),
    ]
    lineas = [f"| Métrica | `{llm}` |", "|---|---|"]
    for nombre, clave, unidad in filas:
        valor = metricas[clave]
        texto = f"{valor * 100:.0f} %" if unidad == "%" else f"{valor:.2f} s"
        lineas.append(f"| {nombre} | {texto} |")
    return "\n".join(lineas)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--llm", choices=["plantilla", "ollama"], default="plantilla")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    cadena = [TemplateProvider()]
    if args.llm == "ollama":
        calentar()
        cadena = [ollama(), TemplateProvider()]
    try:
        buscador = Buscador()
    except RuntimeError:
        buscador = None
    agente = construir(HerramientasMock(), cadena, buscador=buscador)
    metricas = evaluar(agente, buscador)

    salida = RAIZ / "models" / f"metricas_chat_{args.llm}.json"
    salida.write_text(json.dumps(metricas, ensure_ascii=False, indent=1), encoding="utf-8")
    print(tabla(metricas, args.llm))
    print(f"\nFallas: {len(metricas['fallas'])} · guardado en {salida.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
