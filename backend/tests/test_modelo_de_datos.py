"""Modelo de datos (PostgreSQL): el esquema cubre cada columna de los Parquet, sus relaciones apuntan a tablas que existen, y el documento esta al dia. Si hay un Postgres, se prueba de verdad."""
import glob
import importlib.util
import os
import re

import pyarrow.parquet as pq
import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SQL = os.path.join(RAIZ, "docs", "modelo_de_datos", "schema_postgres.sql")
DATOS = os.path.join(RAIZ, "data", "generado")


def _gen():
    spec = importlib.util.spec_from_file_location("generar_modelo_de_datos", os.path.join(RAIZ, "analitica", "eval", "generar_modelo_de_datos.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _tablas():
    return _gen().parsear(open(SQL, encoding="utf-8").read())


def _columnas_parquet(patron: str) -> set:
    arch = sorted(glob.glob(os.path.join(DATOS, patron)))
    return {f.name for f in pq.read_schema(arch[0])}


hay_datos = pytest.mark.skipif(not os.path.isdir(os.path.join(DATOS, "saldo_diario")), reason="falta data/generado")


def test_el_esquema_define_las_25_tablas_en_dos_esquemas():
    t = _tablas()
    assert len(t) == 25 and {n.split(".")[0] for n in t} == {"lucas", "simulacion"}


@hay_datos
@pytest.mark.parametrize("parquet,tablas,sobran", [
    ("clientes.parquet", ["lucas.cliente", "simulacion.cliente_verdad"], set()),
    ("transacciones/*.parquet", ["lucas.transaccion", "simulacion.transaccion_verdad"], {"movimiento_id"}),
    ("saldo_diario/*.parquet", ["lucas.saldo_diario"], set()), ("panel_mensual/*.parquet", ["lucas.panel_mensual"], set()), ("mensajes/*.parquet", ["lucas.mensaje"], {"mensaje_id"}),
    ("contexto_diario.parquet", ["lucas.contexto_diario"], set()), ("eventos.parquet", ["lucas.evento"], set()), ("macro_mensual.parquet", ["lucas.macro_mensual"], set()),
    ("etiquetas_calidad/*.parquet", ["simulacion.calidad_etiqueta"], set())])
def test_cada_columna_de_los_parquet_tiene_su_lugar_en_el_esquema_y_no_sobra_ninguna(parquet, tablas, sobran):
    t = _tablas()
    ddl = set().union(*({c[0] for c in t[n]["columnas"]} for n in tablas)) - sobran - {"creado_el"}
    assert _columnas_parquet(parquet) == ddl, f"{parquet}: faltan {_columnas_parquet(parquet) - ddl}, sobran {ddl - _columnas_parquet(parquet)}"


def test_lo_observable_y_la_verdad_oculta_estan_separados_como_en_columnas_py():
    from src.models import columnas as C
    t = _tablas()
    observables = {c[0] for c in t["lucas.cliente"]["columnas"]}
    verdad = {c[0] for c in t["simulacion.cliente_verdad"]["columnas"]}
    assert set(C.OBSERVABLES_CLIENTE) <= observables and not (observables & (set(C.ETIQUETAS_CLIENTE) | set(C.INTERNAS_GENERADOR)))
    assert (set(C.ETIQUETAS_CLIENTE) | set(C.INTERNAS_GENERADOR)) <= verdad
    assert not ({c[0] for c in t["lucas.transaccion"]["columnas"]} & set(C.ETIQUETAS_TRANSACCION))
    assert set(C.ETIQUETAS_TRANSACCION) <= {c[0] for c in t["simulacion.transaccion_verdad"]["columnas"]}


def test_toda_relacion_apunta_a_una_tabla_que_existe_y_lo_de_un_cliente_se_borra_con_el():
    sql = open(SQL, encoding="utf-8").read()
    t = _tablas()
    rel = _gen().relaciones(sql)
    assert rel and all(padre in t and hija in t for hija, _, padre in rel)
    for hija, col, padre in rel:
        if padre == "lucas.cliente" and hija != "lucas.consulta_chat":
            assert re.search(rf"{col}\s+[^\n]*REFERENCES lucas\.cliente \(customer_id\) ON DELETE CASCADE", sql), hija


def test_el_dinero_va_en_numeric_y_el_rag_en_vectores_de_768():
    t = _tablas()
    for n in ("lucas.transaccion", "lucas.saldo_diario", "lucas.panel_mensual"):
        for c, tipo, _, _ in t[n]["columnas"]:
            assert tipo not in ("REAL", "DOUBLE PRECISION", "FLOAT"), (n, c)
    emb = {c[0]: c[1] for c in t["lucas.rag_fragmento"]["columnas"]}
    assert emb["embedding"] == "vector(768)" and "texto_tsv" in emb
    assert "USING hnsw (embedding vector_ip_ops)" in open(SQL, encoding="utf-8").read()


def test_el_documento_esta_al_dia_con_el_esquema():
    doc = open(os.path.join(RAIZ, "docs", "modelo_de_datos", "README.md"), encoding="utf-8").read()
    for n in _tablas():
        assert f"### `{n}`" in doc, f"{n} no esta en docs/modelo_de_datos/README.md: python analitica/eval/generar_modelo_de_datos.py"


def test_la_validacion_contra_postgres_real_quedo_guardada_y_paso():
    import json
    v = json.load(open(os.path.join(RAIZ, "docs", "modelo_de_datos", "validacion_postgres.json"), encoding="utf-8"))
    assert v["todo_ok"] and v["tablas"] == 25 and v["version_de_postgres"].startswith("PostgreSQL")


@pytest.mark.skipif(not os.environ.get("DATABASE_URL_PRUEBA"), reason="defina DATABASE_URL_PRUEBA (una base de prueba vacia con pgvector) para probar contra un Postgres real")
def test_el_esquema_se_crea_en_un_postgres_real():
    import psycopg
    with psycopg.connect(os.environ["DATABASE_URL_PRUEBA"]) as con, con.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS lucas CASCADE; DROP SCHEMA IF EXISTS simulacion CASCADE;")
        cur.execute(open(SQL, encoding="utf-8").read())
        cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema IN ('lucas', 'simulacion') AND table_type = 'BASE TABLE'")
        assert cur.fetchone()[0] == 25
        con.rollback()
