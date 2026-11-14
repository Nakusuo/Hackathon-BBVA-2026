"""Inventario de las sesiones de Claude Code de este repo, leídas de ~/.claude/projects.

Uso:
    python .claude/skills/documentar-uso-ia/inventario_sesiones.py            # una línea por sesión
    python .claude/skills/documentar-uso-ia/inventario_sesiones.py <id>       # pedidos humanos de una sesión

Solo lee. Los registros son locales de cada persona y traen rutas, cuentas y
correos: se resumen, nunca se copian al repo.
"""
import json
import sys
from pathlib import Path

REPO = "Hackathon-BBVA-2026-Equipo-2"


def sesiones():
    raiz = Path.home() / ".claude" / "projects"
    return sorted(p for d in raiz.glob(f"*{REPO}*") for p in d.glob("*.jsonl"))


def pedidos_humanos(lineas):
    for d in lineas:
        if d.get("type") == "user" and not d.get("isMeta") and not d.get("isSidechain"):
            contenido = d["message"]["content"]
            if isinstance(contenido, str):
                yield d["timestamp"], contenido


def leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return [json.loads(linea) for linea in f if linea.strip()]


def resumen(ruta):
    lineas = leer(ruta)
    marcas = sorted(d["timestamp"] for d in lineas if "timestamp" in d)
    ramas = sorted({d["gitBranch"] for d in lineas if d.get("gitBranch")})
    modelos = sorted({d["message"]["model"] for d in lineas if d.get("type") == "assistant"})
    return {
        "id": ruta.stem,
        "inicio": marcas[0][:16] if marcas else "?",
        "fin": marcas[-1][:16] if marcas else "?",
        "ramas": ",".join(ramas) or "-",
        "modelos": ",".join(modelos) or "-",
        "pedidos": sum(1 for _ in pedidos_humanos(lineas)),
    }


def main():
    # La consola de Windows usa cp1252 y rompe con «→» o emojis de los pedidos.
    sys.stdout.reconfigure(encoding="utf-8")
    rutas = sesiones()
    if len(sys.argv) > 1:
        ruta = next(p for p in rutas if p.stem.startswith(sys.argv[1]))
        for marca, texto in pedidos_humanos(leer(ruta)):
            print(f"--- {marca[:16]}\n{texto[:1500]}")
        return
    filas = sorted((resumen(p) for p in rutas), key=lambda r: r["inicio"])
    for n, r in enumerate(filas, 1):
        print(f"{n} · {r['inicio']} → {r['fin']} · {r['id']} · ramas: {r['ramas']} · "
              f"modelos: {r['modelos']} · pedidos: {r['pedidos']}")


if __name__ == "__main__":
    main()
