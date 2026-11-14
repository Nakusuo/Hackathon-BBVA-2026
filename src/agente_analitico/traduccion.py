"""Idiomas del agente: espanol, ingles y quechua. Detecta el idioma, traduce la pregunta al espanol y la respuesta al idioma del usuario.
Las cifras, los montos y los nombres propios se protegen con marcadores antes de traducir y se verifican despues: una traduccion que los altere se descarta
y el usuario recibe el espanol. Proveedores en orden: Google Cloud Translation (solo si hay GOOGLE_TRANSLATE_API_KEY), Gemini y espanol.
Quechua: la variedad es la sureña (Cusco-Collao y Ayacucho-Chanka). La calidad no esta validada por un hablante nativo."""
import os
import re
import time

import requests

from src.comun.rutas import cargar_env
from src.agente_analitico.verificador import numeros_de

IDIOMAS = {"es": "espanol", "en": "ingles", "qu": "quechua sureño (Cusco-Collao o Ayacucho-Chanka), en alfabeto latino"}
ENTIDADES = ["Banco Kawsay", "Lucas", "ENFEN", "BCRP", "SBS", "INEI", "El Nino", "El Niño", "Tumbes", "Piura", "Lambayeque", "La Libertad", "Cajamarca", "Lima", "Callao", "Ica", "Ancash",
             "Arequipa", "Moquegua", "Tacna", "Cusco", "Puno", "Junin", "Loreto", "Ucayali", "San Martin", "Amazonas"]
PAT_VALOR = re.compile(r"S/\s?\d[\d.,]*|\d[\d.,]*\s?%|\d[\d.,]*")
QUECHUA = {"qullqi", "qolqe", "qullqiy", "ñuqa", "noqa", "ñoqa", "kay", "chay", "ima", "imatan", "imataq", "mana", "manan", "allin", "sumaq", "wasi", "runa", "kunan", "kunanqa", "munani", "munaymi", "yachay",
           "tukuy", "hukllaman", "ñuqaqa", "qanqa", "qan", "imayna", "hayk'a", "haykaq", "kachun", "yanapay", "yanapayuway", "willay", "huk", "iskay", "kinsa", "tawa", "pisqa", "chaymanta", "hinaspa", "ichaqa",
           "paypa", "kanku", "kani", "kashan", "kachkan", "tarpuy", "tantay", "ayllu", "llaqta", "mikhuy", "pagay", "pagaq", "wakichiy", "waqaychay", "waqaychana", "ñawpaq", "qhipa"}
INGLES = {"the", "is", "are", "my", "how", "do", "i", "can", "money", "what", "will", "should", "have", "need", "loan", "save", "much", "with", "this", "that", "for", "you", "your", "month", "end", "enough"}
ESPANOL = {"el", "la", "los", "las", "que", "de", "mi", "mis", "como", "cuanto", "puedo", "tengo", "plata", "para", "con", "una", "un", "en", "es", "por", "me", "se", "mes", "fin", "llego"}


def detectar_idioma(texto: str) -> str:
    """Heuristica por palabras frecuentes. Es / en / qu. Ante la duda, espanol."""
    pal = re.findall(r"[a-zA-ZñÑáéíóúÁÉÍÓÚ']+", texto.lower())
    if not pal:
        return "es"
    q, e, s = (sum(p in L for p in pal) for L in (QUECHUA, INGLES, ESPANOL))
    if q >= 2 and q >= max(e, s):
        return "qu"
    if e >= 2 and e > s:
        return "en"
    return "es"


def proteger(texto: str) -> tuple[str, list[str]]:
    """Cambia cifras, montos y nombres propios por marcadores que la traduccion debe conservar.
    Un solo recorrido con una expresion que junta cifras y nombres: los marcadores no pasan por otro filtro."""
    valores: list[str] = []
    ents = "|".join(re.escape(e) for e in sorted(ENTIDADES, key=len, reverse=True))
    patron = re.compile("(?:" + PAT_VALOR.pattern + ")|" + chr(92) + "b(?:" + ents + ")" + chr(92) + "b")

    def marca(m):
        valores.append(m.group(0))
        return "⟦" + str(len(valores) - 1) + "⟧"
    return patron.sub(marca, texto), valores


def restaurar(texto: str, valores: list[str]) -> tuple[str, bool]:
    """Devuelve (texto, ok). ok es False si falta algun marcador o aparece uno repetido o desconocido."""
    hallados = re.findall(r"⟦(\d+)⟧", texto)
    ok = sorted(int(h) for h in hallados) == list(range(len(valores)))
    for i, v in enumerate(valores):
        texto = texto.replace(f"⟦{i}⟧", v)
    return texto, ok


def _gemini(sistema: str, usuario: str, timeout: int = 40) -> str:
    cargar_env()
    clave = os.environ.get("GEMINI_API_KEY", "")
    if not clave:
        raise RuntimeError("sin clave de Gemini")
    modelo = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
    r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent", headers={"x-goog-api-key": clave}, timeout=timeout,
                      json={"systemInstruction": {"parts": [{"text": sistema}]}, "contents": [{"role": "user", "parts": [{"text": usuario}]}], "generationConfig": {"temperature": 0, "maxOutputTokens": 900}})
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def _google_cloud(texto: str, origen: str, destino: str, timeout: int = 25) -> str:
    cargar_env()
    clave = os.environ.get("GOOGLE_TRANSLATE_API_KEY", "")
    if not clave:
        raise RuntimeError("sin GOOGLE_TRANSLATE_API_KEY")
    r = requests.post("https://translation.googleapis.com/language/translate/v2", headers={"x-goog-api-key": clave}, timeout=timeout,
                      json={"q": texto, "source": origen, "target": destino, "format": "text"})
    r.raise_for_status()
    return r.json()["data"]["translations"][0]["translatedText"]


def _por_gemini(texto: str, origen: str, destino: str) -> str:
    sistema = f"Eres un traductor profesional. Traduce de {IDIOMAS[origen]} a {IDIOMAS[destino]}. "
    if "⟦" in texto:   # el ejemplo de marcador solo se nombra si el texto los lleva: si no, el modelo lo inventa
        n = len(re.findall(r"⟦\d+⟧", texto))
        sistema += (f"El texto contiene {n} marcador(es) como ⟦0⟧: conservalos EXACTAMENTE, una sola vez cada uno (no los traduzcas, no los muevas de oracion sin necesidad, no agregues ni quites ninguno). ")
    sistema += "No inventes informacion; usa frases cortas y lenguaje sencillo; responde SOLO con la traduccion, sin comillas ni comentarios."
    return _gemini(sistema, texto)


PROVEEDORES = [("google_cloud", _google_cloud), ("gemini", _por_gemini)]


def traducir(texto: str, origen: str, destino: str) -> dict:
    """Traduce protegiendo cifras y nombres. Si ningun proveedor devuelve una traduccion integra, devuelve el texto original con ok=False."""
    t0 = time.time()
    if origen == destino or not texto.strip():
        return {"texto": texto, "ok": True, "proveedor": "ninguno", "segundos": 0.0, "motivo": "mismo idioma"}
    protegido, valores = proteger(texto)
    errores = []
    for nombre, f in PROVEEDORES:
        try:
            salida = f(protegido, origen, destino)
        except Exception as e:  # sin red, sin clave o limite de uso: se prueba el siguiente
            errores.append(f"{nombre}: {type(e).__name__}")
            continue
        if nombre == "google_cloud":  # Google no conoce los marcadores: puede espaciarlos, se normalizan
            salida = re.sub(r"⟦\s*(\d+)\s*⟧", r"⟦\1⟧", salida)
        final, ok = restaurar(salida, valores)
        if ok and not set(numeros_de(final)) - set(numeros_de(texto)):
            return {"texto": final, "ok": True, "proveedor": nombre, "segundos": round(time.time() - t0, 2), "motivo": ""}
        errores.append(f"{nombre}: marcadores o cifras alterados")
    return {"texto": texto, "ok": False, "proveedor": "ninguno", "segundos": round(time.time() - t0, 2), "motivo": "; ".join(errores)}


AVISO = {"en": "(Automatic translation. If in doubt, ask in Spanish or talk to an advisor.)",
         "qu": "(Traduccion automatica al quechua. Si tienes dudas, pregunta en espanol o consulta con un asesor.)"}
NOTA_FALLO = {"en": "(I could not translate this safely, so here it is in Spanish.)", "qu": "(No pude traducir esto con seguridad, por eso te respondo en espanol.)"}
