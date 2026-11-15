"""Serie diaria del pronostico: interpolacion, orden de la banda, coincidencia con el modelo de 30 dias, forma del contrato y metricas guardadas."""
import json
import os
from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from src.comun.rutas import DATA_GENERADO, MODELOS
from src.models import serie_diaria as SD

HAY_MODELOS = os.path.isfile(os.path.join(MODELOS, "serie_diaria.pkl")) and os.path.isdir(os.path.join(DATA_GENERADO, "saldo_diario"))
requiere_modelos = pytest.mark.skipif(not HAY_MODELOS, reason="faltan los datos o la serie diaria (python analitica/eval/entrenar_serie_diaria.py)")


class _Const:
    """Cuantil de juguete: devuelve el mismo valor para todas las filas."""
    def __init__(self, v):
        self.v = v

    def predict(self, X):
        return np.full(len(X), self.v)


def _serie_de_juguete(alto_en_30=3.0):
    """Un modelo cuyos cuantiles crecen de forma lineal con el horizonte: permite comprobar la interpolacion a mano."""
    s = SD.SerieDiaria(modelo30=None, features=["x"], params={})
    s.modelos = {h: {0.1: _Const(-0.1 * h), 0.5: _Const(0.05 * h), 0.9: _Const(0.2 * h)} for h in SD.ANCLAS}
    s.modelo30 = type("M30", (), {"modelos": {0.1: _Const(-3.0), 0.5: _Const(1.5), 0.9: _Const(alto_en_30 * 2)}})()
    return s


def test_interpolacion_lineal_pasa_por_los_nodos_y_parte_de_cero():
    s = _serie_de_juguete()
    lo, mid, hi = s._interpolar(pd.DataFrame({"x": [0.0, 1.0]}))
    assert lo.shape == (2, SD.H + 1)
    assert np.allclose(lo[:, 0], 0) and np.allclose(mid[:, 0], 0) and np.allclose(hi[:, 0], 0)   # el dia 0 es el saldo de hoy: sin incertidumbre
    assert np.allclose(mid[:, 10], 0.5) and np.allclose(mid[:, 7], 0.05 * 5 + (0.05 * 10 - 0.05 * 5) * 2 / 5)   # entre los nodos 5 y 10
    assert np.allclose(mid[:, SD.H], 1.5)


def test_los_cuantiles_cruzados_se_ordenan_por_fila():
    s = SD.SerieDiaria(modelo30=None, features=["x"], params={})
    s.modelos = {h: {0.1: _Const(1.0), 0.5: _Const(0.0), 0.9: _Const(-1.0)} for h in SD.ANCLAS}   # al reves a proposito
    s.modelo30 = type("M30", (), {"modelos": {0.1: _Const(1.0), 0.5: _Const(0.0), 0.9: _Const(-1.0)}})()
    lo, mid, hi = s._interpolar(pd.DataFrame({"x": [0.0]}))
    assert (lo <= mid + 1e-12).all() and (mid <= hi + 1e-12).all()


def test_conformal_es_el_cuantil_finito():
    s = SD.SerieDiaria(modelo30=None, features=["x"], params={}, alfa=0.2)
    e = np.arange(1, 101, dtype=float)
    assert s._conformal(e) == pytest.approx(np.quantile(e, np.ceil(101 * 0.8) / 100))


def test_metricas_por_dia_banda_perfecta_cubre_todo():
    n = 50
    esc, base = np.full(n, 100.0), np.full(n, 1000.0)
    df = pd.DataFrame({"escala": esc, "saldo_t": base, **{SD.objetivo(d): np.full(n, 0.01 * d) for d in range(1, SD.H + 1)}})
    y = np.stack([base + 0.01 * d * esc for d in range(1, SD.H + 1)], axis=1)
    t = SD.metricas_por_dia(df, {"esperado": y, "bajo": y - 1, "alto": y + 1})
    assert len(t) == SD.H and (t["cobertura_80"] == 1.0).all() and (t["mae_rel_ingreso"] < 1e-9).all()


# ---------------------------------------------------------------------------- integracion con los modelos entrenados
@pytest.fixture(scope="module")
def cliente(repo_y_buscador):
    repo, _ = repo_y_buscador
    return repo, repo.clientes.index[3]


@requiere_modelos
def test_contrato_tiene_la_forma_pedida_y_30_dias_seguidos(cliente):
    from src.agente_analitico.contrato import pronostico_contrato
    repo, cid = cliente
    r = pronostico_contrato(repo, cid, hoy=repo.fecha.date())
    assert {"customer_id", "currency", "horizon_days", "confidence_level", "forecast", "first_risk_date", "model"} <= set(r)
    assert r["currency"] == "PEN" and r["horizon_days"] == 30 and r["confidence_level"] == 0.8 and r["sample_only"] is False and r["synthetic_data"] is True
    f = r["forecast"]
    assert len(f) == 30
    fechas = [date.fromisoformat(x["date"]) for x in f]
    assert fechas[0] == repo.fecha.date() + timedelta(days=1) and all((b - a).days == 1 for a, b in zip(fechas, fechas[1:]))
    assert all(x["lower_bound"] <= x["predicted_balance"] <= x["upper_bound"] for x in f)


@requiere_modelos
def test_el_dia_30_es_el_pronostico_validado(cliente):
    from src.agente_analitico.contrato import pronostico_contrato
    repo, cid = cliente
    r = pronostico_contrato(repo, cid, hoy=repo.fecha.date())
    fila = repo.origen[repo.origen["cliente_idx"] == repo.pos[cid]].index[0]
    p = repo._pronostico(fila)
    ultimo = r["forecast"][-1]
    assert ultimo["predicted_balance"] == pytest.approx(p["saldo_esperado"], abs=0.01)
    assert ultimo["lower_bound"] <= p["saldo_bajo"] + 0.01 and ultimo["upper_bound"] >= p["saldo_alto"] - 0.01   # la banda solo puede ensancharse, nunca estrecharse


@requiere_modelos
def test_horizonte_menor_devuelve_solo_esos_dias_y_horizonte_invalido_falla(cliente):
    from src.agente_analitico.contrato import HorizonteInvalido, pronostico_contrato
    repo, cid = cliente
    r = pronostico_contrato(repo, cid, dias=10, hoy=repo.fecha.date())
    assert r["horizon_days"] == 10 and len(r["forecast"]) == 10
    for malo in (0, 31, -1, 2.5, "30", True):
        with pytest.raises(HorizonteInvalido):
            pronostico_contrato(repo, cid, dias=malo, hoy=repo.fecha.date())


@requiere_modelos
def test_primer_dia_de_riesgo_solo_si_la_probabilidad_pasa_el_umbral(cliente):
    from src.agente_analitico.contrato import UMBRAL_RIESGO, pronostico_contrato
    repo, _ = cliente
    vistos = {"con": 0, "sin": 0}
    for cid in list(repo.clientes.index[:60]):
        r = pronostico_contrato(repo, cid, hoy=repo.fecha.date())
        if r["first_risk_date"] is None:
            vistos["sin"] += 1
        else:
            vistos["con"] += 1
            assert r["risk_probability"] >= UMBRAL_RIESGO
            d = date.fromisoformat(r["first_risk_date"])
            assert repo.fecha.date() < d <= repo.fecha.date() + timedelta(days=30)
    assert vistos["sin"] > 0   # no todos los clientes estan en riesgo


@requiere_modelos
def test_un_gasto_vivo_baja_el_saldo_de_partida(cliente):
    repo, cid = cliente
    a = repo.serie_diaria(cid, 0.0)
    b = repo.serie_diaria(cid, -500.0)
    assert b["saldo_inicial"] == pytest.approx(a["saldo_inicial"] - 500.0)
    assert b["esperado"][0] < a["esperado"][0]


@requiere_modelos
def test_metricas_guardadas_cubren_cerca_del_80_en_cada_dia_y_ganan_a_las_dos_lineas_base():
    with open(os.path.join(MODELOS, "metricas_serie_diaria.json"), encoding="utf-8") as f:
        m = json.load(f)
    dias = m["por_dia"]["serie_diaria"]
    assert len(dias) == 30
    assert all(0.75 <= d["cobertura_80"] <= 0.86 for d in dias), "la cobertura de la banda debe medirse y mantenerse cerca del 80 % en TODOS los dias"
    assert m["serie_diaria"]["mae_rel_medio"] < m["linea_base_recta_al_dia_30"]["mae_rel_medio"] < m["linea_base_promedio_movil_3_meses"]["mae_rel_medio"]
    assert m["ultimo_punto_coincide_con_el_modelo_de_30_dias"]["esperado_identico"] and m["ultimo_punto_coincide_con_el_modelo_de_30_dias"]["banda_nunca_se_estrecha"]
