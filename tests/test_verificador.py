"""Juez determinista de cifras: lo que acepta, lo que rechaza y los casos ambiguos de formato (miles frente a decimales), que son el origen tipico de falsos positivos."""
import pytest

from src.agente_analitico.verificador import numeros_de, verificar


def test_una_cifra_que_sale_de_las_herramientas_pasa_y_una_inventada_no():
    assert verificar("Tu saldo sera S/ 4,137.97.", {4137.97})["ok"]
    v = verificar("Tu saldo sera S/ 9,999.", {4137.97})
    assert not v["ok"] and v["cifras_sin_respaldo"] == [9999.0]


@pytest.mark.parametrize("texto,permitido", [("El tipo de cambio es S/ 3.406", 3.406), ("Bajo S/ 0.005 frente a ayer", 0.005), ("Son S/ 3.406 en total", 3406.0), ("Hay 1,500 clientes", 1500.0), ("Son 1.500 clientes", 1500.0)])
def test_un_numero_ambiguo_entre_miles_y_decimal_se_acepta_si_cualquiera_de_sus_lecturas_tiene_respaldo(texto, permitido):
    assert verificar(texto, {permitido})["ok"]


@pytest.mark.parametrize("texto", ["El tipo de cambio es S/ 3.406", "Bajo S/ 0.005", "Hay 1,500 clientes"])
def test_pero_sin_respaldo_en_ninguna_lectura_se_rechaza(texto):
    assert not verificar(texto, {99.0})["ok"]


def test_los_numeros_inequivocos_no_cambian_de_lectura():
    assert numeros_de("S/ 4,137.97 y 28 % y 2.5 meses") == [4137.97, 28.0, 2.5]


def test_las_frases_prohibidas_se_detectan_aunque_las_cifras_esten_bien():
    for frase in ("Te recomiendo comprar dolares ahora", "Te recomiendo vender dolares ya", "Resultado garantizado", "```print(1)```", "import os"):
        v = verificar(frase, set())
        assert v["prohibidos"], frase
    assert not verificar("Es solo un dato de referencia, no una recomendacion de operar con dolares.", set())["prohibidos"]
