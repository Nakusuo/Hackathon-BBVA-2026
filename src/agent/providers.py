"""Proveedores que redactan: Ollama local → Gemini (opcional) → plantillas.

`LLM_PROVIDER` elige la cadena: `ollama` (por defecto), `gemini` (agrega Gemini detrás de
Ollama) o `plantilla` (sin LLM). Ante error, timeout o 429: un reintento y luego el siguiente.
"""

import logging
import os
import time
from typing import Protocol

import httpx

from agent import plantillas
from agent.prompts import mensajes

log = logging.getLogger(__name__)

TIMEOUT_S = 8
MODELO_OLLAMA = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
MODELO_GEMINI = "gemini-3.5-flash-lite"


def host_ollama() -> str:
    """`OLLAMA_HOST` como URL a la que el cliente puede conectarse.

    El servidor acepta `0.0.0.0:11434` para escuchar en todas las interfaces, pero un cliente
    no puede conectarse a esa dirección (lo vio Michael en su laptop).
    """
    host = os.getenv("OLLAMA_HOST", "").strip() or "localhost:11434"
    if "://" not in host:
        host = f"http://{host}"
    return host.replace("://0.0.0.0", "://localhost")


class ProveedorNoDisponible(Exception):
    """El proveedor no respondió: sin red, timeout, cuota agotada o modelo ausente."""


class LLMProvider(Protocol):
    nombre: str

    def redactar(self, intencion: str, datos: dict) -> str: ...


class TemplateProvider:
    nombre = "plantilla"

    def redactar(self, intencion: str, datos: dict) -> str:
        return plantillas.responder(intencion, datos)


class ProveedorChat:
    """Envuelve un chat de LangChain y traduce sus errores de red o cuota."""

    def __init__(self, nombre: str, chat, errores: tuple[type[BaseException], ...]):
        self.nombre = nombre
        self.chat = chat
        self.errores = errores

    def redactar(self, intencion: str, datos: dict) -> str:
        try:
            respuesta = self.chat.invoke(mensajes(intencion, datos))
        except self.errores as e:
            raise ProveedorNoDisponible(f"{self.nombre}: {type(e).__name__}") from e
        texto = _texto(respuesta.content).strip()
        if not texto:
            raise ProveedorNoDisponible(f"{self.nombre}: respuesta vacía")
        return texto


def _texto(contenido) -> str:
    # Gemini puede devolver una lista de partes en lugar de un string.
    if isinstance(contenido, list):
        return "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in contenido)
    return contenido


_ERRORES_RED = (httpx.HTTPError, OSError, TimeoutError)


def ollama() -> ProveedorChat:
    import ollama as sdk
    from langchain_ollama import ChatOllama

    chat = ChatOllama(
        model=MODELO_OLLAMA,
        base_url=host_ollama(),
        temperature=0.2,
        num_predict=160,
        # 4096 alcanza porque el prompt lleva solo salidas de tools, y así el 3b cabe entero
        # en los 4 GB de la RTX 3050 de la demo (plan maestro, nota GPU).
        num_ctx=4096,
        # Cargar el modelo tarda más que el timeout; -1 lo deja cargado toda la demo.
        keep_alive=-1,
        client_kwargs={"timeout": TIMEOUT_S},
    )
    return ProveedorChat("ollama", chat, (*_ERRORES_RED, sdk.ResponseError))


def gemini(api_key: str) -> ProveedorChat:
    from google.genai.errors import APIError
    from langchain_core.exceptions import ModelError
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

    chat = ChatGoogleGenerativeAI(
        model=MODELO_GEMINI,
        google_api_key=api_key,
        timeout=TIMEOUT_S,
        max_retries=0,
    )
    errores = (*_ERRORES_RED, APIError, ModelError, ChatGoogleGenerativeAIError)
    return ProveedorChat("gemini", chat, errores)


def cadena_desde_entorno() -> list[LLMProvider]:
    eleccion = os.getenv("LLM_PROVIDER", "ollama").lower()
    if eleccion == "plantilla":
        return [TemplateProvider()]
    cadena: list[LLMProvider] = [ollama()]
    if eleccion == "gemini":
        clave = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if clave:
            cadena.append(gemini(clave))
        else:
            log.warning("LLM_PROVIDER=gemini sin GEMINI_API_KEY en .env; se omite Gemini")
    cadena.append(TemplateProvider())
    return cadena


def calentar(timeout_s: float = 120) -> bool:
    """Carga el modelo al arrancar la API para que la primera pregunta no pague esa espera.

    Usa su propio cliente porque la carga tarda más que el timeout de las respuestas.
    """
    import ollama as sdk

    cliente = sdk.Client(host=host_ollama(), timeout=timeout_s)
    try:
        cliente.generate(
            model=MODELO_OLLAMA, prompt="hola", keep_alive=-1, options={"num_ctx": 4096}
        )
    except (*_ERRORES_RED, sdk.ResponseError) as e:
        log.warning("No se pudo calentar Ollama: %s", type(e).__name__)
        return False
    return True


def redactar_con_respaldo(
    cadena: list[LLMProvider], intencion: str, datos: dict, espera_s: float = 1.0
) -> tuple[str, str]:
    """Devuelve (texto, nombre del proveedor que respondió). La plantilla nunca falla."""
    for proveedor in cadena:
        for intento in range(2):
            try:
                return proveedor.redactar(intencion, datos), proveedor.nombre
            except ProveedorNoDisponible as e:
                log.warning("Proveedor no disponible (intento %d): %s", intento + 1, e)
                if intento == 0:
                    time.sleep(espera_s)
    return TemplateProvider().redactar(intencion, datos), "plantilla"
