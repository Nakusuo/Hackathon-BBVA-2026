"""Prompt de sistema fijo y armado del mensaje. Cualquier cambio se anota en PROMPTS.md."""

import json

VERSION_PROMPT = "redaccion-v3"

# Sin cifras de ejemplo: con v2 el modelo copiaba las del ejemplo de formato como si fueran datos.
SISTEMA = """Eres Lucas, un compañero que ayuda a trabajadores en Perú con su plata del mes.
Redactas una respuesta corta (máximo 4 frases) a partir de DATOS que ya calcularon nuestros modelos.

Reglas que no rompes:
1. Menciona los montos clave de DATOS copiados tal cual. No calcules, no sumes, no restes ni inventes cifras.
2. Pon «S/» delante de cada monto en soles. Escribe las fechas con el número del día y el mes, sin el día de la semana.
3. Háblale de tú al usuario («tu saldo», «te conviene»). Sin tono alarmista.
4. No des asesoría: nunca digas que compre o venda dólares, que invierta en algo ni prometas rentabilidad.
5. No ofrezcas hacer operaciones ni mover dinero. No numeres listas.
6. Termina con: «Es una simulación para orientarte, no una asesoría. Tú decides.»"""

# Claves que nunca salen hacia un LLM, ni siquiera local: así el contenido es igual en todos
# los proveedores y se puede probar una sola vez (ISO 27001, control 8.12).
CLAVES_PRIVADAS = {"customer_id"}


def datos_para_llm(datos):
    """Copia de las salidas de las tools sin identificadores."""
    if isinstance(datos, dict):
        return {k: datos_para_llm(v) for k, v in datos.items() if k not in CLAVES_PRIVADAS}
    if isinstance(datos, list):
        return [datos_para_llm(v) for v in datos]
    return datos


def resumen_para_llm(intencion: str, datos: dict) -> dict:
    """Solo los campos que responden la pregunta, con nombres claros. Nada se calcula aquí.

    Con la serie completa el modelo mezclaba cifras reales de días distintos («entre S/ 420
    y S/ 980») y el juez no podía notarlo. El juez valida contra este mismo resumen.
    """
    if intencion == "pronostico":
        f = datos["get_forecast"]
        ultimo = f["forecast"][-1]
        return {
            "fecha_final": ultimo["date"],
            "saldo_previsto_final": ultimo["predicted_balance"],
            "saldo_minimo_probable": ultimo["lower_bound"],
            "saldo_maximo_probable": ultimo["upper_bound"],
            "confianza": f["confidence_level"],
            "primer_dia_en_rojo": f.get("first_risk_date"),
        }
    if intencion == "simular":
        s = datos["simulate"]
        return {
            "gasto_consultado": s["request"]["changes"][0]["amount"],
            "saldo_final_sin_el_gasto": s["baseline"]["final_balance"],
            "saldo_final_con_el_gasto": s["simulated"]["final_balance"],
        }
    if intencion == "salud":
        h = datos["get_health"]
        return {
            # «colchón» confundía al 3b: lo leyó como el mueble y sugirió comprar uno.
            "puntaje_de_salud_sobre_100": h["score"],
            "estado": h["status"],
            "meses_que_cubre_tu_ahorro_de_emergencia": h["emergency_fund_months"],
        }
    if intencion == "recos":
        return {
            "recomendaciones": [
                {
                    "accion": r["action"],
                    "impacto_mensual_soles": r["estimated_impact"],
                    "tipo": "gasto que evitas"
                    if r.get("impact_type") == "expense_reduction"
                    else "plata que apartas",
                    "confianza": r["confidence"],
                }
                for r in datos["get_recos"]["recommendations"]
            ]
        }
    return datos_para_llm(datos)


def mensajes(intencion: str, datos: dict) -> list[tuple[str, str]]:
    """El texto del usuario no se envía: el LLM recibe la intención ya clasificada y los datos."""
    cuerpo = json.dumps(resumen_para_llm(intencion, datos), ensure_ascii=False, indent=1)
    return [
        ("system", SISTEMA),
        ("human", f"Intención: {intencion}\nDATOS:\n{cuerpo}"),
    ]
