"""Ofertas y recomendaciones por perfil: consumir mejor, ahorrar, invertir (educación y simulación), pedir un crédito o una tarjeta.
Cada oferta pasa por reglas de idoneidad que se explican; si no pasa, se dice por que y se propone el paso previo. Catalogo ficticio y generico."""
import numpy as np

from src.models import recomendador as R

CATEGORIAS_BENEFICIO = {
    "alimentos": "descuento en bodegas y mercados afiliados de tu zona", "transporte": "descuento en combustible y movilidad afiliada", "salud": "descuento en farmacias y consultas afiliadas",
    "educacion": "descuento en utiles y cursos afiliados", "hormiga": "alternativas más baratas a tus gastos pequenos de delivery y antojos",
}
TASA_DEMO_PLAZO_PP = 1.0   # supuesto visible: tasa pasiva demo = tasa de referencia del BCRP - 1 punto; nunca una promesa


def _meses_de_ingreso(f: dict, x: float) -> float:
    return x / max(f["ingreso_medio"], 1.0)


def _es_independiente(c: dict) -> bool:
    return c.get("tipo_trabajo") in ("independiente", "mixto")


def ofertas_por_perfil(c: dict, top_categorias: list | None = None) -> list[dict]:
    """Devuelve ofertas con su necesidad detectada, idoneidad y razones. No decide por el usuario."""
    f, pr = c["features"], c.get("pronostico", {})
    p_rojo = float(pr.get("p_rojo", 0.0))
    ingreso = f["ingreso_medio"]
    indep = _es_independiente(c)
    colchon_meta = 4.5 if indep else 3.0
    tasa_ref = float(c.get("tasa_ref", 4.5))
    deuda_cara = c.get("tcea", 0) > R.TCEA_DEUDA_CARA and c.get("deuda", 0) > 0
    sal = []

    for cat in (top_categorias or [])[:2]:
        if cat in CATEGORIAS_BENEFICIO:
            sal.append({"id": f"beneficio_{cat}", "familia": "consumir", "accion": f"Aprovecha un {CATEGORIAS_BENEFICIO[cat]}: es donde más gastas.", "impacto_soles": None, "urgencia": 0.3, "facilidad": 0.9,
                        "por_que": [f"{cat} está entre tus categorias de mayor gasto"], "supuestos": ["beneficio del catálogo ficticio; no te pide gastar más"], "confianza": "media", "idoneo": True})

    if f["ahorro_pct"] < 0.05 or f["colchon_observado"] < colchon_meta:
        faltan = max(colchon_meta - f["colchon_observado"], 0) * ingreso
        sal.append({"id": "ahorro_apartados", "familia": "ahorrar", "accion": f"Abre un apartado para tu colchón y aporta de a poco: tu meta es llegar a {colchon_meta:.1f} meses de ingreso.",
                    "impacto_soles": round(faltan, 0), "urgencia": 0.55, "facilidad": 0.6, "tipo_producto": "cuenta con apartados para una meta de ahorro",
                    "por_que": [f"hoy tu colchón alcanza para {f['colchon_observado']:.1f} meses", "los ingresos variables piden más colchón" if indep else "lo recomendado es tener entre 3 y 6 meses"], "supuestos": ["meta de colchón según tu tipo de trabajo"],
                    "confianza": "media", "idoneo": True, "puntos": "aporte_a_meta_de_ahorro"})
        redondeo = c.get("ahorro_redondeo_mensual")
        if redondeo:
            sal.append({"id": "ahorro_redondeo", "familia": "ahorrar", "accion": f"Activa el ahorro por redondeo: cada gasto se sube al sol siguiente y la diferencia va a tu apartado, unos S/ {redondeo:,.0f} al mes.",
                        "impacto_soles": round(redondeo * 12, 0), "urgencia": 0.35, "facilidad": 0.95, "por_que": ["se calcula sobre tus movimientos reales"], "supuestos": ["se mantiene tu cantidad de gastos"], "confianza": "alta", "idoneo": True})

    ok_inv = f["colchon_observado"] >= colchon_meta and not deuda_cara and f["ahorro_pct"] >= 0.10 and f["dias_rojo_3m"] == 0
    if ok_inv:
        tasa = max(tasa_ref - TASA_DEMO_PLAZO_PP, 0.1)
        ejemplo = 1000.0 * (1 + tasa / 100 * 6 / 12)
        sal.append({"id": "inversion_plazo_educativa", "familia": "invertir", "accion": f"Ya tienes colchón: aprende como funciona un depósito a plazo. Con una tasa de demostración de {tasa:.2f}% anual, S/ 1000 a 6 meses serían S/ {ejemplo:,.0f}.",
                    "impacto_soles": None, "urgencia": 0.3, "facilidad": 0.7, "tipo_producto": "depósito a plazo fijo", "por_que": ["tu colchón ya cubre la meta", "no tienes deuda cara"],
                    "supuestos": [f"tasa de demostración = tasa de referencia del BCRP ({tasa_ref:.2f}%) menos {TASA_DEMO_PLAZO_PP:.0f} punto", "es una simulación educativa, no una promesa de rentabilidad ni una recomendación de invertir"], "confianza": "media", "idoneo": True})

    # credito de capital de trabajo para independientes con base solida
    if indep:
        monto = round(min(max(ingreso * 1.5, 1500.0), 8000.0), -2)
        tea = (tasa_ref + 14.0) / 100
        cuota = R.cuota_mensual(monto, tea, 12)
        ok, razones = R.idoneo_para_credito(f, p_rojo, cuota)
        oferta = {"id": "credito_capital_de_trabajo", "familia": "credito", "accion": f"Podrias pedir un crédito de capital de trabajo de unos S/ {monto:,.0f} a 12 meses (cuota estimada S/ {cuota:,.0f}) para tu negocio.",
                  "impacto_soles": None, "urgencia": 0.4, "facilidad": 0.4, "tipo_producto": "crédito de capital de trabajo", "por_que": ["tu ingreso es independiente y un capital puede ayudarte a crecer"] if ok else razones,
                  "supuestos": [f"tasa efectiva anual de {tea:.1%} (tasa de referencia del BCRP + margen supuesto)", "simulación; no es una oferta real"], "confianza": "media", "idoneo": ok}
        if not ok:
            oferta.update({"accion": "Aún no te conviene un crédito de capital de trabajo; primero fortalece tu caja.", "razones_no_idoneo": razones})
        sal.append(oferta)

    # tarjeta de credito basica: solo con historial limpio y colchon
    sin_credito = c.get("deuda", 0) == 0
    if sin_credito and ingreso >= 1500:
        ok, razones = R.idoneo_para_credito(f, p_rojo)
        t = {"id": "tarjeta_linea_basica", "familia": "tarjeta", "accion": "Podrias pedir una tarjeta con línea baja para construir tu historial.", "impacto_soles": None, "urgencia": 0.25, "facilidad": 0.5,
             "tipo_producto": "tarjeta de crédito con línea básica", "por_que": ["no tienes deudas y tu caja esta ordenada"] if ok else razones, "supuestos": ["simulación; no es una oferta real"], "confianza": "media", "idoneo": ok}
        if not ok:
            t.update({"accion": "Aún no es buen momento para una tarjeta; cuida tu caja y vuelve a mirarlo.", "razones_no_idoneo": razones})
        sal.append(t)

    # deuda cara: comparar y ordenar antes que endeudarse mas
    if deuda_cara:
        sal.append({"id": "ordenar_deuda_cara", "familia": "credito", "accion": f"Tu deuda cuesta {c['tcea']:.0%} al año: compara el costo total y prioriza pagarla antes de tomar otra.",
                    "impacto_soles": None, "urgencia": 0.7, "facilidad": 0.5, "por_que": ["tu tasa supera el 45 % anual"], "supuestos": ["comparación educativa, no una oferta"], "confianza": "media", "idoneo": True})
    if c.get("paga_en_usd"):
        sal.append({"id": "pago_en_dolares", "familia": "ahorrar", "accion": "Tienes un pago fijo en dólares: separa cada mes la parte que necesitaras para no depender del tipo de cambio del día.", "impacto_soles": None, "urgencia": 0.5, "facilidad": 0.7,
                    "por_que": ["uno de tus pagos fijos es en dólares"], "supuestos": ["no es una recomendación de comprar ni vender dólares: solo ordenar un pago propio"], "confianza": "media", "idoneo": True})
    return sal


def ahorro_por_redondeo(montos_gasto: np.ndarray, meses: float) -> float:
    """Cuanto se apartaria por mes subiendo cada gasto al sol siguiente. Sale de movimientos reales."""
    montos = np.asarray(montos_gasto, dtype=float)
    return float((np.ceil(montos) - montos).sum() / max(meses, 1.0))


def necesidad_cubierta(recos_ids: list[str]) -> dict:
    """Que necesidad sembrada cubre cada oferta o recomendación: sirve para medir precision@3."""
    mapa = {"pago_usd": {"pago_en_dolares"}, "deuda_cara": {"ordenar_deuda_cara", "comparar_tasas"}, "ingreso_irregular": {"sueldo_lucas"}}
    return {n: bool(set(recos_ids) & ids) for n, ids in mapa.items()}
