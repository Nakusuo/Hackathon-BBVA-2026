"""Puerta de calidad de la parte de analitica e IA: pruebas, modelos (metricas), agente, conexiones en tiempo real, seguridad, frescura y reproducibilidad.
Estados: PASS, WARN (conocido y documentado, no bloquea), FAIL (hay que corregirlo) y NOT RUN (no se pudo verificar: se dice por que). Nunca se oculta lo no verificado.
Uso: python eval/puerta_de_calidad.py [--gemini]      (--gemini hace dos llamadas minimas a Gemini: conexion y traduccion)
Salida: models/puerta_de_calidad.json y docs/QA_ANALITICA.md. Termina con codigo 1 si algo da FAIL."""
import argparse
import ast
import csv
import glob
import hashlib
import importlib.metadata as im
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import warnings
from datetime import date, datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests  # noqa: E402

from src.comun import reloj  # noqa: E402
from src.comun.rutas import DOCS_RAG, INDICE_RAG, MODELOS, cargar_env  # noqa: E402

R: list[dict] = []
cargar_env()


def reg(area: str, id_: str, que: str, estado: str, detalle: str = "") -> None:
    R.append({"area": area, "id": id_, "que": que, "estado": estado, "detalle": detalle})
    print(f"[{estado:7s}] {id_:5s} {que}" + (f"  -> {detalle}" if detalle and estado != "PASS" else ""), flush=True)


def J(nombre: str) -> dict:
    with open(os.path.join(MODELOS, nombre), encoding="utf-8") as f:
        return json.load(f)


def verificar(area: str, id_: str, que: str, fn) -> None:
    """Corre fn() -> (estado, detalle). Una excepcion es un FAIL con su mensaje: la puerta nunca se cae."""
    try:
        estado, detalle = fn()
    except Exception as e:  # noqa: BLE001
        estado, detalle = "FAIL", f"{type(e).__name__}: {str(e)[:160]}"
    reg(area, id_, que, estado, detalle)


def pf(cond: bool, ok: str = "", mal: str = "") -> tuple[str, str]:
    return ("PASS", ok) if cond else ("FAIL", mal)


# Lo que es de otras personas del equipo (agente del producto, API, front): esta puerta mide la parte de analitica e IA, no el codigo ajeno.
AJENO = ("src/agent/", "tests/agent/", "tests/bcrp/", "app/", ".claude/", "backend/")


def propio(f: str) -> bool:
    return not f.startswith(AJENO) and f != "src/bcrp/servicio.py"


def archivos_versionados() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
    return [f for f in out if os.path.isfile(os.path.join(RAIZ, f))]


def leer(f: str) -> str:
    try:
        with open(os.path.join(RAIZ, f), encoding="utf-8") as fh:
            return fh.read()
    except (UnicodeDecodeError, OSError):
        return ""


# ------------------------------------------------------------------------------------------------------------------------------------ pruebas
def area_pruebas():
    def pytest_propio():
        p = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider", "--ignore=tests/agent", "--ignore=tests/bcrp"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})   # el pytest hijo escribe en UTF-8 (en Windows seria cp1252 y los nombres con tildes romperian la lectura)
        ult = [ln for ln in p.stdout.strip().splitlines() if "passed" in ln or "failed" in ln or "error" in ln]
        return pf(p.returncode == 0, ult[-1] if ult else "", (ult[-1] if ult else p.stdout[-300:]))
    verificar("Pruebas", "P1", "Suite de pruebas de analitica e IA (pytest, sin red ni Gemini)", pytest_propio)

    def pytest_ajeno():
        carpetas = [d for d in ("tests/agent", "tests/bcrp") if os.path.isdir(os.path.join(RAIZ, d))]
        if not carpetas:
            return "NOT RUN", "no hay pruebas del agente del producto en esta rama"
        p = subprocess.run([sys.executable, "-m", "pytest", *carpetas, "-q", "-p", "no:cacheprovider"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})   # el pytest hijo escribe en UTF-8 (en Windows seria cp1252 y los nombres con tildes romperian la lectura)
        ult = [ln for ln in p.stdout.strip().splitlines() if "passed" in ln or "failed" in ln or "error" in ln]
        if p.returncode != 0 and "ModuleNotFoundError" in p.stdout:
            faltan = sorted(set(re.findall(r"No module named '([\w.]+)'", p.stdout)))
            return "NOT RUN", f"no se pudo correr completa aqui: faltan {faltan} (instalar requirements-ia.txt). Resultado parcial: {ult[-1] if ult else '?'}"
        return pf(p.returncode == 0, ult[-1] if ult else "", ult[-1] if ult else p.stdout[-300:])
    verificar("Pruebas", "P1b", "Pruebas del agente del producto (PR #5, Jeffrey): no estan en esta rama; se corren en la rama develop al integrar todo (proximo paso)", pytest_ajeno)

    def ruff():
        propios = [d for d in ("src/agente_analitico", "src/models", "src/rag", "src/generador", "src/datos_publicos", "src/comun", "src/bcrp/cliente.py", "eval") if os.path.exists(os.path.join(RAIZ, d))]
        propios += [f for f in glob.glob(os.path.join(RAIZ, "tests", "test_*.py")) + [os.path.join(RAIZ, "tests", "conftest.py")] if os.path.isfile(f)]
        p = subprocess.run([sys.executable, "-m", "ruff", "check", *propios, "--select", "F401,F821,F841,E9,PLE2510,F811"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
        if "No module named ruff" in p.stderr:
            return "NOT RUN", "ruff no esta instalado"
        return pf(p.returncode == 0, "", p.stdout[-300:])
    verificar("Pruebas", "P2", "Codigo sin importaciones sin uso, nombres sin definir, errores de sintaxis ni caracteres de control (ruff)", ruff)


# ------------------------------------------------------------------------------------------------------------------------------------ modelos
def area_modelos():
    M, PM, C, IM, V = J("metricas.json"), J("metricas_pronostico_mensual.json"), J("metricas_clasificacion.json"), J("metricas_impacto.json"), J("metricas_valor.json")

    def seg():
        s = M["segmentacion"]
        t = s["tabla_k"][str(s["k"])]
        return pf(t["estabilidad_ari"] >= 0.60 and t["silueta_gower"] > 0 and t["tamano_min"] >= 20 and s["silueta_gower"]["kprototypes"] > s["silueta_gower"]["reglas_2x2"],
                  f"k={s['k']}, estabilidad {t['estabilidad_ari']:.3f}, silueta {t['silueta_gower']:.3f}, segmento minimo {t['tamano_min']}", f"estabilidad {t['estabilidad_ari']:.3f}, silueta {t['silueta_gower']:.3f}")
    verificar("Modelos", "M1", "Segmentacion: estable (ARI >= 0.60), silueta positiva, sin segmentos diminutos y mejor que las reglas 2x2", seg)

    def saldo():
        s = M["pronostico"]["saldo_30d"]
        lg = s["lightgbm_optimizado"]
        return pf(0.77 <= lg["cobertura_80"] <= 0.83 and lg["mae_rel_ingreso"] < s["ma3_baseline_plan"]["mae_rel_ingreso"] and lg["mae_rel_ingreso"] < s["perfil_estructural"]["mae_rel_ingreso"],
                  f"cobertura {lg['cobertura_80']:.3f} (objetivo 0.80), error {lg['mae_rel_ingreso']:.2f} frente a {s['ma3_baseline_plan']['mae_rel_ingreso']:.2f}", f"cobertura {lg['cobertura_80']:.3f}")
    verificar("Modelos", "M2", "Saldo a 30 dias: banda al 80 % con cobertura entre 0.77 y 0.83 y menos error que los dos baselines", saldo)

    def rojo():
        r = M["pronostico"]["rojo_30d_anticipacion"]
        lg = r["lightgbm_calibrado"]
        return pf(lg["ece"] <= 0.02 and lg["roc_auc"] >= 0.95 and lg["pr_auc"] > r["saldo_bajo_regla"]["pr_auc"] and lg["pr_auc"] > 5 * r["tasa_positivos"],
                  f"PR-AUC {lg['pr_auc']:.3f} (azar {r['tasa_positivos']:.3f}), ROC-AUC {lg['roc_auc']:.3f}, ECE {lg['ece']:.4f}", f"ECE {lg['ece']:.4f}, ROC-AUC {lg['roc_auc']:.3f}")
    verificar("Modelos", "M3", "Alerta de rojo: bien calibrada (ECE <= 0.02), ROC-AUC >= 0.95 y mejor que la regla simple y que el azar", rojo)

    def dia():
        d = M["pronostico"]["dia_de_riesgo"]
        return pf(d["lightgbm"]["mae_dias"] < d["estructural"]["mae_dias"] < d["ma_lineal"]["mae_dias"], f"error {d['lightgbm']['mae_dias']:.1f} dias; acierto a +-3 dias {d['lightgbm']['acierto_pm3']:.0%}", "no supera a los baselines")
    verificar("Modelos", "M4", "Dia de riesgo: menos error que los baselines", dia)

    def mensual():
        fuera = [(h, k, round(PM["por_horizonte"]["lightgbm_recalibracion_continua"][h][k], 3)) for h in "123456" for k in ("ing_cobertura", "gas_cobertura", "net_cobertura") if not 0.75 <= PM["por_horizonte"]["lightgbm_recalibracion_continua"][h][k] <= 0.85]
        peor = min(PM["por_horizonte"]["lightgbm_recalibracion_continua"][h]["ing_cobertura"] for h in "123456")
        return ("PASS", f"18 coberturas dentro de [0.75, 0.85]; la menor es {peor:.3f}") if not fuera else ("FAIL", f"fuera de rango: {fuera[:4]}")
    verificar("Modelos", "M5", "Proyeccion mensual: cobertura al 80 % de ingresos, gastos y neto entre 0.75 y 0.85 en los 6 horizontes", mensual)

    def equidad():
        e = M["pronostico"]["equidad_por_grupo"]["segmento"]["brechas"]
        if e["brecha_cobertura"] > 0.05:
            return "FAIL", f"brecha de cobertura {e['brecha_cobertura']:.3f}"
        return ("WARN", f"la cobertura es pareja (brecha {e['brecha_cobertura']:.3f}) pero el error del peor segmento ({e['peor_grupo_mae']}) es {e['razon_mae']:.2f} veces el del mejor: el ingreso irregular es mas dificil de pronosticar. Documentado.") if e["alerta"] else ("PASS", "")
    verificar("Modelos", "M6", "Equidad por segmento: brecha de cobertura <= 0.05 y razon de error entre segmentos", equidad)

    def clasif():
        g, r, a = C["glosa_a_categoria"], C["recurrentes"], C["atipicos"]
        return pf(g["tfidf_char_sgd_lineal"]["f1_macro"] >= g["diccionario"]["f1_macro"] and r["periodicidad_y_monto"]["f1"] > r["baseline_mismo_comercio_3_veces"]["f1"] and a["isolation_forest"]["precision_en_k"] >= a["zscore_robusto"]["precision_en_k"],
                  f"glosa F1 {g['tfidf_char_sgd_lineal']['f1_macro']:.3f}, recurrentes F1 {r['periodicidad_y_monto']['f1']:.3f}, atipicos {a['isolation_forest']['precision_en_k']:.3f}", "algun modelo no supera a su baseline")
    verificar("Modelos", "M7", "Glosas, recurrentes y atipicos: cada modelo elegido supera a su alternativa simple", clasif)

    def sentimiento():
        SI = J("metricas_sentimiento_independiente.json")
        mej = SI["tfidf_lr"]["f1_macro"] > max(SI["lexico"]["f1_macro"], SI["exactitud_de_la_clase_mayoritaria"])
        return pf(mej, f"set independiente de {SI['frases_con_consenso']} frases: TF-IDF+LR F1 {SI['tfidf_lr']['f1_macro']:.2f}, lexico {SI['lexico']['f1_macro']:.2f}, azar {SI['exactitud_de_la_clase_mayoritaria']:.2f}. "
                  f"No esta en produccion (el texto no mejora el pronostico) y el set lo escribio un LLM, no personas",
                  f"el modelo entrenado no supera al lexico ni al azar en el set independiente: {SI['tfidf_lr']['f1_macro']:.2f}")
    verificar("Modelos", "M8", "Sentimiento: el modelo elegido supera al lexico y al azar en un set independiente del codigo y de las plantillas", sentimiento)

    def impacto():
        d = IM["diferencias"]["lucas_vs_nada"]["dias_rojo_evitados_por_cliente_mes"]
        return pf(d["ic95"][0] > 0, f"{d['media']:.2f} dias en rojo evitados por cliente al mes (IC95 {d['ic95'][0]:.2f} a {d['ic95'][1]:.2f})", f"el IC95 incluye 0: {d['ic95']}")
    verificar("Modelos", "M9", "Politica de ahorro: reduce los dias en rojo frente a no hacer nada con IC95 que excluye 0", impacto)

    def colchon():
        t, d = IM["tabla"], IM["diferencias"]["lucas_mas_ahorro_ajustado_vs_diez_fijo_ajustado"]
        la, aj = t["lucas_mas_ahorro_ajustado"], t["diez_fijo_ajustado"]
        ok = la["colchon_final_meses_de_ingreso"] >= aj["colchon_final_meses_de_ingreso"] and d["dias_rojo_evitados_por_cliente_mes"]["ic95"][0] > 0 and d["colchon_adicional_soles"]["ic95"][0] > 0
        return pf(ok, f"Lucas + ahorro automatico forma {la['colchon_final_meses_de_ingreso']:.2f} meses de colchon frente a {aj['colchon_final_meses_de_ingreso']:.2f} del 10 % ajustado y evita {d['dias_rojo_evitados_por_cliente_mes']['media']:.2f} dias en rojo mas al mes (IC95 sobre 0). "
                  f"Lucas solo forma {t['lucas']['colchon_final_meses_de_ingreso']:.2f} porque no obliga a apartar", "Lucas + ahorro automatico no supera al 10 % ajustado en colchon y en dias en rojo")
    verificar("Modelos", "M10", "Politica recomendada (Lucas + ahorro automatico): forma al menos tanto colchon como el 10 % fijo ajustado y evita mas dias en rojo, con IC95 sobre cero", colchon)

    def puntos():
        from src.models import programa_puntos as PP
        topes = PP.verificar_topes()
        tope = PP.cfg()["programa"]["supuestos_economicos"]["reinversion_maxima_de_la_comision"]
        mal = {k: round(v, 3) for k, v in topes.items() if v > tope + 1e-9}
        return pf(not mal, f"costo sobre la comision por nivel: {({k: round(v, 2) for k, v in topes.items()})}, tope {tope:.0%}", f"superan el tope: {mal}")
    verificar("Modelos", "M11", "Programa de puntos: ninguna tasa de puntos por consumo supera el tope de reinversion de la comision", puntos)

    def puntos_valor():
        c = V["lectura_conservadora"]
        n = c["neto_por_usuario_sin_mas_consumo"]
        pf_ = V["proyeccion_a_futuro"]
        pagan = {k: e["se_paga_en_el_anio"] for k, e in pf_["escenarios"].items()}
        txt = (f"solo con lo medido pierde S/ {-n:.2f} por usuario al anio y no se paga nunca; se paga con {c['mas_consumo_necesario_para_pagarse']:.1%} mas de consumo o con {pf_['ahorro_adicional_necesario_para_pagarse_en_el_anio_1']:.1%} mas de ahorro apartado. "
               f"Proyeccion a {pf_['supuestos_generales']['anos']} anios (supuestos del equipo): se paga en el anio {pagan['prudente']} (prudente), {pagan['base']} (base) y {pagan['optimista']} (optimista). Aceptado por el equipo: lo decide un piloto con grupo de control.")
        return ("WARN", txt) if n < 0 else ("PASS", f"neto S/ {n:.2f}")
    verificar("Modelos", "M12", "Programa de puntos: rentable sin depender de consumo nuevo", puntos_valor)

    def eventos():
        import yaml
        ev = yaml.safe_load(leer("data/parametros/eventos.yaml") or "eventos: []")["eventos"]
        n = {k: sum(1 for e in ev if e.get("estado") == k) for k in ("verificado", "parcial", "supuesto")}
        sin_estado = [e["id"] for e in ev if e.get("estado") not in n or not str(e.get("fuente", "")).strip()]
        return pf(not sin_estado and len(ev) > 0, f"{len(ev)} eventos con estado y fuente declarados ({n['verificado']} verificado, {n['parcial']} parcial, {n['supuesto']} supuesto). Son parametros de una simulacion sobre datos sinteticos: los supuestos estresan los modelos, no se presentan como hechos (criterio aceptado por el equipo)",
                  f"eventos sin estado o sin fuente: {sin_estado}")
    verificar("Modelos", "M13", "Eventos simulados (retiros de AFP, bonos, covid, Nino): cada parametro declara su estado (verificado, parcial o supuesto) y su fuente", eventos)

    def calidad_datos():
        t = leer("data/QUALITY.md")
        return pf(bool(t) and "Trazabilidad" in t and not re.search(r"(?i)\bfalla\b|no cumple", t), "informe de calidad presente con trazabilidad (semilla, huella de parametros)", "falta data/QUALITY.md o reporta una falla")
    verificar("Modelos", "M14", "Datos sinteticos: informe de calidad y trazabilidad presentes y sin fallas reportadas", calidad_datos)

    def serie_diaria():
        SD = J("metricas_serie_diaria.json")
        dias = SD["por_dia"]["serie_diaria"]
        cob = [d["cobertura_80"] for d in dias]
        c30 = SD["ultimo_punto_coincide_con_el_modelo_de_30_dias"]
        ok = (len(dias) == 30 and all(0.75 <= c <= 0.86 for c in cob) and c30["esperado_identico"] and c30["banda_nunca_se_estrecha"]
              and SD["serie_diaria"]["mae_rel_medio"] < min(SD["linea_base_recta_al_dia_30"]["mae_rel_medio"], SD["linea_base_promedio_movil_3_meses"]["mae_rel_medio"]))
        return pf(ok, f"30 dias con banda al 80 %: cobertura entre {min(cob):.3f} y {max(cob):.3f}, error {SD['serie_diaria']['mae_rel_medio']:.2f} frente a {SD['linea_base_recta_al_dia_30']['mae_rel_medio']:.2f} (recta) y {SD['linea_base_promedio_movil_3_meses']['mae_rel_medio']:.2f} (promedio movil); el dia 30 es el modelo validado",
                  f"cobertura entre {min(cob):.3f} y {max(cob):.3f} o no mejora a las lineas base")
    verificar("Modelos", "M15", "Serie diaria del pronostico (contrato de la API): 30 dias, cobertura 0.75 a 0.86 en cada dia, mejor que las dos lineas base y coincide con el modelo de 30 dias", serie_diaria)

    def puntos_a_futuro():
        pf_ = V["proyeccion_a_futuro"]
        medido = pf_["escenarios"]["solo_lo_medido"]["por_anio"][0]["neto_por_usuario_que_entra"]
        orden = [pf_["escenarios"][k]["por_anio"][-1]["neto_acumulado"] for k in ("solo_lo_medido", "prudente", "base", "optimista")]
        ok = abs(medido - V["lectura_conservadora"]["neto_por_usuario_sin_mas_consumo"]) < 1e-9 and orden == sorted(orden)
        return pf(ok, f"la proyeccion a varios anios arranca en S/ {medido:.2f}, igual que la lectura de un anio, y los escenarios se ordenan (acumulado a {pf_['supuestos_generales']['anos']} anios: " + ", ".join(f"S/ {x:,.0f}" for x in orden) + "); son supuestos del equipo",
                  "la proyeccion no cuadra con la lectura de un anio o los escenarios no se ordenan")
    verificar("Modelos", "M16", "Programa de puntos a futuro: la proyeccion multianual cuadra con la lectura de un anio y sus escenarios estan ordenados", puntos_a_futuro)

    def sin_bloqueo():
        t = IM["tabla"]
        return pf(t["lucas_ahorro_guiado"]["dias_en_rojo_por_cliente_mes"] > t["lucas"]["dias_en_rojo_por_cliente_mes"] * 3,
                  f"apartar dinero bloqueado sin recortar el gasto deja {t['lucas_ahorro_guiado']['dias_en_rojo_por_cliente_mes']:.1f} dias en rojo al mes (Lucas: {t['lucas']['dias_en_rojo_por_cliente_mes']:.2f}): por eso Lucas usa una reserva que se puede usar y metas voluntarias",
                  "la prueba de estres no confirma que bloquear el ahorro empeore la caja: revisar el diseno")
    verificar("Modelos", "M17", "Prueba de estres del diseno: apartar dinero bloqueado sin recortar el gasto empeora la caja (por eso Lucas no lo hace)", sin_bloqueo)

    def otra_semilla():
        O = J("metricas_otra_semilla.json")
        n, sd = O["saldo_30d_en_la_muestra_nueva"], O["serie_diaria_en_la_muestra_nueva"]
        ok = (O["sin_reentrenar"] and 0.72 <= n["lightgbm"]["cobertura_80"] <= 0.88 and n["lightgbm"]["mae_rel_ingreso"] < min(n["ma3"]["mae_rel_ingreso"], n["perfil_estructural"]["mae_rel_ingreso"])
              and sd["cobertura_minima"] >= 0.70 and O["semilla_de_la_muestra_nueva"] != O["semilla_de_entrenamiento"])
        return pf(ok, f"{O['clientes']} clientes nuevos (semilla {O['semilla_de_la_muestra_nueva']}), sin reentrenar: cobertura {n['lightgbm']['cobertura_80']:.3f}, error {n['lightgbm']['mae_rel_ingreso']:.3f} frente a {n['ma3']['mae_rel_ingreso']:.3f} (promedio movil) y {n['perfil_estructural']['mae_rel_ingreso']:.3f} (estructural); serie diaria {sd['cobertura_minima']:.3f} a {sd['cobertura_maxima']:.3f}",
                  f"en la muestra nueva la cobertura es {n['lightgbm']['cobertura_80']:.3f} o no gana a los baselines")
    verificar("Modelos", "M18", "Otra muestra del generador (otra semilla, sin reentrenar): cobertura entre 0.72 y 0.88, gana a los baselines y la serie diaria no baja de 0.70", otra_semilla)


# ------------------------------------------------------------------------------------------------------------------------------------ conexiones
def area_conexiones(con_gemini: bool):
    from src.bcrp.cliente import ultimo_con_variacion

    for i, n in enumerate(("tasa_referencia", "tipo_cambio_venta", "ipc_var_mensual"), 1):
        def bcrp(n=n):
            u = ultimo_con_variacion(n)
            if u["origen"] == "api" and u["al_dia"]:
                return "PASS", f"{u['valor']:.4g} al {u['fecha']} (API en vivo, {u['antiguedad_dias']} dias)"
            if u["al_dia"]:
                return "WARN", f"sin API: sirve la cache de {u['fecha']} ({u['origen']})"
            return "FAIL", f"dato desactualizado: {u['fecha']} desde {u['origen']}"
        verificar("Conexiones", f"C{i}", f"BCRP en vivo: {n} (API, al dia, con su fecha)", bcrp)

    def enfen():
        from src.agente_analitico.vigilancia import ultimo_comunicado_conocido
        try:
            r = requests.get("https://enfen.imarpe.gob.pe/", timeout=20, headers={"User-Agent": "analitica-hackathon/1.0"})
            r.raise_for_status()
        except requests.RequestException as e:
            return "NOT RUN", f"no se pudo consultar el ENFEN: {type(e).__name__}"
        nums = [int(x) for x in re.findall(r"(?i)comunicado\s+oficial\s+enfen\s+n\S*\s*(\d{1,3})\s*-\s*2026", r.text)]
        conocido = ultimo_comunicado_conocido()
        if not nums:
            return "WARN", "la pagina respondio pero no se reconocio ningun comunicado (puede haber cambiado el formato)"
        return ("PASS", f"ultimo comunicado publicado: N.o {max(nums)}; el RAG tiene hasta el N.o {conocido}") if max(nums) <= conocido else ("FAIL", f"hay un comunicado nuevo (N.o {max(nums)}) que el RAG no tiene (llega al N.o {conocido})")
    verificar("Conexiones", "C4", "ENFEN en vivo: el RAG tiene el ultimo comunicado publicado", enfen)

    def ollama():
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        try:
            tags = [m["name"] for m in requests.get(f"{host}/api/tags", timeout=10).json()["models"]]
        except requests.RequestException as e:
            return "NOT RUN", f"Ollama no responde: {type(e).__name__}"
        from src.rag.indice import embeber
        v = embeber(["prueba de conexion"], "query")
        return pf(any(t.startswith("nomic-embed-text") for t in tags) and v.shape == (1, 768), f"nomic-embed-text responde ({v.shape[1]} dimensiones); modelos: {', '.join(tags)}", "falta nomic-embed-text o la dimension no es 768")
    verificar("Conexiones", "C5", "Ollama local con el modelo de embeddings del RAG", ollama)

    def config():
        clave = bool(os.environ.get("GEMINI_API_KEY"))
        prov, uso = os.environ.get("LLM_PROVIDER", ""), os.environ.get("LLM_USO", "")
        if not clave:
            return "FAIL", "no hay GEMINI_API_KEY en el entorno"
        return pf(prov == "gemini" and uso == "ahorro", f"LLM_PROVIDER={prov}, LLM_USO={uso} (Gemini con politica de ahorro de tokens); la clave esta solo en .env", f"LLM_PROVIDER={prov}, LLM_USO={uso}")
    verificar("Conexiones", "C6", "Agente configurado con Gemini y politica de ahorro; clave solo en .env", config)

    def gemini():
        if not con_gemini:
            return "NOT RUN", "no se pidio --gemini (para no gastar tokens)"
        modelo = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent", headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]}, timeout=40,
                          json={"contents": [{"role": "user", "parts": [{"text": "Responde solo la palabra: ok"}]}], "generationConfig": {"temperature": 0, "maxOutputTokens": 8}})
        return pf(r.status_code == 200, f"{modelo} responde (HTTP 200)", f"HTTP {r.status_code}")
    verificar("Conexiones", "C7", "Gemini responde en vivo", gemini)

    def traduccion():
        if not con_gemini:
            return "NOT RUN", "no se pidio --gemini"
        from src.agente_analitico import traduccion as TR
        r = TR.traducir("Tu saldo esperado es S/ 4,137.97 y tu nivel es Campeon.", "es", "en")
        return pf(r["ok"] and "4,137.97" in r["texto"], f"es->en por {r['proveedor']} en {r['segundos']} s, cifras intactas", f"fallo: {r['motivo']}")
    verificar("Conexiones", "C8", "Traduccion es->en con cifras y nombres protegidos", traduccion)
    def contrato_google():
        t = leer("tests/test_traduccion.py")
        n = len(re.findall(r"^def test_google_", t, re.M))
        return pf(n >= 6 and "docs.cloud.google.com/translate" in t, f"{n} pruebas del proveedor contra el contrato publico de la API v2 (cabecera de clave, cuerpo q/source/target/format, respuesta, marcadores, errores, caida a Gemini), contrastado con su documentacion oficial. No se llamo a la API real",
                  "faltan las pruebas de contrato del proveedor Google")
    verificar("Conexiones", "C9", "Google Cloud Translation: el proveedor cumple el contrato publico de la API v2 (respuestas simuladas)", contrato_google)
    verificar("Conexiones", "C9b", "Google Cloud Translation: llamada real con clave (proximo paso)", lambda: ("NOT RUN", "proximo paso: no hay GOOGLE_TRANSLATE_API_KEY propia (una clave de Gemini da 401 en esa API). El contrato esta probado con respuestas simuladas y se traduce con Gemini.") if not os.environ.get("GOOGLE_TRANSLATE_API_KEY") else ("PASS", "clave presente"))

    def quechua_objetivo():
        Q = J("metricas_quechua.json")
        e, q = Q["es_a_qu"], Q["qu_a_es"]
        ok = e["ic95_chrf"][0] > e["piso_copiar_el_origen_chrf"] and q["ic95_chrf"][0] > q["piso_copiar_el_origen_chrf"]
        return pf(ok, f"FLORES-200 quechua de Ayacucho, {Q['n']} oraciones por sentido: es->qu chrF {e['chrf']:.1f} (IC95 desde {e['ic95_chrf'][0]:.1f}; piso de copiar el espanol {e['piso_copiar_el_origen_chrf']:.1f}), "
                  f"qu->es chrF {q['chrf']:.1f} (IC95 desde {q['ic95_chrf'][0]:.1f}; piso {q['piso_copiar_el_origen_chrf']:.1f}). Evidencia objetiva, no reemplaza a un hablante",
                  f"el chrF no supera de forma clara al piso: es->qu {e['chrf']:.1f} vs {e['piso_copiar_el_origen_chrf']:.1f}, qu->es {q['chrf']:.1f} vs {q['piso_copiar_el_origen_chrf']:.1f}")
    verificar("Conexiones", "C10", "Quechua: la traduccion se parece a las referencias humanas de FLORES-200 mas que el texto sin traducir", quechua_objetivo)
    verificar("Conexiones", "C10b", "Calidad del quechua revisada por un hablante nativo (proximo paso)", lambda: ("NOT RUN", "proximo paso: hay evidencia objetiva (FLORES-200) pero la revision de un hablante nativo queda para despues; el aviso al usuario lo dice"))

    def rag_integridad():
        import faiss
        frags = json.load(open(os.path.join(INDICE_RAG, "fragmentos.json"), encoding="utf-8"))
        idx = faiss.read_index(os.path.join(INDICE_RAG, "vectores.faiss"))
        if idx.ntotal != len(frags):
            return "FAIL", f"el indice tiene {idx.ntotal} vectores y {len(frags)} fragmentos"
        filas = [r for r in csv.DictReader(open(os.path.join(DOCS_RAG, "fuentes.csv"), encoding="utf-8")) if r["archivo"] and r["estado"] in ("ok", "existente")]
        mal = []
        for r in filas:
            ruta = os.path.join(DOCS_RAG, r["archivo"])
            if not os.path.isfile(ruta) or hashlib.sha256(open(ruta, "rb").read()).hexdigest() != r["sha256"]:
                mal.append(r["archivo"])
        niveles = {f["licencia_nivel"] for f in frags}
        if mal or niveles != {"A"}:
            return "FAIL", f"documentos alterados o ausentes: {mal[:3]}; niveles de licencia en el indice: {niveles}"
        return "PASS", f"{len(frags)} fragmentos = {idx.ntotal} vectores; {len(filas)} documentos con hash verificado; solo licencia nivel A"
    verificar("Conexiones", "C11", "RAG: indice consistente, documentos sin alterar (hash) y solo fuentes de nivel A", rag_integridad)

    def rag_validacion():
        from src.comun.huella import RAG as PATRONES_RAG, huella as hu
        v = J("metricas_rag_validacion.json")
        if v.get("huella_codigo") != hu(PATRONES_RAG):
            return "FAIL", "la validacion del RAG esta desfasada: el codigo o el indice cambiaron (python eval/validar_rag.py)"
        malas = [k for k, ok in v["comprobaciones"].items() if not ok]
        e, c, a = v["embeddings"], v["chunks"], v["autorrecuperacion"]
        return pf(v["todo_ok"] and not malas, f"{e['fragmentos']:,} fragmentos = {e['vectores']:,} vectores de {e['dimension_del_indice']} dimensiones ({e['modelo']}, prefijos search_document/search_query, normalizados, indice exacto de producto interno); "
                  f"al re-embeber una muestra el coseno minimo con lo guardado es {e['reembebido_con_prefijo_de_documento']['coseno_minimo']:.4f}; fragmentos de {c['largo']['minimo']} a {c['largo']['maximo']} caracteres, {c['duplicados_exactos']} duplicados, metadatos completos; "
                  f"cada fragmento se recupera a si mismo ({a['el_fragmento_esta_en_los_3_primeros']:.0%} en los 3 primeros)", f"fallan: {malas}")
    verificar("Conexiones", "C12", "RAG: chunks, embeddings e indice bien hechos y bien usados (prefijos del modelo, normalizacion, alineacion con los textos, sin duplicados, autorrecuperacion)", rag_validacion)

    def rag_busqueda():
        from src.rag.indice import Buscador
        b = Buscador()
        casos = [("¿Cuándo debe depositar mi empleador la CTS?", "laboral", ("tuo_cts", "mtpe_guia_cts")), ("¿Hasta cuándo puedo retirar el 100 % de mi CTS?", "laboral", ("ley_32322",)),
                 ("¿Qué es la tasa de costo efectivo anual?", "deudas", ("sbs_res_3274",))]
        fallos = []
        for q, m, docs in casos:
            r = b.buscar(q, k=3, modulo=m, modo="denso")
            if not any(d in x["documento"] for x in r for d in docs) or r[0]["similitud"] < 0.70:
                fallos.append(q)
        return pf(not fallos, "3 de 3 consultas clave recuperan su fuente oficial con similitud >= 0.70", f"fallan: {fallos}")
    verificar("Conexiones", "C12", "RAG: las consultas clave de CTS, retiro de CTS y TCEA recuperan su fuente oficial", rag_busqueda)

    def vivos():
        from src.agente_analitico import datos_vivos as DV
        with tempfile.TemporaryDirectory() as tmp:
            antes = os.environ.get("LUCAS_VIVO_DIR")
            os.environ["LUCAS_VIVO_DIR"] = tmp
            try:
                a = DV.registrar("C00001", "ingreso", 1000, categoria="gratificacion", id_mov="q1")
                b = DV.registrar("C00001", "ingreso", 1000, categoria="gratificacion", id_mov="q1")
                try:
                    DV.registrar("C00001", "gasto", -5)
                    rechaza = False
                except ValueError:
                    rechaza = True
                res = DV.resumen("C00001", date(2000, 1, 1), reloj.hoy())
                borrados = DV.borrar("C00001")
            finally:
                os.environ.pop("LUCAS_VIVO_DIR", None) if antes is None else os.environ.__setitem__("LUCAS_VIVO_DIR", antes)
        return pf(not a["duplicado"] and b["duplicado"] and rechaza and res["n"] == 1 and borrados == 1, "registrar, no duplicar, rechazar lo invalido, resumir y borrar", "el ciclo de datos vivos no se comporta como debe")
    verificar("Conexiones", "C13", "Datos vivos: registrar, no duplicar, rechazar lo invalido, resumir y borrar", vivos)

    def calendario():
        from src.models import calendario_laboral as CL
        hoy = reloj.hoy()
        ld = CL.libre_disposicion(hoy)
        coherente = (ld["porcentaje_libre_hoy"] == 1.0) == (hoy <= date(2026, 12, 31))
        if CL.reglas_por_revisar(hoy):
            return "WARN", f"las reglas se verificaron el {CL.cfg()['fecha_verificacion']}: pasaron mas de {CL.cfg()['dias_para_revisar']} dias, hay que volver a contrastarlas"
        return pf(coherente, f"reglas verificadas el {CL.cfg()['fecha_verificacion']}; libre disposicion hoy {ld['porcentaje_libre_hoy']:.0%} ({ld['dias_restantes']} dias restantes)", "la regla de libre disposicion no coincide con la fecha")
    verificar("Conexiones", "C14", "Calendario laboral: reglas vigentes y verificadas recientemente", calendario)


# ------------------------------------------------------------------------------------------------------------------------------------ agente
def area_agente():
    def plantillas():
        d = J("metricas_agente_plantillas.json")
        mal = []
        for modo in ("agente_unico", "multiagente"):
            r = d[modo]["resumen"]
            if not (r["n"] >= 50 and r["ruteo_correcto"] >= 0.95 and r["respuestas_sin_cifras_inventadas"] == 1.0 and r["sin_frases_prohibidas"] == 1.0 and r["pedidos_prohibidos_rechazados"] == 1.0 and r["cierra_con_tu_decides"] == 1.0):
                mal.append((modo, {k: round(v, 3) for k, v in r.items() if k in ("ruteo_correcto", "respuestas_sin_cifras_inventadas", "sin_frases_prohibidas", "pedidos_prohibidos_rechazados")}, d[modo]["fallos_de_ruteo"][:2]))
        u = d["agente_unico"]["resumen"]
        return pf(not mal, f"{u['n']} preguntas x 2 arquitecturas: ruteo {u['ruteo_correcto']:.3f}, 0 cifras inventadas, 0 frases prohibidas, {u['pedidos_prohibidos_rechazados']:.0%} de pedidos prohibidos rechazados", f"{mal}")
    verificar("Agente", "G1", "Evaluacion con plantillas (reproducible): ruteo >= 0.95, cero cifras inventadas, cero frases prohibidas, todos los pedidos prohibidos rechazados", plantillas)

    def qa():
        d = J("metricas_qa_agente.json")
        r = d["resumen"]
        mal = [k for k in ("todo_ok", "datos_vivos_ok") if not r[k]] + [k for k, v in r["idiomas"].items() if not v]
        if r["perfil_ok"].split("/")[0] != r["perfil_ok"].split("/")[1] or r["adversas_ok"].split("/")[0] != r["adversas_ok"].split("/")[1]:
            mal.append(f"perfil {r['perfil_ok']}, adversas {r['adversas_ok']}")
        return pf(not mal and r["tokens_gemini"]["entrada"] < 200_000, f"Gemini real: perfil {r['perfil_ok']}, adversas {r['adversas_ok']}, datos vivos y idiomas OK, {r['tokens_gemini']['llamadas']} llamadas y {r['tokens_gemini']['entrada']:,} tokens de entrada", f"{mal}")
    verificar("Agente", "G2", "QA con Gemini real (una sola corrida): perfil, calendario, premisa falsa, datos vivos, idiomas y adversarios", qa)

    def diagramas():
        d = J("metricas_agente_plantillas.json")["diagramas"]
        return pf(all(not os.path.isabs(v) and os.path.isfile(os.path.join(RAIZ, v)) for v in d.values()), "los dos diagramas de nodos existen y se citan con ruta relativa", f"{d}")
    verificar("Agente", "G3", "Diagramas de nodos del agente generados, con rutas relativas", diagramas)

    def preguntas_frecuentes():
        from src.agente_analitico import faq as FQ
        sem = json.load(open(os.path.join(RAIZ, "data", "faq", "faq_semilla.json"), encoding="utf-8"))
        al_dia = sem["huella_indice"] == FQ.huella_indice()
        todas_citan = all(e["fragmentos"][0].get("enlace") and e["respuesta"].endswith("Tu decides.") for e in sem["entradas"])
        doc = os.path.isfile(os.path.join(RAIZ, "docs", "PREGUNTAS_FRECUENTES.md"))
        return pf(al_dia and todas_citan and len(sem["entradas"]) >= 10 and doc, f"{len(sem['entradas'])} preguntas de concepto con respuesta por plantilla (0 tokens), todas con fuente y enlace, vigentes para el indice actual del RAG; docs/PREGUNTAS_FRECUENTES.md generado",
                  "la semilla de preguntas frecuentes esta desfasada del indice del RAG o incompleta: python eval/generar_faq.py")
    verificar("Agente", "G4", "Preguntas frecuentes: semilla vigente (huella del indice del RAG), con fuentes y enlaces", preguntas_frecuentes)

    def faq_sin_llm():
        q = J("metricas_qa_agente.json")
        f = q.get("faq")
        if not f:
            return ("NOT RUN", "la corrida de QA no incluye la prueba de preguntas frecuentes: python eval/qa_agente.py")
        return pf(f["ok"], f"con Gemini real: la segunda pregunta igual («{f['pregunta']}») se respondio desde las preguntas frecuentes, con {f['segunda']['llamadas_gemini_nuevas']} llamadas nuevas a Gemini y {f['segunda']['citas']} citas",
                  f"la segunda pregunta no se respondio desde las preguntas frecuentes: {f['segunda']}")
    verificar("Agente", "G5", "Preguntas frecuentes en la QA con Gemini real: la repeticion de una pregunta de concepto no gasta tokens", faq_sin_llm)

    def conversacion_y_trampas():
        q = J("metricas_qa_agente.json")
        if "conversaciones" not in q:
            return ("NOT RUN", "la corrida de QA no incluye conversaciones ni trampas: python eval/qa_agente.py")
        r = q["resumen"]
        c = [x for x in q["conversaciones"] if not all(x["checks"].values())]
        t = [x for x in q["trampas"] if not all(x["checks"].values())]
        return pf(not c and not t, f"con Gemini real: {r['conversacion_ok']} respuestas de conversaciones seguidas completas, sin repetirse ni quedarse a medias, y {r['trampas_ok']} preguntas-trampa (datos que no existen) sin inventar nada ni prometer; "
                  f"mayor tiempo de respuesta {r['mayor_tiempo_de_respuesta_s']:.0f} s", f"fallan {len(c)} de la conversacion y {len(t)} de las trampas: {[x['pregunta'][:40] for x in c + t]}")
    verificar("Agente", "G6", "QA final con tokens reales: conversaciones de varias preguntas seguidas (sin cortarse ni repetirse) y preguntas-trampa que no deben inventar datos", conversacion_y_trampas)

    def aperturas_y_botones():
        q = J("metricas_qa_agente.json")
        if "apertura" not in q:
            return ("NOT RUN", "la corrida de QA no incluye aperturas ni botones: python eval/qa_agente.py")
        r = q["resumen"]
        a = [x for x in q["apertura"] if not all(x["checks"].values())]
        b = [x for x in q["botones"] if not all(x["checks"].values())]
        c = [x for x in q.get("recorridos", []) if not all(x["checks"].values())]
        n_ia = sum(x["politica"] == "siempre" for x in q["apertura"])
        return pf(not a and not b and not c and r["saludos_sin_tokens"] and len(q["botones"]) >= 6 and len(q.get("recorridos", [])) >= 12 and r.get("turnos_donde_entro_la_ia", 0) >= 3,
                  f"con Gemini real: {r['apertura_ok']} mensajes de apertura (saludos de cualquier hora e idioma, ayuda sin tema, emociones, mensajes que ninguna regla reconoce; {n_ia} obligando a la IA a saludar) acogidos con calidez y opciones, sin «no entiendo»; "
                  f"{r['botones_ok']} botones que llevan a una respuesta real; {r['recorridos_ok']} turnos de recorridos de varias preguntas (saludo, algo que no entiende, pregunta ajena y luego una consulta concreta) sin colgarse ni cerrarse, con la IA entrando en {r['turnos_donde_entro_la_ia']} turnos; "
                  f"los saludos no gastan tokens; reintentos por cuota del plan gratuito: {r['reintentos_por_cuota']}",
                  f"fallan {len(a)} aperturas, {len(b)} botones y {len(c)} turnos de recorridos (o un saludo gasto tokens, o la IA no entro): {[(x.get('mensaje') or x.get('boton'))[:40] for x in a + b + c]}")
    verificar("Agente", "G7", "Chat conversacional con tokens reales: saludos de cualquier hora e idioma, ayuda sin tema y emociones se acogen con calidez y opciones (sin tokens en los saludos); lo que ninguna regla entiende lo interpreta la IA; cada boton lleva a una respuesta real y la conversacion de varios turnos nunca se cuelga", aperturas_y_botones)

    def cache_gemini_obsoleto():
        return pf(not os.path.isfile(os.path.join(MODELOS, "metricas_agente_gemini.json")), "no queda el JSON de Gemini anterior al endurecimiento de seguridad", "metricas_agente_gemini.json es anterior a las salvaguardas y miente: eliminarlo")
    verificar("Agente", "G4", "No hay metricas de Gemini desfasadas (las anteriores a la seguridad se retiraron)", cache_gemini_obsoleto)


# ------------------------------------------------------------------------------------------------------------------------------------ seguridad y limpieza
def area_seguridad():
    tracked = archivos_versionados()
    texto = [f for f in tracked if f.endswith((".py", ".md", ".yaml", ".yml", ".json", ".toml", ".txt", ".csv", ".ipynb", ".example", ".env"))]

    def secretos():
        pat = re.compile(r"AIza[0-9A-Za-z_\-]{30,}|AQ\.[A-Za-z0-9_\-]{30,}|sk-[A-Za-z0-9]{30,}|ghp_[A-Za-z0-9]{30,}")
        hallados = [f for f in texto if pat.search(leer(f))]
        return pf(not hallados, f"{len(texto)} archivos versionados sin claves de API", f"posibles claves en: {hallados[:5]}")
    verificar("Seguridad", "S1", "Ninguna clave de API en lo versionado", secretos)

    def env():
        p = subprocess.run(["git", "ls-files", "--error-unmatch", ".env"], cwd=RAIZ, capture_output=True, text=True)
        ign = subprocess.run(["git", "check-ignore", "-q", ".env"], cwd=RAIZ).returncode == 0
        return pf(p.returncode != 0 and ign, ".env ignorado y no versionado", ".env esta versionado o no esta ignorado")
    verificar("Seguridad", "S2", ".env no versionado e ignorado", env)

    def rutas():
        propios = [f for f in texto if propio(f) and f.startswith(("src/", "eval/", "tests/", "data/parametros/", "models/", "docs/RESUMEN", "docs/EVALUACION", "docs/comparativa", "docs/QA", "notebooks/"))]
        pat = re.compile(r"[A-Za-z]:\\{1,2}(?:Users|hackathon)|/Users/[A-Za-z]|C:/hackathon")
        # la propia prueba que busca rutas absolutas las nombra: se excluye esta puerta y las pruebas
        hallados = [f for f in propios if pat.search(leer(f)) and not f.startswith("tests/") and f != "eval/puerta_de_calidad.py"]
        return pf(not hallados, f"{len(propios)} archivos propios sin rutas absolutas", f"rutas absolutas en: {hallados[:6]}")
    verificar("Seguridad", "S3", "Sin rutas absolutas de ninguna laptop en codigo, parametros, metricas ni documentos", rutas)

    def marca():
        propios = [f for f in texto if propio(f) and f.startswith(("src/", "eval/", "tests/", "data/parametros/", "docs/RESUMEN", "docs/EVALUACION", "docs/comparativa", "docs/QA", "data/catalogo", "models/")) and f != "eval/puerta_de_calidad.py"]
        pat = re.compile(r"(?i)\bbbva\b|interbank|scotiabank|banco de cr[eé]dito|\bBCP\b")
        hallados = [f for f in propios if pat.search(leer(f))]
        return pf(not hallados, "ninguna mencion a un banco real en lo propio (la entidad es inventada: Banco Kawsay)", f"menciones en: {hallados[:6]}")
    verificar("Seguridad", "S4", "Ninguna mencion a un banco real en codigo, datos, metricas ni documentos propios", marca)

    def pesados():
        grandes = [(f, os.path.getsize(os.path.join(RAIZ, f)) // 2 ** 20) for f in tracked if os.path.getsize(os.path.join(RAIZ, f)) > 50 * 2 ** 20]
        generados = [f for f in tracked if f.startswith("data/generado/")]
        intrusos = [f for f in generados if any(x in f for x in ("cache_", "memoria/", "vivo/"))]   # caches y memoria de pruebas nunca se versionan
        if grandes or intrusos:
            return "FAIL", f"grandes: {grandes}; caches o memoria versionadas: {intrusos[:3]}"
        if generados:
            if "data/generado/_manifiesto.json" in generados:
                return "WARN", f"{len(generados)} archivos de data/generado cargados A PROPOSITO para la integracion final (ver _manifiesto.json, todo sintetico); quitarlos al terminar con: git rm -r --cached data/generado"
            return "FAIL", f"datos generados versionados sin manifiesto: {generados[:3]}"
        return "PASS", "ningun archivo de mas de 50 MB ni datos generados versionados"
    verificar("Seguridad", "S5", "Sin archivos pesados ni datos generados en el repositorio (solo data/sample), salvo la carga temporal documentada", pesados)


# ------------------------------------------------------------------------------------------------------------------------------------ reproducibilidad y frescura
def area_reproducibilidad():
    def dependencias():
        stdlib = set(sys.stdlib_module_names)
        usados = set()
        for carpeta in ("src", "eval", "tests"):
            for ruta in glob.glob(os.path.join(RAIZ, carpeta, "**", "*.py"), recursive=True):
                if not propio(os.path.relpath(ruta, RAIZ).replace(os.sep, "/")):
                    continue   # el agente del producto tiene su propio requirements-ia.txt
                try:
                    arbol = ast.parse(open(ruta, encoding="utf-8").read())
                except SyntaxError:
                    continue
                for nodo in ast.walk(arbol):
                    if isinstance(nodo, ast.Import):
                        usados |= {a.name.split(".")[0] for a in nodo.names}
                    elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0:
                        usados.add(nodo.module.split(".")[0])
        usados -= stdlib | {"src", "tests", "eval"}
        mapa = im.packages_distributions()
        req = {re.split(r"[=<>\[]", ln.strip())[0].lower().replace("_", "-") for ln in leer("requirements-analitica.txt").splitlines() if ln.strip() and not ln.startswith("#")}
        faltan = sorted({mapa[u][0] for u in usados if u in mapa and mapa[u][0].lower().replace("_", "-") not in req})
        sin_mapa = sorted(u for u in usados if u not in mapa)
        if faltan:
            return "FAIL", f"se importan pero no estan en requirements-analitica.txt: {faltan}"
        return ("WARN", f"importaciones sin paquete instalado: {sin_mapa}") if sin_mapa else ("PASS", f"las {len(usados)} bibliotecas de terceros que importa el codigo estan en requirements-analitica.txt")
    verificar("Reproducibilidad", "R1", "Todo lo que importa el codigo esta en requirements-analitica.txt (un companero puede recrear el entorno)", dependencias)

    def frescura():
        """Compara CONTENIDO, no fechas de archivo (un clon o un rebase las reescriben): cada evaluacion guarda la huella del codigo del que depende y cada informe la de las metricas."""
        from src.comun.huella import AGENTE, METRICAS, RAG, huella
        viejos = []
        for nombre, patrones in (("metricas_qa_agente.json", AGENTE), ("metricas_agente_plantillas.json", AGENTE), ("metricas_rag.json", RAG)):
            guardada = J(nombre).get("huella_codigo")
            if guardada is None:
                viejos.append(f"{nombre} (sin huella: volver a correrla)")
            elif guardada != huella(patrones):
                viejos.append(f"{nombre} (el codigo cambio despues de correrla)")
        hm = huella(METRICAS)
        for doc in ("docs/RESUMEN_DIEGO.md", "docs/EVALUACION_ANALITICA.md", "docs/comparativa_modelos.md"):
            m = re.search(r"huella_metricas: ([0-9a-f]{16})", leer(doc))
            if not m:
                viejos.append(f"{doc} (sin huella: regenerarlo)")
            elif m.group(1) != hm:
                viejos.append(f"{doc} (las metricas cambiaron despues de generarlo)")
        return ("FAIL", f"desfasado: {viejos}") if viejos else ("PASS", "las evaluaciones corresponden al codigo actual y los informes a las metricas actuales (huella de contenido)")
    verificar("Reproducibilidad", "R2", "Nada desfasado: cada evaluacion corresponde al codigo actual y cada informe a las metricas actuales (huella de contenido)", frescura)

    def fuentes():
        filas = [r for r in csv.DictReader(open(os.path.join(DOCS_RAG, "fuentes.csv"), encoding="utf-8")) if r["archivo"]]
        fechas = [datetime.fromisoformat(r["fecha_consulta"]).date() for r in filas]
        dias = (reloj.hoy() - max(fechas)).days
        return pf(dias <= 30, f"{len(filas)} fuentes del RAG, ultima consulta hace {dias} dias", f"las fuentes se consultaron hace {dias} dias")
    verificar("Reproducibilidad", "R3", "Las fuentes oficiales del RAG se consultaron en los ultimos 30 dias", fuentes)

    def presentacion():
        idx = leer("docs/presentacion/README.md")
        rutas = re.findall(r"^\| `([^`]+)` \|", idx, re.M)
        faltan = [r for r in rutas if not os.path.isfile(os.path.join(RAIZ, "docs", "presentacion", r))]
        with open(os.path.join(RAIZ, "docs", "comparativa_modelos.csv"), encoding="utf-8") as fh:
            problemas = len({r["problema"] for r in csv.DictReader(fh)})
        modelos = [r for r in rutas if r.startswith("modelos/") and r.endswith(".png") and "comparativa_modelos" not in r and "mejora_en_porcentaje" not in r]   # la de mejora en % es un resumen, no un problema
        sueltos = [f for f in glob.glob(os.path.join(RAIZ, "docs", "presentacion", "**", "*.png"), recursive=True) if os.path.relpath(f, os.path.join(RAIZ, "docs", "presentacion")).replace(os.sep, "/") not in rutas]
        ok = bool(rutas) and not faltan and len(modelos) == problemas and not sueltos and not os.path.isdir(os.path.join(RAIZ, "docs", "figuras"))
        return pf(ok, f"{len(rutas)} artefactos indexados en docs/presentacion/README.md, todos existen: una grafica por cada uno de los {problemas} problemas de la comparativa, diagramas de nodos y graficas de valor",
                  f"faltan {faltan}; graficas sin indexar {[os.path.basename(x) for x in sueltos]}; problemas {problemas} frente a {len(modelos)} graficas de modelos")
    verificar("Reproducibilidad", "R4", "Carpeta de presentacion y documentacion completa: cada artefacto indexado existe, hay una grafica por problema y no quedan figuras sueltas ni duplicadas", presentacion)

    def mlflow_seguimiento():
        from src.comun.huella import METRICAS as PM, huella as hu
        txt = leer("docs/presentacion/mlflow_resumen.md")
        m = re.search(r"huella_metricas: ([0-9a-f]+)", txt)
        if not m:
            return "FAIL", "falta docs/presentacion/mlflow_resumen.md: python eval/registrar_en_mlflow.py"
        if m.group(1) != hu(PM):
            return "FAIL", "el resumen de MLflow esta desfasado (las metricas cambiaron): python eval/registrar_en_mlflow.py"
        filas = re.findall(r"^\| (.+?) \| .+ \| \*\*(.+?)\*\* \|", txt, re.M)
        modelos = re.findall(r"^\| `(lucas-[a-z0-9-]+)` \|", txt, re.M)
        return pf(len(filas) >= 14 and len(modelos) >= 6, f"{len(filas)} comparaciones (baseline frente a elegido) y {len(modelos)} modelos de produccion registrados con alias «produccion»; resumen vigente (huella {m.group(1)})",
                  f"el resumen de MLflow esta incompleto: {len(filas)} comparaciones y {len(modelos)} modelos")
    verificar("Reproducibilidad", "R5", "Seguimiento con MLflow: comparaciones y modelos de produccion registrados, resumen al dia con las metricas", mlflow_seguimiento)

    def modelo_de_datos():
        base = os.path.join(RAIZ, "docs", "modelo_de_datos")
        sql = leer("docs/modelo_de_datos/schema_postgres.sql")
        n = len(re.findall(r"^CREATE TABLE ", sql, re.M))
        val = json.load(open(os.path.join(base, "validacion_postgres.json"), encoding="utf-8"))
        doc = leer("docs/modelo_de_datos/README.md")
        ok = n == val["tablas"] and val["todo_ok"] and doc.count("\n### `") == n and os.path.isfile(os.path.join(RAIZ, "eval", "cargar_a_postgres.py"))
        return pf(ok, f"esquema de {n} tablas (lucas y simulacion) probado contra {val['version_de_postgres'].split(' on ')[0]} con pgvector {val['version_de_pgvector']}: carga completa con conteos iguales a los Parquet, cascadas, restricciones y busqueda vectorial; documento al dia",
                  f"el modelo de datos esta desfasado: {n} tablas en el SQL, {val['tablas']} validadas, {doc.count(chr(10) + '### ')} documentadas")
    verificar("Reproducibilidad", "R6", "Modelo de datos para PostgreSQL: esquema, documento y cargador validados contra una base real", modelo_de_datos)

    def registro_equipo():
        txt = leer(".claude/equipo/diego/registro.md")
        informe = leer("docs/RESUMEN_DIEGO.md")
        ok = all(x in txt for x in ("## Lo que hice", "## Lo que acordamos", "## Lo que falta", "## Informe final completo")) and "## 9. Como integrarlo" in txt.replace("### 9. Como integrarlo", "## 9. Como integrarlo") and len(txt.splitlines()) > len(informe.splitlines())
        return pf(ok, f"informe final guardado en el formato del equipo (.claude/equipo/diego/registro.md): lo que hice, lo que acordamos, lo que falta y el informe completo ({len(txt.splitlines())} lineas)", "falta .claude/equipo/diego/registro.md o esta incompleto: python eval/generar_docs.py")
    verificar("Reproducibilidad", "R7", "Informe final guardado en la rama con el formato del equipo (.claude/equipo/<nombre>/registro.md)", registro_equipo)


NO_VERIFICADO = [
    "Proximo paso: revision del quechua por un hablante nativo (hoy hay evidencia objetiva: FLORES-200, chrF 34 frente a un piso de 18; la respuesta lleva un aviso).",
    "Proximo paso: llamada real a Google Cloud Translation con clave propia (el contrato esta probado con respuestas simuladas y contra su documentacion; una clave de Gemini da 401 en esa API). Se traduce con Gemini.",
    "Proximo paso: piloto con grupo de control del programa de puntos (la rentabilidad a varios anios depende de supuestos de conducta del equipo; con solo lo medido pierde S/ 5.52 por usuario al anio).",
    "Proximo paso, en la rama develop al integrar: las pruebas del agente de Jeffrey (PR #5) y el adaptador al contrato de la API.",
    "Proximo paso: medir la carga en produccion (se midio el costo por consulta en esta laptop, no miles de usuarios simultaneos).",
    "Limite: el set independiente de sentimiento lo escribio un modelo de lenguaje (no personas) y el sentimiento no esta en produccion.",
    "Limite: JUEZ_LLM esta apagado por ahorro de tokens; la verificacion de cifras es determinista y la calidad de redaccion de Gemini se reviso en corridas de QA.",
    "Estado verificado el 2026-11-14 (CTS): la libre disposicion del 100 % vence el 31-12-2026 (Ley 32322, texto oficial) y el proyecto de ley que propone extenderla hasta 2028 (El Peruano, nota 308663, 9-11-2026) esta en evaluacion en el Congreso, no es ley; el agente dice las dos cosas.",
    "Criterio del MVP (cerrado): todo se evaluo con datos sinteticos, como pide el reto; con datos reales de una entidad las metricas seran otras y el generador acepta una tabla semilla (ENAHO) para regenerar.",
]


def escribir(inicio: float) -> int:
    cuenta = {e: sum(1 for x in R if x["estado"] == e) for e in ("PASS", "WARN", "FAIL", "NOT RUN")}
    out = {"fecha": datetime.now().isoformat(timespec="seconds"), "reloj": str(reloj.hoy()), "segundos": round(time.time() - inicio, 1), "cuenta": cuenta, "verificaciones": R, "no_verificado": NO_VERIFICADO}
    json.dump(out, open(os.path.join(MODELOS, "puerta_de_calidad.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    simbolo = {"PASS": "PASS", "WARN": "WARN", "FAIL": "FAIL", "NOT RUN": "NOT RUN"}
    lineas = ["# QA de analítica e IA: puerta de calidad", "",
              f"Generado por `eval/puerta_de_calidad.py` el {out['fecha']} (reloj del agente: {out['reloj']}). Estados: **PASS** cumple; **WARN** conocido y documentado, no bloquea; **FAIL** hay que corregirlo; **NOT RUN** no se pudo verificar y se dice por qué.", "",
              f"**Resultado: {cuenta['PASS']} PASS · {cuenta['WARN']} WARN · {cuenta['FAIL']} FAIL · {cuenta['NOT RUN']} NOT RUN** (de {len(R)} verificaciones, en {out['segundos']} s).", ""]
    for area in dict.fromkeys(x["area"] for x in R):
        lineas += [f"## {area}", "", "| # | Qué se verifica | Estado | Detalle |", "|---|---|---|---|"]
        lineas += [f"| {x['id']} | {x['que']} | **{simbolo[x['estado']]}** | {x['detalle'].replace('|', '/')} |" for x in R if x["area"] == area]
        lineas.append("")
    lineas += ["## Proximos pasos y limites (lo que no se verifico aqui)", "", "Esta lista nunca va vacía: lo que no se verificó se dice, con su motivo y quién lo cierra.", ""] + [f"- {x}" for x in NO_VERIFICADO] + [""]
    with open(os.path.join(RAIZ, "docs", "QA_ANALITICA.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))
    print(f"\nRESULTADO: {cuenta}")
    return 1 if cuenta["FAIL"] else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gemini", action="store_true", help="dos llamadas minimas a Gemini (conexion y traduccion)")
    a = ap.parse_args()
    t0 = time.time()
    area_pruebas()
    area_modelos()
    area_conexiones(a.gemini)
    area_agente()
    area_seguridad()
    area_reproducibilidad()
    return escribir(t0)


if __name__ == "__main__":
    sys.exit(main())
