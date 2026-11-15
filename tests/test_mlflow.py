"""Seguimiento con MLflow: una corrida por candidato de cada comparacion (con un unico elegido por problema), los modelos de produccion registrados y el registro sin duplicados."""
import importlib.util
import os

import pytest

from src.comun.rutas import MODELOS

mlflow = pytest.importorskip("mlflow")
pytestmark = pytest.mark.skipif(not os.path.isfile(os.path.join(MODELOS, "metricas_serie_diaria.json")), reason="faltan las metricas (python eval/entrenar_serie_diaria.py)")


def _modulo():
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "eval", "registrar_en_mlflow.py")
    spec = importlib.util.spec_from_file_location("registrar_en_mlflow", ruta)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def registro(tmp_path_factory):
    d = tmp_path_factory.mktemp("mlflow")
    m = _modulo()
    uri = "sqlite:///" + str(d / "lucas.db").replace(os.sep, "/")
    r1 = m.registrar(uri=uri, artefactos=str(d / "artifacts"), con_pickles=False, resumen=str(d / "resumen.md"))
    r2 = m.registrar(uri=uri, artefactos=str(d / "artifacts"), con_pickles=False, resumen=str(d / "resumen.md"))
    return m, uri, r1, r2, d


def test_hay_una_corrida_por_candidato_y_un_unico_elegido_por_problema(registro):
    m, uri, r1, _, _ = registro
    cm = m._comparativa()
    problemas = cm.problemas()
    c = mlflow.tracking.MlflowClient(tracking_uri=uri)
    runs = c.search_runs([r1["experimento"]], filter_string="tags.tipo = 'comparacion'", max_results=1000)
    assert len(runs) == sum(len(p["candidatos"]) for p in problemas) and r1["problemas"] == len(problemas) == 14
    for p in problemas:
        de_p = [r for r in runs if r.data.params["problema"] == p["slug"]]
        elegidos = [r for r in de_p if r.data.tags["rol"] == "elegido"]
        assert len(elegidos) == 1 and elegidos[0].data.params["candidato"] == p["candidatos"][p["elegido"]][0]
        assert elegidos[0].data.metrics["valor"] == pytest.approx(p["candidatos"][p["elegido"]][1])


def test_los_modelos_de_produccion_llevan_hiperparametros_metricas_y_version_del_codigo(registro):
    m, uri, r1, _, _ = registro
    c = mlflow.tracking.MlflowClient(tracking_uri=uri)
    runs = c.search_runs([r1["experimento"]], filter_string="tags.tipo = 'modelo_de_produccion'", max_results=100)
    nombres = {r.data.tags["modelo"] for r in runs}
    assert {"lucas-pronostico-30d", "lucas-serie-diaria", "lucas-segmentacion", "lucas-pronostico-mensual"} <= nombres
    pron = next(r for r in runs if r.data.tags["modelo"] == "lucas-pronostico-30d")
    assert any(k.startswith("lgbm_") for k in pron.data.params) and "saldo_30d.cobertura_80" in pron.data.metrics
    assert pron.data.tags["commit"] and pron.data.tags["huella_metricas"] and pron.data.tags["datos"] == "sinteticos"


def test_volver_a_registrar_con_las_mismas_metricas_no_duplica_nada(registro):
    m, uri, r1, r2, _ = registro
    c = mlflow.tracking.MlflowClient(tracking_uri=uri)
    runs = c.search_runs([r1["experimento"]], filter_string="tags.origen = 'registrar_en_mlflow'", max_results=1000)
    assert len(runs) == r1["corridas_de_comparacion"] + r1["modelos_de_produccion"] and r2["huella_metricas"] == r1["huella_metricas"]


def test_el_resumen_trae_la_huella_para_detectar_si_esta_desfasado(registro):
    m, _, r1, _, d = registro
    texto = (d / "resumen.md").read_text(encoding="utf-8")
    assert f"huella_metricas: {r1['huella_metricas']}" in texto and "Comparacion por problema" in texto and "Model Registry" in texto
