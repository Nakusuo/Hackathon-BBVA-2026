"""Problemas de calidad sembrados (atipicos, duplicados, faltantes) y el limpiado que los deshace."""
import numpy as np
import pandas as pd


def recalcular_saldo(df: pd.DataFrame, saldo_ini: pd.Series) -> pd.Series:
    """Saldo corrido por cliente tras modificar montos. Requiere df ordenado por cliente y fecha."""
    firmado = np.where(df["tipo"] == "ingreso", df["monto_pen"], -df["monto_pen"]).astype(np.float64)
    corrido = pd.Series(firmado, index=df.index).groupby(df["customer_id"].to_numpy()).cumsum()
    return (corrido + df["customer_id"].map(saldo_ini).to_numpy()).astype("float32")


def vestir_atipicos(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """El monto atipico ya sale del simulador (dentro del presupuesto del mes). Aqui se le da el aspecto de gasto ajeno al patron."""
    idx = np.flatnonzero(df["es_atipico"].to_numpy())
    if idx.size == 0:
        return df
    pos = df.index[idx]
    df.loc[pos, "comercio"] = "Comercio Exterior Ltd"
    df.loc[pos, "canal"] = "tarjeta_credito"
    df.loc[pos, "glosa"] = "CONSUMO TC COMERCIO EXTERIOR LTD"
    hora = pd.to_timedelta(rng.integers(2 * 3600, 5 * 3600, idx.size), unit="s")
    df.loc[pos, "fecha_hora"] = df["fecha_hora"].dt.normalize().to_numpy()[idx] + hora
    return df


def sembrar_ruido(df: pd.DataFrame, cfg: dict, rng: np.random.Generator) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Duplicados y faltantes. Devuelve la tabla sucia y la tabla de etiquetas (que filas se ensuciaron y como)."""
    n = len(df)
    etiquetas = []
    for col, clave, tipo in (("glosa", "p_faltante_glosa", "falta_glosa"), ("categoria", "p_faltante_categoria", "falta_categoria"),
                             ("saldo", "p_faltante_saldo", "falta_saldo"), ("monto", "p_faltante_monto", "falta_monto")):
        idx = np.flatnonzero(rng.random(n) < cfg[clave])
        etiquetas.append(pd.DataFrame({"transaction_id": df["transaction_id"].to_numpy()[idx], "tipo_problema": tipo}))
        df.loc[df.index[idx], col] = np.nan
    idx = np.flatnonzero(rng.random(n) < cfg["p_duplicado"])
    copia = df.iloc[idx].copy()
    cercano = rng.random(len(copia)) < 0.4
    copia.loc[cercano, "fecha_hora"] = copia.loc[cercano, "fecha_hora"] + pd.to_timedelta(rng.integers(5, 120, int(cercano.sum())), unit="s")
    nuevos = [f"{t}D" for t in copia.loc[cercano, "transaction_id"]]
    copia.loc[cercano, "transaction_id"] = nuevos
    etiquetas.append(pd.DataFrame({"transaction_id": copia["transaction_id"].to_numpy(),
                                   "tipo_problema": np.where(cercano, "duplicado_cercano", "duplicado_exacto")}))
    df = pd.concat([df, copia], ignore_index=True).sort_values(["customer_id", "fecha_hora", "transaction_id"], kind="stable").reset_index(drop=True)
    return df, pd.concat(etiquetas, ignore_index=True)


def deduplicar(df: pd.DataFrame, ventana_seg: int = 120) -> pd.DataFrame:
    """Quita duplicados exactos (mismo id) y cercanos (mismo cliente, monto y comercio en una ventana corta)."""
    df = df.drop_duplicates(subset=["transaction_id"], keep="first")
    df = df.sort_values(["customer_id", "comercio", "monto", "fecha_hora"], kind="stable")
    mismo = (df["customer_id"].eq(df["customer_id"].shift()) & df["comercio"].eq(df["comercio"].shift())
             & df["monto"].eq(df["monto"].shift()) & ((df["fecha_hora"] - df["fecha_hora"].shift()).dt.total_seconds().abs() <= ventana_seg))
    return df[~mismo].sort_values(["customer_id", "fecha_hora"], kind="stable").reset_index(drop=True)
