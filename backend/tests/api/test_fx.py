import json
from datetime import date
from decimal import Decimal

import httpx
import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.routers.fx import obtener_servicio
from src.bcrp.servicio import ServicioBCRP

URL = "/api/v1/fx"

GRABADA = {"tipo_cambio": {"periodo": "2026-11-12", "valor": 3.4059, "grabado": "2026-11-14"}}
RESPUESTA_BCRP = {
    "periods": [
        {"name": "13.Nov.26", "values": ["3.41"]},
        {"name": "14.Nov.26", "values": ["n.d."]},
    ]
}


def servicio_con(tmp_path, manejador):
    """Servicio real con la red reemplazada por `manejador` y caché y serie grabada en una carpeta temporal."""
    grabada = tmp_path / "serie_grabada.json"
    grabada.write_text(json.dumps(GRABADA), encoding="utf-8")
    cliente = httpx.Client(transport=httpx.MockTransport(manejador))
    return ServicioBCRP(cliente=cliente, ruta_cache=tmp_path / "cache.json", ruta_grabada=grabada)


def sin_red(peticion):
    raise httpx.ConnectError("sin red", request=peticion)


def con_red(peticion):
    return httpx.Response(200, json=RESPUESTA_BCRP)


@pytest.fixture
def pedir(tmp_path):
    def _pedir(manejador, **params):
        servicio = servicio_con(tmp_path, manejador)
        app.dependency_overrides[obtener_servicio] = lambda: servicio
        try:
            return TestClient(app).get(URL, params=params)
        finally:
            app.dependency_overrides.clear()

    return _pedir


def test_fx_sin_red_usa_la_serie_grabada_y_lo_marca(pedir):
    response = pedir(sin_red)

    assert response.status_code == 200

    data = response.json()

    assert data["base"] == "USD"
    assert data["quote"] == "PEN"
    assert Decimal(data["rate"]) == Decimal("3.406")
    assert date.fromisoformat(data["date"]) == date(2026, 11, 12)
    assert data["source"] == "BCRP PD04638PD"
    assert data["is_fallback"] is True
    assert data["is_stale"] is True


def test_fx_con_red_devuelve_el_dato_fresco(pedir):
    data = pedir(con_red).json()

    assert Decimal(data["rate"]) == Decimal("3.41")
    assert date.fromisoformat(data["date"]) == date(2026, 11, 13)
    assert data["is_fallback"] is False
    assert data["is_stale"] is False


def test_fx_cae_al_ultimo_valor_si_la_red_se_cae_despues(tmp_path):
    servicio = servicio_con(tmp_path, con_red)
    servicio.reloj = lambda: 0
    servicio.obtener("tipo_cambio")
    servicio.reloj = lambda: 10**9  # la caché venció y la red ya no responde
    servicio.cliente = httpx.Client(transport=httpx.MockTransport(sin_red))
    app.dependency_overrides[obtener_servicio] = lambda: servicio
    try:
        data = TestClient(app).get(URL).json()
    finally:
        app.dependency_overrides.clear()

    assert Decimal(data["rate"]) == Decimal("3.41")
    assert data["is_stale"] is True


def test_fx_sin_nada_disponible_da_503(tmp_path):
    servicio = servicio_con(tmp_path, sin_red)
    servicio.ruta_grabada = tmp_path / "no_existe.json"
    app.dependency_overrides[obtener_servicio] = lambda: servicio
    try:
        response = TestClient(app).get(URL)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503


def test_fx_explicit_currencies(pedir):
    assert pedir(sin_red, base="USD", quote="PEN").status_code == 200


def test_fx_invalid_base(pedir):
    assert pedir(sin_red, base="EUR", quote="PEN").status_code == 422


def test_fx_invalid_quote(pedir):
    assert pedir(sin_red, base="USD", quote="EUR").status_code == 422
