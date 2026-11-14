"""Datos vivos: los movimientos que entran al aplicativo despues del ultimo cierre de datos del cliente (un ingreso, un gasto, un sueldo, una gratificacion).
El aplicativo manda cada movimiento con su monto y, si tiene, la categoria o la glosa; Lucas lo guarda y el agente lo suma a lo que ya sabia del cliente.

Reglas de seguridad y de calidad:
  * Se valida todo: tipo, monto finito y positivo, fecha que no sea del futuro. Lo invalido se rechaza con un error claro, no se corrige en silencio.
  * Es idempotente: si el aplicativo reintenta con el mismo id, no se duplica el movimiento.
  * La glosa solo sirve para sugerir la categoria con el clasificador y NO se guarda (puede traer datos personales). Si el clasificador no esta seguro (confianza < 0.80)
    la categoria queda en 'otros': nunca se inventa un ingreso extraordinario.
  * El LLM nunca ve el detalle de los movimientos, solo los totales."""
import json
import os
import re
import threading
import uuid
from datetime import date, datetime, timedelta

import joblib

from src.comun import reloj
from src.comun.rutas import MODELOS, ruta

UMBRAL_GLOSA = 0.80
TIPOS = ("ingreso", "gasto")
CATS_INGRESO = frozenset({"sueldo", "gratificacion", "cts", "comision", "honorarios", "venta_diaria", "bono_estado", "retiro_afp", "ingreso_extra", "transferencia_recibida"})
CATS_GASTO = frozenset({"agua", "alimentos", "alquiler", "celular", "colegio", "compras", "cuota_prestamo", "delivery", "educacion", "internet", "luz", "ocio", "restaurantes", "retiro_efectivo",
                        "salud", "seguro", "snacks", "suscripcion", "transferencias_familiares", "transporte", "pago_credito_informal", "ahorro_programado"})
ID_VALIDO = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
MAX_MONTO = 5_000_000.0
_LOCK = threading.Lock()
_CLASIFICADOR = None


def carpeta() -> str:
    return os.environ.get("LUCAS_VIVO_DIR") or ruta("data", "generado", "vivo")


def _archivo() -> str:
    return os.path.join(carpeta(), "movimientos.jsonl")


def _clasificador():
    global _CLASIFICADOR
    if _CLASIFICADOR is None:
        _CLASIFICADOR = joblib.load(os.path.join(MODELOS, "glosa.pkl"))["modelo"]
    return _CLASIFICADOR


def clasificar_glosa(glosa: str, tipo: str) -> tuple[str, float]:
    """Sugiere la categoria de una glosa. Devuelve ('otros', confianza) si no esta seguro o si la categoria no corresponde al tipo."""
    from src.models.clasificacion import normalizar
    try:
        m = _clasificador()
        p = m.predict_proba([normalizar(glosa)])[0]
    except Exception:  # sin modelo no se categoriza: el movimiento entra igual como 'otros'
        return "otros", 0.0
    i = int(p.argmax())
    cat, conf = str(m.classes_[i]), float(p[i])
    permitidas = CATS_INGRESO if tipo == "ingreso" else CATS_GASTO
    return (cat, conf) if conf >= UMBRAL_GLOSA and cat in permitidas else ("otros", conf)


def _fecha(valor) -> datetime:
    if valor is None:
        return datetime.combine(reloj.hoy(), datetime.now().time().replace(microsecond=0))
    if isinstance(valor, datetime):
        return valor.replace(tzinfo=None)
    if isinstance(valor, date):
        return datetime.combine(valor, datetime.min.time().replace(hour=12))
    try:
        return datetime.fromisoformat(str(valor)).replace(tzinfo=None)
    except ValueError as e:
        raise ValueError(f"fecha invalida: {valor!r}") from e


def _leer() -> list[dict]:
    try:
        with open(_archivo(), encoding="utf-8") as f:
            lineas = f.readlines()
    except OSError:
        return []
    out = []
    for ln in lineas:
        try:
            out.append(json.loads(ln))
        except ValueError:
            continue  # una linea danada no tumba al resto
    return out


def registrar(cid: str, tipo: str, monto: float, categoria: str | None = None, fecha=None, glosa: str | None = None, id_mov: str | None = None) -> dict:
    """Guarda un movimiento y devuelve el registro. Lanza ValueError si algo es invalido. Con el mismo id_mov devuelve el original (duplicado=True)."""
    if not isinstance(cid, str) or not ID_VALIDO.match(cid):
        raise ValueError("customer_id invalido")
    if tipo not in TIPOS:
        raise ValueError(f"tipo invalido: {tipo!r} (debe ser 'ingreso' o 'gasto')")
    if isinstance(monto, bool):   # float(True) seria 1.0: un booleano no es un monto
        raise ValueError("monto invalido")
    try:
        monto = float(monto)
    except (TypeError, ValueError) as e:
        raise ValueError("monto invalido") from e
    if not (0 < monto <= MAX_MONTO) or monto != monto:
        raise ValueError(f"monto fuera de rango: {monto}")
    f = _fecha(fecha)
    if f.date() > reloj.hoy() + timedelta(days=1):
        raise ValueError("el movimiento tiene fecha futura")
    if id_mov is not None and not ID_VALIDO.match(str(id_mov)):
        raise ValueError("id de movimiento invalido")
    permitidas = CATS_INGRESO if tipo == "ingreso" else CATS_GASTO
    if categoria:
        cat, origen, conf = (categoria.strip().lower(), "app", 1.0) if categoria.strip().lower() in permitidas else ("otros", "categoria_desconocida", 0.0)
    elif glosa:
        cat, conf = clasificar_glosa(glosa, tipo)
        origen = "modelo" if cat != "otros" else "sin_clasificar"
    else:
        cat, origen, conf = "otros", "sin_clasificar", 0.0
    with _LOCK:
        if id_mov:
            previo = next((m for m in _leer() if m.get("id") == str(id_mov) and m.get("customer_id") == cid), None)
            if previo:
                return {**previo, "duplicado": True}
        reg = {"id": str(id_mov) if id_mov else uuid.uuid4().hex[:12], "customer_id": cid, "tipo": tipo, "monto": round(monto, 2), "categoria": cat, "origen_categoria": origen,
               "confianza_categoria": round(conf, 3), "fecha": f.isoformat(timespec="seconds"), "registrado_en": datetime.now().isoformat(timespec="seconds")}
        os.makedirs(carpeta(), exist_ok=True)
        with open(_archivo(), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(reg, ensure_ascii=False) + "\n")
    return {**reg, "duplicado": False}


def listar(cid: str, despues_de: date | None = None, hasta: date | None = None) -> list[dict]:
    """Movimientos del cliente con fecha > despues_de y <= hasta (ambos opcionales), del mas antiguo al mas reciente."""
    out = []
    for m in _leer():
        if m.get("customer_id") != cid:
            continue
        d = datetime.fromisoformat(m["fecha"]).date()
        if (despues_de is None or d > despues_de) and (hasta is None or d <= hasta):
            out.append(m)
    return sorted(out, key=lambda m: m["fecha"])


def resumen(cid: str, despues_de: date, hasta: date) -> dict:
    """Totales de lo que entro despues del ultimo cierre de datos. Es lo unico que ve el agente (nunca el detalle ni la glosa)."""
    mov = listar(cid, despues_de, hasta)
    ing = [m for m in mov if m["tipo"] == "ingreso"]
    gas = [m for m in mov if m["tipo"] == "gasto"]

    def por_cat(L):
        d: dict[str, float] = {}
        for m in L:
            d[m["categoria"]] = round(d.get(m["categoria"], 0.0) + m["monto"], 2)
        return dict(sorted(d.items(), key=lambda kv: kv[1], reverse=True)[:3])
    ultimo = mov[-1] if mov else None
    return {"n": len(mov), "desde": (despues_de + timedelta(days=1)).isoformat(), "hasta": hasta.isoformat(), "ingresos": round(sum(m["monto"] for m in ing), 2), "gastos": round(sum(m["monto"] for m in gas), 2),
            "neto": round(sum(m["monto"] for m in ing) - sum(m["monto"] for m in gas), 2), "ingresos_por_categoria": por_cat(ing), "gastos_por_categoria": por_cat(gas),
            "ultimo": {k: ultimo[k] for k in ("tipo", "monto", "categoria", "fecha", "id")} if ultimo else None}


def borrar(cid: str) -> int:
    """Derecho de supresion: elimina todos los movimientos vivos del cliente. Devuelve cuantos borro."""
    with _LOCK:
        todos = _leer()
        quedan = [m for m in todos if m.get("customer_id") != cid]
        if len(quedan) == len(todos):
            return 0
        with open(_archivo(), "w", encoding="utf-8") as fh:
            for m in quedan:
                fh.write(json.dumps(m, ensure_ascii=False) + "\n")
    return len(todos) - len(quedan)
