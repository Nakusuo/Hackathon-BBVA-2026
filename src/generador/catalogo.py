"""Catalogo de categorias, comercios ficticios y canales. Ningun nombre corresponde a una marca real."""
import numpy as np

SEGMENTOS = ["formal_quincena", "base_comision", "independiente_diario", "independiente_proyectos", "mixto"]
ARQUETIPO_DE_SEGMENTO = {
    "formal_quincena": "formal_quincena", "base_comision": "base_comision", "independiente_diario": "independiente",
    "independiente_proyectos": "independiente", "mixto": "mixto",
}
REGIONES = ["lima", "norte", "sur", "centro", "oriente"]
CANALES = ["yape", "plin", "tarjeta_debito", "tarjeta_credito", "transferencia", "debito_automatico", "cajero", "deposito_efectivo"]
DIAS_SEMANA_UNO = [1.0] * 7

# Categorias variables: tasa = transacciones por dia, peso = parte del presupuesto variable, sigma = dispersion del monto (log).
VARIABLES = [
    dict(nombre="alimentos", tasa=0.55, peso=0.28, sigma=0.55, hormiga=False, mucho=1.0,
         canales={"yape": .35, "plin": .10, "tarjeta_debito": .35, "tarjeta_credito": .20},
         comercios=["Bodega Dona Marta", "Minimarket Los Andes", "Mercado Central Puesto 14", "SuperMaxi", "Bodega El Sol", "Frutas y Verduras Rosa"],
         estacion=[1, 1, 1, 1, 1.05, 1, 1.05, 1.05, 1, 1, 1.05, 1.2], dow=[1, .95, .95, 1, 1.1, 1.25, .9]),
    dict(nombre="transporte", tasa=0.35, peso=0.13, sigma=0.50, hormiga=False, mucho=1.0,
         canales={"yape": .45, "plin": .15, "tarjeta_debito": .25, "tarjeta_credito": .15},
         comercios=["TaxiYa", "Gasolinera PetroNorte", "Estacionamiento Plaza", "MotoRapida", "Peaje Ruta Sur"],
         estacion=[1] * 12, dow=[1.25, 1.2, 1.2, 1.2, 1.1, .7, .5]),
    dict(nombre="delivery", tasa=0.10, peso=0.06, sigma=0.45, hormiga=True, mucho=2.0,
         canales={"tarjeta_credito": .45, "tarjeta_debito": .25, "yape": .30},
         comercios=["RapiFood", "ComidaExpress", "PizzaYa", "PollosYa Delivery"],
         estacion=[1, 1, 1, 1, 1, 1, 1.05, 1, 1, 1, 1, 1.15], dow=[.8, .8, .85, .9, 1.2, 1.4, 1.3]),
    dict(nombre="restaurantes", tasa=0.10, peso=0.06, sigma=0.55, hormiga=False, mucho=1.8,
         canales={"tarjeta_credito": .35, "tarjeta_debito": .30, "yape": .35},
         comercios=["Cevicheria El Muelle", "Pollos La Brasa", "Restaurante Sabor Criollo", "Chifa Dragon Rojo"],
         estacion=[1, 1, 1, 1, 1.2, 1, 1.15, 1, 1, 1, 1, 1.25], dow=[.6, .6, .7, .8, 1.3, 1.7, 1.5]),
    dict(nombre="snacks", tasa=0.25, peso=0.03, sigma=0.40, hormiga=True, mucho=1.8,
         canales={"yape": .55, "plin": .15, "tarjeta_debito": .30},
         comercios=["Kiosko 24h", "Cafe Aroma", "Panaderia Dulce Pan", "Heladeria Polar"],
         estacion=[1.1, 1.1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], dow=[1, 1, 1, 1, 1.1, 1.2, 1.1]),
    dict(nombre="ocio", tasa=0.06, peso=0.06, sigma=0.60, hormiga=False, mucho=2.0,
         canales={"tarjeta_credito": .40, "tarjeta_debito": .25, "yape": .35},
         comercios=["CineMas", "Karaoke Estrella", "Parque de Juegos Alegria", "Entradas Show Lima"],
         estacion=[1, 1, 1, 1.05, 1, 1, 1.3, 1.1, 1, 1, 1, 1.3], dow=[.5, .5, .6, .8, 1.4, 1.8, 1.5]),
    dict(nombre="compras", tasa=0.05, peso=0.09, sigma=0.75, hormiga=False, mucho=2.0,
         canales={"tarjeta_credito": .50, "tarjeta_debito": .30, "yape": .20},
         comercios=["TiendaModa", "ElectroHogar", "Zapateria Paso Firme", "TecnoMarket", "Muebleria Casa Bella"],
         estacion=[1, .95, 1.05, 1, 1.35, 1, 1.1, 1, 1, 1, 1.35, 1.5], dow=[.8, .8, .9, .9, 1.1, 1.5, 1.3]),
    dict(nombre="salud", tasa=0.03, peso=0.06, sigma=0.70, hormiga=False, mucho=1.0,
         canales={"tarjeta_debito": .35, "yape": .35, "tarjeta_credito": .30},
         comercios=["Farmacia SaludYa", "Clinica Vida", "Laboratorio Analiza", "Botica Cercana"],
         estacion=[1] * 12, dow=DIAS_SEMANA_UNO),
    dict(nombre="educacion", tasa=0.02, peso=0.05, sigma=0.55, hormiga=False, mucho=1.0,
         canales={"transferencia": .35, "tarjeta_debito": .30, "yape": .35},
         comercios=["Academia Futuro", "Libreria Escolar Saber", "Instituto Tecnico Norte"],
         estacion=[1.3, 1.5, 2.6, 1.1, 1, 1, 1, 1, 1, 1, 1, 1], dow=DIAS_SEMANA_UNO),
    dict(nombre="transferencias_familiares", tasa=0.07, peso=0.08, sigma=0.60, hormiga=False, mucho=1.0,
         canales={"yape": .65, "plin": .25, "transferencia": .10},
         comercios=["Transferencia personal"], estacion=[1, 1, 1, 1, 1.3, 1.1, 1, 1, 1, 1, 1, 1.2], dow=DIAS_SEMANA_UNO),
    dict(nombre="retiro_efectivo", tasa=0.06, peso=0.06, sigma=0.35, hormiga=False, mucho=1.0,
         canales={"cajero": 1.0}, comercios=["Cajero Automatico Centro", "Cajero Automatico Mercado", "Cajero Automatico Terminal"],
         estacion=[1] * 12, dow=[1, 1, 1, 1, 1.2, 1.2, .8]),
    dict(nombre="otros", tasa=0.05, peso=0.04, sigma=0.65, hormiga=False, mucho=1.0,
         canales={"yape": .4, "tarjeta_debito": .3, "tarjeta_credito": .3},
         comercios=["Ferreteria Constructor", "Lavanderia Limpia", "Servicios Varios SAC", "Imprenta Rapida"],
         estacion=[1] * 12, dow=DIAS_SEMANA_UNO),
]
N_VAR = len(VARIABLES)

# Compromisos fijos (una vez al mes) e ingresos. Se numeran a continuacion de las variables.
FIJAS = [
    ("alquiler", "fijo", ["Arrendador Particular"], "transferencia"),
    ("luz", "fijo", ["ElectroSur"], "debito_automatico"),
    ("agua", "fijo", ["AguaClara"], "debito_automatico"),
    ("internet", "fijo", ["FibraNet"], "debito_automatico"),
    ("celular", "fijo", ["CelularPlus"], "debito_automatico"),
    ("cuota_prestamo", "deuda", ["Banco Ejemplo"], "debito_automatico"),
    ("suscripcion", "fijo", ["StreamFlix", "MusicaPlus", "JuegaMas", "VideoMax", "NubeDoc"], "tarjeta_credito"),
    ("colegio", "fijo", ["Colegio Horizonte"], "transferencia"),
    ("seguro", "fijo", ["Seguros Ejemplo"], "debito_automatico"),
    ("ahorro_programado", "ahorro", ["Apartado de ahorro"], "transferencia"),
    ("pago_credito_informal", "deuda", ["Prestamista Particular"], "yape"),
    ("traspaso_ahorro", "ahorro", ["Apartado de ahorro"], "transferencia"),
]
INGRESOS = [
    ("sueldo", ["Comercial Los Andes SAC", "Servicios Norte SAC", "Distribuidora Pacifico SAC", "Constructora Sierra SAC", "Agroexport Valle SAC"], "transferencia"),
    ("gratificacion", ["Comercial Los Andes SAC", "Servicios Norte SAC", "Distribuidora Pacifico SAC"], "transferencia"),
    ("comision", ["Comercial Los Andes SAC", "Distribuidora Pacifico SAC"], "transferencia"),
    ("venta_diaria", ["Cliente Yape", "Cliente Plin", "Venta del dia"], "yape"),
    ("honorarios", ["Cliente Empresa A", "Cliente Empresa B", "Cliente Particular", "Estudio Contable Delta"], "transferencia"),
    ("ingreso_extra", ["Trabajo adicional", "Cliente Particular"], "yape"),
    ("bono_estado", ["Bono del Estado"], "transferencia"),
    ("retiro_afp", ["Retiro de fondos de pensiones"], "transferencia"),
    ("retiro_ahorro", ["Apartado de ahorro"], "transferencia"),
    ("prestamo_informal", ["Prestamista Particular"], "yape"),
    ("transferencia_recibida", ["Transferencia personal"], "yape"),
]

NOMBRES_CAT = [v["nombre"] for v in VARIABLES] + [f[0] for f in FIJAS] + [i[0] for i in INGRESOS]
ID_CAT = {n: i for i, n in enumerate(NOMBRES_CAT)}
ES_INGRESO = np.array([False] * (N_VAR + len(FIJAS)) + [True] * len(INGRESOS))
GRUPO_CAT = ([("hormiga" if v["hormiga"] else "variable") for v in VARIABLES] + [f[1] for f in FIJAS] + ["ingreso"] * len(INGRESOS))
RECURRENTES = {"alquiler", "luz", "agua", "internet", "celular", "cuota_prestamo", "suscripcion", "colegio", "seguro", "ahorro_programado"}
ES_RECURRENTE_CAT = np.array([n in RECURRENTES for n in NOMBRES_CAT])

# Comercios globales: indice unico por nombre para guardar enteros en las tablas internas.
_comercios = []
COMERCIOS_DE_CAT = {}
for _v in VARIABLES:
    COMERCIOS_DE_CAT[_v["nombre"]] = _v["comercios"]
for _f in FIJAS:
    COMERCIOS_DE_CAT[_f[0]] = _f[2]
for _i in INGRESOS:
    COMERCIOS_DE_CAT[_i[0]] = _i[1]
for _lista in COMERCIOS_DE_CAT.values():
    for _c in _lista:
        if _c not in _comercios:
            _comercios.append(_c)
NOMBRES_COMERCIO = np.array(_comercios, dtype=object)
ID_COMERCIO = {c: i for i, c in enumerate(_comercios)}

CANAL_FIJO_DE_CAT = {f[0]: f[3] for f in FIJAS} | {i[0]: i[2] for i in INGRESOS}
CANAL_ID = {c: i for i, c in enumerate(CANALES)}


def sortear_canal(cat_ids: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Canal (indice) segun la categoria: las variables usan su mezcla, el resto su canal fijo."""
    out = np.empty(len(cat_ids), dtype=np.int8)
    for cid in np.unique(cat_ids):
        m = cat_ids == cid
        if cid < N_VAR:
            canales = VARIABLES[cid]["canales"]
            nombres = list(canales)
            p = np.array([canales[c] for c in nombres], dtype=float)
            elegidos = rng.choice(len(nombres), size=int(m.sum()), p=p / p.sum())
            out[m] = np.array([CANAL_ID[n] for n in nombres], dtype=np.int8)[elegidos]
        else:
            out[m] = CANAL_ID[CANAL_FIJO_DE_CAT[NOMBRES_CAT[cid]]]
    return out
