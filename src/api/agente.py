"""El agente de Lucas dentro de la API. Los datos del cliente, los modelos y el grafo se cargan una sola vez por proceso
y se comparten entre pedidos; la ruta /chat solo traduce su respuesta a los nombres del contrato (docs/api.md, sección 12)."""
import logging
import os
import re
import threading
from collections import OrderedDict

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


def para_el_chat(texto: str, intencion: str, opciones: list[dict]) -> str:
    """El chat ya muestra «Orientación, no asesoría. Tú decides.» bajo la caja de texto y saluda una sola vez:
    se quitan el saludo y el cierre que el agente repite en cada respuesta. Si hay opciones, el chat las pinta como botones
    y el menú escrito («A • B • C») sobra."""
    if intencion not in ("conversacion", "apoyo"):
        texto = re.sub(r"^Hola, [^.\n]{1,30}\.\s*", "", texto)
    if opciones:
        texto = texto.replace(" • ".join(o["texto"] for o in opciones), "").replace("  ", " ")
    return re.sub(r"\s*T[uú] decides?\.\s*$", "", texto.strip(), flags=re.I).strip() or texto.strip()


# Conversaciones recordadas en memoria del proceso: solo la ultima pregunta con tema, nunca la respuesta. Se olvidan al reiniciar la API.
CONVERSACIONES_RECORDADAS = 500
# Cada seguimiento lleva la pregunta anterior detrás: se recorta para que no crezca sin fin. Lo nuevo va delante, así que se pierde lo más viejo.
LARGO_RECORDADO = 300


def _propuesta(p: dict | None) -> dict | None:
    return {"name": p["nombre"], "target": p["objetivo"], "date": p["fecha"]} if p else None


class Agente:
    def __init__(self, repo, grafo, alias: dict[str, str]):
        self.repo, self.grafo, self.alias = repo, grafo, alias
        self._previas: OrderedDict[tuple[str, str], str] = OrderedDict()
        self._candado = threading.Lock()

    def _recordar(self, clave: tuple[str, str], pregunta: str) -> None:
        with self._candado:
            self._previas[clave] = pregunta[:LARGO_RECORDADO]
            self._previas.move_to_end(clave)
            while len(self._previas) > CONVERSACIONES_RECORDADAS:
                self._previas.popitem(last=False)

    def cliente(self, customer_id: str) -> str:
        real = self.alias.get(customer_id, customer_id)
        if real not in self.repo.pos:
            raise ClienteDesconocido(customer_id)
        return real

    def responder(self, customer_id: str, mensaje: str, conversacion: str | None = None) -> dict:
        from src.agente_analitico.grafo import con_contexto, responder

        cliente = self.cliente(customer_id)
        clave = (cliente, conversacion or "")
        pregunta = con_contexto(mensaje, self._previas.get(clave)) if conversacion else mensaje
        r = responder(self.grafo, cliente, pregunta)
        if conversacion and r["intencion"] not in ("general", "fuera_de_tema", "conversacion", "apoyo", "seguridad", "fuera_de_alcance"):
            self._recordar(clave, pregunta)
        return {
            "answer": para_el_chat(r["respuesta"], r["intencion"], r.get("opciones") or []),
            "provider": r["proveedor"],
            # Verificada = ninguna cifra del texto final quedó sin respaldo en lo que devolvieron las herramientas.
            "verified": not r["cifras_sin_respaldo"],
            "sources": [
                {"id": c["documento"], "title": c["titulo"], "page": c["pagina"], "url": c["enlace"] or None}
                for c in r["citas"]
            ],
            "tools_used": [t.split(":", 1)[1] for t in r["trazas"] if t.startswith("agente:")],
            "intent": r["intencion"],
            "goal_proposal": _propuesta(r.get("propuesta_meta")),
            "options": [{"id": o["id"], "label": o["texto"], "question": o["pregunta"]} for o in r.get("opciones") or []],
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
