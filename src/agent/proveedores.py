"""Proveedores de lenguaje: Ollama local (por defecto) -> Gemini en nivel gratuito (apagado por defecto) -> plantillas.
El LLM solo redacta con los datos que recibe; las cifras salen de herramientas y pasan por el juez."""
import os
import time

import requests

from src.comun.rutas import cargar_env

SISTEMA = (
    "Eres Lucas, un copiloto de plata para personas en Peru. Solo redactas: usa EXCLUSIVAMENTE los datos de la seccion DATOS. "
    "No inventes cifras, fechas, tasas ni nombres de productos. No calcules numeros nuevos. No des asesoria personalizada de inversion, "
    "no prometas rentabilidad, no digas comprar ni vender dolares y no ofrezcas hacer operaciones ni transferencias. "
    "La moneda es el sol: escribe siempre S/ y nunca el signo $. No plantees escenarios hipoteticos ni inventes casos: solo cuenta lo que dicen los DATOS. "
    "Escribe en espanol sencillo, frases cortas y tono {tono}. Explica el porque de cada consejo. Termina con la frase exacta: Tu decides. (una sola vez)."
)


class ErrorProveedor(Exception):
    pass


def _prompt(pregunta: str, datos: str, tono: str, feedback: str | None) -> tuple[str, str]:
    sistema = SISTEMA.format(tono=tono)
    usuario = f"PREGUNTA O SITUACION:\n{pregunta}\n\nDATOS:\n{datos}\n"
    if feedback:
        usuario += f"\nCORRIGE ESTO DEL BORRADOR ANTERIOR: {feedback}\n"
    return sistema, usuario


class Ollama:
    nombre = "ollama"

    def __init__(self):
        cargar_env()
        self.host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.modelo = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")

    def redactar(self, pregunta: str, datos: str, tono: str, feedback: str | None = None, timeout: int = 90) -> str:
        sistema, usuario = _prompt(pregunta, datos, tono, feedback)
        try:
            r = requests.post(f"{self.host}/api/chat", json={"model": self.modelo, "stream": False, "keep_alive": "30m", "options": {"temperature": 0.2, "num_ctx": 4096},
                                                            "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}]}, timeout=timeout)
            r.raise_for_status()
            return r.json()["message"]["content"].strip()
        except (requests.RequestException, KeyError, ValueError) as e:
            raise ErrorProveedor(f"ollama: {e}") from e


class Gemini:
    nombre = "gemini"

    def __init__(self):
        cargar_env()
        self.clave = os.environ.get("GEMINI_API_KEY", "")
        self.modelo = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

    def disponible(self) -> bool:
        return bool(self.clave)

    def redactar(self, pregunta: str, datos: str, tono: str, feedback: str | None = None, timeout: int = 40) -> str:
        if not self.clave:
            raise ErrorProveedor("gemini: sin clave en .env")
        sistema, usuario = _prompt(pregunta, datos, tono, feedback)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.modelo}:generateContent"
        cuerpo = {"systemInstruction": {"parts": [{"text": sistema}]}, "contents": [{"role": "user", "parts": [{"text": usuario}]}], "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600}}
        for intento in range(2):
            try:
                r = requests.post(url, json=cuerpo, headers={"x-goog-api-key": self.clave}, timeout=timeout)
                if r.status_code == 429 and intento == 0:
                    time.sleep(2)
                    continue
                r.raise_for_status()
                return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            except (requests.RequestException, KeyError, IndexError, ValueError) as e:
                raise ErrorProveedor(f"gemini: {type(e).__name__}") from e
        raise ErrorProveedor("gemini: limite de uso")


def cadena() -> list:
    """Orden de proveedores segun LLM_PROVIDER. Las plantillas siempre quedan al final, fuera de esta lista."""
    cargar_env()
    modo = os.environ.get("LLM_PROVIDER", "ollama").lower()
    if modo == "gemini":
        return [Gemini(), Ollama()]
    if modo == "plantillas":
        return []
    return [Ollama()]


def probar_gemini() -> dict:
    """Prueba minima de la clave con un texto sin datos personales."""
    g = Gemini()
    t0 = time.time()
    try:
        txt = g.redactar("Responde solo con la palabra OK.", "ninguno", "neutro")
        return {"ok": True, "modelo": g.modelo, "respuesta": txt[:40], "segundos": round(time.time() - t0, 1)}
    except ErrorProveedor as e:
        return {"ok": False, "modelo": g.modelo, "error": str(e)}
