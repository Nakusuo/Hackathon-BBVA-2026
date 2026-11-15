"""Chats falsos para probar el agente sin red ni modelos."""

from types import SimpleNamespace


class ChatFijo:
    """Devuelve siempre el mismo texto y guarda lo que recibió."""

    def __init__(self, texto: str):
        self.texto = texto
        self.recibidos: list = []

    def invoke(self, mensajes):
        self.recibidos.append(mensajes)
        return SimpleNamespace(content=self.texto)


class ChatQueFalla:
    """Simula red apagada, timeout o cuota agotada."""

    def __init__(self, error: BaseException):
        self.error = error
        self.llamadas = 0

    def invoke(self, mensajes):
        self.llamadas += 1
        raise self.error
