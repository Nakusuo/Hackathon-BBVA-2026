"""Tools de solo lectura del agente, con la forma del contrato `docs/api.md` (MG-01).

- `HerramientasAPI` (JF-03) llama a la API de Miguel. Cuando la API pase de mocks a los modelos
  de Diego (MG-06), el agente recibe datos reales sin cambiar nada aquí.
- `HerramientasMock` lee `data/sample/mocks/` para probar sin servidor.

El `customer_id` llega del estado del grafo (lo pone la API con la sesión), nunca del LLM.
Ninguna tool mueve dinero: `simulate` solo pide un escenario hipotético.
"""

import copy
import json
import os
from pathlib import Path
from typing import Protocol
from urllib.parse import quote

import httpx

RUTA_MOCKS = Path(__file__).resolve().parents[2] / "data" / "sample" / "mocks"
TIMEOUT_TOOLS_S = 5


class HerramientaNoDisponible(Exception):
    """La API no respondió o devolvió un error: el agente responde sin cifras."""


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


class HerramientasAPI:
    """Tools sobre la API REST del contrato (`LUCAS_API_URL`, por defecto localhost:8000)."""

    def __init__(self, base_url: str | None = None, cliente: httpx.Client | None = None):
        url = base_url or os.getenv("LUCAS_API_URL", "http://localhost:8000")
        self.cliente = cliente or httpx.Client(base_url=url, timeout=TIMEOUT_TOOLS_S)

    def _pedir(self, metodo: str, ruta: str, **kwargs) -> dict:
        try:
            respuesta = self.cliente.request(metodo, ruta, **kwargs)
            respuesta.raise_for_status()
            return respuesta.json()
        except (httpx.HTTPError, ValueError) as e:
            raise HerramientaNoDisponible(f"{metodo} {ruta}: {type(e).__name__}") from e

    def get_health(self, customer_id: str) -> dict:
        return self._pedir("GET", f"/api/v1/customers/{quote(customer_id, safe='')}/health")

    def get_forecast(self, customer_id: str) -> dict:
        return self._pedir("GET", f"/api/v1/customers/{quote(customer_id, safe='')}/forecast")

    def get_recos(self, customer_id: str) -> dict:
        return self._pedir(
            "GET", f"/api/v1/customers/{quote(customer_id, safe='')}/recommendations"
        )

    def simulate(self, customer_id: str, monto_gasto: float) -> dict:
        pedido = pedido_simulacion(customer_id, monto_gasto)
        respuesta = self._pedir("POST", "/api/v1/simulations", json=pedido)
        # La respuesta del contrato no repite lo pedido; se agrega para que el juez acepte
        # el monto que el usuario preguntó (la tool devuelve también sus entradas).
        return {**respuesta, "request": pedido}

    def get_fx(self) -> dict:
        return self._pedir("GET", "/api/v1/fx")
