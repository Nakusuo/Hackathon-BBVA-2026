"""Contexto de un cliente a una fecha: lo que ven las herramientas del agente. Solo lectura."""
import os

import joblib
import pandas as pd

from src.agent import memoria
from src.comun.rutas import DATA_GENERADO, MODELOS
from src.models import clasificacion as KL
from src.models import datos, niveles as N, ofertas as O, pronostico as P, pronostico_mensual as PM, salud as SA, segmentacion as S


class Repositorio:
    def __init__(self, carpeta: str = DATA_GENERADO, fecha: str = "2025-11-29"):
        self.carpeta, self.fecha = carpeta, pd.Timestamp(fecha)
        self.series = datos.cargar_series(carpeta)
        self.clientes = datos.cargar_clientes(carpeta)
        self.contexto_diario = datos.cargar_contexto(carpeta)
        self.seg = joblib.load(os.path.join(MODELOS, "segmentacion.pkl"))
        self.pron = joblib.load(os.path.join(MODELOS, "pronostico.pkl"))
        hasta = self.fecha + pd.Timedelta(days=1)
        self.features = S.features_cliente(carpeta, str(hasta.date()))
        self.etiqueta_seg = pd.Series(S.asignar(self.seg, self.features), index=self.features.index)
        self.salud = SA.puntaje_salud(self.features)
        tx = datos.cargar_transacciones(carpeta, ["customer_id", "fecha_hora", "comercio", "monto_pen", "categoria", "tipo"], desde=self.fecha - pd.Timedelta(days=180), hasta=hasta)
        tx["comercio"] = tx["comercio"].astype(str)
        self.duplicadas = KL.detectar_suscripciones_duplicadas(tx.assign(tipo="gasto"))
        g = tx[tx["tipo"].astype(str) == "gasto"].copy()
        g["categoria"] = g["categoria"].astype(str).replace({"delivery": "hormiga", "snacks": "hormiga"})
        parte = g.groupby(["customer_id", "categoria"])["monto_pen"].sum().reset_index().sort_values("monto_pen", ascending=False)
        self.top_cat = {c: list(x["categoria"]) for c, x in parte.groupby("customer_id")}
        self.redondeo = g.groupby("customer_id")["monto_pen"].apply(lambda m: O.ahorro_por_redondeo(m.to_numpy(), 6.0)).to_dict()
        subs = tx[tx["comercio"].isin(KL.SUBS)].groupby("customer_id")["monto_pen"].median()
        self.monto_dup = subs.to_dict()
        t = int(self.series.fechas.searchsorted(self.fecha))
        seg_map = {i: int(self.etiqueta_seg.get(i, -1)) for i in self.series.ids}
        self.origen = P.construir_origenes(self.series, self.clientes, self.contexto_diario, seg_map, origenes_dias=[t])
        self.pos = {c: i for i, c in enumerate(self.series.ids)}
        self.pred = self.pron["modelo"].predecir(self.origen)
        self.seg_map = seg_map
        ruta_m = os.path.join(MODELOS, "pronostico_mensual.pkl")
        self.mensual = joblib.load(ruta_m) if os.path.isfile(ruta_m) else None
        self._filas_mensual = None

    def proyeccion_mensual(self, cid: str) -> list | None:
        """Ingresos, gastos y neto esperados de los proximos 6 meses, con rango al 80 %, desde el ultimo mes completo anterior a la fecha."""
        if self.mensual is None:
            return None
        if self._filas_mensual is None:
            A = PM.panel_arrays(self.carpeta)
            t = int(A["meses"].get_loc(pd.Period(self.fecha - pd.DateOffset(months=1), "M")))
            filas = PM.construir_filas(self.carpeta, self.clientes, self.seg_map, con_objetivo=False, origenes=[t])
            self._filas_mensual = (filas, self.mensual["modelo"].predecir(filas))
        filas, pred = self._filas_mensual
        idx = filas.index[filas["cliente_idx"] == self.pos[cid]]
        out = []
        for i in idx:
            r, p = filas.loc[i], pred.loc[i]
            out.append({"mes": r["mes_objetivo"], "ingreso_esperado": round(float(p["ing_esperado"]), 0), "ingreso_bajo": round(float(p["ing_bajo"]), 0), "ingreso_alto": round(float(p["ing_alto"]), 0),
                        "gasto_esperado": round(float(p["gas_esperado"]), 0), "gasto_bajo": round(float(p["gas_bajo"]), 0), "gasto_alto": round(float(p["gas_alto"]), 0),
                        "neto_esperado": round(float(p["net_esperado"]), 0), "neto_bajo": round(float(p["net_bajo"]), 0), "neto_alto": round(float(p["net_alto"]), 0)})
        return sorted(out, key=lambda x: x["mes"])

    def contexto(self, cid: str) -> dict:
        f = self.features.loc[cid]
        seg = int(self.etiqueta_seg[cid])
        salud = float(self.salud[cid])
        nivel = N.nivel_individual(self.seg["niveles"][seg], salud)
        fila = self.origen[self.origen["cliente_idx"] == self.pos[cid]].index[0]
        pr = self.pred.loc[fila]
        cl = self.clientes.loc[cid]
        return {
            "customer_id": cid, "fecha": str(self.fecha.date()), "hoy": str(self.fecha.date()), "segmento": seg, "nivel": nivel, "salud": round(salud, 1),
            "features": {k: float(f[k]) for k in S.NUMERICAS}, "departamento": cl["departamento"], "tipo_trabajo": cl["tipo_trabajo"], "tcea": float(cl["tcea_promedio"]),
            "deuda": float(cl["deuda_total"]), "saldo_actual": float(self.origen.loc[fila, "saldo_t"]),
            "pronostico": {"saldo_esperado": float(pr["saldo_esperado"]), "saldo_bajo": float(pr["saldo_bajo"]), "saldo_alto": float(pr["saldo_alto"]), "p_rojo": float(pr["p_rojo"]),
                           "dia_riesgo": float(pr["dia_riesgo"]) if pr["p_rojo"] >= 0.15 else None, "ancho_rel": float(pr["ancho_rel"])},
            "paga_en_usd": bool(cl["paga_en_usd"]), "top_categorias": [x for x in self.top_cat.get(cid, []) if x in ("alimentos", "transporte", "salud", "educacion", "hormiga")][:2],
            "ahorro_redondeo_mensual": round(float(self.redondeo.get(cid, 0.0)), 0), "duplicadas": cid in self.duplicadas, "monto_duplicada": float(self.monto_dup.get(cid, 30.0)),
            "memoria": memoria.cargar(cid),
        }
