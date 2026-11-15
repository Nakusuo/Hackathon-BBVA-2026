"""Calendario laboral: fechas, montos, regla de retiro de la CTS y, sobre todo, que cada regla tenga respaldo literal en el documento oficial del RAG."""
import os
import re
import unicodedata
from datetime import date, timedelta

import pytest
from pypdf import PdfReader

from src.comun.rutas import DOCS_RAG
from src.models import calendario_laboral as CL

_TEXTOS: dict = {}


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFC", t).replace("ﬁ", "fi").replace("/f_", "f")   # los PDF traen ligaduras partidas
    return re.sub(r"\s+", " ", t).lower()


def _texto(doc: str) -> str:
    if doc not in _TEXTOS:
        ruta = os.path.join(DOCS_RAG, doc)
        assert os.path.isfile(ruta), f"falta el documento oficial {doc}: python -m src.datos_publicos.descargar"
        _TEXTOS[doc] = _norm(" ".join((p.extract_text() or "") for p in PdfReader(ruta).pages)) if doc.endswith(".pdf") else _norm(open(ruta, encoding="utf-8").read())
    return _TEXTOS[doc]


def _evidencias():
    c = CL.cfg()
    return [(sec, e["doc"], e["frase"]) for sec in ("alcance", "gratificacion", "cts", "libre_disposicion") for e in c[sec]["evidencia"]]


@pytest.mark.parametrize("seccion,doc,frase", _evidencias())
def test_cada_regla_tiene_su_frase_en_el_documento_oficial(seccion, doc, frase):
    """Una regla que no aparece en su fuente no pasa: asi el agente no afirma lo que ningun documento oficial dice."""
    assert _norm(frase) in _texto(doc), f"[{seccion}] la frase no esta en {doc}: {frase}"


def test_las_reglas_del_yaml_coinciden_con_lo_que_dice_la_fuente():
    c = CL.cfg()
    assert c["gratificacion"]["meses"] == [7, 12] and c["cts"]["meses_deposito"] == [5, 11] and c["cts"]["dia_limite"] == c["gratificacion"]["dia_limite"] == 15
    assert c["gratificacion"]["bonificacion_extraordinaria"] == {"essalud": 0.09, "eps": 0.0675}
    assert c["libre_disposicion"]["vigente_hasta"] == "2026-12-31" and c["libre_disposicion"]["porcentaje_permanente"] == 0.5
    assert abs(c["cts"]["fraccion_de_gratificacion_en_la_remuneracion_computable"] - 1 / 6) < 1e-6


def test_el_deposito_de_cts_pasa_al_siguiente_dia_habil_si_el_15_es_inhabil():
    assert CL.fecha_limite("cts", 2026, 11) == date(2026, 11, 16)    # el 15 de noviembre de 2026 es domingo
    assert CL.fecha_limite("cts", 2025, 11) == date(2025, 11, 17)    # sabado: El Peruano informo el plazo hasta el lunes 17
    assert CL.fecha_limite("cts", 2026, 5) == date(2026, 5, 15)      # viernes
    assert CL.fecha_limite("cts", 2027, 5) == date(2027, 5, 17)      # el 15 es sabado
    assert CL.fecha_limite("gratificacion", 2026, 12) == date(2026, 12, 15)


def test_montos_con_la_formula_de_la_norma():
    g = CL.monto_gratificacion(3000)
    assert g == {"gratificacion": 3000, "bonificacion_extraordinaria": 270, "total": 3270, "porcentaje_bonificacion": 0.09}
    cts = CL.monto_cts(3000)   # computable = 3000 + 3000/6; se depositan 6 dozavos
    assert cts == {"remuneracion_computable": 3500, "deposito_semestral": 1750}


def test_los_eventos_vienen_ordenados_y_con_dias_y_texto_correctos():
    ev = CL.eventos(date(2026, 11, 14), 3000)
    assert [e["tipo"] for e in ev[:3]] == ["cts", "gratificacion", "cts"]
    assert ev[0]["fecha_limite_texto"] == "lunes 16 de noviembre de 2026" and ev[0]["dias_para"] == 2
    assert ev[1]["fecha_limite_texto"] == "martes 15 de diciembre de 2026" and ev[1]["dias_para"] == 31
    assert all(ev[i]["fecha_limite"] <= ev[i + 1]["fecha_limite"] for i in range(len(ev) - 1))


def test_un_evento_vencido_se_marca_como_pasado_y_no_sale_en_el_calendario():
    pasado = [e for e in CL.eventos(date(2026, 12, 20), 3000, desde_dias=30, hasta_dias=0)]
    assert pasado and pasado[-1]["tipo"] == "gratificacion" and pasado[-1]["estado"] == "pasado" and pasado[-1]["dias_para"] == -5
    cal = CL.calendario(date(2026, 12, 20), "dependiente", 3000, "historial")
    assert all(e["estado"] != "pasado" for e in cal["eventos"])


def test_el_independiente_no_tiene_cts_ni_gratificacion():
    cal = CL.calendario(date(2026, 11, 14), "independiente", 3000)
    assert cal["aplica"] is False and "independiente" in cal["motivo"] and "eventos" not in cal


def test_sin_base_no_se_inventa_un_monto():
    assert CL.calendario(date(2026, 11, 14), "dependiente", None)["aplica"] is False
    assert CL.calendario(date(2026, 11, 14), "dependiente", 0)["aplica"] is False


def test_la_confianza_depende_de_si_la_base_sale_del_historial():
    assert CL.calendario(date(2026, 11, 14), "dependiente", 3000, "historial")["confianza"] == "alta"
    assert CL.calendario(date(2026, 11, 14), "dependiente", 3000, "ingreso_medio")["confianza"] == "media"


def test_libre_disposicion_el_ultimo_dia_y_el_dia_siguiente():
    ult = CL.libre_disposicion(date(2026, 12, 31))
    assert ult["regimen_transitorio_vigente"] and ult["porcentaje_libre_hoy"] == 1.0 and ult["dias_restantes"] == 0 and ult["por_vencer"]
    sig = CL.libre_disposicion(date(2027, 1, 1))
    assert not sig["regimen_transitorio_vigente"] and sig["porcentaje_libre_hoy"] == 0.5 and sig["dias_restantes"] == 0 and not sig["por_vencer"]


def test_la_alerta_de_vencimiento_solo_salta_dentro_de_los_60_dias():
    assert CL.libre_disposicion(date(2026, 11, 14))["por_vencer"] and CL.libre_disposicion(date(2026, 11, 14))["dias_restantes"] == 47
    assert not CL.libre_disposicion(date(2026, 6, 1))["por_vencer"]


def test_un_proyecto_de_ley_no_cambia_la_regla_vigente():
    ld = CL.libre_disposicion(date(2027, 3, 1))   # aunque exista un proyecto para ampliar el plazo, la ley vigente dice 50 %
    assert ld["porcentaje_libre_hoy"] == 0.5 and "todavia no es ley" in ld["nota_proyectos"] and "se esta evaluando" in ld["nota_proyectos"]
    pr = ld["proyecto_en_evaluacion"]   # el proyecto se cita como estado del tramite: nunca cambia el porcentaje ni la fecha vigentes
    assert pr["plazo_propuesto"] == "2028-12-31" and pr["verificado_el"] and "elperuano.pe/noticia/308663" in pr["fuente"]
    assert ld["vigente_hasta"] == "2026-12-31" and CL.libre_disposicion(date(2026, 12, 31))["porcentaje_libre_hoy"] == 1.0


def test_las_reglas_piden_revision_pasado_el_plazo():
    v = date.fromisoformat(CL.cfg()["fecha_verificacion"])
    plazo = CL.cfg()["dias_para_revisar"]
    assert not CL.reglas_por_revisar(v + timedelta(days=plazo)) and CL.reglas_por_revisar(v + timedelta(days=plazo + 1))
