"""Contexto de un cliente a una fecha: lo que ven las herramientas del agente. Solo lectura."""
import os

from datetime import date

import joblib
import pandas as pd

from src.agente_analitico import datos_vivos as DV
from src.agente_analitico import memoria
from src.comun import reloj
from src.comun.rutas import DATA_GENERADO, MODELOS
from src.models import calendario_laboral as CL
from src.models import clasificacion as KL
from src.models import datos, niveles as N, ofertas as O, pronostico as P, pronostico_mensual as PM, salud as SA, segmentacion as S

VENTANA_RECALCULO_DIAS = 45   # el riesgo a 30 dias solo se reestima con los movimientos vivos si el cierre de datos no es muy viejo


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
        gr = tx[tx["categoria"].astype(str) == "gratificacion"].sort_values("fecha_hora")
        self.ultima_gratificacion = gr.groupby("customer_id")["monto_pen"].last().to_dict()   # una gratificacion equivale a una remuneracion: la mejor base para estimar CTS y la proxima
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

    def _pronostico(self, fila: int, neto_vivo: float = 0.0) -> dict:
        """Pronostico a 30 dias. Con movimientos vivos se vuelve a puntuar el modelo con el saldo corregido (se mueve el saldo y su escala relativa)."""
        pr = self.pred.loc[fila]
        if neto_vivo:
            x = self.origen.loc[[fila]].copy()
            x["saldo_t"] = x["saldo_t"] + neto_vivo
            x["saldo_rel"] = x["saldo_t"] / x["escala"]
            pr = self.pron["modelo"].predecir(x).iloc[0]
        return {"saldo_esperado": float(pr["saldo_esperado"]), "saldo_bajo": float(pr["saldo_bajo"]), "saldo_alto": float(pr["saldo_alto"]), "p_rojo": float(pr["p_rojo"]),
                "dia_riesgo": float(pr["dia_riesgo"]) if pr["p_rojo"] >= 0.15 else None, "ancho_rel": float(pr["ancho_rel"])}

    def contexto(self, cid: str, hoy: date | None = None) -> dict:
        """Todo lo que el agente sabe de un cliente. 'hoy' viene del reloj unico; los datos del cliente llegan hasta fecha_datos y lo que entro despues (datos vivos) se suma aparte."""
        hoy = hoy or reloj.hoy()
        f = self.features.loc[cid]
        seg = int(self.etiqueta_seg[cid])
        salud = float(self.salud[cid])
        nivel = N.nivel_individual(self.seg["niveles"][seg], salud)
        fila = self.origen[self.origen["cliente_idx"] == self.pos[cid]].index[0]
        cl = self.clientes.loc[cid]
        fecha_datos = self.fecha.date()
        desfase = (hoy - fecha_datos).days
        vivo = DV.resumen(cid, fecha_datos, max(hoy, fecha_datos))
        reestimar = vivo["n"] > 0 and vivo["neto"] != 0 and 0 <= desfase <= VENTANA_RECALCULO_DIAS
        saldo_base = float(self.origen.loc[fila, "saldo_t"])
        ult = self.ultima_gratificacion.get(cid)
        base_lab, origen_base = (float(ult), "historial") if ult else (float(f["ingreso_medio"]), "ingreso_medio")
        return {
            "customer_id": cid, "fecha": str(fecha_datos), "hoy": str(hoy), "fecha_datos": str(fecha_datos), "desfase_datos_dias": desfase, "segmento": seg, "nivel": nivel, "salud": round(salud, 1),
            "aviso_datos": (f"Los movimientos del cliente llegan hasta el {CL.texto_fecha(fecha_datos)} (demostracion con datos sinteticos); lo que entro despues se suma aparte." if desfase > VENTANA_RECALCULO_DIAS else None),
            "features": {k: float(f[k]) for k in S.NUMERICAS}, "departamento": cl["departamento"], "tipo_trabajo": cl["tipo_trabajo"], "tcea": float(cl["tcea_promedio"]),
            "deuda": float(cl["deuda_total"]), "saldo_base": saldo_base, "saldo_actual": saldo_base + vivo["neto"], "movimientos_vivos": vivo,
            "pronostico": self._pronostico(fila, vivo["neto"] if reestimar else 0.0), "pronostico_reestimado": reestimar,
            "calendario": CL.calendario(hoy, cl["tipo_trabajo"], base_lab, origen_base),
            "paga_en_usd": bool(cl["paga_en_usd"]), "top_categorias": [x for x in self.top_cat.get(cid, []) if x in ("alimentos", "transporte", "salud", "educacion", "hormiga")][:2],
            "ahorro_redondeo_mensual": round(float(self.redondeo.get(cid, 0.0)), 0), "duplicadas": cid in self.duplicadas, "monto_duplicada": float(self.monto_dup.get(cid, 30.0)),
            "memoria": memoria.cargar(cid),
        }
