"""Generador de datos sinteticos. Uso:
    python data/generator.py --perfil muestra            # liviano, queda en data/sample
    python data/generator.py --perfil completo           # 500 clientes, 2019 a 2025, queda en data/generado
    python data/generator.py --clientes 200 --inicio 2022-01-01 --fin 2025-12-31 --semilla 7
"""
import argparse
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "backend"))

from src.comun.rutas import DATA_GENERADO, DATA_SAMPLE  # noqa: E402
from src.generador.pipeline import generar  # noqa: E402

PERFILES = {
    "muestra": dict(clientes=40, inicio="2025-01-01", fin="2025-12-31", salida=DATA_SAMPLE, lote=40),
    "modelado": dict(clientes=500, inicio="2019-01-01", fin="2025-12-31", salida=DATA_GENERADO, lote=50),
    "completo": dict(clientes=500, inicio="2019-01-01", fin="2025-12-31", salida=DATA_GENERADO, lote=50),
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--perfil", choices=PERFILES, default=None)
    ap.add_argument("--clientes", type=int)
    ap.add_argument("--inicio")
    ap.add_argument("--fin")
    ap.add_argument("--semilla", type=int, default=2026)
    ap.add_argument("--salida")
    ap.add_argument("--lote", type=int)
    ap.add_argument("--incluir-prospectivos", action="store_true", help="incluye el escenario El Nino 2026-2027 (la ventana debe llegar a 2027)")
    a = ap.parse_args()
    cfg = dict(PERFILES[a.perfil or "completo"])
    for k in ("clientes", "inicio", "fin", "salida", "lote"):
        v = getattr(a, k)
        if v is not None:
            cfg[k] = v
    meta = generar(semilla=a.semilla, incluir_prospectivos=a.incluir_prospectivos, **cfg)
    print({k: meta[k] for k in ("clientes", "inicio", "fin", "movimientos", "segundos", "semilla")})


if __name__ == "__main__":
    main()
