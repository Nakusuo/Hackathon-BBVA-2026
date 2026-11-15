import pytest


@pytest.fixture(scope="session")
def repo_y_buscador():
    """El repositorio de clientes y el buscador del RAG tardan en cargar: se construyen una sola vez para toda la suite."""
    from src.agente_analitico.repositorio import Repositorio
    from src.rag.indice import Buscador
    return Repositorio(), Buscador()


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
