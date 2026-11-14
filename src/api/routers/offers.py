
from fastapi import APIRouter, HTTPException

from src.api.schemas.offers import OffersResponse


router = APIRouter(
    prefix="/api/v1/customers",
    tags=["Financial Offers"]
)


@router.get(
    "/{customer_id}/offers",
    response_model=OffersResponse
)
def get_financial_offers(customer_id: str):
    if customer_id != "demo-001":
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    offers = [
        {
            "id": "offer-001",
            "name": "Plan de ahorro flexible",
            "category": "savings",
            "description": (
                "Alternativa ficticia para organizar "
                "ahorros periódicos sin comprometer "
                "el dinero por un plazo fijo."
            ),
            "reason": (
                "El cliente puede priorizar la "
                "construcción de su fondo de emergencia."
            ),
            "estimated_benefit": "0.00",
            "eligible": True,
            "disclaimer": (
                "Oferta ficticia con fines demostrativos. "
                "No representa un producto bancario real."
            )
        },
        {
            "id": "offer-002",
            "name": "Herramienta de control de gastos",
            "category": "financial_education",
            "description": (
                "Herramienta ficticia para identificar "
                "gastos y mejorar la planificación mensual."
            ),
            "reason": (
                "Ayuda a identificar oportunidades "
                "de ahorro sin asumir nuevas deudas."
            ),
            "estimated_benefit": "0.00",
            "eligible": True,
            "disclaimer": (
                "Beneficios no garantizados. "
                "Contenido únicamente informativo."
            )
        }
    ]

    return {
        "customer_id": customer_id,
        "currency": "PEN",
        "offers": offers
    }
