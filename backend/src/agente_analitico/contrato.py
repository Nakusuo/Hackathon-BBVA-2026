"""Respuesta con la forma del contrato de la API de Miguel para GET /api/v1/customers/{customer_id}/forecast.
La serie diaria sale del modelo entrenado y validado (models/serie_diaria.pkl); aqui solo se le da forma de contrato. Quien integre la API puede llamar
a pronostico_contrato() desde la ruta y devolver el dict tal cual."""
from datetime import timedelta

from src.agente_analitico import datos_vivos as DV
from src.agente_analitico.repositorio import VENTANA_RECALCULO_DIAS
from src.comun import reloj
from src.models import pronostico as P

MODELO_ID = "lightgbm-cuantil-conformal-serie-diaria-v1"
NIVEL_CONFIANZA = 0.8
UMBRAL_RIESGO = 0.15   # misma regla que usa el agente: solo se avisa de un dia de riesgo si la probabilidad de quedar en rojo es al menos 15 %


class HorizonteInvalido(ValueError):
    pass


def pronostico_contrato(repo, cid: str, dias: int = P.H, hoy=None) -> dict:
    """Pronostico diario con banda al 80 %. 'dias' es el parametro opcional del contrato (1 a 30, por defecto 30).
    Los datos del cliente son sinteticos y la respuesta lo dice (synthetic_data). Si faltan los modelos devuelve None."""
    if isinstance(dias, bool) or not isinstance(dias, int) or not 1 <= dias <= P.H:
        raise HorizonteInvalido(f"days debe ser un entero entre 1 y {P.H}")
    hoy = hoy or reloj.hoy()
    base = repo.fecha.date()
    vivo = DV.resumen(cid, base, max(hoy, base))
    desfase = (hoy - base).days
    neto = vivo["neto"] if (vivo["n"] > 0 and vivo["neto"] != 0 and 0 <= desfase <= VENTANA_RECALCULO_DIAS) else 0.0   # misma regla que Repositorio.contexto
    s = repo.serie_diaria(cid, neto, dias)
    if s is None:
        return None
    fila = repo.origen[repo.origen["cliente_idx"] == repo.pos[cid]].index[0]
    pr = repo._pronostico(fila, neto)
    primer_riesgo = None
    if pr["dia_riesgo"] is not None and int(pr["dia_riesgo"]) <= dias:
        primer_riesgo = str(base + timedelta(days=int(pr["dia_riesgo"])))
    serie = [{"date": str(base + timedelta(days=i + 1)), "predicted_balance": round(s["esperado"][i], 2), "lower_bound": round(s["bajo"][i], 2), "upper_bound": round(s["alto"][i], 2)}
             for i in range(s["dias"])]
    return {"customer_id": cid, "currency": "PEN", "horizon_days": s["dias"], "confidence_level": NIVEL_CONFIANZA, "forecast": serie, "first_risk_date": primer_riesgo,
            "model": MODELO_ID, "data_as_of": str(base), "risk_probability": round(pr["p_rojo"], 3), "synthetic_data": True, "sample_only": False}
