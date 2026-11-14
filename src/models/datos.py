"""Cargadores de las tablas generadas. Todo se lee relativo a la raiz del repo."""
import os
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.comun.rutas import DATA_GENERADO


@dataclass
class Series:
    ids: np.ndarray        # customer_id por fila
    fechas: pd.DatetimeIndex
    ing: np.ndarray        # [cliente, dia] ingresos
    gas: np.ndarray        # [cliente, dia] gastos
    saldo: np.ndarray      # [cliente, dia] saldo de cierre


def cargar_series(carpeta: str = DATA_GENERADO) -> Series:
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
    return pd.read_parquet(os.path.join(carpeta, "clientes.parquet")).set_index("customer_id")


def cargar_panel(carpeta: str = DATA_GENERADO) -> pd.DataFrame:
    p = pd.read_parquet(os.path.join(carpeta, "panel_mensual"))
    p["customer_id"] = p["customer_id"].astype(str)
    return p


def cargar_contexto(carpeta: str = DATA_GENERADO) -> pd.DataFrame:
    return pd.read_parquet(os.path.join(carpeta, "contexto_diario.parquet"))


def cargar_transacciones(carpeta: str = DATA_GENERADO, columnas=None, desde=None, hasta=None) -> pd.DataFrame:
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
