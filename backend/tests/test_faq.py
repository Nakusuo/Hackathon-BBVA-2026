"""Preguntas frecuentes: reutilizar respuestas verificadas sin gastar tokens y aprender de lo que se pregunta (en una base de datos), sin guardar nada de la persona."""
import json
import os
import sqlite3

import pytest

from src.agente_analitico import faq as FAQ
from src.comun.rutas import DATA_GENERADO, MODELOS

RESP = "Segun la Resolucion SBS 3274 (pag. 12): la TCEA incluye intereses, comisiones y gastos. Tu decides."


def _est(**kw):
    base = {"intencion": "educacion", "rag_estado": "correcto", "proveedor": "gemini", "pregunta": "¿Que es la TCEA?", "veredicto": {"ok": True}, "customer_id": "C00007",
            "ctx": {"nivel": "Campeon", "departamento": "Piura"},
            "rag": [{"documento": "deudas/sbs.pdf", "titulo": "Resolucion SBS 3274", "pagina": 12, "enlace": "https://ejemplo.test/sbs", "licencia_nivel": "A",
                     "texto": "La tasa de costo efectivo anual (TCEA) incluye intereses, comisiones y gastos. Debe informarse antes de contratar. Pagina 12.", "similitud": 0.82}]}
    base.update(kw)
    return base


def test_normalizar_quita_tildes_digitos_y_palabras_vacias():
    assert FAQ.normalizar("¿Qué es la TCEA de 2026?") == frozenset({"tcea"})
    assert FAQ.normalizar("¿Cómo funciona el crédito?") == FAQ.normalizar("como funciona el credito") == frozenset({"funciona", "credito"})


def test_solo_se_guardan_palabras_que_existen_en_el_corpus_del_rag():
    p = FAQ.normalizar("Soy Zzxqvbn Pxkltre, ¿que es la TCEA?", solo_corpus=True)
    assert "zzxqvbn" not in p and "pxkltre" not in p   # un nombre escrito en la pregunta no llega a la base


def test_se_aprende_una_respuesta_de_concepto_y_se_reutiliza_para_el_mismo_nivel():
    assert FAQ.registrar(_est(), RESP) == "aprendida"
    assert FAQ.registrar(_est(), RESP) == "ya_estaba"
    hit = FAQ.buscar("¿Que es la tcea?", "Campeon")
    assert hit and hit["respuesta"] == RESP and hit["origen"] == "aprendida" and hit["fragmentos"][0]["titulo"] == "Resolucion SBS 3274"
    assert FAQ.buscar("¿Que es la TCEA?", "Luchador") is None   # el tono cambia por nivel: otra persona de otro nivel no recibe esa redaccion
    s = FAQ.estadisticas()
    assert s["preguntas_aprendidas"] == 1 and s["respondidas_sin_llm"] == 1 and s["consultas_de_concepto"] == 2


def test_lo_aprendido_vive_en_una_base_de_datos_con_su_esquema():
    FAQ.registrar(_est(), RESP)
    con = sqlite3.connect(os.path.join(os.environ["LUCAS_FAQ_DIR"], "faq.db"))
    tablas = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"faq_aprendida", "faq_preguntas_vistas", "faq_contadores"} <= tablas
    fila = con.execute("SELECT palabras, nivel, respuesta, veces FROM faq_aprendida").fetchone()
    assert fila == ("tcea", "Campeon", RESP, 1)


def test_una_respuesta_con_cifras_que_no_vienen_de_las_fuentes_no_se_guarda():
    # «tu saldo de S/ 7,395» es de la persona: guardarlo y mostrarlo a otra seria filtrar sus datos
    assert FAQ.registrar(_est(), "Segun la fuente la TCEA incluye comisiones; con tu saldo de S/ 7,395 conviene revisarla. Tu decides.") == "no_reutilizable"
    assert FAQ.buscar("¿Que es la TCEA?", "Campeon") is None


def test_una_respuesta_que_nombra_la_zona_o_el_id_del_cliente_no_se_guarda():
    assert FAQ.registrar(_est(), "En Piura la TCEA incluye comisiones. Tu decides.") == "no_reutilizable"
    assert FAQ.registrar(_est(), "Para C00007 la TCEA incluye comisiones. Tu decides.") == "no_reutilizable"


@pytest.mark.parametrize("cambios", [{"proveedor": "plantilla"}, {"proveedor": "faq"}, {"veredicto": {"ok": False}}, {"pregunta": "¿Que es la TCEA de mi tarjeta 4455?"},
                                     {"intencion": "pronostico"}, {"rag_estado": "sin_evidencia (mejor similitud 0.40)", "rag": []}])
def test_no_se_aprende_lo_que_no_corresponde(cambios):
    FAQ.registrar(_est(**cambios), "Segun la fuente la TCEA incluye comisiones. Tu decides.")
    assert FAQ.estadisticas()["preguntas_aprendidas"] == 0


def test_lo_que_las_fuentes_no_responden_se_cuenta_para_saber_que_documentos_agregar():
    FAQ.registrar(_est(rag_estado="sin_evidencia (mejor similitud 0.40)", rag=[]), "Sobre eso no encuentro informacion. Tu decides.")
    assert FAQ.estadisticas()["sin_evidencia_en_las_fuentes"] == 1


def test_una_respuesta_guardada_deja_de_usarse_si_cambia_el_indice_del_rag(monkeypatch):
    FAQ.registrar(_est(), RESP)
    assert FAQ.buscar("¿Que es la TCEA?", "Campeon", cuenta=False)
    monkeypatch.setattr(FAQ, "_HUELLA_INDICE", "otro_indice")
    assert FAQ.buscar("¿Que es la TCEA?", "Campeon", cuenta=False) is None


def test_la_base_no_guarda_datos_de_la_persona():
    FAQ.registrar(_est(pregunta="Hola soy Zzxqvbn, ¿que es la TCEA?"), RESP)
    con = sqlite3.connect(os.path.join(os.environ["LUCAS_FAQ_DIR"], "faq.db"))
    volcado = "\n".join(con.iterdump()).lower()
    assert "zzxqvbn" not in volcado and "c00007" not in volcado and "piura" not in volcado and "hola soy" not in volcado


def test_las_mas_preguntadas_salen_primero():
    FAQ.registrar(_est(pregunta="¿Que es la TCEA?"), RESP)
    for _ in range(2):
        FAQ.registrar(_est(pregunta="¿Que derechos tengo para reclamar a mi banco?"), "Segun la fuente puedes reclamar. Tu decides.")
    top = FAQ.frecuentes(2)
    assert top[0]["veces"] == 2 and "reclamar" in top[0]["pregunta_normalizada"] and top[0]["respuesta_guardada"] is True


def test_una_pregunta_distinta_no_recibe_la_respuesta_de_otra():
    FAQ.registrar(_est(), RESP)
    assert FAQ.buscar("¿Que es el tipo de cambio?", "Campeon") is None
    assert FAQ.buscar("tasa", "Campeon") is None   # una sola palabra distinta tampoco coincide
    assert FAQ.buscar("¿Que es la TCEA de mi tarjeta de credito?", "Campeon") is None   # una pregunta mas especifica no recibe la respuesta general


def test_se_exporta_para_embeddings_con_lo_aprendido_y_la_semilla():
    FAQ.registrar(_est(), RESP)
    ruta = FAQ.exportar_para_embeddings()
    filas = [json.loads(x) for x in open(ruta, encoding="utf-8")]
    assert any(f["id"].startswith("semilla-") for f in filas) and any(f["id"].startswith("aprendida-") for f in filas)
    aprendida = [f for f in filas if f["id"].startswith("aprendida-")][0]
    assert aprendida["respuesta"] == RESP and aprendida["fuentes"][0]["titulo"] == "Resolucion SBS 3274" and aprendida["nivel"] == "Campeon"


# ---------------------------------------------------------------------------- la semilla
def test_la_semilla_cita_fuentes_y_cada_pregunta_se_responde_sin_llm():
    s = json.load(open(FAQ.SEMILLA, encoding="utf-8"))
    assert s["huella_indice"] == FAQ.huella_indice(), "el indice del RAG cambio: python analitica/eval/generar_faq.py"
    assert len(s["entradas"]) >= 10
    for e in s["entradas"]:
        assert e["respuesta"].endswith("Tu decides.") and e["fragmentos"][0]["enlace"] and e["fragmentos"][0]["licencia_nivel"] == "A"
        hit = FAQ.buscar(e["pregunta"], "Maestro", cuenta=False)
        assert hit and hit["origen"] == "semilla" and hit["respuesta"] == e["respuesta"]


# ---------------------------------------------------------------------------- de punta a punta con una API falsa
requiere_modelos = pytest.mark.skipif(not (os.path.isfile(os.path.join(MODELOS, "pronostico.pkl")) and os.path.isdir(os.path.join(DATA_GENERADO, "saldo_diario"))), reason="faltan los datos o los modelos")


class ApiFalsa:
    def __init__(self):
        from src.agente_analitico import proveedores as PV
        self.nombre, self.externo, self.llamadas, self.Error = "falsa", True, 0, PV.ErrorProveedor

    def redactar(self, pregunta, datos, tono, feedback=None, timeout=0):
        self.llamadas += 1
        return "La TCEA es la tasa de costo efectivo anual: suma intereses, comisiones y gastos. Tu decides."


@requiere_modelos
def test_la_segunda_pregunta_igual_no_llama_al_llm(repo_y_buscador, tmp_path, monkeypatch):
    from src.agente_analitico import grafo, proveedores as PV
    repo, b = repo_y_buscador
    api = ApiFalsa()
    monkeypatch.setenv("LLM_USO", "ahorro")
    monkeypatch.setattr(grafo, "_ruta_cache", lambda: str(tmp_path / "cache_llm.json"))
    monkeypatch.setattr(PV, "cadena", lambda: [api])
    cl = repo.clientes
    cid = cl[(cl["tipo_trabajo"] == "independiente") & (cl["departamento"] == "Piura")].index[0]
    mismo_nivel = [c for c in cl.index if c != cid and repo.contexto(c)["nivel"] == repo.contexto(cid)["nivel"] and cl.loc[c, "departamento"] != "Piura"]
    assert mismo_nivel, "hace falta otra persona del mismo nivel"
    app = grafo.construir_grafo(repo, b, "agente_unico")
    r1 = grafo.responder(app, cid, "¿Qué es la TCEA?")
    assert r1["proveedor"] == "falsa" and api.llamadas == 1
    r2 = grafo.responder(app, mismo_nivel[0], "¿Que es la tcea?")   # otra persona, mismo nivel, la misma pregunta escrita distinto
    assert r2["proveedor"] == "faq" and api.llamadas == 1 and r2["llamadas_llm"] == 0
    assert "intereses, comisiones y gastos" in r2["respuesta"] and r2["citas"] and not r2["cifras_sin_respaldo"]


@requiere_modelos
def test_con_la_api_caida_se_responde_con_la_plantilla_y_no_se_aprende_nada(repo_y_buscador, tmp_path, monkeypatch):
    from src.agente_analitico import grafo, proveedores as PV
    repo, b = repo_y_buscador

    class Caida(ApiFalsa):
        def redactar(self, *a, **k):
            raise self.Error("falsa: API caida")
    monkeypatch.setenv("LLM_USO", "ahorro")
    monkeypatch.setattr(grafo, "_ruta_cache", lambda: str(tmp_path / "cache_llm.json"))
    monkeypatch.setattr(PV, "cadena", lambda: [Caida()])
    cl = repo.clientes
    cid = cl[(cl["tipo_trabajo"] == "independiente") & (cl["departamento"] == "Piura")].index[0]
    r = grafo.responder(grafo.construir_grafo(repo, b, "agente_unico"), cid, "¿Qué es la TCEA?")
    assert r["proveedor"] == "plantilla" and r["respuesta"].rstrip().endswith("Tu decides.") and not r["cifras_sin_respaldo"]
    assert FAQ.estadisticas()["preguntas_aprendidas"] == 0
