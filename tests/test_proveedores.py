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
    assert c["json"]["max_tokens"] == 1024 and c["json"]["temperature"] == 0.2
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


@pytest.mark.parametrize("codigo", [429, 500, 503])
def test_un_error_transitorio_se_reintenta_y_se_recupera(red, compatible, codigo):
    red.respuestas += [Resp(codigo), Resp(200, OK)]
    assert compatible.redactar("hola", "ninguno", "neutro") == "Hola. Tu decides." and len(red.llamadas) == 2


def test_se_reintenta_hasta_tres_veces_con_espera_y_luego_se_rinde_con_su_codigo(red, compatible, monkeypatch):
    esperas = []
    monkeypatch.setattr(PV.time, "sleep", esperas.append)
    red.respuestas += [Resp(503), Resp(503), Resp(503)]
    with pytest.raises(PV.ErrorProveedor, match="HTTP 503"):
        compatible.redactar("hola", "ninguno", "neutro")
    assert len(red.llamadas) == 3 and esperas == [1.5, 3.0]


def test_gemini_tambien_reintenta_un_error_transitorio_y_deja_el_codigo_si_se_rinde(red):
    g = PV.Gemini()
    g.clave = "clave-de-prueba"
    red.respuestas += [Resp(503), Resp(200, {"candidates": [{"content": {"parts": [{"text": "Hola. Tu decides."}]}, "finishReason": "STOP"}]})]
    assert g.redactar("hola", "ninguno", "neutro") == "Hola. Tu decides." and len(red.llamadas) == 2
    red.llamadas.clear()
    red.respuestas += [Resp(429), Resp(429), Resp(429)]
    with pytest.raises(PV.ErrorProveedor, match="HTTP 429"):
        g.redactar("hola", "ninguno", "neutro")
    assert len(red.llamadas) == 3


@pytest.mark.parametrize("codigo", [400, 401, 403])
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
    assert c["json"]["generationConfig"]["maxOutputTokens"] == 1024 and PV.USO["entrada"] == 50 and PV.USO["salida"] == 5


def test_gemini_sin_clave_no_llama(red):
    g = PV.Gemini()
    g.clave = ""
    with pytest.raises(PV.ErrorProveedor, match="sin clave"):
        g.redactar("hola", "ninguno", "neutro")
    assert red.llamadas == []


@pytest.mark.parametrize("modo,esperado", [("gemini", ["gemini"]), ("compatible", ["compatible"]), ("openai", ["compatible"]), ("plantillas", []), ("ollama", ["ollama"]), ("cualquier_otro", ["ollama"])])
def test_la_cadena_de_proveedores_segun_la_configuracion(monkeypatch, modo, esperado):
    monkeypatch.setenv("LLM_PROVIDER", modo)
    assert [p.nombre for p in PV.cadena()] == esperado


def test_solo_el_proveedor_local_no_es_externo():
    assert (PV.Ollama.externo, PV.Gemini.externo, PV.Compatible.externo) == (False, True, True)


def test_el_prompt_prohibe_lo_que_el_agente_no_hace():
    s = PV.SISTEMA.lower()
    for regla in ("exclusivamente los datos", "no inventes cifras", "no calcules numeros nuevos", "nunca nombres la seccion datos", "tu decides", "codigo, problemas de matematica"):
        assert regla in s, regla


# ---------------------------------------------------------------------------- respuestas cortadas a la mitad
# Salio de un fallo real de la QA con Gemini: el tope de tokens corto dos respuestas («...en la entidad financiera que eleg») y el agente las mostro y las guardo en la cache.
def test_gemini_rechaza_una_respuesta_cortada_por_el_tope_de_tokens(red):
    g = PV.Gemini()
    g.clave = "clave-de-prueba"
    red.respuestas.append(Resp(200, {"candidates": [{"content": {"parts": [{"text": "Tu deposito llega a tu cuenta de CTS en la entidad financiera que eleg"}]}, "finishReason": "MAX_TOKENS"}],
                                     "usageMetadata": {"promptTokenCount": 50, "candidatesTokenCount": 450}}))
    with pytest.raises(PV.ErrorProveedor, match="incompleta"):
        g.redactar("hola", "ninguno", "neutro")
    assert PV.USO["salida"] == 450   # el costo se cuenta aunque la respuesta se descarte


def test_gemini_acepta_una_respuesta_que_termino_bien(red):
    g = PV.Gemini()
    g.clave = "clave-de-prueba"
    red.respuestas.append(Resp(200, {"candidates": [{"content": {"parts": [{"text": "Hola. Tu decides."}]}, "finishReason": "STOP"}]}))
    assert g.redactar("hola", "ninguno", "neutro") == "Hola. Tu decides."


def test_compatible_rechaza_una_respuesta_cortada_por_longitud(red, compatible):
    red.respuestas.append(Resp(200, {"choices": [{"message": {"content": "Tu saldo sera de S/ 4"}, "finish_reason": "length"}], "usage": {"prompt_tokens": 10, "completion_tokens": 1024}}))
    with pytest.raises(PV.ErrorProveedor, match="incompleta"):
        compatible.redactar("hola", "ninguno", "neutro")


def test_ollama_rechaza_una_respuesta_cortada_por_longitud(red):
    o = PV.Ollama()
    red.respuestas.append(Resp(200, {"message": {"content": "Tu saldo sera de S/ 4"}, "done_reason": "length"}))
    with pytest.raises(PV.ErrorProveedor, match="incompleta"):
        o.redactar("hola", "ninguno", "neutro")


@pytest.mark.parametrize("texto,esperado", [("Tu decides.", True), ("Tu saldo es bajo (S/ 4).", True), ("¿Quieres ver mas?", True), ("**Tu decides.**", True),
                                            ("llega a tu cuenta de CTS en la entidad financiera que eleg", False), ("¡Hola! ¡Que gran nivel el", False), ("", False)])
def test_el_juez_solo_acepta_borradores_que_terminan_en_una_oracion_completa(texto, esperado):
    from src.agente_analitico.grafo import _termina_en_oracion_completa
    assert _termina_en_oracion_completa(texto) is esperado


def test_gemini_une_todas_las_partes_de_texto_y_deja_fuera_el_razonamiento(red):
    # fallo real: la API devolvio la respuesta en dos partes y el agente solo leia la primera (texto cortado a la mitad con finishReason STOP)
    g = PV.Gemini()
    g.clave = "clave-de-prueba"
    red.respuestas.append(Resp(200, {"candidates": [{"content": {"parts": [{"text": "razonamiento interno", "thought": True}, {"text": "Prepara tu hogar y arma un fondo "}, {"text": "de S/ 7,144 para protegerte. Tu decides."}]}, "finishReason": "STOP"}]}))
    assert g.redactar("hola", "ninguno", "neutro") == "Prepara tu hogar y arma un fondo de S/ 7,144 para protegerte. Tu decides."


def test_texto_de_gemini_con_una_sola_parte_no_cambia_nada():
    assert PV.texto_de_gemini({"candidates": [{"content": {"parts": [{"text": "  Hola.  "}]}}]}) == "Hola."


@pytest.mark.parametrize("texto,filtra", [("por ahora solo rige lo que dicen los DATOS.", True), ("DATOS:\nsaldo: 100", True), ("Tus datos estan protegidos.", False), ("Los datos del cliente llegan hasta noviembre.", False)])
def test_el_juez_rechaza_un_borrador_que_nombra_la_seccion_interna_del_prompt(texto, filtra):
    from src.agente_analitico.grafo import _filtra_el_prompt
    assert _filtra_el_prompt(texto) is filtra


def test_el_respaldo_local_es_opcional_y_por_defecto_si_la_api_cae_responden_las_plantillas(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    assert [p.nombre for p in PV.cadena()] == ["gemini"]   # sin respaldo local: si Gemini falla, el agente contesta con plantillas
    monkeypatch.setenv("LLM_FALLBACK_LOCAL", "1")
    assert [p.nombre for p in PV.cadena()] == ["gemini", "ollama"]


@pytest.mark.parametrize("texto,vacia", [("Tu decides.", True), ("  Tu decides  ", True), ("Si.", True), ("No lo se. Tu decides.", True),
                                         ("Tu saldo esperado es de S/ 7,395 en 30 dias, con un rango razonable. Tu decides.", False), ("La TCEA es el costo total anual de un credito, con intereses y comisiones.", False)])
def test_el_juez_rechaza_un_borrador_que_casi_no_dice_nada(texto, vacia):
    from src.agente_analitico.grafo import _es_respuesta_vacia
    assert _es_respuesta_vacia(texto) is vacia
