"""El agente de Lucas dentro de la API. Los datos del cliente, los modelos y el grafo se cargan una sola vez por proceso
y se comparten entre pedidos; la ruta /chat solo traduce su respuesta a los nombres del contrato (docs/api.md, sección 12)."""
import logging
import os
import threading

from src.comun.rutas import cargar_env

log = logging.getLogger("lucas.api.agente")

# Identificadores que usa el front (el de la demo y sus dos personas) → cliente sintético de la base.
# Se cambian con LUCAS_CLIENTES_DEMO="alias=customer_id,..." sin tocar código.
ALIAS_POR_DEFECTO = "demo-001=C00016,independiente=C00016,formal=C00168"


class ClienteDesconocido(LookupError):
    pass


def _leer_alias(texto: str) -> dict[str, str]:
    pares = (par.split("=", 1) for par in texto.split(",") if "=" in par)
    return {alias.strip(): cliente.strip() for alias, cliente in pares}


class Agente:
    def __init__(self, repo, grafo, alias: dict[str, str]):
        self.repo, self.grafo, self.alias = repo, grafo, alias

    def cliente(self, customer_id: str) -> str:
        real = self.alias.get(customer_id, customer_id)
        if real not in self.repo.pos:
            raise ClienteDesconocido(customer_id)
        return real

    def responder(self, customer_id: str, mensaje: str) -> dict:
        from src.agente_analitico.grafo import responder

        r = responder(self.grafo, self.cliente(customer_id), mensaje)
        return {
            "answer": r["respuesta"],
            "provider": r["proveedor"],
            # Verificada = ninguna cifra del texto final quedó sin respaldo en lo que devolvieron las herramientas.
            "verified": not r["cifras_sin_respaldo"],
            "sources": [
                {"id": c["documento"], "title": c["titulo"], "page": c["pagina"], "url": c["enlace"] or None}
                for c in r["citas"]
            ],
            "tools_used": [t.split(":", 1)[1] for t in r["trazas"] if t.startswith("agente:")],
            "intent": r["intencion"],
        }


_agente: Agente | None = None
_candado = threading.Lock()


def obtener_agente() -> Agente:
    """Dependencia de FastAPI. La primera llamada carga todo (unos segundos); las demás reutilizan lo cargado."""
    global _agente
    with _candado:
        if _agente is None:
            cargar_env()
            from src.agente_analitico.grafo import construir_grafo
            from src.agente_analitico.repositorio import Repositorio
            from src.rag.indice import Buscador

            repo = Repositorio()
            alias = _leer_alias(os.environ.get("LUCAS_CLIENTES_DEMO", ALIAS_POR_DEFECTO))
            _agente = Agente(repo, construir_grafo(repo, Buscador()), alias)
            log.info("Agente listo: %s clientes, datos desde %s", len(repo.pos), os.environ.get("LUCAS_FUENTE_DATOS", "parquet"))
    return _agente
