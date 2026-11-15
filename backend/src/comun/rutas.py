"""Rutas del proyecto calculadas desde la raiz del repo, sin rutas absolutas de nadie."""
import os


def _buscar_raiz() -> str:
    actual = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.isdir(os.path.join(actual, ".claude")) and os.path.isdir(os.path.join(actual, "backend")):
            return actual
        padre = os.path.dirname(actual)
        if padre == actual:
            raise RuntimeError("No se encontro la raiz del repo (carpetas .claude y backend)")
        actual = padre


RAIZ = _buscar_raiz()


def ruta(*partes: str, crear: bool = False) -> str:
    """Ruta dentro del repo. Con crear=True crea la carpeta (o la carpeta padre si hay extension)."""
    destino = os.path.join(RAIZ, *partes)
    if crear:
        carpeta = os.path.dirname(destino) if os.path.splitext(destino)[1] else destino
        os.makedirs(carpeta, exist_ok=True)
    return destino


DATA_GENERADO = ruta("data", "generado")
DATA_PARAMETROS = ruta("data", "parametros")
DATA_SAMPLE = ruta("data", "sample")
DATA_RAW = ruta("data", "raw")
MODELOS = ruta("models")
DOCS_RAG = ruta("docs", "rag")
DOCS_FUENTES = ruta("docs", "fuentes")
INDICE_RAG = ruta("docs", "rag", "indice")


def cargar_env() -> None:
    """Carga .env de la raiz si existe, sin pisar variables ya definidas en el entorno."""
    archivo = ruta(".env")
    if not os.path.isfile(archivo):
        return
    with open(archivo, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip())
