"""Chat de consola con los mocks del contrato: `python -m agent` (o `--plantilla` sin LLM)."""

import argparse
import json
import logging
import sys
import time

from agent.chat import responder
from agent.grafo import construir
from agent.providers import TemplateProvider, cadena_desde_entorno, calentar
from agent.tools import HerramientasMock


def main() -> None:
    parser = argparse.ArgumentParser(description="Prueba el agente de Lucas con los mocks.")
    parser.add_argument("--plantilla", action="store_true", help="responde sin LLM")
    parser.add_argument("--json", action="store_true", help="muestra la respuesta de /chat")
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
    agente = construir(HerramientasMock(), cadena)
    print("Escribe tu pregunta (Enter vacío para salir).\n")

    while pregunta := input("Tú: ").strip():
        inicio = time.perf_counter()
        r = responder(agente, {"customer_id": "demo-001", "message": pregunta})
        segundos = time.perf_counter() - inicio
        print(f"\nLucas: {r['answer']}")
        print(f"  [{r['provider']} · verificado: {r['verified']} · {segundos:.1f} s]\n")
        if args.json:
            print(json.dumps(r, ensure_ascii=False, indent=2), "\n")


if __name__ == "__main__":
    main()
