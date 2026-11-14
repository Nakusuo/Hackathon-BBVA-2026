"""Datos no estructurados: glosas de movimientos y mensajes del usuario con sentimiento ligado al estres financiero real."""
import unicodedata

import numpy as np
import pandas as pd

from src.generador import catalogo as K

NOMBRES = ["JUAN P.", "MARIA L.", "CARLOS R.", "ROSA M.", "LUIS A.", "ANA C.", "PEDRO S.", "LUCIA V.", "JORGE T.", "CARMEN D.",
           "MIGUEL H.", "SOFIA G.", "DANIEL F.", "ELENA B.", "RAUL Q.", "PATRICIA N.", "VICTOR Z.", "GLORIA K.", "OSCAR W.", "FLOR Y."]
PREFIJO = {"yape": "YAPE", "plin": "PLIN", "tarjeta_debito": "COMPRA POS", "tarjeta_credito": "CONSUMO TC", "transferencia": "TRANSF",
           "debito_automatico": "DEB AUT", "cajero": "RETIRO ATM", "deposito_efectivo": "DEP EFECTIVO"}
PLANILLA = {"sueldo": "ABONO REMUNERACION", "gratificacion": "ABONO GRATIFICACION", "comision": "ABONO COMISIONES"}


def _sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def glosas(cat: np.ndarray, canal: np.ndarray, com: np.ndarray, ing: np.ndarray, rng: np.random.Generator, p_ruido: float = 0.35) -> np.ndarray:
    cat_n = np.array(K.NOMBRES_CAT)[cat]
    pref = np.array([PREFIJO[c] for c in K.CANALES])[canal]
    com_n = np.char.upper(K.NOMBRES_COMERCIO[com].astype(str))
    base = np.char.add(np.char.add(pref.astype(str), " "), com_n)
    p2p = np.isin(cat_n, ["transferencias_familiares", "transferencia_recibida"])
    if p2p.any():
        nombres = rng.choice(NOMBRES, int(p2p.sum()))
        base[p2p] = np.char.add(np.char.add(pref[p2p].astype(str), np.where(ing[p2p], " DE ", " A ")), nombres)
    for cat_pl, texto in PLANILLA.items():
        m = cat_n == cat_pl
        if m.any():
            base[m] = np.char.add(texto + " ", com_n[m])
    base = base.astype(object)
    ruido = np.flatnonzero(rng.random(len(base)) < p_ruido)
    variante = rng.integers(0, 5, len(ruido))
    for i, v in zip(ruido, variante):
        s = base[i]
        base[i] = (_sin_tildes(s) if v == 0 else s[:22] if v == 1 else f"{s} *{rng.integers(1000, 9999)}" if v == 2 else s.lower() if v == 3 else s.replace(" ", "  "))
    return base


PLANTILLAS = {
    "positivo": ["Ya cobré, por fin llego tranquilo a fin de mes", "Pude apartar algo este mes, buen avance", "Me pagaron a tiempo y todo quedó en orden",
                 "Este mes salí con plata de sobra para mi meta", "Cancelé una suscripción que no usaba y ahorré", "Cerré bien la quincena, gracias",
                 "Por fin saldé la cuota atrasada", "Hoy tengo colchón para cualquier imprevisto", "Me entró un pago grande, ya me alcanza para el alquiler",
                 "Voy cumpliendo mi plan de ahorro", "Gasté menos en delivery y se nota", "Estoy más ordenado con mis gastos"],
    "neutro": ["¿Cuánto gasté este mes en comida?", "Quiero revisar mis movimientos de la semana", "¿Cuándo vence mi próxima cuota?",
               "¿Qué suscripciones tengo activas?", "Muéstrame mis gastos fijos", "¿Cuánto me queda disponible hoy?",
               "¿Cómo va mi ahorro del año?", "Necesito ver cuánto pago de servicios", "¿Cuánto cobré el mes pasado?",
               "Quiero comparar este mes con el anterior", "¿Qué es la TCEA de un préstamo?", "¿Cómo se calcula mi puntaje de salud?"],
    "preocupado": ["No sé si me alcanza para el alquiler este mes", "Me da miedo quedarme sin plata antes de cobrar", "Estoy justo, ¿qué puedo recortar?",
                   "Se me acumularon las cuotas y no sé cómo llego", "Mi cliente no me ha pagado todavía y vence el recibo", "Creo que me voy a pasar de mi presupuesto",
                   "Los precios subieron y ya no me rinde el sueldo", "Tengo que pagar el colegio y no me alcanza", "¿Llego a fin de mes con estos gastos?",
                   "Este mes vendí poco y me preocupa", "Se me juntaron varios pagos la misma semana", "Estoy gastando más de lo que gano"],
    "negativo": ["Estoy en rojo otra vez y no veo salida", "No me alcanza para nada, me siento ahogado", "Otra vez pidiendo prestado para llegar a fin de mes",
                 "Me quedé sin plata y todavía faltan días para cobrar", "Estoy harto, siempre llego con el agua al cuello", "No pude pagar la cuota y me van a cobrar mora",
                 "Debo plata a todos y no sé qué hacer", "Se acabó la plata y tengo que seguir comprando comida", "Perdí clientes y ya no cubro mis gastos",
                 "Siento que nunca voy a salir de las deudas", "Me atrasé con el alquiler", "Esto ya no se sostiene"],
}
POR_EVENTO = {
    "covid_confinamiento": ["Con la cuarentena no puedo salir a trabajar", "No hay ventas por el aislamiento", "Me suspendieron el sueldo por la pandemia"],
    "covid_reapertura": ["Recién estoy retomando mis ventas pero aún es poco", "Todavía no se recupera mi trabajo después de la cuarentena"],
    "covid_segunda_ola": ["Con la segunda ola volvieron las restricciones y vendo menos", "Otra vez restricciones y bajaron mis ingresos"],
    "protestas_2022_2023": ["Con los bloqueos no llega la mercadería", "No puedo trabajar por los paros"],
    "nino_costero_2023": ["Las lluvias me dejaron sin clientes", "Con el huaico se paró todo en mi zona y subió la comida"],
}


def mensajes(cl: pd.DataFrame, ctx, saldo_cierre: np.ndarray, ing_dia: np.ndarray, mult_ing: np.ndarray, rng: np.random.Generator, tasa_dia: float,
             props=(0.25, 0.38, 0.22, 0.15)) -> pd.DataFrame:
    B, D = saldo_cierre.shape
    ing_obs = (cl["ingreso_base"] * (1 - cl["fraccion_efectivo"])).to_numpy()
    n = rng.poisson(tasa_dia, (B, D))
    bi, di = np.nonzero(n)
    reps = n[bi, di]
    bi, di = np.repeat(bi, reps), np.repeat(di, reps)
    rojo = (saldo_cierre < 0).astype(np.int32)
    acum = np.concatenate([np.zeros((B, 1), np.int32), np.cumsum(rojo, axis=1)], axis=1)
    rojo_30 = (acum[bi, di + 1] - acum[bi, np.maximum(di - 29, 0)]) > 0
    ing_acum = np.concatenate([np.zeros((B, 1)), np.cumsum(ing_dia > 0, axis=1)], axis=1)
    pago_3 = (ing_acum[bi, di + 1] - ing_acum[bi, np.maximum(di - 2, 0)]) > 0
    saldo_rel = saldo_cierre[bi, di] / ing_obs[bi]
    shock = np.clip(1 - mult_ing[bi, di], 0, 1)
    tension = ((cl["gasto_ratio"].to_numpy() - 0.9) / 0.15)[bi]
    score = (1.6 * rojo_30 + 1.2 * np.clip(-saldo_rel, 0, 2) + 2.0 * shock + 0.9 * (saldo_rel < 0.4) + 0.8 * tension
             - 0.8 * np.clip(saldo_rel, 0, 3) / 3 - 0.5 * pago_3 + rng.normal(0, 0.8, len(bi)))
    # Las clases se asignan por cuantiles del puntaje de estres: reparto balanceado y la senal de estres se conserva.
    cortes = np.quantile(score, np.cumsum(props)[:-1])
    etiqueta = np.array(["positivo", "neutro", "preocupado", "negativo"], dtype=object)[np.searchsorted(cortes, score)]
    textos = np.empty(len(bi), dtype=object)
    for et, lista in PLANTILLAS.items():
        m = etiqueta == et
        textos[m] = rng.choice(lista, int(m.sum()))
    # en un evento activo, parte de los mensajes inquietos lo menciona
    fuerza = ctx.fuerza[:, di]
    for k, ev in enumerate(ctx.eventos):
        frases = POR_EVENTO.get(ev["id"])
        if not frases:
            continue
        m = (fuerza[k] > 0.3) & np.isin(etiqueta, ["preocupado", "negativo"]) & (rng.random(len(bi)) < 0.5)
        if m.any():
            textos[m] = rng.choice(frases, int(m.sum()))
    fecha = ctx.fechas[di] + pd.to_timedelta(rng.integers(7 * 3600, 23 * 3600, len(bi)), unit="s")
    return pd.DataFrame({"customer_id": cl["customer_id"].to_numpy()[bi], "fecha_hora": fecha, "texto": textos, "sentimiento": etiqueta})
