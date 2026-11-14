"""Tools de solo lectura del agente, con la forma del contrato `docs/api.md` (MG-01).

`HerramientasMock` responde con los mocks de `data/sample/mocks/` para probar el grafo antes
de que exista la API (MG-03). JF-03 agrega la versión que llama a la API real con el rol
`lucas_agente`. Ninguna tool mueve dinero.
"""

import copy
import json
from pathlib import Path
from typing import Protocol

RUTA_MOCKS = Path(__file__).resolve().parents[2] / "data" / "sample" / "mocks"


class Herramientas(Protocol):
    def get_health(self, customer_id: str) -> dict: ...
    def get_forecast(self, customer_id: str) -> dict: ...
    def get_recos(self, customer_id: str) -> dict: ...
    def simulate(self, customer_id: str, monto_gasto: float) -> dict: ...
    def get_fx(self) -> dict: ...


def pedido_simulacion(customer_id: str, monto_gasto: float) -> dict:
    """Cuerpo de `POST /api/v1/simulations` para un gasto único."""
    return {
        "customer_id": customer_id,
        "horizon_days": 30,
        "changes": [
            {
                "type": "expense",
                "amount": monto_gasto,
                "frequency": "once",
                "description": "Gasto consultado en el chat",
            }
        ],
    }


class HerramientasMock:
    def __init__(self, ruta: Path = RUTA_MOCKS):
        self.ruta = ruta

    def _mock(self, nombre: str, customer_id: str | None = None) -> dict:
        datos = json.loads((self.ruta / f"{nombre}.json").read_text(encoding="utf-8"))
        if customer_id is not None:
            datos["customer_id"] = customer_id
        return datos

    def get_health(self, customer_id: str) -> dict:
        return self._mock("health", customer_id)

    def get_forecast(self, customer_id: str) -> dict:
        return self._mock("forecast", customer_id)

    def get_recos(self, customer_id: str) -> dict:
        return self._mock("recommendations", customer_id)

    def simulate(self, customer_id: str, monto_gasto: float) -> dict:
        # El mock de Miguel trae un escenario fijo; aquí se arma uno coherente con el monto
        # preguntado, partiendo del último día del pronóstico mock. Lo reemplaza MG-07.
        pronostico = self.get_forecast(customer_id)["forecast"]
        base = pronostico[-1]["predicted_balance"]
        final = round(base - monto_gasto, 2)
        dias_rojo_base = sum(d["predicted_balance"] < 0 for d in pronostico)
        respuesta = copy.deepcopy(self._mock("simulation", customer_id))
        respuesta["request"] = pedido_simulacion(customer_id, monto_gasto)
        respuesta["baseline"] = {"final_balance": base, "negative_balance_days": dias_rojo_base}
        respuesta["simulated"] = {
            "final_balance": final,
            "negative_balance_days": dias_rojo_base + (1 if final < 0 <= base else 0),
        }
        respuesta["difference"] = round(final - base, 2)
        return respuesta

    def get_fx(self) -> dict:
        return self._mock("fx")
