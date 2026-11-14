import pytest

from src.agente_analitico import traduccion as TR
from src.agente_analitico.verificador import numeros_de


def test_detecta_el_idioma_de_la_pregunta():
    assert TR.detectar_idioma("¿Llego a fin de mes con mi plata?") == "es"
    assert TR.detectar_idioma("How much money will I have at the end of the month?") == "en"
    assert TR.detectar_idioma("Kunan ima qullqiyta waqaychani mana allin") == "qu"
    assert TR.detectar_idioma("") == "es"


def test_las_cifras_y_los_nombres_se_protegen_y_se_restauran():
    t = "En Piura tu saldo sera S/ 7,281 (28 %) segun el ENFEN, con 3 recomendaciones."
    p, v = TR.proteger(t)
    assert "Piura" not in p and "7,281" not in p and "ENFEN" not in p
    r, ok = TR.restaurar(p, v)
    assert ok and r == t


def test_se_detecta_un_marcador_perdido_o_repetido():
    p, v = TR.proteger("Saldo S/ 100 y 20 %")
    assert TR.restaurar(p.replace("⟦0⟧", ""), v)[1] is False
    assert TR.restaurar(p + " ⟦0⟧", v)[1] is False


def _con_proveedor(monkeypatch, f):
    monkeypatch.setattr(TR, "PROVEEDORES", [("falso", f)])


def test_traduccion_integra_se_acepta(monkeypatch):
    _con_proveedor(monkeypatch, lambda t, o, d: "Your balance will be " + t.split("saldo sera ")[1])
    r = TR.traducir("Tu saldo sera S/ 500.", "es", "en")
    assert r["ok"] and "S/ 500" in r["texto"] and r["proveedor"] == "falso"


def test_traduccion_que_altera_una_cifra_se_descarta(monkeypatch):
    _con_proveedor(monkeypatch, lambda t, o, d: "Your balance will be 999")
    r = TR.traducir("Tu saldo sera S/ 500.", "es", "en")
    assert not r["ok"] and r["texto"] == "Tu saldo sera S/ 500."


def test_si_no_hay_proveedor_queda_el_espanol(monkeypatch):
    def cae(t, o, d):
        raise RuntimeError("sin red")
    _con_proveedor(monkeypatch, cae)
    r = TR.traducir("Tu saldo sera S/ 500.", "es", "qu")
    assert not r["ok"] and "S/ 500" in r["texto"] and "RuntimeError" in r["motivo"]


def _error_http(codigo):
    import requests
    resp = requests.Response()
    resp.status_code = codigo
    return requests.HTTPError(f"HTTP {codigo}", response=resp)


@pytest.mark.parametrize("codigo", [429, 500, 503])
def test_un_error_transitorio_se_reintenta_una_vez_y_se_recupera(monkeypatch, codigo):
    monkeypatch.setattr(TR.time, "sleep", lambda s: None)
    llamadas = []

    def inestable(t, o, d):
        llamadas.append(1)
        if len(llamadas) == 1:
            raise _error_http(codigo)
        return "Your balance will be " + t.split("saldo sera ")[1]
    _con_proveedor(monkeypatch, inestable)
    r = TR.traducir("Tu saldo sera S/ 500.", "es", "en")
    assert r["ok"] and len(llamadas) == 2 and "S/ 500" in r["texto"]


@pytest.mark.parametrize("codigo", [400, 401, 403])
def test_un_error_definitivo_no_se_reintenta_y_deja_su_codigo_en_el_diagnostico(monkeypatch, codigo):
    monkeypatch.setattr(TR.time, "sleep", lambda s: None)
    llamadas = []

    def malo(t, o, d):
        llamadas.append(1)
        raise _error_http(codigo)
    _con_proveedor(monkeypatch, malo)
    r = TR.traducir("Tu saldo sera S/ 500.", "es", "en")
    assert not r["ok"] and len(llamadas) == 1 and f"HTTP {codigo}" in r["motivo"]


def test_si_el_error_transitorio_persiste_se_rinde_tras_el_reintento(monkeypatch):
    monkeypatch.setattr(TR.time, "sleep", lambda s: None)
    llamadas = []

    def siempre_429(t, o, d):
        llamadas.append(1)
        raise _error_http(429)
    _con_proveedor(monkeypatch, siempre_429)
    r = TR.traducir("Tu saldo sera S/ 500.", "es", "en")
    assert not r["ok"] and len(llamadas) == 2 and "HTTP 429" in r["motivo"] and "S/ 500" in r["texto"]


def test_el_prompt_solo_habla_de_marcadores_si_el_texto_los_lleva(monkeypatch):
    """Regresion: con una pregunta sin cifras el prompt mencionaba ⟦0⟧ como ejemplo y Gemini lo inventaba en la traduccion."""
    vistos = []
    monkeypatch.setattr(TR, "_gemini", lambda sistema, usuario, timeout=40: vistos.append(sistema) or "ok")
    TR._por_gemini("¿Cuanto voy a ganar?", "es", "qu")
    TR._por_gemini("Tu saldo sera ⟦0⟧ en ⟦1⟧.", "es", "qu")
    assert "⟦" not in vistos[0]
    assert "2 marcador" in vistos[1] and "⟦0⟧" in vistos[1]


def test_mismo_idioma_no_traduce():
    assert TR.traducir("Hola S/ 5", "es", "es")["ok"]


@pytest.mark.parametrize("texto", ["Hola, Campeon. Tu saldo sera S/ 7,281 con 28 % de riesgo.", "Alerta en Piura por El Nino segun el ENFEN: 3 acciones."])
def test_ninguna_traduccion_aceptada_inventa_numeros(monkeypatch, texto):
    _con_proveedor(monkeypatch, lambda t, o, d: t)
    r = TR.traducir(texto, "es", "en")
    assert set(numeros_de(r["texto"])) <= set(numeros_de(texto))


# ---------------------------------------------------------------------------- Google Cloud Translation v2: contrato con respuestas simuladas
# No hay clave propia y la de Gemini no se usa contra otras APIs de Google: aqui se prueba, sin red, que el pedido tiene la forma del contrato publico de la API v2
# (POST /language/translate/v2, clave en la cabecera X-Goog-Api-Key, cuerpo q/source/target/format, respuesta data.translations[].translatedText)
# y que el resto del flujo (marcadores, cifras, errores) reacciona bien a lo que esa API puede devolver.
# Contrastado el 2026-11-14 con la documentacion oficial: docs.cloud.google.com/translate/docs/reference/rest/v2/translate (endpoint, q/source/target/format, data.translations[].translatedText),
# .../translate/docs/basic/translate-text-basic (ejemplo con cuerpo JSON), .../translate/docs/languages (quechua "qu" esta soportado) y .../docs/authentication/api-keys-use (la clave puede ir en la
# cabecera X-goog-api-key y se advierte contra ponerla en la URL). Lo que NO se probo: una llamada real con clave (no hay clave propia).
class _Resp:
    def __init__(self, cuerpo, codigo=200):
        self._c, self.status_code = cuerpo, codigo

    def json(self):
        return self._c

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            e = requests.HTTPError(f"HTTP {self.status_code}")
            e.response = self
            raise e


def _simular_google(monkeypatch, responder, visto):
    monkeypatch.setenv("GOOGLE_TRANSLATE_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(TR, "cargar_env", lambda: None)
    monkeypatch.setattr(TR, "PROVEEDORES", [("google_cloud", TR._google_cloud)])

    def post(url, headers=None, json=None, timeout=None):
        visto.update(url=url, headers=headers, json=json, timeout=timeout)
        return responder(json)
    monkeypatch.setattr(TR.requests, "post", post)


def test_google_el_pedido_tiene_la_forma_del_contrato_y_la_clave_va_en_la_cabecera(monkeypatch):
    visto = {}
    _simular_google(monkeypatch, lambda j: _Resp({"data": {"translations": [{"translatedText": "Hello"}]}}), visto)
    r = TR.traducir("Hola", "es", "en")
    assert r["ok"] and r["texto"] == "Hello" and r["proveedor"] == "google_cloud"
    assert visto["url"] == "https://translation.googleapis.com/language/translate/v2"
    assert visto["headers"] == {"x-goog-api-key": "clave-de-prueba"} and "key=" not in visto["url"]   # la clave nunca va en la URL (queda en registros)
    assert visto["json"] == {"q": "Hola", "source": "es", "target": "en", "format": "text"} and visto["timeout"] > 0


def test_google_sin_clave_no_hace_ningun_pedido_y_cae_al_espanol(monkeypatch):
    llamado = []
    monkeypatch.delenv("GOOGLE_TRANSLATE_API_KEY", raising=False)
    monkeypatch.setattr(TR, "cargar_env", lambda: None)
    monkeypatch.setattr(TR, "PROVEEDORES", [("google_cloud", TR._google_cloud)])
    monkeypatch.setattr(TR.requests, "post", lambda *a, **k: llamado.append(1))
    r = TR.traducir("Hola", "es", "en")
    assert not llamado and not r["ok"] and r["texto"] == "Hola" and "google_cloud" in r["motivo"]


def test_google_con_marcadores_espaciados_se_normalizan_y_las_cifras_vuelven(monkeypatch):
    visto = {}
    # Google no conoce los marcadores y a veces los separa con espacios: se aceptan si vuelven todos
    _simular_google(monkeypatch, lambda j: _Resp({"data": {"translations": [{"translatedText": "You will have ⟦ 0 ⟧ left in ⟦1 ⟧"}]}}), visto)
    r = TR.traducir("Te quedaran S/ 120 en Piura", "es", "en")
    assert r["ok"] and r["texto"] == "You will have S/ 120 left in Piura"
    assert "⟦0⟧" in visto["json"]["q"] and "⟦1⟧" in visto["json"]["q"] and "120" not in visto["json"]["q"]   # las cifras y los nombres no viajan en claro


def test_google_que_pierde_un_marcador_se_descarta(monkeypatch):
    _simular_google(monkeypatch, lambda j: _Resp({"data": {"translations": [{"translatedText": "You will have little left"}]}}), {})
    r = TR.traducir("Te quedaran S/ 120", "es", "en")
    assert not r["ok"] and r["texto"] == "Te quedaran S/ 120" and "marcadores" in r["motivo"]


@pytest.mark.parametrize("codigo,reintenta", [(429, True), (503, True), (403, False), (400, False), (401, False)])
def test_google_errores_http_se_clasifican_y_dejan_su_codigo(monkeypatch, codigo, reintenta):
    monkeypatch.setattr(TR.time, "sleep", lambda s: None)
    visto, llamadas = {}, []
    _simular_google(monkeypatch, lambda j: llamadas.append(1) or _Resp({"error": {"message": "x"}}, codigo), visto)
    r = TR.traducir("Hola", "es", "en")
    assert not r["ok"] and f"HTTP {codigo}" in r["motivo"] and r["texto"] == "Hola"
    assert len(llamadas) == (2 if reintenta else 1)


def test_google_con_respuesta_mal_formada_no_rompe_el_agente(monkeypatch):
    _simular_google(monkeypatch, lambda j: _Resp({"data": {}}), {})
    r = TR.traducir("Hola", "es", "en")
    assert not r["ok"] and r["texto"] == "Hola"


def test_google_cae_a_gemini_si_falla_y_gemini_si_traduce(monkeypatch):
    visto = {}
    _simular_google(monkeypatch, lambda j: _Resp({}, 403), visto)
    monkeypatch.setattr(TR, "PROVEEDORES", [("google_cloud", TR._google_cloud), ("gemini", lambda t, o, d: "Hello")])
    r = TR.traducir("Hola", "es", "en")
    assert r["ok"] and r["proveedor"] == "gemini" and r["texto"] == "Hello"


def test_la_traduccion_de_gemini_une_las_partes_y_descarta_una_cortada(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(TR, "cargar_env", lambda: None)
    visto = {}
    _simular_google(monkeypatch, lambda j: None, visto)   # reutiliza el sustituto de requests.post

    def post(url, headers=None, json=None, timeout=None):
        return _Resp(visto["respuesta"])
    monkeypatch.setattr(TR.requests, "post", post)
    visto["respuesta"] = {"candidates": [{"content": {"parts": [{"text": "Hello, "}, {"text": "your balance is low."}]}, "finishReason": "STOP"}]}
    assert TR._gemini("sistema", "Hola, tu saldo es bajo.") == "Hello, your balance is low."
    visto["respuesta"] = {"candidates": [{"content": {"parts": [{"text": "Hello, your bal"}]}, "finishReason": "MAX_TOKENS"}]}
    with pytest.raises(RuntimeError, match="incompleta"):
        TR._gemini("sistema", "Hola, tu saldo es bajo.")
