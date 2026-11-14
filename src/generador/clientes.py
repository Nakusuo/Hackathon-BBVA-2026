"""Perfiles de clientes: cuotas por estrato, bootstrap suavizado y pesos muestrales."""
import itertools

import numpy as np
import pandas as pd



def _cuotas_enteras(n: int, p: np.ndarray, piso: int) -> np.ndarray:
    """Reparte n unidades segun p, con un minimo por celda (metodo del resto mayor)."""
    cuentas = np.maximum(np.floor(n * p).astype(int), piso)
    while cuentas.sum() > n:
        sobrante = np.where(cuentas > piso, cuentas, -1)
        cuentas[np.argmax(sobrante)] -= 1
    while cuentas.sum() < n:
        cuentas[np.argmax(n * p - cuentas)] += 1
    return cuentas


def _asignar(m: int, valores: dict, rng: np.random.Generator) -> np.ndarray:
    """Asigna categorias a m unidades respetando las proporciones objetivo con error maximo de 1 unidad."""
    claves = list(valores)
    p = np.array([valores[k] for k in claves], dtype=float)
    cuentas = _cuotas_enteras(m, p / p.sum(), 0)
    arr = np.repeat(np.array(claves, dtype=object), cuentas)
    rng.shuffle(arr)
    return arr


def _uniforme(rng, rango, tam=None):
    return rng.uniform(rango[0], rango[1], tam)


def generar_clientes(n: int, gen: dict, rng: np.random.Generator, tabla_semilla: pd.DataFrame | None = None,
                     inicio_global: int = 1) -> pd.DataFrame:
    pob, comp = gen["poblacion"], gen["comportamiento"]
    arqs = pob["arquetipos"]

    # 1. Estratos arquetipo x ahorro x gasto con probabilidad objetivo y piso minimo.
    estratos, p_obj = [], []
    for a, cfg in arqs.items():
        for ah, ga in itertools.product(("ahorra", "no_ahorra"), ("gasta_poco", "gasta_mucho")):
            pa = cfg["p_ahorra"] if ah == "ahorra" else 1 - cfg["p_ahorra"]
            pg = cfg["p_gasta_mucho"] if ga == "gasta_mucho" else 1 - cfg["p_gasta_mucho"]
            estratos.append((a, ah, ga))
            p_obj.append(cfg["peso"] * pa * pg)
    p_obj = np.array(p_obj) / np.sum(p_obj)
    piso = max(1, int(np.ceil(gen["estratos"]["piso_por_estrato"] * n)))
    piso = min(piso, n // len(estratos)) if n >= len(estratos) else 0
    cuentas = _cuotas_enteras(n, p_obj, piso)

    filas = []
    for (a, ah, ga), c, p in zip(estratos, cuentas, p_obj):
        if c == 0:
            continue
        subtipos = (_asignar(c, {s: v["peso"] for s, v in arqs[a]["subtipos"].items()}, rng)
                    if "subtipos" in arqs[a] else np.array([""] * c, dtype=object))
        region = _asignar(c, pob["region"]["values"], rng)
        edad = _asignar(c, pob["edad"]["values"], rng)
        peso_muestral = p / (c / n)
        for j in range(c):
            filas.append((a, ah, ga, subtipos[j], region[j], edad[j], peso_muestral))
    cl = pd.DataFrame(filas, columns=["arquetipo", "perfil_ahorro_real", "perfil_gasto_real", "subtipo", "region", "rango_edad", "peso_muestral"])
    cl = cl.sample(frac=1.0, random_state=int(rng.integers(0, 2**31 - 1))).reset_index(drop=True)
    cl["segmento"] = np.where(cl["arquetipo"] == "independiente", "independiente_" + cl["subtipo"], cl["arquetipo"])
    N = len(cl)

    # 2. Ingreso por bootstrap suavizado de perfiles semilla.
    bs = gen["bootstrap_perfiles"]
    ingreso = np.zeros(N)
    for seg in cl["segmento"].unique():
        m = (cl["segmento"] == seg).to_numpy()
        if tabla_semilla is not None and (tabla_semilla["segmento"] == seg).any():
            semillas = tabla_semilla.loc[tabla_semilla["segmento"] == seg, "ingreso"].to_numpy()
        else:
            if seg.startswith("independiente_"):
                cfg = arqs["independiente"]["subtipos"][seg.split("_", 1)[1]]
            else:
                cfg = arqs[seg]
            semillas = rng.lognormal(np.log(cfg["mediana"]), cfg["sigma"], bs["n_semillas"])
        elegidos = semillas[rng.integers(0, len(semillas), m.sum())]
        ingreso[m] = elegidos * np.exp(rng.normal(0, bs["ancho_banda_log"], m.sum()))
    cl["ingreso_base"] = ingreso.round(2)

    # 3. Comportamiento y atributos del contrato de datos.
    cl["gasto_ratio"] = np.where(cl["perfil_gasto_real"] == "gasta_mucho", _uniforme(rng, comp["gasto_ratio"]["gasta_mucho"], N),
                                 _uniforme(rng, comp["gasto_ratio"]["gasta_poco"], N))
    cl["ahorro_tasa"] = np.where(cl["perfil_ahorro_real"] == "ahorra", _uniforme(rng, comp["ahorro_tasa"]["ahorra"], N),
                                 _uniforme(rng, comp["ahorro_tasa"]["no_ahorra"], N))
    cl["fraccion_efectivo"] = [rng.uniform(*comp["fraccion_efectivo"][s]) for s in cl["segmento"]]
    cl["traspaso_inflacion"] = [comp["traspaso_inflacion"][a] for a in cl["arquetipo"]]
    cl["planilla"] = np.where(cl["arquetipo"].isin(["formal_quincena", "base_comision"]), True,
                              np.where(cl["arquetipo"] == "mixto", rng.random(N) < 0.5, False))
    cl["tiene_alquiler"] = rng.random(N) < comp["prob_alquiler"]
    cl["alquiler_share"] = np.where(cl["tiene_alquiler"], _uniforme(rng, comp["alquiler_share"], N), 0.0)
    cl["tiene_deuda"] = rng.random(N) < comp["prob_deuda"]
    cl["cuota_share"] = np.where(cl["tiene_deuda"], _uniforme(rng, comp["cuota_share"], N), 0.0)
    cl["cuota_mensual"] = (cl["cuota_share"] * cl["ingreso_base"]).round(2)
    cl["n_creditos"] = np.where(cl["tiene_deuda"], rng.integers(1, 4, N), 0)
    cl["deuda_total"] = (cl["cuota_mensual"] * rng.integers(8, 48, N)).round(2)
    cl["tcea_promedio"] = np.where(cl["tiene_deuda"], rng.uniform(0.18, 0.65, N), 0.0).round(3)
    cl["paga_en_usd"] = rng.random(N) < comp["prob_usd"]
    edad_lam = cl["rango_edad"].map({"18-24": 0.2, "25-34": 0.8, "35-44": 1.6, "45-54": 1.4, "55+": 0.8}).to_numpy()
    cl["personas_a_cargo"] = np.minimum(rng.poisson(edad_lam), 5)
    cl["colchon_meses"] = np.clip(np.where(cl["perfil_ahorro_real"] == "ahorra", rng.lognormal(np.log(2.5), 0.6, N),
                                           rng.lognormal(np.log(0.35), 0.8, N)), 0, 12).round(2)
    cl["saldo_inicial"] = (cl["ingreso_base"] * (1 - cl["fraccion_efectivo"]) * rng.uniform(0.15, 0.9, N)).round(2)
    cl["ahorro_inicial"] = (cl["colchon_meses"] * cl["ingreso_base"] * 0.8).round(2)
    cl["meta_ahorro"] = np.where(rng.random(N) < 0.4, cl["ingreso_base"] * rng.uniform(1, 6, N), 0.0).round(0)
    cl["antiguedad_cliente_meses"] = rng.integers(3, 120, N)
    cl["acceso_credito_informal"] = rng.random(N) < np.where(cl["perfil_ahorro_real"] == "ahorra", comp["prob_credito_informal"]["ahorra"],
                                                              comp["prob_credito_informal"]["no_ahorra"])
    cl["tasa_credito_informal"] = _uniforme(rng, comp["tasa_credito_informal_mensual"], N).round(3)
    cl["prob_acepta_reco"] = np.clip(rng.beta(2, 3, N) + np.where(cl["perfil_ahorro_real"] == "ahorra", 0.10, 0.0), 0.02, 0.98).round(3)
    cl["necesidad_oculta"] = np.select(
        [cl["paga_en_usd"], (cl["tcea_promedio"] > 0.45) & cl["tiene_deuda"], cl["arquetipo"] == "independiente"],
        ["pago_usd", "deuda_cara", "ingreso_irregular"], default="ninguna")
    cl["cambio_patron"] = rng.random(N) < comp["prob_cambio_patron"]
    cl["pos_cambio_patron"] = np.where(cl["cambio_patron"], rng.uniform(0.2, 0.8, N), np.nan).round(3)
    cl["factor_cambio_ingreso"] = np.where(cl["cambio_patron"], np.where(rng.random(N) < 0.6, rng.uniform(0.60, 0.85, N), rng.uniform(1.2, 1.5, N)), 1.0).round(3)
    cl["heterogeneidad_consumo"] = rng.lognormal(0, 0.2, N).round(3)
    cl["tipo_trabajo"] = cl["segmento"].map({"formal_quincena": "dependiente", "base_comision": "dependiente_con_comision", "independiente_diario": "independiente",
                                             "independiente_proyectos": "independiente", "mixto": "mixto"})
    cl["frecuencia_ingreso"] = cl["segmento"].map({"formal_quincena": "quincenal", "base_comision": "mensual_mas_comision", "independiente_diario": "diaria",
                                                    "independiente_proyectos": "irregular", "mixto": "mensual_mas_extra"})
    cl["customer_id"] = [f"C{inicio_global + i:05d}" for i in range(N)]
    return cl
