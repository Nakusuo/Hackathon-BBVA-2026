"""Calendario peruano, series reales del BCRP (inflacion y tipo de cambio) y fuerza diaria de cada evento."""
import json
import os
from dataclasses import dataclass

import holidays
import numpy as np
import pandas as pd
import yaml

from src.comun.rutas import DATA_PARAMETROS, DATA_RAW

MES_ES = {"Ene": 1, "Feb": 2, "Mar": 3, "Abr": 4, "May": 5, "Jun": 6, "Jul": 7, "Ago": 8, "Set": 9, "Sep": 9, "Oct": 10, "Nov": 11, "Dic": 12}
IPC_MENSUAL_SUPUESTO = 0.25  # % mensual cuando la serie real no cubre la ventana pedida


def cargar_yaml(nombre: str) -> dict:
    with open(os.path.join(DATA_PARAMETROS, nombre), encoding="utf-8") as f:
        return yaml.safe_load(f)


def _leer_bcrp(nombre: str) -> pd.Series:
    """Serie del BCRP como pandas.Series indexada por fecha. Devuelve vacia si el archivo no existe."""
    ruta = os.path.join(DATA_RAW, "bcrp", f"{nombre}.json")
    if not os.path.isfile(ruta):
        return pd.Series(dtype=float)
    with open(ruta, encoding="utf-8") as f:
        periodos = json.load(f)["periods"]
    fechas, valores = [], []
    for p in periodos:
        partes = p["name"].split(".")
        try:
            if len(partes) == 3:  # 01.Ene.19
                f_ = pd.Timestamp(2000 + int(partes[2]), MES_ES[partes[1]], int(partes[0]))
            else:  # Ene.2019
                f_ = pd.Timestamp(int(partes[1]), MES_ES[partes[0]], 1)
            v = float(p["values"][0])
        except (ValueError, KeyError):
            continue
        fechas.append(f_)
        valores.append(v)
    return pd.Series(valores, index=pd.DatetimeIndex(fechas)).sort_index()


@dataclass
class Contexto:
    fechas: pd.DatetimeIndex          # un elemento por dia
    meses: pd.PeriodIndex             # un elemento por mes
    mes_de_dia: np.ndarray            # indice de mes de cada dia
    ini_mes: np.ndarray               # primer dia (indice) de cada mes
    fin_mes: np.ndarray               # ultimo dia (indice, inclusive) de cada mes
    dow: np.ndarray                   # 0 = lunes
    dom: np.ndarray                   # dia del mes
    mes_cal: np.ndarray               # 1 a 12
    pago_15: np.ndarray               # dia (indice) de pago de la primera quincena, por mes
    pago_fin: np.ndarray              # dia (indice) de pago de fin de mes, por mes
    ipc_rel: np.ndarray               # precios relativos al ultimo mes real (1 = 2025-12)
    ipc_var_mensual: np.ndarray       # % mensual real
    tasa_ref: np.ndarray              # tasa de referencia BCRP (%)
    fx: np.ndarray                    # tipo de cambio venta promedio del mes (S/ por US$)
    fuerza: np.ndarray                # [evento, dia] entre 0 y 1
    eventos: list                     # definicion de cada evento (dict)
    shocks: list

    @property
    def n_dias(self) -> int:
        return len(self.fechas)

    @property
    def n_meses(self) -> int:
        return len(self.meses)


def _habil_anterior(fecha: pd.Timestamp, feriados) -> pd.Timestamp:
    while fecha.day_of_week >= 5 or fecha in feriados:
        fecha -= pd.Timedelta(days=1)
    return fecha


def construir_contexto(inicio: str, fin: str, incluir_prospectivos: bool = False) -> Contexto:
    fechas = pd.date_range(inicio, fin, freq="D")
    meses = pd.period_range(fechas[0], fechas[-1], freq="M")
    mes_de_dia = np.searchsorted(meses.to_timestamp(), fechas.to_period("M").to_timestamp(), side="left")
    ini = np.array([np.flatnonzero(mes_de_dia == m)[0] for m in range(len(meses))])
    fin_ = np.array([np.flatnonzero(mes_de_dia == m)[-1] for m in range(len(meses))])
    feriados = holidays.country_holidays("PE", years=range(fechas[0].year - 1, fechas[-1].year + 2))
    pos = {f: i for i, f in enumerate(fechas)}

    def _idx(f):
        return pos.get(f, None)

    p15, pfin = [], []
    for per in meses:
        d15 = _habil_anterior(pd.Timestamp(per.year, per.month, 15), feriados)
        dfin = _habil_anterior(per.to_timestamp(how="end").normalize(), feriados)
        i15, ifin = _idx(d15), _idx(dfin)
        p15.append(ini[len(p15)] + 14 if i15 is None else i15)
        pfin.append(fin_[len(pfin)] if ifin is None else ifin)

    # IPC real (var % mensual). El indice se expresa relativo al ultimo mes con dato real.
    var = _leer_bcrp("ipc_lima_var_mensual")
    serie = pd.Series(IPC_MENSUAL_SUPUESTO, index=meses.to_timestamp())
    if len(var):
        comunes = serie.index.intersection(var.index)
        serie.loc[comunes] = var.loc[comunes].to_numpy()
        ultimo_real = var.index.max()
    else:
        ultimo_real = serie.index[-1]
    indice = (1 + serie / 100).cumprod()
    ref = indice.loc[:ultimo_real].iloc[-1] if (indice.index <= ultimo_real).any() else indice.iloc[-1]
    ipc_rel = (indice / ref).to_numpy()

    tr = _leer_bcrp("tasa_referencia_bcrp")
    tasa_ref = tr.reindex(meses.to_timestamp()).ffill().bfill().fillna(4.5).to_numpy() if len(tr) else np.full(len(meses), 4.5)
    fxd = _leer_bcrp("tc_interbancario_venta_diario")
    if len(fxd):
        fxm = fxd.ffill().resample("MS").mean().reindex(meses.to_timestamp()).ffill().bfill().to_numpy()
    else:
        fxm = np.full(len(meses), 3.5)

    ev_cfg = cargar_yaml("eventos.yaml")
    eventos = [e for e in ev_cfg["eventos"] if incluir_prospectivos or e.get("tipo") != "prospectivo"]
    fuerza = np.zeros((len(eventos), len(fechas)), dtype=np.float32)
    for k, e in enumerate(eventos):
        a, b = pd.Timestamp(e["inicio"]), pd.Timestamp(e["fin"])
        rec = max(int(e.get("recuperacion_dias", 0)), 1)
        dias_desde_fin = (fechas - b).days.to_numpy()
        dentro = (fechas >= a) & (fechas <= b)
        rampa = np.clip(1 - dias_desde_fin / rec, 0, 1) * (fechas > b)
        fuerza[k] = np.where(dentro, 1.0, rampa)
    return Contexto(
        fechas=fechas, meses=meses, mes_de_dia=mes_de_dia, ini_mes=ini, fin_mes=fin_, dow=fechas.day_of_week.to_numpy(),
        dom=fechas.day.to_numpy(), mes_cal=fechas.month.to_numpy(), pago_15=np.array(p15), pago_fin=np.array(pfin),
        ipc_rel=ipc_rel, ipc_var_mensual=serie.to_numpy(), tasa_ref=tasa_ref, fx=fxm, fuerza=fuerza,
        eventos=eventos, shocks=ev_cfg.get("shocks", []),
    )
