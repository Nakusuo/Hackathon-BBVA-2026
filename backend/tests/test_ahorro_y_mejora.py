"""Los porcentajes y los soles de los graficos de ahorro y de mejora salen de funciones puras: aqui se comprueba que las cuentas cuadran (nada escrito a mano que se pueda desalinear)."""
import importlib.util
import os

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _modulo(nombre: str, archivo: str):
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(RAIZ, "analitica", "eval", archivo))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mapa():
    return _modulo("mapa_de_consultas_t", "mapa_de_consultas.py")


@pytest.fixture(scope="module")
def comparativa():
    return _modulo("comparativa_modelos_t", "comparativa_modelos.py")


MEZCLA = {"preguntas": 40, "van_a_la_ia": 8, "plantilla_fija": 10, "herramientas_y_plantilla": 22, "proporcion_ia": 0.2}


def test_los_tokens_de_una_llamada_se_reparten_en_mensaje_lectura_y_respuesta(mapa):
    K = mapa._costos(entrada=2600, salida=200, lectura=400, corpus=600_000, parrafo_n=7, parrafo_ia=1, mezcla=MEZCLA)
    t = K["por_llamada"]["tokens"]
    assert t == {"mensaje": 2200, "lectura_de_fuentes": 400, "respuesta": 200}
    assert sum(K["por_llamada"]["pct_de_los_tokens"].values()) == pytest.approx(1.0)
    assert sum(K["por_llamada"]["pct_del_costo"].values()) == pytest.approx(1.0)


def test_la_salida_cuesta_mas_por_token_que_la_entrada(mapa):
    K = mapa._costos(2600, 200, 400, 600_000, 7, 1, MEZCLA)["por_llamada"]
    assert K["pct_del_costo"]["respuesta"] > K["pct_de_los_tokens"]["respuesta"]   # 2.50 frente a 0.30 USD por millon


def test_el_costo_de_una_llamada_es_precio_por_tokens_por_tipo_de_cambio(mapa):
    K = mapa._costos(2600, 200, 400, 600_000, 7, 1, MEZCLA)
    tc = K["tipo_de_cambio"]["valor"]
    esperado = ((2600 * mapa.PRECIO["usd_por_millon_de_entrada"] + 200 * mapa.PRECIO["usd_por_millon_de_salida"]) / 1e6) * tc
    assert K["por_llamada"]["soles"]["total"] == pytest.approx(esperado)


def test_el_ahorro_por_ruteo_es_uno_menos_la_parte_que_llega_a_la_ia(mapa):
    K = mapa._costos(2600, 200, 400, 600_000, 7, 1, MEZCLA)
    assert K["parrafo_de_ejemplo"]["ahorro_pct"] == pytest.approx(1 - 1 / 7)
    assert K["mezcla_de_evaluacion"]["ahorro_pct"] == pytest.approx(0.8)
    e = K["mezcla_de_evaluacion"]
    assert e["con_ruteo_soles"] == pytest.approx(e["sin_ruteo_soles"] * 0.2) and e["ahorro_soles"] == pytest.approx(e["sin_ruteo_soles"] - e["con_ruteo_soles"])


def test_leer_solo_tres_fragmentos_en_vez_de_todo_el_corpus_reduce_casi_todo(mapa):
    L = mapa._costos(2600, 200, 400, 600_000, 7, 1, MEZCLA)["lectura_del_corpus"]
    assert L["reduccion_pct"] == pytest.approx(1 - 400 / 600_000)
    assert 0 < L["soles_por_consulta_con_rag"] < L["soles_por_consulta_leyendo_todo"] and 0.9 < L["ahorro_pct"] < 1


def test_el_tipo_de_cambio_trae_valor_fecha_y_fuente(mapa):
    tc = mapa._tipo_de_cambio()
    assert 2.5 < tc["valor"] < 5.0 and tc["fecha"] and tc["fuente"]


def _problema(mejor, candidatos, elegido=0):
    return {"titulo": "p", "metrica": "m", "mejor": mejor, "candidatos": candidatos, "elegido": elegido}


def test_la_mejora_se_mide_frente_al_rival_mas_fuerte_y_al_mas_debil(comparativa):
    P = [_problema("menor", [("elegido", 0.6), ("fuerte", 1.0), ("debil", 2.0)]), _problema("mayor", [("elegido", 0.9), ("fuerte", 0.8), ("debil", 0.3)])]
    M = {r["metrica"] + str(i): r for i, r in enumerate(comparativa.mejora_porcentual(P))}
    menor = next(r for r in comparativa.mejora_porcentual(P) if r["rival_mas_fuerte"] == "fuerte" and r["mejora_vs_mas_fuerte"] == pytest.approx(0.4))
    assert menor["mejora_vs_mas_debil"] == pytest.approx(0.7) and menor["rival_mas_debil"] == "debil"   # error 0.6 frente a 1.0 es 40 % menos; frente a 2.0, 70 %
    mayor = next(r for r in comparativa.mejora_porcentual(P) if r["mejora_vs_mas_fuerte"] == pytest.approx(0.125))
    assert mayor["mejora_vs_mas_debil"] == pytest.approx(2.0) and len(M) == 2   # 0.9 frente a 0.8 es 12.5 % mas; frente a 0.3, 200 %


def test_un_empate_se_reporta_como_cero_y_lo_que_se_mide_contra_un_objetivo_no_entra(comparativa):
    P = [_problema("menor", [("elegido", 1.0), ("igual", 1.0)]), _problema("objetivo", [("a", 0.8), ("b", 0.7)])]
    M = comparativa.mejora_porcentual(P)
    assert len(M) == 1 and M[0]["mejora_vs_mas_fuerte"] == pytest.approx(0.0)
