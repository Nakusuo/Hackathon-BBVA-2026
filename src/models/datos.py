"""Cargadores de las tablas del cliente. Por defecto leen los Parquet generados (relativos a la raiz del repo);
con LUCAS_FUENTE_DATOS=postgres leen las mismas tablas del esquema `lucas` de la base (DATABASE_URL), que es lo que usa el aplicativo."""
import io
import os
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.comun.rutas import DATA_GENERADO, cargar_env


@dataclass
class Series:
    ids: np.ndarray        # customer_id por fila
    fechas: pd.DatetimeIndex
    ing: np.ndarray        # [cliente, dia] ingresos
    gas: np.ndarray        # [cliente, dia] gastos
    saldo: np.ndarray      # [cliente, dia] saldo de cierre


# Solo lo observable: la tabla `lucas.transaccion` no tiene las etiquetas es_* del simulador (viven en el esquema `simulacion`, que ningun modelo lee)
COLUMNAS_TX = ["customer_id", "transaction_id", "fecha_hora", "monto", "moneda", "monto_pen", "tipo", "categoria", "comercio", "glosa", "canal", "saldo"]
_FECHAS = ("fecha", "fecha_hora")
_TEXTO = ("customer_id", "transaction_id", "mes", "moneda", "tipo", "categoria", "comercio", "glosa", "canal", "rango_edad", "region", "departamento", "tipo_trabajo", "frecuencia_ingreso")
_ENTERAS_32 = ("dia_semana", "dia_mes")


def desde_postgres() -> bool:
    cargar_env()
    return os.environ.get("LUCAS_FUENTE_DATOS", "parquet").strip().lower() == "postgres"


def leer_tabla(consulta: str, parametros: tuple = ()) -> pd.DataFrame:
    """Trae una consulta del esquema `lucas` con COPY (rapido con millones de filas). El dinero llega como float32 y las fechas como datetime, igual que en los Parquet."""
    import psycopg

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError("LUCAS_FUENTE_DATOS=postgres necesita DATABASE_URL en .env")
    crudo = io.BytesIO()
    with psycopg.connect(dsn) as con, con.cursor() as cur, cur.copy(f"COPY ({consulta}) TO STDOUT WITH (FORMAT csv, HEADER)", parametros) as copia:
        for bloque in copia:
            crudo.write(bloque)
    crudo.seek(0)
    df = pd.read_csv(crudo, dtype=dict.fromkeys(_TEXTO, str), true_values=["t"], false_values=["f"], keep_default_na=False, na_values=[""])
    for c in df.columns:
        if c in _FECHAS:
            df[c] = pd.to_datetime(df[c]).astype("datetime64[us]")
        elif c in _ENTERAS_32:
            df[c] = df[c].astype(np.int32)
        elif df[c].dtype == np.float64:
            df[c] = df[c].astype(np.float32)
    return df


def cargar_series(carpeta: str = DATA_GENERADO) -> Series:
    if desde_postgres():
        sd = leer_tabla("SELECT customer_id, fecha, ingresos, gastos, saldo_cierre FROM lucas.saldo_diario")
    else:
        sd = pd.read_parquet(os.path.join(carpeta, "saldo_diario"))
    sd["customer_id"] = sd["customer_id"].astype(str)
    sd = sd.sort_values(["customer_id", "fecha"], kind="stable")
    ids = np.array(sorted(sd["customer_id"].unique()))
    fechas = pd.DatetimeIndex(np.sort(sd["fecha"].unique()))
    B, D = len(ids), len(fechas)
    if len(sd) != B * D:
        raise ValueError("saldo_diario no es rectangular: cada cliente debe tener todos los dias")
    f = lambda c: sd[c].to_numpy(dtype=np.float32).reshape(B, D)  # noqa: E731
    return Series(ids=ids, fechas=fechas, ing=f("ingresos"), gas=f("gastos"), saldo=f("saldo_cierre"))


def cargar_clientes(carpeta: str = DATA_GENERADO) -> pd.DataFrame:
    if desde_postgres():
        cl = leer_tabla("SELECT customer_id, rango_edad, region, departamento, tipo_trabajo, frecuencia_ingreso, personas_a_cargo, deuda_total, n_creditos, cuota_mensual, tcea_promedio, colchon_meses, "
                        "antiguedad_cliente_meses, meta_ahorro, paga_en_usd FROM lucas.cliente ORDER BY customer_id")
        dinero = ["deuda_total", "cuota_mensual", "tcea_promedio", "colchon_meses", "meta_ahorro"]
        cl[dinero] = cl[dinero].astype(np.float64)
        return cl.set_index("customer_id")
    return pd.read_parquet(os.path.join(carpeta, "clientes.parquet")).set_index("customer_id")


def cargar_panel(carpeta: str = DATA_GENERADO) -> pd.DataFrame:
    if desde_postgres():
        return leer_tabla("SELECT customer_id, mes, ahorro_movido, gasto_deuda, gasto_fijo, gasto_hormiga, gasto_variable, ingreso_extraordinario, ingreso_financiero, ingreso_operativo, n_transacciones, "
                          "saldo_fin, saldo_min, dias_en_rojo FROM lucas.panel_mensual ORDER BY customer_id, mes")
    p = pd.read_parquet(os.path.join(carpeta, "panel_mensual"))
    p["customer_id"] = p["customer_id"].astype(str)
    return p


def cargar_contexto(carpeta: str = DATA_GENERADO) -> pd.DataFrame:
    if desde_postgres():
        return leer_tabla("SELECT fecha, dia_semana, dia_mes, mes, fuerza_covid_confinamiento, fuerza_covid_reapertura, fuerza_covid_segunda_ola, fuerza_protestas_2022_2023, fuerza_nino_costero_2023 "
                          "FROM lucas.contexto_diario ORDER BY fecha").astype({"mes": np.int32})
    return pd.read_parquet(os.path.join(carpeta, "contexto_diario.parquet"))


def cargar_macro(carpeta: str = DATA_GENERADO) -> pd.DataFrame:
    if desde_postgres():
        return leer_tabla("SELECT mes, ipc_var_mensual, ipc_relativo, tasa_referencia_bcrp, tipo_cambio_venta FROM lucas.macro_mensual ORDER BY mes")
    return pd.read_parquet(os.path.join(carpeta, "macro_mensual.parquet"))


def _transacciones_de_postgres(columnas, desde, hasta) -> pd.DataFrame:
    columnas = list(columnas or COLUMNAS_TX)
    ajenas = [c for c in columnas if c not in COLUMNAS_TX]
    if ajenas:
        raise ValueError(f"lucas.transaccion no tiene {ajenas}: las etiquetas del simulador solo estan en los Parquet")
    filtros, parametros = [], []
    if desde is not None:
        filtros.append("fecha_hora >= %s")
        parametros.append(pd.Timestamp(desde).to_pydatetime())
    if hasta is not None:
        filtros.append("fecha_hora < %s")
        parametros.append(pd.Timestamp(hasta).to_pydatetime())
    donde = f" WHERE {' AND '.join(filtros)}" if filtros else ""
    return leer_tabla(f"SELECT {', '.join(columnas)} FROM lucas.transaccion{donde} ORDER BY movimiento_id", tuple(parametros))


def cargar_transacciones(carpeta: str = DATA_GENERADO, columnas=None, desde=None, hasta=None) -> pd.DataFrame:
    if desde_postgres():
        return _transacciones_de_postgres(columnas, desde, hasta)
    tx = pd.read_parquet(os.path.join(carpeta, "transacciones"), columns=columnas)
    if "customer_id" in tx:
        tx["customer_id"] = tx["customer_id"].astype(str)
    if desde is not None or hasta is not None:
        f = tx["fecha_hora"]
        m = np.ones(len(tx), dtype=bool)
        if desde is not None:
            m &= (f >= pd.Timestamp(desde)).to_numpy()
        if hasta is not None:
            m &= (f < pd.Timestamp(hasta)).to_numpy()
        tx = tx[m]
    return tx
