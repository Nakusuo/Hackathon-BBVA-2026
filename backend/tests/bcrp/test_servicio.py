import json

import httpx
import pytest

from agent.juez import juzgar
from bcrp.servicio import (
    SerieNoDisponible,
    ServicioBCRP,
    fx_contrato,
    periodo_iso,
    rango,
    ultimo_valor,
)

RESPUESTA_TC = {
    "periods": [
        {"name": "11.Nov.26", "values": ["3.41085714285714"]},
        {"name": "12.Nov.26", "values": ["3.40585714285714"]},
        {"name": "13.Nov.26", "values": ["n.d."]},
    ]
}


def servicio(tmp_path, manejador, ahora=1000.0, grabada=None):
    ruta_grabada = tmp_path / "grabada.json"
    if grabada is not None:
        ruta_grabada.write_text(json.dumps(grabada), encoding="utf-8")
    cliente = httpx.Client(transport=httpx.MockTransport(manejador))
    reloj = {"t": ahora}
    s = ServicioBCRP(cliente, tmp_path / "cache.json", ruta_grabada, reloj=lambda: reloj["t"])
    return s, reloj


def api_ok(request):
    return httpx.Response(200, json=RESPUESTA_TC)


def api_caida(request):
    raise httpx.ConnectError("sin red")


@pytest.mark.parametrize(
    "nombre, iso",
    [("12.Nov.26", "2026-11-12"), ("01.Set.26", "2026-09-01"), ("Oct.2026", "2026-10")],
)
def test_periodo_iso(nombre, iso):
    assert periodo_iso(nombre) == iso


def test_ultimo_valor_salta_dias_sin_dato():
    assert ultimo_valor(RESPUESTA_TC) == ("2026-11-12", 3.40585714285714)


def test_sin_ningun_valor_falla_claro():
    with pytest.raises(SerieNoDisponible):
        ultimo_valor({"periods": [{"name": "13.Nov.26", "values": ["n.d."]}]})


def test_rango_mensual_cruza_el_anio():
    from datetime import date

    assert rango("mensual", date(2026, 3, 10)) == ("2025-9", "2026-3")


def test_api_ok_guarda_en_cache_y_luego_no_vuelve_a_llamar(tmp_path):
    llamadas = []

    def contar(request):
        llamadas.append(str(request.url))
        return api_ok(request)

    s, _ = servicio(tmp_path, contar)
    assert s.obtener("tipo_cambio")["origen"] == "api"
    r = s.obtener("tipo_cambio")
    assert r["origen"] == "cache" and r["valor"] == 3.406
    assert len(llamadas) == 1
    assert "PD04638PD" in llamadas[0]


def test_sin_red_usa_el_ultimo_valor_aunque_este_vencido(tmp_path):
    s, reloj = servicio(tmp_path, api_ok)
    s.obtener("tipo_cambio")
    reloj["t"] += 7 * 3600
    s.cliente = httpx.Client(transport=httpx.MockTransport(api_caida))
    r = s.obtener("tipo_cambio")
    assert r["origen"] == "ultimo_valor" and r["periodo"] == "2026-11-12"


def test_sin_red_ni_cache_usa_la_serie_grabada(tmp_path):
    grabada = {"inflacion_12m": {"periodo": "2026-10", "valor": 5.251}}
    s, _ = servicio(tmp_path, api_caida, grabada=grabada)
    r = s.obtener("inflacion_12m")
    assert r["origen"] == "serie_grabada" and r["valor"] == 5.251


def test_sin_nada_disponible_falla_claro(tmp_path):
    s, _ = servicio(tmp_path, api_caida, grabada={})
    with pytest.raises(SerieNoDisponible):
        s.obtener("tipo_cambio")


def test_error_500_tambien_cae_al_respaldo(tmp_path):
    grabada = {"tipo_cambio": {"periodo": "2026-11-12", "valor": 3.406}}
    s, _ = servicio(tmp_path, lambda r: httpx.Response(500), grabada=grabada)
    assert s.obtener("tipo_cambio")["origen"] == "serie_grabada"


def test_el_juez_acepta_las_cifras_del_bcrp(tmp_path):
    s, _ = servicio(tmp_path, api_ok)
    datos = {"get_fx": fx_contrato(s.obtener("tipo_cambio"))}
    assert juzgar("El 12 de noviembre de 2026 el dólar estaba en S/ 3.406.", datos).ok
