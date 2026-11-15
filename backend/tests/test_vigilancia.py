"""Vigilancia: cada detector con su caso positivo Y con los casos que NO deben avisar (falsos positivos), mas deduplicacion y tope semanal."""
from datetime import date, datetime, timedelta

import pytest

from src.agente_analitico import datos_vivos as DV
from src.agente_analitico import memoria
from src.agente_analitico import vigilancia as V
from src.comun import reloj
from src.models import calendario_laboral as CL

CID = "C00003"


@pytest.fixture(autouse=True)
def entorno(tmp_path, monkeypatch):
    monkeypatch.setenv("LUCAS_VIVO_DIR", str(tmp_path / "vivo"))
    monkeypatch.setattr(memoria, "CARPETA", str(tmp_path / "memoria"))
    reloj.fijar("2026-11-14")
    yield
    reloj.fijar(None)


def ctx(hoy="2026-11-14", tipo="dependiente", base=3000.0, origen="historial", vivos_n=0, desfase=11, p_rojo=0.0, dep="Lima"):
    return {"customer_id": CID, "hoy": hoy, "departamento": dep, "features": {"ingreso_medio": 3000.0}, "calendario": CL.calendario(date.fromisoformat(hoy), tipo, base, origen),
            "movimientos_vivos": {"n": vivos_n}, "desfase_datos_dias": desfase, "pronostico": {"p_rojo": p_rojo, "dia_riesgo": None}}


def tipos(evs):
    return [e["tipo"] for e in evs]


# ---------------------------------------------------------------- calendario
def test_a_dos_dias_del_deposito_de_cts_avisa_y_recuerda_que_el_retiro_total_vence():
    ev = V.detectar_calendario(ctx("2026-11-14"))
    assert tipos(ev) == ["calendario_laboral", "libre_disposicion_por_vencer"]
    assert ev[0]["clave"] == "cal:cts:2026-11-16" and ev[1]["clave"] == "libre:2026-12-31:60"


def test_la_gratificacion_a_31_dias_todavia_no_avisa_y_a_5_dias_si():
    assert not any(e["tipo"] == "calendario_laboral" and e["evento"]["tipo"] == "gratificacion" for e in V.detectar_calendario(ctx("2026-11-14")))
    ev = [e for e in V.detectar_calendario(ctx("2026-12-10")) if e["tipo"] == "calendario_laboral"]
    assert [e["evento"]["tipo"] for e in ev] == ["gratificacion"] and ev[0]["evento"]["dias_para"] == 5


def test_el_aviso_de_vencimiento_se_repite_solo_por_tramos_no_todos_los_dias():
    assert V.detectar_calendario(ctx("2026-11-14"))[-1]["clave"].endswith(":60")
    assert V.detectar_calendario(ctx("2026-11-20"))[-1]["clave"].endswith(":60")   # misma clave: no se avisa de nuevo
    assert V.detectar_calendario(ctx("2026-12-20"))[-1]["clave"].endswith(":15")


def test_pasado_el_vencimiento_no_se_avisa_nada_de_libre_disposicion():
    assert "libre_disposicion_por_vencer" not in tipos(V.detectar_calendario(ctx("2027-01-05")))


def test_el_independiente_no_recibe_avisos_de_cts_ni_gratificacion():
    assert V.detectar_calendario(ctx("2026-11-14", tipo="independiente")) == []


# ---------------------------------------------------------------- ingresos y gastos que entran
@pytest.mark.parametrize("mov,esperado", [
    ({"tipo": "ingreso", "categoria": "gratificacion", "monto": 1500.0}, True),
    ({"tipo": "ingreso", "categoria": "retiro_afp", "monto": 6000.0}, True),
    ({"tipo": "ingreso", "categoria": "gratificacion", "monto": 900.0}, False),     # pesa menos de la mitad de un ingreso mensual
    ({"tipo": "ingreso", "categoria": "otros", "monto": 9000.0}, False),            # sin categoria clara no se inventa un ingreso extraordinario
    ({"tipo": "ingreso", "categoria": "sueldo", "monto": 3000.0}, False),           # el sueldo normal no es un ingreso extra
    ({"tipo": "gasto", "categoria": "gratificacion", "monto": 5000.0}, False),      # un gasto nunca es ingreso
])
def test_ingreso_extra_solo_con_categoria_extraordinaria_y_monto_relevante(mov, esperado):
    assert bool(V.detectar_ingreso_extra([mov], 2000.0)) is esperado


@pytest.mark.parametrize("mov,esperado", [
    ({"tipo": "gasto", "categoria": "compras", "monto": 1000.0, "id": "a"}, True),     # 33 % del ingreso
    ({"tipo": "gasto", "categoria": "compras", "monto": 900.0, "id": "a"}, True),      # exactamente 30 %
    ({"tipo": "gasto", "categoria": "compras", "monto": 899.0, "id": "a"}, False),
    ({"tipo": "gasto", "categoria": "alquiler", "monto": 2000.0, "id": "a"}, False),   # pago recurrente esperado
    ({"tipo": "gasto", "categoria": "cuota_prestamo", "monto": 1500.0, "id": "a"}, False),
    ({"tipo": "ingreso", "categoria": "compras", "monto": 5000.0, "id": "a"}, False),
])
def test_gasto_atipico_pesa_mucho_y_no_es_recurrente(mov, esperado):
    assert bool(V.detectar_gasto_atipico([mov], 3000.0)) is esperado


def test_el_gasto_atipico_lleva_la_clave_del_movimiento_para_no_repetirse():
    e = V.detectar_gasto_atipico([{"tipo": "gasto", "categoria": "compras", "monto": 1200.0, "id": "m7"}], 3000.0)[0]
    assert e["clave"] == "mov:m7" and e["fraccion_del_ingreso"] == 0.4


# ---------------------------------------------------------------- gratificacion que no llego
def _registrar_en(hoy: str, **kw):
    reloj.fijar(hoy)
    return DV.registrar(CID, **kw)


def test_avisa_si_la_gratificacion_no_llego_pasada_la_tolerancia():
    reloj.fijar("2026-12-20")
    e = V.detectar_atraso_gratificacion(ctx("2026-12-20", vivos_n=1, desfase=400), date(2026, 12, 20))
    assert e and e["tipo"] == "gratificacion_pendiente" and e["clave"] == "pend:2026-12-15"


def test_no_avisa_si_la_gratificacion_si_llego():
    _registrar_en("2026-12-20", tipo="ingreso", monto=3000, categoria="gratificacion", fecha="2026-12-14", id_mov="g")
    assert V.detectar_atraso_gratificacion(ctx("2026-12-20", vivos_n=1, desfase=400), date(2026, 12, 20)) is None


def test_no_avisa_dentro_de_la_tolerancia():
    reloj.fijar("2026-12-17")   # dos dias despues del 15: la tolerancia es de 3
    assert V.detectar_atraso_gratificacion(ctx("2026-12-17", vivos_n=1, desfase=400), date(2026, 12, 17)) is None


def test_no_avisa_a_quien_nunca_recibio_una_gratificacion():
    reloj.fijar("2026-12-20")
    assert V.detectar_atraso_gratificacion(ctx("2026-12-20", origen="ingreso_medio", vivos_n=1, desfase=400), date(2026, 12, 20)) is None


def test_no_afirma_que_algo_no_llego_si_no_hay_informacion_reciente():
    reloj.fijar("2026-12-20")
    assert V.detectar_atraso_gratificacion(ctx("2026-12-20", vivos_n=0, desfase=400), date(2026, 12, 20)) is None
    assert V.detectar_atraso_gratificacion(ctx("2026-12-20", vivos_n=0, desfase=10), date(2026, 12, 20)) is not None


# ---------------------------------------------------------------- tasa de referencia en vivo
def _tasa(variacion, al_dia, origen="api"):
    return {"valor": 4.0, "valor_previo": 4.0 - variacion, "variacion": variacion, "fecha": "2026-10-01", "origen": origen, "al_dia": al_dia}


@pytest.mark.parametrize("variacion,al_dia,aviso", [(-0.25, True, True), (-0.10, True, True), (-0.05, True, False), (0.25, True, False), (-0.25, False, False)])
def test_baja_de_tasa_solo_si_es_real_reciente_y_el_dato_esta_al_dia(monkeypatch, variacion, al_dia, aviso):
    monkeypatch.setattr(V, "ultimo_con_variacion", lambda n: _tasa(variacion, al_dia))
    assert bool(V.detectar_baja_de_tasa()) is aviso


# ---------------------------------------------------------------- orden, filtro por perfil, deduplicacion y tope
def test_el_riesgo_de_rojo_va_primero_y_el_nino_solo_aplica_en_zona_expuesta():
    glob = [{"tipo": "fen_comunicado", "numero": 21, "clave": "fen:21"}]
    cusco = V.eventos_para(ctx(p_rojo=0.5, dep="Cusco"), glob, hoy=date(2026, 11, 14))     # sierra sur oriental: exposicion baja segun el ENFEN
    lima = V.eventos_para(ctx(p_rojo=0.5, dep="Lima"), glob, hoy=date(2026, 11, 14))       # exposicion media (cuencas Chillon, Rimac y Lurin)
    piura = V.eventos_para(ctx(p_rojo=0.5, dep="Piura"), glob, hoy=date(2026, 11, 14))     # exposicion alta
    assert tipos(cusco)[0] == "riesgo_rojo" and "fen_comunicado" not in tipos(cusco)
    for expuesto in (lima, piura):
        assert tipos(expuesto)[0] == "riesgo_rojo" and tipos(expuesto)[-1] == "fen_comunicado"


class _App:
    pass


@pytest.fixture
def respuesta_falsa(monkeypatch):
    llamadas = []

    def falso(app, cid, pregunta, evento):
        llamadas.append(evento["tipo"])
        return {"respuesta": "aviso", "proveedor": "plantilla", "cifras_verificadas": 0, "llamadas_llm": 0}
    monkeypatch.setattr(V, "responder", falso)
    return llamadas


def _eventos(n):
    return [{"tipo": "gasto_atipico", "monto": 100.0 + i, "categoria": "compras", "fraccion_del_ingreso": 0.3, "clave": f"mov:{i}"} for i in range(n)]


def test_maximo_tres_avisos_por_semana_y_el_resto_espera(respuesta_falsa):
    ahora = datetime(2026, 11, 14, 10)
    assert len(V.avisar(_App(), None, CID, _eventos(5), ahora)) == 3
    assert len(V.avisar(_App(), None, CID, _eventos(5), ahora + timedelta(days=1))) == 0       # mismo tope, los 3 primeros ya se avisaron
    sig = V.avisar(_App(), None, CID, _eventos(5), ahora + timedelta(days=8))
    assert [a["evento"]["clave"] for a in sig] == ["mov:3", "mov:4"]                           # la semana siguiente sale solo lo pendiente


def test_un_hecho_ya_avisado_no_se_repite_aunque_el_vigilante_corra_muchas_veces(respuesta_falsa):
    ahora = datetime(2026, 11, 14, 10)
    for k in range(4):
        V.avisar(_App(), None, CID, _eventos(1), ahora + timedelta(days=9 * k))
    assert len(respuesta_falsa) == 1


def test_un_evento_sin_clave_se_avisa_sin_romper(respuesta_falsa):
    assert len(V.avisar(_App(), None, CID, [{"tipo": "riesgo_rojo", "p_rojo": 0.5, "dia_riesgo": None}], datetime(2026, 11, 14, 10))) == 1
