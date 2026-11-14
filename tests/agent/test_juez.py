import pytest

from agent import plantillas
from agent.juez import interpretar_numero, juzgar
from agent.tools import HerramientasMock

T = HerramientasMock()
PRONOSTICO = {"get_forecast": T.get_forecast("c-001")}


@pytest.mark.parametrize(
    "texto, valor",
    [
        ("1 680", 1680.0),
        ("1,680", 1680.0),
        ("1,680.50", 1680.5),
        ("1.680,50", 1680.5),
        ("85,5", 85.5),
        ("85.50", 85.5),
        ("0.25", 0.25),
        ("1 250 000", 1250000.0),
    ],
)
def test_interpreta_formatos_de_numero(texto, valor):
    assert interpretar_numero(texto)[0] == valor


@pytest.mark.parametrize("intencion", list(plantillas.TOOLS_POR_INTENCION))
def test_aprueba_cada_plantilla(intencion):
    llamadas = {
        "get_health": lambda: T.get_health("c-001"),
        "get_forecast": lambda: T.get_forecast("c-001"),
        "get_recos": lambda: T.get_recos("c-001"),
        "simulate": lambda: T.simulate("c-001", 150.0),
        "get_fx": T.get_fx,
    }
    datos = {n: llamadas[n]() for n in plantillas.TOOLS_POR_INTENCION[intencion]}
    exigir = intencion not in plantillas.INTENCIONES_SOLO_PLANTILLA
    assert juzgar(plantillas.responder(intencion, datos), datos, exigir_cifra=exigir).ok


@pytest.mark.parametrize("monto", [150.0, 500.0, 1200.0])
def test_aprueba_plantilla_de_simulacion(monto):
    datos = {"simulate": T.simulate("c-001", monto)}
    assert juzgar(plantillas.responder("simular", datos), datos).ok


def test_acepta_redondeo_a_la_decena_en_montos_grandes():
    datos = {"get_goals": {"projected_year_end_savings": 1683.2}}
    assert juzgar("En diciembre tendrías unos S/ 1 680.", datos).ok


def test_acepta_porcentaje_de_una_fraccion():
    assert juzgar("Ahorras el 25 % de tu ingreso.", {"tasa_ahorro": 0.25}).ok


def test_acepta_partes_de_una_fecha():
    assert juzgar("El miércoles 18/11 podrías quedar en rojo.", PRONOSTICO).ok


# Respuestas trampa: el LLM inventa, calcula o redondea de más.


def test_rechaza_cifra_inventada():
    v = juzgar("Te quedarían S/ 999 a fin de mes.", PRONOSTICO)
    assert not v.ok and v.cifras_no_verificadas == [999.0]


def test_rechaza_cifra_calculada_por_el_llm():
    # 210 - (-310) = 520 es una cuenta del LLM, no una salida de tool.
    assert not juzgar("Tu banda mide S/ 520.", PRONOSTICO).ok


def test_rechaza_redondeo_excesivo():
    assert not juzgar("Terminarías con S/ 500.", PRONOSTICO).ok


@pytest.mark.parametrize("escrito, ok", [(420, True), (418, False), (422, False)])
def test_solo_acepta_la_cifra_exacta_o_redondeada(escrito, ok):
    assert juzgar(f"Te quedarían S/ {escrito}.", {"saldo": 420.0}).ok is ok


@pytest.mark.parametrize("escrito, ok", [(1680, True), (1700, True), (1690, False)])
def test_redondeo_a_decena_o_centena_en_montos_grandes(escrito, ok):
    assert juzgar(f"Tendrías unos S/ {escrito}.", {"saldo": 1683.2}).ok is ok


def test_no_redondea_a_la_centena_un_monto_chico():
    assert not juzgar("Gastarías unos S/ 200.", {"gasto": 150.0}).ok


# El error más caro: decirle «estás bien» a quien se queda en rojo.


@pytest.mark.parametrize(
    "texto",
    [
        "En el peor caso terminas con S/ 310 a favor.",
        "En el peor caso tu saldo sería S/ 310.",
        "En el peor caso tendrías S/ 310, tranquilo.",
        "No quedarás en rojo, terminas con S/ 310.",
        "Sin quedar en rojo, tendrías S/ 310.",
        "No te faltará nada: tendrías S/ 310.",
        "Tendrías S/ 310, ni un sol de deuda.",
        "Tendrías por lo menos S/ 310.",
        "No quedarías en rojo por S/ 310.",
        "No vas a quedar en rojo por S/ 310.",
        "No creo que quedes en rojo por S/ 310.",
        "En ningún caso quedarías en rojo por S/ 310.",
        "No quedarías, en el peor caso, en rojo por S/ 310.",
        "Lejos de estar en rojo, tendrías S/ 310 de margen.",
    ],
)
def test_rechaza_saldo_negativo_presentado_como_positivo(texto):
    v = juzgar(texto, PRONOSTICO)
    assert not v.ok and 310.0 in v.cifras_no_verificadas


@pytest.mark.parametrize(
    "texto",
    [
        "En el peor caso quedarías en rojo por S/ 310.",
        "En el peor caso te faltarían S/ 310.",
        "En el peor caso tu saldo sería -S/ 310.",
        "Terminarías entre S/ 310 en rojo y S/ 210 a favor.",
        "Podrías quedar en rojo por S/ 310 o tener S/ 210 a favor.",
        "Quedarías S/ 310 abajo.",
        "Te quedarías corto por S/ 310.",
    ],
)
def test_acepta_saldo_negativo_dicho_como_rojo(texto):
    assert juzgar(texto, PRONOSTICO).ok


@pytest.mark.parametrize("texto", ["Terminarías con -S/ 210.", "Quedarías en rojo por S/ 210."])
def test_rechaza_saldo_positivo_escrito_como_negativo(texto):
    assert not juzgar(texto, PRONOSTICO).ok


def test_con_negacion_el_negativo_solo_vale_con_signo():
    assert juzgar("Si no recortas, tu saldo sería -S/ 310.", PRONOSTICO).ok


def test_la_marca_de_rojo_de_otra_frase_no_cuenta():
    texto = "Podrías quedar en rojo el 18. Igual terminas con S/ 310."
    assert not juzgar(texto, PRONOSTICO).ok


@pytest.mark.parametrize(
    "texto",
    [
        "Podrías sacar un préstamo de S/ 420.",
        "Pide un crédito para cubrirlo.",
        "Es un ahorro sin riesgo.",
        "Tendrías una ganancia segura.",
    ],
)
def test_rechaza_sugerir_credito_o_prometer(texto):
    assert juzgar(texto, {"saldo": 420.0}).frases_prohibidas


def test_mencionar_la_tarjeta_de_credito_no_es_sugerirla():
    assert not juzgar("Paga el total de tu tarjeta de crédito.", {}).frases_prohibidas


def test_rechaza_decimal_falso():
    assert not juzgar("Tu saldo final es S/ 420.70.", PRONOSTICO).ok


def test_rechaza_cifra_escondida_entre_cifras_validas():
    texto = "Terminarías entre S/ 180 y S/ 660, con S/ 45 de margen."
    v = juzgar(texto, PRONOSTICO)
    assert not v.ok and v.cifras_no_verificadas == [45.0]
    assert set(v.cifras_verificadas) == {180.0, 660.0}


def test_rechaza_cita_que_no_existe():
    texto = "La TCEA incluye todos los costos [fuente: sbs-3274-art-9]."
    v = juzgar(texto, {}, fuentes_validas={"sbs-3274-art-11"})
    assert not v.ok and v.citas_invalidas == ["sbs-3274-art-9"]


def test_aprueba_cita_valida_y_no_cuenta_sus_numeros_como_cifras():
    texto = "La TCEA incluye todos los costos [fuente: sbs-3274-art-11]."
    assert juzgar(texto, {}, fuentes_validas={"sbs-3274-art-11"}).ok


def test_numeracion_de_lista_no_cuenta_como_cifra():
    texto = "1. Revisa tus suscripciones: S/ 35.\n2) Baja el delivery: S/ 120."
    assert juzgar(texto, {"get_recos": T.get_recos("c-001")}).ok


def test_numero_a_mitad_de_linea_si_cuenta():
    assert not juzgar("Haz 2. cosas: S/ 35.", {"get_recos": T.get_recos("c-001")}).ok


def test_rechaza_dia_de_la_semana_equivocado():
    v = juzgar("El jueves 18 de noviembre podrías quedar en rojo.", PRONOSTICO)
    assert not v.ok and v.fechas_incorrectas == ["jueves 18"]


def test_acepta_dia_de_la_semana_correcto():
    assert juzgar("El miércoles 18 de noviembre podrías quedar en rojo.", PRONOSTICO).ok


def test_la_fecha_sola_no_cuenta_como_cifra_exigida():
    v = juzgar("El 18 de noviembre podrías quedar en rojo.", PRONOSTICO, exigir_cifra=True)
    assert not v.ok


# Trampas vistas con qwen2.5:3b real: cifras que existen, pero usadas como otra cosa.

SALUD = {"get_health": T.get_health("c-001")}


def test_rechaza_puntaje_presentado_como_soles():
    v = juzgar("Tu saldo es S/ 72.", SALUD)
    assert not v.ok and v.cifras_no_verificadas == [72.0]


def test_acepta_puntaje_sin_soles():
    assert juzgar("Tu salud está en 72 puntos.", SALUD).ok


def test_acepta_soles_escritos_despues_del_numero():
    assert juzgar("Tendrías -310.0 S/ como mínimo.", PRONOSTICO).ok


@pytest.mark.parametrize(
    "texto",
    [
        "Te conviene invertir en un colchón nuevo.",
        "Podrías comprar dólares ahora.",
        "Te transfiero el dinero.",
        "Tienes rentabilidad garantizada.",
    ],
)
def test_rechaza_frases_de_asesoria_u_operacion(texto):
    v = juzgar(texto, {})
    assert not v.ok and v.frases_prohibidas


def test_las_plantillas_pueden_negar_con_esas_palabras():
    texto = "No puedo decirte si comprar o vender dólares."
    assert juzgar(texto, {}, revisar_frases=False).ok


def test_texto_sin_cifras_se_aprueba_si_no_se_exigen():
    assert juzgar("Vas bien, sigue así.", PRONOSTICO).ok


def test_respuesta_vacia_de_cifras_se_rechaza_si_se_exigen():
    assert not juzgar("Tú decides.", PRONOSTICO, exigir_cifra=True).ok


def test_exigir_cifra_no_aplica_si_las_tools_no_traen_numeros():
    assert juzgar("Tu perfil es Gastador.", {"perfil": "Gastador"}, exigir_cifra=True).ok
