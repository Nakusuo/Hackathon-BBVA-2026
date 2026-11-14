"""Huella de contenido de un conjunto de archivos. Cada evaluacion guarda la huella del codigo del que depende y la puerta de calidad la recalcula:
si el codigo cambio despues de la evaluacion, la evaluacion esta desfasada. Es mas robusta que comparar fechas de archivo, que un clon nuevo o un rebase reescriben.
Los saltos de linea se normalizan: da lo mismo un archivo con LF (Linux) que con CRLF (Windows)."""
import glob
import hashlib
import os

from src.comun.rutas import RAIZ

# Codigo y parametros de los que depende cada evaluacion
AGENTE = ["src/agente_analitico/*.py", "src/models/calendario_laboral.py", "src/models/recomendador.py", "src/models/programa_puntos.py", "src/models/niveles.py", "src/models/ofertas.py",
          "src/models/riesgo_clima.py", "src/models/salud.py", "src/rag/*.py", "src/bcrp/cliente.py", "src/comun/reloj.py", "data/parametros/normas_laborales.yaml", "data/parametros/niveles.yaml",
          "data/parametros/zonas_riesgo_fen.yaml", "data/catalogo_ofertas.json"]
RAG = ["src/rag/*.py", "data/parametros/preguntas_rag.yaml", "docs/rag/indice/*"]
METRICAS = ["models/metricas*.json"]


def huella(patrones: list[str]) -> str:
    h = hashlib.sha256()
    archivos = sorted({f for p in patrones for f in glob.glob(os.path.join(RAIZ, p), recursive=True) if os.path.isfile(f)})
    for f in archivos:
        h.update(os.path.relpath(f, RAIZ).replace(os.sep, "/").encode())
        with open(f, "rb") as fh:
            h.update(fh.read().replace(b"\r\n", b"\n"))
    return h.hexdigest()[:16]
