import glob
import os
import re

import pandas as pd
import pyarrow.parquet as pq
import pytest

from src.comun.rutas import RAIZ, ruta
from src.generador import calidad
from src.generador.pipeline import generar


@pytest.fixture(scope="module")
def datos(tmp_path_factory):
    carpeta = str(tmp_path_factory.mktemp("datos"))
    generar(clientes=32, inicio="2024-01-01", fin="2024-12-31", semilla=11, salida=carpeta, lote=16, verbose=False)
    return carpeta


def _hash(carpeta, tabla):
    p = os.path.join(carpeta, tabla)
    df = pd.read_parquet(p)
    return int(pd.util.hash_pandas_object(df.astype(str), index=False).sum())


def test_misma_semilla_misma_salida(datos, tmp_path):
    otra = str(tmp_path / "otra")
    generar(clientes=32, inicio="2024-01-01", fin="2024-12-31", semilla=11, salida=otra, lote=16, verbose=False)
    for tabla in ("clientes.parquet", "transacciones", "saldo_diario", "mensajes"):
        assert _hash(datos, tabla) == _hash(otra, tabla), tabla


def test_otra_semilla_cambia_los_datos(datos, tmp_path):
    otra = str(tmp_path / "otra")
    generar(clientes=32, inicio="2024-01-01", fin="2024-12-31", semilla=12, salida=otra, lote=16, verbose=False)
    assert _hash(datos, "transacciones") != _hash(otra, "transacciones")


def test_ningun_estrato_vacio_ni_peso_extremo(datos):
    cl = pd.read_parquet(os.path.join(datos, "clientes.parquet"))
    n = cl.groupby(["arquetipo", "perfil_ahorro_real", "perfil_gasto_real"]).size()
    assert len(n) == 16 and n.min() >= 1
    assert cl["peso_muestral"].between(0.4, 2.5).all()
    assert abs(cl["peso_muestral"].mean() - 1) < 0.05


def test_invariantes_de_movimientos(datos):
    tx = pd.read_parquet(os.path.join(datos, "transacciones"))
    et = pd.read_parquet(os.path.join(datos, "etiquetas_calidad"))
    assert (tx["monto_pen"].dropna() > 0).all()
    assert tx["transaction_id"].nunique() == len(tx) - (et["tipo_problema"] == "duplicado_exacto").sum()
    assert set(tx["tipo"].unique()) == {"ingreso", "gasto"}
    assert tx["fecha_hora"].min() >= pd.Timestamp("2024-01-01")


def test_la_limpieza_deshace_los_duplicados(datos):
    tx = pd.read_parquet(os.path.join(datos, "transacciones")).dropna(subset=["monto"])
    et = pd.read_parquet(os.path.join(datos, "etiquetas_calidad"))
    sembrados = int(et["tipo_problema"].isin(["duplicado_exacto", "duplicado_cercano"]).sum())
    limpio = calidad.deduplicar(tx)
    quitados = len(tx) - len(limpio)
    assert sembrados > 0
    assert quitados >= 0.9 * sembrados * (len(tx) / (len(tx) + 1))


def test_saldo_diario_coherente_con_los_movimientos(datos):
    tx = pd.read_parquet(os.path.join(datos, "transacciones")).dropna(subset=["saldo"]).sort_values("fecha_hora")
    sd = pd.read_parquet(os.path.join(datos, "saldo_diario"))
    ultimo = tx.groupby("customer_id", observed=True)["saldo"].last()
    cierre = sd[sd["fecha"] == sd["fecha"].max()].set_index("customer_id")["saldo_cierre"]
    assert (ultimo - cierre.reindex(ultimo.index)).abs().median() < 1


def test_el_confinamiento_reduce_el_ingreso_de_independientes(tmp_path):
    carpeta = str(tmp_path / "covid")
    generar(clientes=64, inicio="2020-01-01", fin="2020-06-30", semilla=5, salida=carpeta, lote=64, verbose=False)
    cl = pd.read_parquet(os.path.join(carpeta, "clientes.parquet")).set_index("customer_id")
    pm = pd.read_parquet(os.path.join(carpeta, "panel_mensual"))
    pm["seg"] = pm["customer_id"].map(cl["segmento"])
    m = pm[pm["mes"].isin(["2020-02", "2020-04"])].pivot_table(index="seg", columns="mes", values="ingreso_operativo", aggfunc="mean")
    assert (m["2020-04"] / m["2020-02"])["independiente_diario"] < 0.7


def test_no_hay_rutas_absolutas_en_el_codigo():
    patron = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]|/c/Users|/home/\w+|\\Users\\")
    archivos = glob.glob(os.path.join(RAIZ, "src", "**", "*.py"), recursive=True) + [os.path.join(RAIZ, "data", "generator.py")]
    sucios = []
    for a in archivos:
        for i, linea in enumerate(open(a, encoding="utf-8"), 1):
            if patron.search(linea) and "http" not in linea:
                sucios.append(f"{os.path.relpath(a, RAIZ)}:{i}")
    assert not sucios, sucios


def test_el_diccionario_coincide_con_el_esquema(datos):
    doc = open(ruta("data", "dictionary.md"), encoding="utf-8").read()
    secciones = re.split(r"^## ", doc, flags=re.M)[1:]
    documentadas = {s.split("\n", 1)[0].strip(): set(re.findall(r"^\| `([a-z_0-9]+)` \|", s, flags=re.M)) for s in secciones}
    for tabla, cols in documentadas.items():
        p = os.path.join(datos, tabla + ".parquet")
        archivo = p if os.path.isfile(p) else sorted(glob.glob(os.path.join(datos, tabla, "*.parquet")))[0]
        reales = set(pq.read_schema(archivo).names)
        if tabla == "contexto_diario":
            reales = {c for c in reales if not c.startswith("fuerza_")}
            cols = {c for c in cols if not c.startswith("fuerza_")}
        assert cols == reales, f"{tabla}: sobran {cols - reales}, faltan {reales - cols}"
