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
