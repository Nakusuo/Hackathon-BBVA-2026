"""Manifiesto de la data sintetica generada que se carga TEMPORALMENTE al repositorio para la integracion final.
Registra cada archivo con su tamano y su hash, la semilla, la huella de los parametros y el comando para regenerarla identica; deja fuera las caches y la memoria de pruebas.
Despues de integrar se quita del control de versiones (queda en .gitignore): git rm -r --cached data/generado
Uso: python eval/manifiesto_datos.py   ->  data/generado/_manifiesto.json y la lista de lo que hay que agregar con git add -f"""
import hashlib
import json
import os
import sys
from datetime import datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.comun.rutas import DATA_GENERADO, DATA_PARAMETROS  # noqa: E402

EXCLUIDOS = {"cache_llm.json", "cache_bcrp", "memoria", "vivo", "_manifiesto.json"}   # caches y memoria de pruebas: no son datos del generador


def sha(ruta: str) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def main() -> None:
    archivos = []
    for base, dirs, files in os.walk(DATA_GENERADO):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUIDOS)
        for f in sorted(files):
            if f in EXCLUIDOS:
                continue
            ruta = os.path.join(base, f)
            archivos.append({"ruta": os.path.relpath(ruta, DATA_GENERADO).replace(os.sep, "/"), "bytes": os.path.getsize(ruta), "sha256": sha(ruta)})
    meta = {}
    p_meta = os.path.join(DATA_GENERADO, "meta.json")
    if os.path.isfile(p_meta):
        with open(p_meta, encoding="utf-8") as f:
            meta = json.load(f)
    manifiesto = {
        "que_es": "Datos 100 % sinteticos generados por data/generator.py (semilla fija). Se cargan al repositorio de forma temporal para la integracion final; no hay datos personales reales.",
        "creado": datetime.now().isoformat(timespec="seconds"), "semilla": meta.get("semilla", meta.get("seed")), "meta": meta,
        "huella_parametros": {n: sha(os.path.join(DATA_PARAMETROS, n))[:16] for n in ("generador.yaml", "eventos.yaml")},
        "regenerar_identica": "python data/generator.py --perfil completo   (misma semilla y mismos parametros dan las mismas tablas; lo comprueba tests/test_generador.py)",
        "como_usar": "python eval/entrenar_modelos.py y la clase Repositorio leen estas tablas desde data/generado/",
        "quitar_al_terminar": "git rm -r --cached data/generado   (la carpeta ya esta en .gitignore: los archivos siguen en disco y dejan de versionarse)",
        "total_archivos": len(archivos), "total_mb": round(sum(a["bytes"] for a in archivos) / 2 ** 20, 1), "archivos": archivos}
    with open(os.path.join(DATA_GENERADO, "_manifiesto.json"), "w", encoding="utf-8") as f:
        json.dump(manifiesto, f, ensure_ascii=False, indent=1)
    print(f"{len(archivos)} archivos, {manifiesto['total_mb']} MB -> data/generado/_manifiesto.json")


if __name__ == "__main__":
    main()
