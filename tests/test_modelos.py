import numpy as np
import pandas as pd
import pytest

from src.agent import memoria
from src.agent.verificador import aplanar, numeros_de, verificar
from src.models import niveles as N
from src.models import recomendador as R
from src.models import riesgo_clima as RC
from src.models import salud as SA


def _fila(**kw):
    base = dict(ingreso_medio=2000.0, cv_ingreso=0.2, fijo_sobre_ingreso=0.4, cuota_sobre_ingreso=0.1, gasto_sobre_ingreso=0.8, pct_hormiga=0.05, ahorro_pct=0.1, dias_rojo_3m=0.0,
                n_suscripciones=1.0, pct_billetera=0.4, volatilidad_gasto=0.1, colchon_observado=2.0, tipo_trabajo="dependiente")
    base.update(kw)
    return pd.DataFrame([base])


# ---------------------------------------------------------------- salud financiera
@pytest.mark.parametrize("col,sube", [("colchon_observado", True), ("ahorro_pct", True), ("cuota_sobre_ingreso", False), ("dias_rojo_3m", False), ("cv_ingreso", False)])
@pytest.mark.parametrize("tipo", ["dependiente", "independiente"])
def test_salud_es_monotona(col, sube, tipo):
    valores = np.linspace(0, {"colchon_observado": 8, "ahorro_pct": 0.4, "cuota_sobre_ingreso": 0.8, "dias_rojo_3m": 30, "cv_ingreso": 1.5}[col], 25)
    t = pd.concat([_fila(tipo_trabajo=tipo)] * len(valores), ignore_index=True)
    t[col] = valores
    d = np.diff(SA.puntaje_salud(t).to_numpy())
    assert np.all(d >= -1e-9) if sube else np.all(d <= 1e-9)


def test_salud_esta_entre_0_y_100_y_pesos_suman_uno():
    for fam, pesos in SA.PESOS.items():
        assert abs(sum(pesos.values()) - 1) < 1e-9, fam
    extremos = pd.concat([_fila(colchon_observado=0, ahorro_pct=0, cuota_sobre_ingreso=1, dias_rojo_3m=90, cv_ingreso=3, fijo_sobre_ingreso=1.0), _fila(colchon_observado=20, ahorro_pct=1, cuota_sobre_ingreso=0, dias_rojo_3m=0, cv_ingreso=0, fijo_sobre_ingreso=0.1)])
    s = SA.puntaje_salud(extremos)
    assert s.between(0, 100).all() and s.iloc[0] < 5 and s.iloc[1] > 95


def test_al_independiente_se_le_pide_mas_colchon():
    dep = SA.componentes(_fila(colchon_observado=3.0, tipo_trabajo="dependiente")).iloc[0]["colchon"]
    ind = SA.componentes(_fila(colchon_observado=3.0, tipo_trabajo="independiente")).iloc[0]["colchon"]
    assert dep == 100 and ind < 100


# ---------------------------------------------------------------- niveles y puntos
def test_puntos_se_multiplican_por_nivel():
    assert N.puntos_por("aporte_a_meta_de_ahorro", "luchador")["puntos"] == 150
    assert N.puntos_por("aporte_a_meta_de_ahorro", "campeon")["puntos"] == 100
    assert N.puntos_por("quincena_sin_dias_en_rojo", "aprendiz", veces=2)["puntos"] == 130


def test_canjes_solo_con_puntos_suficientes():
    assert N.canjes_disponibles(100) == []
    assert {c["id"] for c in N.canjes_disponibles(500)} >= {"descuento_mantenimiento", "asesoria_educativa"}


def test_escalera_de_nombres_va_de_menor_a_mayor_salud():
    f = pd.concat([_fila(colchon_observado=0.2, dias_rojo_3m=20, ahorro_pct=0), _fila(colchon_observado=1.5), _fila(colchon_observado=3.5, ahorro_pct=0.15), _fila(colchon_observado=6, ahorro_pct=0.25, cuota_sobre_ingreso=0.02)], ignore_index=True)
    nombres = N.nombres_por_segmento(f, np.array([0, 1, 2, 3]))
    esc = N._cfg()["escalera"]
    assert [esc.index(nombres[i]) for i in range(4)] == sorted(esc.index(nombres[i]) for i in range(4))
    assert len(set(nombres.values())) == 4


def test_progreso_indica_lo_que_falta_para_subir():
    p = N.progreso("luchador", pd.Series({"dias_rojo_3m": 10, "colchon_observado": 0.3, "ahorro_pct": 0.0}), 30.0)
    assert p["siguiente"] == "aprendiz" and not p["cumple"] and p["faltantes"]
    assert N.progreso("campeon", pd.Series({"dias_rojo_3m": 0}), 95)["siguiente"] is None


# ---------------------------------------------------------------- reglas de seguridad del recomendador (valores limite)
def _feat(**kw):
    return _fila(**kw).iloc[0].to_dict()


@pytest.mark.parametrize("colchon,esperado", [(0.99, False), (1.00, True), (1.01, True)])
def test_credito_exige_colchon_de_un_mes(colchon, esperado):
    ok, _ = R.idoneo_para_credito(_feat(colchon_observado=colchon), p_rojo=0.0)
    assert ok is esperado


@pytest.mark.parametrize("cuota,esperado", [(0.29, True), (0.30, True), (0.31, False)])
def test_credito_limita_las_cuotas_al_30_por_ciento(cuota, esperado):
    ok, _ = R.idoneo_para_credito(_feat(colchon_observado=2.0, cuota_sobre_ingreso=cuota), p_rojo=0.0)
    assert ok is esperado


def test_credito_se_bloquea_con_dias_en_rojo_o_riesgo_alto():
    assert not R.idoneo_para_credito(_feat(dias_rojo_3m=2), 0.0)[0]
    assert not R.idoneo_para_credito(_feat(), 0.31)[0]


def _ctx(**kw):
    c = {"features": _feat(), "pronostico": {"p_rojo": 0.0, "ancho_rel": 1.0, "saldo_esperado": 500.0, "saldo_bajo": 100.0, "saldo_alto": 900.0, "dia_riesgo": None}, "nivel": "aprendiz", "salud": 60.0,
         "departamento": "Lima", "tipo_trabajo": "dependiente", "tcea": 0.0, "deuda": 0.0, "hoy": "2026-11-14", "memoria": {"respuestas_reco": {}}, "paga_en_usd": False}
    c.update(kw)
    return c


def test_nunca_se_ofrece_credito_a_quien_no_pasa_la_idoneidad():
    c = _ctx(features=_feat(colchon_observado=0.3, dias_rojo_3m=8, cuota_sobre_ingreso=0.35, tipo_trabajo="independiente"), tipo_trabajo="independiente", departamento="Piura",
             pronostico={"p_rojo": 0.5, "ancho_rel": 1.5, "saldo_esperado": -100.0, "saldo_bajo": -500.0, "saldo_alto": 200.0, "dia_riesgo": 12.0})
    recs = R.candidatos(c)
    for r in recs:
        if r.get("familia") in ("credito", "tarjeta") or r["id"] == "oferta_mejora_vivienda":
            assert r.get("idoneo") is False or r["id"] == "ordenar_deuda_cara", r["id"]
            assert r["accion"].startswith("Aun no") or r["id"] == "ordenar_deuda_cara"
    assert "oferta_mejora_vivienda" not in {r["id"] for r in R.recomendar(c, 10)}


def test_toda_recomendacion_deja_la_decision_al_usuario_y_trae_su_fundamento():
    c = _ctx(features=_feat(cv_ingreso=0.6, colchon_observado=0.5, pct_hormiga=0.1), duplicadas=True, tipo_trabajo="independiente")
    for r in R.recomendar(c, 6):
        assert r["tu_decides"] is True and r["por_que"] and r["supuestos"] and r["confianza"] in ("alta", "media", "baja")


def test_la_recomendacion_rechazada_no_vuelve_a_aparecer():
    c = _ctx(features=_feat(pct_hormiga=0.12))
    assert "reducir_gasto_hormiga" in {r["id"] for r in R.recomendar(c, 10)}
    c["memoria"] = {"respuestas_reco": {"reducir_gasto_hormiga": "no_me_sirve"}}
    assert "reducir_gasto_hormiga" not in {r["id"] for r in R.recomendar(c, 10)}


def test_el_aviso_de_el_nino_solo_aparece_en_zona_expuesta():
    assert "prevencion_fen" in {r["id"] for r in R.candidatos(_ctx(departamento="Piura"))}
    assert "prevencion_fen" not in {r["id"] for r in R.candidatos(_ctx(departamento="Cusco"))}


def test_cuota_mensual_es_coherente():
    assert R.cuota_mensual(1200, 0.0, 12) == pytest.approx(100.0)
    c = R.cuota_mensual(4000, 0.25, 18)
    assert 4000 / 18 < c < 4000 / 18 * 1.3


# ---------------------------------------------------------------- riesgo climatico
def test_exposicion_fen_por_departamento():
    assert RC.exposicion_fen("Piura")["nivel"] == "alta" and RC.exposicion_fen("Lima")["nivel"] == "media" and RC.exposicion_fen("Ica")["nivel"] == "media" and RC.exposicion_fen("Cusco")["nivel"] == "baja"
    assert RC.alerta_fen("Piura", "2026-11-14")["acciones"]
    assert RC.alerta_fen("Piura", "2027-08-15") is None and RC.alerta_fen("Cusco", "2026-11-14") is None


# ---------------------------------------------------------------- verificador (pruebas adversas)
def test_el_verificador_acepta_cifras_con_respaldo_y_rechaza_inventadas():
    datos = {"saldo": 1234.5, "p_rojo": 0.28}
    ok = verificar("Tu saldo esperado es S/ 1,235 y hay un 28 % de probabilidad de rojo.", aplanar(datos))
    assert ok["ok"] and ok["cifras_verificadas"] == 2
    mal = verificar("Tu saldo esperado es S/ 9,999.", aplanar(datos))
    assert not mal["ok"] and mal["cifras_sin_respaldo"] == [9999.0]


@pytest.mark.parametrize("texto", ["Te recomiendo comprar dolares hoy.", "Con esto tienes rentabilidad asegurada.", "Invierte en BitX ahora.", "Te garantizo que ganas.", "Yo te transferire la plata."])
def test_el_verificador_bloquea_promesas_y_operaciones(texto):
    assert not verificar(texto, set())["ok"]


def test_lectura_de_numeros_con_formatos_distintos():
    assert numeros_de("S/ 1,234.50 y 1.234,50 y 45%") == [1234.5, 1234.5, 45.0]


# ---------------------------------------------------------------- memoria del usuario
def test_la_memoria_se_puede_ver_y_borrar(tmp_path, monkeypatch):
    monkeypatch.setattr(memoria, "CARPETA", str(tmp_path))
    memoria.registrar_respuesta("C1", "meta_colchon", "util")
    memoria.sumar_puntos("C1", "aporte_a_meta_de_ahorro", 150)
    m = memoria.cargar("C1")
    assert m["respuestas_reco"]["meta_colchon"] == "util" and m["puntos"] == 150
    assert memoria.olvidar("C1") is True and memoria.cargar("C1")["puntos"] == 0 and memoria.olvidar("C1") is False


def test_maximo_tres_avisos_por_semana(tmp_path, monkeypatch):
    from datetime import datetime, timedelta
    monkeypatch.setattr(memoria, "CARPETA", str(tmp_path))
    hoy = datetime(2026, 11, 14, 10, 0)
    for i in range(3):
        assert memoria.puede_avisar("C2", hoy)
        memoria.registrar_aviso("C2", "riesgo_rojo", hoy)
    assert not memoria.puede_avisar("C2", hoy)
    assert memoria.puede_avisar("C2", hoy + timedelta(days=8))


def test_el_nivel_individual_respeta_la_salud():
    assert N.nivel_individual("campeon", 90) == "campeon"
    assert N.nivel_individual("campeon", 72) == "maestro"
    assert N.nivel_individual("campeon", 60) == "constructor"
    assert N.nivel_individual("campeon", 45) == "aprendiz"
    assert N.nivel_individual("campeon", 20) == "luchador"
    assert N.nivel_individual("luchador", 95) == "luchador"
    assert N.nivel_individual("constructor", 90) == "constructor"
