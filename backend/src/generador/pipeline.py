"""Pipeline de generacion por lotes: clientes -> simulacion -> texto -> calidad -> Parquet.
El pico de memoria depende del tamano del lote, no del total de clientes."""
import hashlib
import json
import os
import platform
import time

import numpy as np
import pandas as pd

from src.comun.rutas import DATA_PARAMETROS
from src.generador import calidad, catalogo as K, texto
from src.generador.clientes import generar_clientes
from src.generador.contexto import Contexto, cargar_yaml, construir_contexto
from src.generador.simulacion import LAB_ATIPICO, LAB_SUB_DUP, simular_lote

BUCKET = {}
for _n in K.NOMBRES_CAT:
    BUCKET[_n] = ("ingreso_operativo" if _n in {"sueldo", "gratificacion", "comision", "venta_diaria", "honorarios", "ingreso_extra"}
                  else "ingreso_extraordinario" if _n in {"bono_estado", "retiro_afp"}
                  else "ingreso_financiero" if _n in {"retiro_ahorro", "prestamo_informal", "transferencia_recibida"}
                  else "ahorro_movido" if _n in {"ahorro_programado", "traspaso_ahorro"}
                  else "gasto_deuda" if _n in {"cuota_prestamo", "pago_credito_informal"}
                  else "gasto_fijo" if _n in {"alquiler", "luz", "agua", "internet", "celular", "suscripcion", "colegio", "seguro"}
                  else "gasto_hormiga" if _n in {"delivery", "snacks"} else "gasto_variable")
BUCKETS = sorted(set(BUCKET.values()))
BUCKET_DE_ID = np.array([BUCKET[n] for n in K.NOMBRES_CAT])


def _categorico(df: pd.DataFrame, cols) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = df[c].astype("category")
    return df


def _tabla_transacciones(f: dict, cl: pd.DataFrame, ctx: Contexto, rng) -> pd.DataFrame:
    cat = f["cat"].astype(int)
    canal = K.sortear_canal(cat, rng)
    fecha = ctx.fechas[f["day"]] + pd.to_timedelta(f["secs"], unit="s")
    df = pd.DataFrame({
        "customer_id": cl["customer_id"].to_numpy()[f["b"]], "fecha_hora": fecha, "monto": f["monto"], "moneda": np.where(f["moneda"] == 1, "USD", "PEN"),
        "monto_pen": f["pen"], "tipo": np.where(f["ing"], "ingreso", "gasto"), "categoria": np.array(K.NOMBRES_CAT)[cat],
        "comercio": K.NOMBRES_COMERCIO[f["com"]], "canal": np.array(K.CANALES)[canal], "saldo": f["saldo"],
        "es_recurrente": K.ES_RECURRENTE_CAT[cat] | (f["ing"] & np.isin(np.array(K.NOMBRES_CAT)[cat], ["sueldo"])),
        "es_atipico": (f["lab"] & LAB_ATIPICO) > 0, "es_suscripcion_duplicada": f["lab"] == LAB_SUB_DUP, "dia_idx": f["day"], "cliente_idx": f["b"],
    })
    df["glosa"] = texto.glosas(cat, canal, f["com"], f["ing"], rng)
    return df


def _saldo_diario(tx: pd.DataFrame, cl: pd.DataFrame, ctx: Contexto) -> pd.DataFrame:
    B, D = len(cl), ctx.n_dias
    ing = np.zeros((B, D), dtype=np.float64)
    gas = np.zeros((B, D), dtype=np.float64)
    es_ing = (tx["tipo"] == "ingreso").to_numpy()
    np.add.at(ing, (tx["cliente_idx"].to_numpy()[es_ing], tx["dia_idx"].to_numpy()[es_ing]), tx["monto_pen"].to_numpy()[es_ing])
    np.add.at(gas, (tx["cliente_idx"].to_numpy()[~es_ing], tx["dia_idx"].to_numpy()[~es_ing]), tx["monto_pen"].to_numpy()[~es_ing])
    saldo = cl["saldo_inicial"].to_numpy()[:, None] + np.cumsum(ing - gas, axis=1)
    return pd.DataFrame({
        "customer_id": np.repeat(cl["customer_id"].to_numpy(), D), "fecha": np.tile(ctx.fechas.to_numpy(), B),
        "ingresos": ing.ravel().astype("float32"), "gastos": gas.ravel().astype("float32"), "saldo_cierre": saldo.ravel().astype("float32"),
        "en_rojo": (saldo.ravel() < 0),
    }), ing.astype("float32"), saldo.astype("float32")


def _panel_mensual(tx: pd.DataFrame, diario: pd.DataFrame, ctx: Contexto) -> pd.DataFrame:
    mes_dia = pd.Series(ctx.meses.astype(str)[ctx.mes_de_dia], index=ctx.fechas.to_numpy())
    tx = tx.assign(mes=mes_dia.reindex(tx["fecha_hora"].dt.normalize().to_numpy()).to_numpy(),
                   bucket=BUCKET_DE_ID[pd.Index(K.NOMBRES_CAT).get_indexer(tx["categoria"])])
    p = tx.pivot_table(index=["customer_id", "mes"], columns="bucket", values="monto_pen", aggfunc="sum", fill_value=0.0, observed=True)
    p = p.reindex(columns=BUCKETS, fill_value=0.0)
    p["n_transacciones"] = tx.groupby(["customer_id", "mes"], observed=True).size()
    d = diario.assign(mes=mes_dia.reindex(diario["fecha"].to_numpy()).to_numpy())
    g = d.groupby(["customer_id", "mes"], observed=True)
    p["saldo_fin"] = g["saldo_cierre"].last()
    p["saldo_min"] = g["saldo_cierre"].min()
    p["dias_en_rojo"] = g["en_rojo"].sum()
    return p.reset_index().astype({c: "float32" for c in BUCKETS})


def tabla_contexto(ctx: Contexto) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    eventos = pd.DataFrame([{"evento_id": e["id"], "nombre": e["nombre"], "tipo": e["tipo"], "inicio": e["inicio"], "fin": e["fin"],
                             "estado": e["estado"], "fuente": e["fuente"]} for e in ctx.eventos])
    diario = pd.DataFrame({"fecha": ctx.fechas, "dia_semana": ctx.dow, "dia_mes": ctx.dom, "mes": ctx.mes_cal})
    for k, e in enumerate(ctx.eventos):
        diario[f"fuerza_{e['id']}"] = ctx.fuerza[k]
    macro = pd.DataFrame({"mes": ctx.meses.astype(str), "ipc_var_mensual": ctx.ipc_var_mensual.astype("float32"), "ipc_relativo": ctx.ipc_rel.astype("float32"),
                          "tasa_referencia_bcrp": ctx.tasa_ref.astype("float32"), "tipo_cambio_venta": ctx.fx.astype("float32")})
    return eventos, diario, macro


def generar(clientes: int, inicio: str, fin: str, semilla: int, salida: str, lote: int = 50, incluir_prospectivos: bool = False,
            tabla_semilla: pd.DataFrame | None = None, verbose: bool = True) -> dict:
    t0 = time.time()
    gen = cargar_yaml("generador.yaml")
    ctx = construir_contexto(inicio, fin, incluir_prospectivos)
    cl = generar_clientes(clientes, gen, np.random.default_rng([semilla, 0]), tabla_semilla)
    cl["lote"] = np.arange(len(cl)) // lote
    for sub in ("transacciones", "saldo_diario", "mensajes", "etiquetas_calidad", "panel_mensual"):
        os.makedirs(os.path.join(salida, sub), exist_ok=True)
    n_filas = 0
    for nl, cb in cl.groupby("lote"):
        cb = cb.reset_index(drop=True)
        rng = np.random.default_rng([semilla, 1 + int(nl)])
        res = simular_lote(cb, ctx, rng, gen["calidad"]["p_atipico"])
        tx = _tabla_transacciones(res.filas, cb, ctx, rng)
        tx = calidad.vestir_atipicos(tx, rng)
        tx = tx.sort_values(["cliente_idx", "fecha_hora"], kind="stable").reset_index(drop=True)
        tx["saldo"] = calidad.recalcular_saldo(tx, pd.Series(cb["saldo_inicial"].to_numpy(), index=cb["customer_id"]))
        tx["transaction_id"] = [f"T{int(nl) * 10_000_000 + i:010d}" for i in range(len(tx))]
        diario, ing_dia, saldo_cierre = _saldo_diario(tx, cb, ctx)
        panel = _panel_mensual(tx, diario, ctx)
        msg = texto.mensajes(cb, ctx, saldo_cierre, ing_dia, res.mult_ing, rng, gen["mensajes"]["tasa_dia"])
        sucio, etiquetas = calidad.sembrar_ruido(tx.drop(columns=["cliente_idx", "dia_idx"]), gen["calidad"], rng)
        cols = ["customer_id", "transaction_id", "fecha_hora", "monto", "moneda", "monto_pen", "tipo", "categoria", "comercio", "glosa", "canal",
                "saldo", "es_recurrente", "es_atipico", "es_suscripcion_duplicada"]
        sucio = _categorico(sucio[cols], ["customer_id", "moneda", "tipo", "categoria", "comercio", "canal"])
        nombre = f"lote_{int(nl):03d}.parquet"
        sucio.to_parquet(os.path.join(salida, "transacciones", nombre), index=False)
        _categorico(diario, ["customer_id"]).to_parquet(os.path.join(salida, "saldo_diario", nombre), index=False)
        _categorico(msg, ["customer_id", "sentimiento"]).to_parquet(os.path.join(salida, "mensajes", nombre), index=False)
        etiquetas.to_parquet(os.path.join(salida, "etiquetas_calidad", nombre), index=False)
        _categorico(panel, ["customer_id"]).to_parquet(os.path.join(salida, "panel_mensual", nombre), index=False)
        n_filas += len(sucio)
        if verbose:
            print(f"lote {int(nl) + 1}/{cl['lote'].nunique()}: {len(sucio):,} movimientos ({time.time() - t0:.0f}s)", flush=True)
    cl.to_parquet(os.path.join(salida, "clientes.parquet"), index=False)
    eventos, diario_ctx, macro = tabla_contexto(ctx)
    eventos.to_parquet(os.path.join(salida, "eventos.parquet"), index=False)
    diario_ctx.to_parquet(os.path.join(salida, "contexto_diario.parquet"), index=False)
    macro.to_parquet(os.path.join(salida, "macro_mensual.parquet"), index=False)
    huella = {}
    for nombre_y in ("generador.yaml", "eventos.yaml"):
        with open(os.path.join(DATA_PARAMETROS, nombre_y), "rb") as fh:
            huella[nombre_y] = hashlib.sha256(fh.read()).hexdigest()[:16]
    meta = {"semilla": semilla, "clientes": int(clientes), "inicio": inicio, "fin": fin, "lote": lote, "movimientos": int(n_filas),
            "segundos": round(time.time() - t0, 1), "python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
            "huella_parametros": huella, "incluye_prospectivos": incluir_prospectivos, "fuente_perfiles": "tabla externa" if tabla_semilla is not None else "parametrica"}
    with open(os.path.join(salida, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)
    return meta
