import logging

from fastapi import APIRouter, HTTPException, Query

from src.api import persona_demo
from src.api.agente import ClienteDesconocido, obtener_agente
from src.api.schemas.forecast import ForecastResponse

log = logging.getLogger("lucas.api.forecast")

router = APIRouter(prefix="/api/v1/customers", tags=["Forecast"])


def _pronostico_real(customer_id: str, days: int) -> dict | None:
    """Pronóstico del modelo entrenado. None si faltan los modelos o los datos de esta máquina."""
    from src.agente_analitico.contrato import pronostico_contrato

    try:
        agente = obtener_agente()
        return pronostico_contrato(agente.repo, agente.cliente(customer_id), days)
    except ClienteDesconocido:
        raise
    except Exception:  # sin datos o modelos en esta máquina la ruta responde 404 en vez de caerse
        log.warning("Pronóstico real no disponible", exc_info=True)
        return None


@router.get("/{customer_id}/forecast", response_model=ForecastResponse)
def get_forecast(customer_id: str, days: int = Query(30, ge=1, le=30)):
    # La persona de la demo sale del motor del front; el modelo entrenado atiende a los clientes de la base.
    if customer_id == persona_demo.ID_DEMO:
        return persona_demo.pronostico(days)
    try:
        real = _pronostico_real(customer_id, days)
    except ClienteDesconocido:
        raise HTTPException(status_code=404, detail="Cliente no encontrado") from None

    if real is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {**real, "customer_id": customer_id}
