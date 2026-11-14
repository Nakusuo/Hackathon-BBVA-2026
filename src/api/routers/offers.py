
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

    # Perfil sintético para el MVP.
    # No representa un análisis financiero real.
    emergency_fund_months = 1.5
    has_expensive_debt = False

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

    # Una oferta de ahorro a plazo solo sería elegible
    # con un colchón de al menos tres meses
    # y sin deuda cara.
    if (
        emergency_fund_months >= 3
        and not has_expensive_debt
    ):
        offers.append({
            "id": "offer-003",
            "name": "Ahorro a plazo referencial",
            "category": "term_savings",
            "description": (
                "Producto ficticio de ahorro a plazo "
                "para evaluar alternativas financieras."
            ),
            "reason": (
                "El perfil simulado cumple las "
                "condiciones mínimas de seguridad."
            ),
            "estimated_benefit": "0.00",
            "eligible": True,
            "disclaimer": (
                "No garantiza rentabilidad ni "
                "representa una oferta comercial real."
            )
        })

    return {
        "customer_id": customer_id,
        "currency": "PEN",
        "offers": offers
    }
