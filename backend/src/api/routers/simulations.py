
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException

from src.api.schemas.simulations import (
    SimulationRequest,
    SimulationResponse,
)


router = APIRouter(
    prefix="/api/v1",
    tags=["Simulations"]
)


@router.post(
    "/simulations",
    response_model=SimulationResponse
)
def create_simulation(request: SimulationRequest):
    if request.customer_id != "demo-001":
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    # Datos sintéticos para validar el contrato MG-01.
    # No se utiliza todavía el modelo de pronóstico real.
    initial_balance = 1500.0
    daily_expense = 10.0

    baseline_forecast = []
    simulated_forecast = []

    baseline_negative_days = 0
    simulated_negative_days = 0

    today = date.today()

    for day in range(1, request.horizon_days + 1):
        current_date = today + timedelta(days=day)

        baseline_balance = initial_balance - daily_expense * day

        # Aplicar cambios hipotéticos acumulados.
        simulated_adjustment = 0.0

        for change in request.changes:
            sign = 1 if change.type == "income" else -1

            if change.frequency == "once":
                simulated_adjustment += sign * change.amount

            elif change.frequency == "monthly":
                occurrences = 1 + (day - 1) // 30
                simulated_adjustment += (
                    sign * change.amount * occurrences
                )

        simulated_balance = (
            baseline_balance + simulated_adjustment
        )

        baseline_forecast.append({
            "date": current_date,
            "predicted_balance": round(baseline_balance, 2)
        })

        simulated_forecast.append({
            "date": current_date,
            "predicted_balance": round(simulated_balance, 2)
        })

        if baseline_balance < 0:
            baseline_negative_days += 1

        if simulated_balance < 0:
            simulated_negative_days += 1

    baseline_final = baseline_forecast[-1]["predicted_balance"]
    simulated_final = simulated_forecast[-1]["predicted_balance"]

    return {
        "customer_id": request.customer_id,
        "currency": "PEN",
        "horizon_days": request.horizon_days,
        "baseline": {
            "final_balance": baseline_final,
            "negative_balance_days": baseline_negative_days,
            "forecast": baseline_forecast
        },
        "simulated": {
            "final_balance": simulated_final,
            "negative_balance_days": simulated_negative_days,
            "forecast": simulated_forecast
        },
        "difference": round(
            simulated_final - baseline_final, 2
        ),
        "disclaimer": (
            "Esta es una simulación con datos sintéticos, "
            "no una predicción garantizada. Tú decides."
        )
    }
