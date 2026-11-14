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
