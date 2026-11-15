"""RAG por módulos (JF-05) sobre el índice que construyó Diego en `docs/rag/indice/`.

Se reutiliza su índice tal cual (3 761 fragmentos, `nomic-embed-text`, 768 dimensiones) y su
configuración ganadora en `models/metricas_rag.json`: búsqueda densa con filtro de módulo
(recall@4 0,94), umbral de relevancia 0,70 y expansión de siglas. Para reconstruir el índice
se usa `backend/src/rag/indice.py` de su rama; aquí solo se consulta.

Los embeddings son siempre locales (Ollama): la pregunta no sale de la máquina.
"""

import json
import logging
import re
from collections.abc import Callable
from pathlib import Path

import faiss
import httpx
import numpy as np

log = logging.getLogger(__name__)

RUTA_INDICE = Path(__file__).resolve().parents[3] / "docs" / "rag" / "indice"
MODELO_EMBEDDINGS = "nomic-embed-text"
UMBRAL_RELEVANCIA = 0.70
K = 3
TIMEOUT_EMBEDDING_S = 10

# Tomado de `backend/src/rag/indice.py` de Diego: el modelo de embeddings casi no sabe qué significa
# una sigla sola («TCEA» rinde menos que «tasa de costo efectivo anual»).
ACRONIMOS = {
    "TCEA": "tasa de costo efectivo anual",
    "TEA": "tasa efectiva anual",
    "TREA": "tasa de rendimiento efectivo anual",
    "CTS": "compensación por tiempo de servicios",
    "AFP": "administradora de fondos de pensiones",
    "ONP": "oficina de normalización previsional",
    "SBS": "Superintendencia de Banca, Seguros y AFP",
    "SMV": "Superintendencia del Mercado de Valores",
    "BCRP": "Banco Central de Reserva del Perú",
    "ENFEN": "estudio nacional del fenómeno El Niño",
    "UIT": "unidad impositiva tributaria",
}
_SIGLAS = re.compile(r"\b(" + "|".join(ACRONIMOS) + r")\b", re.IGNORECASE)


class SinEmbeddings(Exception):
    """Ollama no respondió al calcular el embedding de la consulta."""


def expandir_siglas(consulta: str) -> str:
    """«qué es la TCEA» → «qué es la TCEA (tasa de costo efectivo anual)», una vez por sigla."""
    vistas: set[str] = set()

    def reemplazo(m: re.Match) -> str:
        sigla = m.group(1).upper()
        if sigla in vistas:
            return m.group(0)
        vistas.add(sigla)
        return f"{m.group(0)} ({ACRONIMOS[sigla]})"

    return _SIGLAS.sub(reemplazo, consulta)


def embeber_consulta(texto: str) -> np.ndarray:
    """Vector normalizado de la consulta con el mismo modelo y prefijo con que se indexó."""
    # Import aquí: providers → plantillas → rag sería un import circular.
    from .providers import host_ollama

    try:
        r = httpx.post(
            f"{host_ollama()}/api/embed",
            json={"model": MODELO_EMBEDDINGS, "input": [f"search_query: {texto}"]},
            timeout=TIMEOUT_EMBEDDING_S,
        )
        r.raise_for_status()
        vector = np.array(r.json()["embeddings"], dtype=np.float32)
    except (httpx.HTTPError, KeyError, ValueError) as e:
        raise SinEmbeddings(type(e).__name__) from e
    faiss.normalize_L2(vector)
    return vector


class Buscador:
    def __init__(
        self,
        ruta: Path = RUTA_INDICE,
        embeber: Callable[[str], np.ndarray] = embeber_consulta,
    ):
        self.indice = faiss.read_index(str(ruta / "vectores.faiss"))
        self.fragmentos = json.loads((ruta / "fragmentos.json").read_text(encoding="utf-8"))
        self.modulos = np.array([f["modulo"] for f in self.fragmentos])
        self.embeber = embeber

    def buscar(self, consulta: str, modulos: list[str] | None = None, k: int = K) -> list[dict]:
        """Hasta `k` fragmentos sobre el umbral, del módulo pedido. Lista vacía si no hay evidencia."""
        vector = self.embeber(expandir_siglas(consulta))
        _, ids = self.indice.search(vector, min(80, len(self.fragmentos)))
        permitidos = [
            int(i) for i in ids[0] if i >= 0 and (not modulos or self.modulos[i] in modulos)
        ]
        resultados = []
        for i in permitidos[:k]:
            similitud = float(vector[0] @ self.indice.reconstruct(i))
            if similitud < UMBRAL_RELEVANCIA:
                continue
            f = self.fragmentos[i]
            resultados.append(
                {
                    "id": f"frag-{i}",
                    "modulo": f["modulo"],
                    "titulo": f["titulo"],
                    "institucion": f["institucion"],
                    "pagina": f["pagina"],
                    "contexto": f["contexto"],
                    "enlace": f["enlace"],
                    "texto": f["texto"],
                }
            )
            # La similitud no va en el resultado: el juez la tomaría como cifra permitida.
            log.info("RAG frag-%d (%s) similitud %.3f", i, f["modulo"], similitud)
        return resultados
