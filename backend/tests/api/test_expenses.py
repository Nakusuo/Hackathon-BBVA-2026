import json
import os
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from src.agente_analitico import datos_vivos
from src.api.agente import cliente_de_la_base
from src.api.main import app
from src.comun import reloj
from src.comun.rutas import MODELOS, ruta

client = TestClient(app)

BASE_URL = "/api/v1/customers"


@pytest.fixture(autouse=True)
def carpeta_temporal(tmp_path, monkeypatch):
    """Los gastos se guardan en una carpeta temporal, nunca en data/generado/vivo."""
    monkeypatch.setenv("LUCAS_VIVO_DIR", str(tmp_path))
    return tmp_path


def lineas_guardadas(carpeta):
    archivo = carpeta / "movimientos.jsonl"
    if not archivo.exists():
        return []
    return [json.loads(linea) for linea in archivo.read_text(encoding="utf-8").splitlines()]


def valid_expense():
    return {
        "amount": 45.90,
        "currency": "PEN",
        "category": "alimentos",
        "description": "Almuerzo",
        "date": str(reloj.hoy()),
    }


def test_create_expense_success(carpeta_temporal):
    response = client.post(f"{BASE_URL}/demo-001/expenses", json=valid_expense())

    assert response.status_code == 201

    data = response.json()

    assert data["customer_id"] == "demo-001"
    assert Decimal(str(data["amount"])) == Decimal("45.90")
    assert data["currency"] == "PEN"
    assert data["category"] == "alimentos"
    assert data["date"] == str(reloj.hoy())
    assert data["duplicate"] is False

    [guardado] = lineas_guardadas(carpeta_temporal)
    assert guardado["id"] == data["id"]
    assert guardado["customer_id"] == "C00016"
    assert guardado["tipo"] == "gasto"
    assert guardado["monto"] == 45.9


def test_create_expense_no_guarda_la_descripcion(carpeta_temporal):
    response = client.post(f"{BASE_URL}/demo-001/expenses", json=valid_expense())

    assert response.json()["description"] is None
    assert "Almuerzo" not in (carpeta_temporal / "movimientos.jsonl").read_text(encoding="utf-8")


def test_create_expense_timestamp():
    response = client.post(f"{BASE_URL}/demo-001/expenses", json=valid_expense())

    assert response.status_code == 201

    created_at = datetime.fromisoformat(response.json()["created_at"])

    assert created_at.tzinfo is not None


def test_mismo_id_no_duplica(carpeta_temporal):
    payload = {**valid_expense(), "id": "gasto-abc"}

    primero = client.post(f"{BASE_URL}/demo-001/expenses", json=payload)
    segundo = client.post(f"{BASE_URL}/demo-001/expenses", json=payload)

    assert primero.status_code == 201
    assert primero.json()["duplicate"] is False
    assert segundo.status_code == 200
    assert segundo.json()["duplicate"] is True
    assert segundo.json()["id"] == primero.json()["id"] == "gasto-abc"
    assert len(lineas_guardadas(carpeta_temporal)) == 1


def test_sin_id_cada_envio_es_un_gasto_distinto(carpeta_temporal):
    first = client.post(f"{BASE_URL}/demo-001/expenses", json=valid_expense())
    second = client.post(f"{BASE_URL}/demo-001/expenses", json=valid_expense())

    assert first.json()["id"] != second.json()["id"]
    assert len(lineas_guardadas(carpeta_temporal)) == 2


def test_categoria_desconocida_queda_en_otros():
    payload = {**valid_expense(), "category": "inventada"}

    assert client.post(f"{BASE_URL}/demo-001/expenses", json=payload).json()["category"] == "otros"


@pytest.mark.parametrize("amount", [0, -50])
def test_create_expense_invalid_amount(amount, carpeta_temporal):
    payload = {**valid_expense(), "amount": amount}

    response = client.post(f"{BASE_URL}/demo-001/expenses", json=payload)

    assert response.status_code == 422
    assert lineas_guardadas(carpeta_temporal) == []


def test_monto_fuera_de_rango_da_422(carpeta_temporal):
    payload = {**valid_expense(), "amount": datos_vivos.MAX_MONTO + 1}

    assert client.post(f"{BASE_URL}/demo-001/expenses", json=payload).status_code == 422
    assert lineas_guardadas(carpeta_temporal) == []


def test_fecha_futura_da_422(carpeta_temporal):
    payload = {**valid_expense(), "date": str(reloj.hoy() + timedelta(days=3))}

    response = client.post(f"{BASE_URL}/demo-001/expenses", json=payload)

    assert response.status_code == 422
    assert lineas_guardadas(carpeta_temporal) == []


def test_id_invalido_da_422():
    payload = {**valid_expense(), "id": "con espacios"}

    assert client.post(f"{BASE_URL}/demo-001/expenses", json=payload).status_code == 422


def test_create_expense_invalid_currency():
    payload = {**valid_expense(), "currency": "USD"}

    assert client.post(f"{BASE_URL}/demo-001/expenses", json=payload).status_code == 422


def test_create_expense_invalid_date():
    payload = {**valid_expense(), "date": "fecha-invalida"}

    assert client.post(f"{BASE_URL}/demo-001/expenses", json=payload).status_code == 422


def test_create_expense_empty_category():
    payload = {**valid_expense(), "category": ""}

    assert client.post(f"{BASE_URL}/demo-001/expenses", json=payload).status_code == 422


def test_create_expense_optional_description():
    payload = valid_expense()
    payload.pop("description")

    assert client.post(f"{BASE_URL}/demo-001/expenses", json=payload).status_code == 201


def test_create_expense_not_found(carpeta_temporal):
    response = client.post(f"{BASE_URL}/demo-999/expenses", json=valid_expense())

    assert response.status_code == 404
    assert response.json()["detail"] == "Cliente no encontrado"
    assert lineas_guardadas(carpeta_temporal) == []


@pytest.mark.skipif(
    not (
        os.path.isdir(ruta("data", "generado", "saldo_diario"))
        and os.path.exists(os.path.join(MODELOS, "serie_diaria.pkl"))
    ),
    reason="faltan los datos generados o el modelo de serie diaria",
)
def test_un_gasto_grande_baja_el_saldo_del_pronostico(monkeypatch):
    # El /forecast de demo-001 sale del motor del front; el gasto se guarda en su cliente de la base, que es el que mueve el modelo.
    real = cliente_de_la_base("demo-001")
    # Con la fecha real el cierre de datos ya es muy viejo y el pronóstico ignora los movimientos vivos: se fija un "hoy" cercano al cierre.
    base = date.fromisoformat(client.get(f"{BASE_URL}/{real}/forecast?days=1").json()["data_as_of"])
    monkeypatch.setenv("LUCAS_HOY", str(base + timedelta(days=5)))
    antes = client.get(f"{BASE_URL}/{real}/forecast?days=30").json()
    assert antes["sample_only"] is False

    payload = {**valid_expense(), "amount": 800, "date": str(base + timedelta(days=3))}
    assert client.post(f"{BASE_URL}/demo-001/expenses", json=payload).status_code == 201

    despues = client.get(f"{BASE_URL}/{real}/forecast?days=30").json()
    assert despues["forecast"][0]["predicted_balance"] < antes["forecast"][0]["predicted_balance"]
