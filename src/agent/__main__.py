"""Chat de consola con los mocks del contrato: `python -m agent` (o `--plantilla` sin LLM)."""

import argparse
import json
import logging
import sys
import time

from agent import plantillas
from agent.chat import responder
from agent.grafo import construir
from agent.providers import TemplateProvider, cadena_desde_entorno, calentar
from agent.rag import Buscador
from agent.tools import HerramientasAPI, HerramientasMock


def main() -> None:
    parser = argparse.ArgumentParser(description="Prueba el agente de Lucas con los mocks.")
    parser.add_argument("--plantilla", action="store_true", help="responde sin LLM")
    parser.add_argument("--json", action="store_true", help="muestra la respuesta de /chat")
    parser.add_argument(
        "--simular-con-llm",
        action="store_true",
        help="la simulación la redacta el LLM y no la plantilla (prueba de CP-SIS-10)",
    )
    parser.add_argument(
        "--api",
        metavar="URL",
        help="usa la API de Miguel en vez de los mocks, por ejemplo http://localhost:8000",
    )
    parser.add_argument("--cliente", default="demo-001", help="customer_id de la consulta")
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING, format="  [%(name)s] %(message)s")
    sys.stdout.reconfigure(encoding="utf-8")

    if args.plantilla:
        cadena = [TemplateProvider()]
    else:
        cadena = cadena_desde_entorno()
        print("Cargando el modelo de Ollama...")
        if not calentar():
            print("Ollama no responde: contestará la plantilla.")
    solo_plantilla = None
    if args.simular_con_llm:
        solo_plantilla = plantillas.INTENCIONES_SOLO_PLANTILLA - {"simular"}
    herramientas = HerramientasAPI(args.api) if args.api else HerramientasMock()
    agente = construir(herramientas, cadena, solo_plantilla=solo_plantilla, buscador=Buscador())
    print("Escribe tu pregunta (Enter vacío para salir).\n")

    while pregunta := input("Tú: ").strip():
        inicio = time.perf_counter()
        r = responder(agente, {"customer_id": args.cliente, "message": pregunta})
        segundos = time.perf_counter() - inicio
        print(f"\nLucas: {r['answer']}")
        print(f"  [{r['provider']} · verificado: {r['verified']} · {segundos:.1f} s]")
        for fuente in r["sources"]:
            print(f"  Fuente: {fuente['title']} ({fuente['institution']}, p. {fuente['page']})")
        print()
        if args.json:
            print(json.dumps(r, ensure_ascii=False, indent=2), "\n")


if __name__ == "__main__":
    main()
