"""Proveedores de LLM: el contrato de cada uno (peticion, respuesta, reintento y errores) sin red. Un proveedor nuevo debe cumplir lo mismo."""
import pytest
import requests

from src.agente_analitico import proveedores as PV


class Resp:
    def __init__(self, codigo=200, cuerpo=None):
        self.status_code, self._cuerpo = codigo, cuerpo

    def json(self):
        if self._cuerpo is None:
            raise ValueError("sin json")
        return self._cuerpo

    def raise_for_status(self):
        if self.status_code >= 400:
            e = requests.HTTPError(f"HTTP {self.status_code}")
            e.response = self
            raise e


@pytest.fixture
def red(monkeypatch):
    """Reemplaza requests.post: guarda cada llamada y responde con lo que se le encole."""
    class Red:
        llamadas, respuestas = [], []

        def post(self, url, json=None, headers=None, timeout=None):
            self.llamadas.append({"url": url, "json": json, "headers": headers, "timeout": timeout})
            return self.respuestas.pop(0)
    r = Red()
    r.llamadas, r.respuestas = [], []
    monkeypatch.setattr(PV.requests, "post", r.post)
    monkeypatch.setattr(PV.time, "sleep", lambda s: None)
    monkeypatch.setitem(PV.USO, "llamadas", 0)
    monkeypatch.setitem(PV.USO, "entrada", 0)
    monkeypatch.setitem(PV.USO, "salida", 0)
    return r


@pytest.fixture
def compatible(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.ejemplo.test/v1/")
    monkeypatch.setenv("LLM_API_KEY", "clave-de-prueba")
    monkeypatch.setenv("LLM_MODEL", "modelo-x")
    return PV.Compatible()


OK = {"choices": [{"message": {"content": "  Hola. Tu decides.  "}}], "usage": {"prompt_tokens": 120, "completion_tokens": 8}}


def test_compatible_arma_la_peticion_chat_completions_y_cuenta_los_tokens(red, compatible):
    red.respuestas.append(Resp(200, OK))
    assert compatible.redactar("¿Llego a fin de mes?", "saldo: 100", "cercano") == "Hola. Tu decides."
    c = red.llamadas[0]
    assert c["url"] == "https://llm.ejemplo.test/v1/chat/completions" and c["headers"] == {"Authorization": "Bearer clave-de-prueba"}
    assert c["json"]["model"] == "modelo-x" and [m["role"] for m in c["json"]["messages"]] == ["system", "user"] and "DATOS:\nsaldo: 100" in c["json"]["messages"][1]["content"]
    assert c["json"]["max_tokens"] == 450 and c["json"]["temperature"] == 0.2
    assert PV.USO == {"llamadas": 1, "entrada": 120, "salida": 8}


def test_compatible_sin_configuracion_no_hace_ninguna_llamada(red, monkeypatch):
    for v in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        monkeypatch.delenv(v, raising=False)
    p = PV.Compatible()
    p.base = p.clave = p.modelo = ""
    assert not p.disponible()
    with pytest.raises(PV.ErrorProveedor, match="faltan"):
        p.redactar("hola", "ninguno", "neutro")
    assert red.llamadas == []


def test_un_limite_de_uso_se_reintenta_una_vez_y_se_recupera(red, compatible):
    red.respuestas += [Resp(429), Resp(200, OK)]
    assert compatible.redactar("hola", "ninguno", "neutro") == "Hola. Tu decides." and len(red.llamadas) == 2


def test_un_limite_de_uso_persistente_se_rinde_con_su_codigo(red, compatible):
    red.respuestas += [Resp(429), Resp(429)]
    with pytest.raises(PV.ErrorProveedor, match="HTTP 429"):
        compatible.redactar("hola", "ninguno", "neutro")
    assert len(red.llamadas) == 2


@pytest.mark.parametrize("codigo", [400, 401, 403, 500])
def test_un_error_definitivo_no_se_reintenta(red, compatible, codigo):
    red.respuestas.append(Resp(codigo))
    with pytest.raises(PV.ErrorProveedor, match=f"HTTP {codigo}"):
        compatible.redactar("hola", "ninguno", "neutro")
    assert len(red.llamadas) == 1


@pytest.mark.parametrize("cuerpo", [{}, {"choices": []}, {"choices": [{"mensaje": "x"}]}, None])
def test_una_respuesta_mal_formada_es_un_error_del_proveedor_no_una_caida(red, compatible, cuerpo):
    red.respuestas.append(Resp(200, cuerpo))
    with pytest.raises(PV.ErrorProveedor):
        compatible.redactar("hola", "ninguno", "neutro")


def test_gemini_manda_la_clave_en_el_encabezado_y_nunca_en_la_url(red):
    g = PV.Gemini()
    g.clave, g.modelo = "clave-secreta-de-prueba", "gemini-prueba"
    red.respuestas.append(Resp(200, {"candidates": [{"content": {"parts": [{"text": " Hola. Tu decides. "}]}}], "usageMetadata": {"promptTokenCount": 50, "candidatesTokenCount": 5}}))
    assert g.redactar("hola", "ninguno", "neutro") == "Hola. Tu decides."
    c = red.llamadas[0]
    assert "clave-secreta" not in c["url"] and c["headers"] == {"x-goog-api-key": "clave-secreta-de-prueba"} and c["url"].endswith("/models/gemini-prueba:generateContent")
    assert c["json"]["generationConfig"]["maxOutputTokens"] == 450 and PV.USO["entrada"] == 50 and PV.USO["salida"] == 5


def test_gemini_sin_clave_no_llama(red):
    g = PV.Gemini()
    g.clave = ""
    with pytest.raises(PV.ErrorProveedor, match="sin clave"):
        g.redactar("hola", "ninguno", "neutro")
    assert red.llamadas == []


@pytest.mark.parametrize("modo,esperado", [("gemini", ["gemini", "ollama"]), ("compatible", ["compatible", "ollama"]), ("openai", ["compatible", "ollama"]), ("plantillas", []), ("ollama", ["ollama"]), ("cualquier_otro", ["ollama"])])
def test_la_cadena_de_proveedores_segun_la_configuracion(monkeypatch, modo, esperado):
    monkeypatch.setenv("LLM_PROVIDER", modo)
    assert [p.nombre for p in PV.cadena()] == esperado


def test_solo_el_proveedor_local_no_es_externo():
    assert (PV.Ollama.externo, PV.Gemini.externo, PV.Compatible.externo) == (False, True, True)


def test_el_prompt_prohibe_lo_que_el_agente_no_hace():
    s = PV.SISTEMA.lower()
    for regla in ("exclusivamente los datos", "no inventes cifras", "no calcules numeros nuevos", "nunca nombres la seccion datos", "tu decides", "codigo, problemas de matematica"):
        assert regla in s, regla
