import os

import numpy as np
import pytest
import requests


def _ollama_responde() -> bool:
    from src.comun.rutas import cargar_env

    cargar_env()
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    try:
        return requests.get(f"{host}/api/tags", timeout=2).ok
    except requests.RequestException:
        return False


def embebedor_lexico(buscador):
    """Embebedor falso y determinista para cuando Ollama no corre: cada consulta toma el vector guardado del fragmento con mejor BM25.
    Asi la parte densa usa vectores reales del indice y la similitud sale de ellos; sin ninguna palabra en comun el vector es cero y no hay evidencia."""

    def embeber(textos, tipo="document", lote=24):
        vecs = np.zeros((len(textos), buscador.idx.d), dtype=np.float32)
        for fila, texto in enumerate(textos):
            puntajes = buscador.bm25.get_scores(buscador._tok(texto))
            mejor = int(np.argmax(puntajes))
            if puntajes[mejor] > 0:
                vecs[fila] = buscador.idx.reconstruct(mejor)
        return vecs

    return embeber


@pytest.fixture(scope="session")
def repo_y_buscador():
    """El repositorio de clientes y el buscador del RAG tardan en cargar: se construyen una sola vez para toda la suite.
    Sin Ollama, las consultas se embeben con embebedor_lexico en vez de fallar por conexion."""
    from src.agente_analitico.repositorio import Repositorio
    from src.rag import indice

    buscador = indice.Buscador()
    with pytest.MonkeyPatch.context() as mp:
        if not _ollama_responde():
            mp.setattr(indice, "embeber", embebedor_lexico(buscador))
        yield Repositorio(), buscador


@pytest.fixture(autouse=True)
def _faq_aislado(tmp_path, monkeypatch):
    """Cada prueba con su propia base de preguntas frecuentes aprendidas: lo que una prueba aprende nunca cambia el resultado de otra ni queda en data/generado."""
    monkeypatch.setenv("LUCAS_FAQ_DIR", str(tmp_path / "faq"))


@pytest.fixture(autouse=True)
def _sin_red_en_la_traduccion(monkeypatch):
    """La suite no toca la red ni gasta tokens: sin esto, una clave de Gemini en `.env` o en el entorno hacia que las pruebas del chat en ingles o quechua usaran la traduccion REAL (y su resultado cambiara segun
    hubiera clave o cuota). Los proveedores de traduccion quedan vacios: se responde en espanol con el aviso. Las pruebas de traduccion se arman sus propios proveedores falsos (`_con_proveedor`)."""
    from src.agente_analitico import traduccion as TR
    monkeypatch.setattr(TR, "PROVEEDORES", [])
