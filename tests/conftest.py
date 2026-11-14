import pytest


@pytest.fixture(scope="session")
def repo_y_buscador():
    """El repositorio de clientes y el buscador del RAG tardan en cargar: se construyen una sola vez para toda la suite."""
    from src.agente_analitico.repositorio import Repositorio
    from src.rag.indice import Buscador
    return Repositorio(), Buscador()
