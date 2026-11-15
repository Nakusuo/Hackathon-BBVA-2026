"""Datos vivos: lo que entra al aplicativo despues del cierre de datos. Validacion estricta, idempotencia, privacidad y categoria sin falsos positivos."""
import os
from datetime import date

import pytest

from src.agente_analitico import datos_vivos as DV
from src.agente_analitico import memoria
from src.comun import reloj
from src.comun.rutas import MODELOS

CID = "C00003"
necesita_modelo = pytest.mark.skipif(not os.path.isfile(os.path.join(MODELOS, "glosa.pkl")), reason="falta models/glosa.pkl (python analitica/eval/entrenar_modelos.py)")


@pytest.fixture(autouse=True)
def entorno(tmp_path, monkeypatch):
    monkeypatch.setenv("LUCAS_VIVO_DIR", str(tmp_path / "vivo"))
    monkeypatch.setattr(memoria, "CARPETA", str(tmp_path / "memoria"))
    reloj.fijar("2026-11-14")
    yield tmp_path
    reloj.fijar(None)


@pytest.mark.parametrize("args,motivo", [
    (dict(cid="", tipo="ingreso", monto=10), "customer_id"), (dict(cid="C 1;x", tipo="ingreso", monto=10), "customer_id"),
    (dict(cid=CID, tipo="deposito", monto=10), "tipo"), (dict(cid=CID, tipo="ingreso", monto=0), "monto"), (dict(cid=CID, tipo="ingreso", monto=-5), "monto"),
    (dict(cid=CID, tipo="ingreso", monto=float("nan")), "monto"), (dict(cid=CID, tipo="ingreso", monto=float("inf")), "monto"), (dict(cid=CID, tipo="ingreso", monto="abc"), "monto"),
    (dict(cid=CID, tipo="ingreso", monto=True), "monto"), (dict(cid=CID, tipo="ingreso", monto=1e9), "monto"), (dict(cid=CID, tipo="gasto", monto=10, fecha="2026-11-20"), "futura"),
    (dict(cid=CID, tipo="gasto", monto=10, fecha="no es fecha"), "fecha"), (dict(cid=CID, tipo="gasto", monto=10, id_mov="id raro;"), "id"),
])
def test_lo_invalido_se_rechaza_con_un_error_claro(args, motivo):
    a = dict(args)
    cid, tipo, monto = a.pop("cid"), a.pop("tipo"), a.pop("monto")
    with pytest.raises(ValueError, match=motivo):
        DV.registrar(cid, tipo, monto, **a)
    assert not os.path.isfile(DV._archivo())   # un rechazo no deja nada escrito a medias


def test_la_fecha_de_manana_se_acepta_por_la_zona_horaria_y_la_de_pasado_manana_no():
    assert DV.registrar(CID, "gasto", 10, fecha="2026-11-15")["monto"] == 10
    with pytest.raises(ValueError):
        DV.registrar(CID, "gasto", 10, fecha="2026-11-16")


def test_reintentar_con_el_mismo_id_no_duplica():
    a = DV.registrar(CID, "ingreso", 1500, categoria="ingreso_extra", id_mov="m1")
    b = DV.registrar(CID, "ingreso", 1500, categoria="ingreso_extra", id_mov="m1")
    assert not a["duplicado"] and b["duplicado"] and len(DV.listar(CID)) == 1


def test_el_mismo_id_en_otro_cliente_es_otro_movimiento():
    DV.registrar(CID, "gasto", 10, id_mov="m1")
    assert not DV.registrar("C00004", "gasto", 10, id_mov="m1")["duplicado"]


def test_categoria_explicita_valida_y_desconocida():
    assert DV.registrar(CID, "ingreso", 100, categoria="Gratificacion")["categoria"] == "gratificacion"
    r = DV.registrar(CID, "ingreso", 100, categoria="premio_gordo")
    assert r["categoria"] == "otros" and r["origen_categoria"] == "categoria_desconocida"


def test_una_categoria_de_gasto_no_vale_para_un_ingreso():
    assert DV.registrar(CID, "ingreso", 100, categoria="alimentos")["categoria"] == "otros"
    assert DV.registrar(CID, "gasto", 100, categoria="gratificacion")["categoria"] == "otros"


@necesita_modelo
def test_la_glosa_conocida_se_categoriza_y_la_ajena_queda_en_otros():
    assert DV.registrar(CID, "ingreso", 2800, glosa="ABONO GRATIFICACION")["categoria"] == "gratificacion"
    assert DV.registrar(CID, "gasto", 40, glosa="COMPRA BODEGA DONA ROSA")["categoria"] == "alimentos"
    for ajena in ("uber viaje", "premio sorteo", "venta de mi laptop", "xyz qwerty", "devolucion de impuestos"):
        r = DV.registrar(CID, "ingreso", 100, glosa=ajena)
        assert r["categoria"] == "otros" and r["origen_categoria"] == "sin_clasificar", ajena


@necesita_modelo
def test_una_glosa_de_ingreso_no_convierte_un_gasto_en_ingreso_extraordinario():
    assert DV.registrar(CID, "gasto", 500, glosa="ABONO GRATIFICACION")["categoria"] == "otros"


@necesita_modelo
def test_la_glosa_no_se_guarda(entorno):
    DV.registrar(CID, "gasto", 40, glosa="COMPRA BODEGA DONA ROSA")
    contenido = open(DV._archivo(), encoding="utf-8").read()
    assert "BODEGA" not in contenido.upper() and "glosa" not in contenido


def test_el_resumen_solo_cuenta_lo_posterior_al_cierre_de_datos():
    DV.registrar(CID, "ingreso", 500, categoria="sueldo", fecha="2025-11-20")   # antes del cierre: ya esta en los datos del cliente
    DV.registrar(CID, "ingreso", 1000, categoria="ingreso_extra", fecha="2026-11-10", id_mov="a")
    DV.registrar(CID, "gasto", 300, categoria="alimentos", fecha="2026-11-11", id_mov="b")
    DV.registrar("C00099", "ingreso", 7777, fecha="2026-11-11")                  # de otro cliente
    r = DV.resumen(CID, date(2025, 11, 29), date(2026, 11, 14))
    assert (r["n"], r["ingresos"], r["gastos"], r["neto"]) == (2, 1000.0, 300.0, 700.0)
    assert r["ultimo"]["id"] == "b" and r["gastos_por_categoria"] == {"alimentos": 300.0}


def test_un_movimiento_de_hoy_cuenta_y_uno_posterior_a_hoy_no():
    DV.registrar(CID, "gasto", 50, fecha="2026-11-14", id_mov="hoy")
    DV.registrar(CID, "gasto", 70, fecha="2026-11-15", id_mov="manana")
    assert DV.resumen(CID, date(2025, 11, 29), date(2026, 11, 14))["gastos"] == 50.0


def test_sin_movimientos_el_resumen_es_neutro():
    r = DV.resumen(CID, date(2025, 11, 29), date(2026, 11, 14))
    assert r["n"] == 0 and r["neto"] == 0 and r["ultimo"] is None


def test_una_linea_danada_no_tumba_al_resto():
    DV.registrar(CID, "gasto", 10, id_mov="ok1")
    with open(DV._archivo(), "a", encoding="utf-8") as f:
        f.write("{esto no es json\n")
    DV.registrar(CID, "gasto", 20, id_mov="ok2")
    assert [m["id"] for m in DV.listar(CID)] == ["ok1", "ok2"]


def test_el_derecho_de_supresion_borra_los_movimientos_vivos():
    memoria.sumar_puntos(CID, "prueba", 5)
    DV.registrar(CID, "gasto", 10, id_mov="x")
    DV.registrar("C00004", "gasto", 10, id_mov="y")
    assert memoria.olvidar(CID) is True
    assert DV.listar(CID) == [] and len(DV.listar("C00004")) == 1
    assert memoria.olvidar(CID) is False
