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
    def pytest_todo():
        p = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
        ult = [ln for ln in p.stdout.strip().splitlines() if "passed" in ln or "failed" in ln or "error" in ln]
        return pf(p.returncode == 0, ult[-1] if ult else "", (ult[-1] if ult else p.stdout[-300:]))
    verificar("Pruebas", "P1", "Toda la suite de pruebas (pytest)", pytest_todo)

    def ruff():
        p = subprocess.run([sys.executable, "-m", "ruff", "check", "src", "eval", "tests", "--select", "F401,F821,F841,E9,PLE2510,F811"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
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

    verificar("Modelos", "M8", "Sentimiento: el modelo entrenado generaliza a frases escritas a mano", lambda: ("WARN", f"no: F1 {C['sentimiento']['escritas_a_mano']['tfidf_lr_f1']:.2f} con {C['sentimiento']['escritas_a_mano']['n']} frases contra {C['sentimiento']['plantillas_futuras']['tfidf_lr_f1']:.2f} en plantillas. Documentado; no esta en produccion."))

    def impacto():
        d = IM["diferencias"]["lucas_vs_nada"]["dias_rojo_evitados_por_cliente_mes"]
        return pf(d["ic95"][0] > 0, f"{d['media']:.2f} dias en rojo evitados por cliente al mes (IC95 {d['ic95'][0]:.2f} a {d['ic95'][1]:.2f})", f"el IC95 incluye 0: {d['ic95']}")
    verificar("Modelos", "M9", "Politica de ahorro: reduce los dias en rojo frente a no hacer nada con IC95 que excluye 0", impacto)

    def colchon():
        t = IM["tabla"]
        mas = t["diez_fijo_ajustado"]["colchon_final_meses_de_ingreso"] - t["lucas"]["colchon_final_meses_de_ingreso"]
        return ("WARN", f"el 10 % fijo ajustado forma {mas:.1f} meses mas de colchon que Lucas. Hallazgo abierto, documentado.") if mas > 0 else ("PASS", "")
    verificar("Modelos", "M10", "Politica de ahorro: Lucas forma al menos tanto colchon como ahorrar 10 % fijo ajustado", colchon)

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
        return ("WARN", f"sin consumo nuevo pierde S/ {-n:.2f} por usuario al anio; se paga con {c['mas_consumo_necesario_para_pagarse']:.1%} mas de consumo elegible. Necesita piloto.") if n < 0 else ("PASS", f"neto S/ {n:.2f}")
    verificar("Modelos", "M12", "Programa de puntos: rentable sin depender de consumo nuevo", puntos_valor)

    def eventos():
        t = leer("data/parametros/eventos.yaml")
        n = {k: len(re.findall(k, t)) for k in ("verificado", "parcial", "supuesto")}
        return ("WARN", f"parametros de eventos: {n['verificado']} verificado, {n['parcial']} parciales y {n['supuesto']} supuestos. Declarados en el YAML; hay que verificarlos antes de afirmarlos.") if n["parcial"] + n["supuesto"] else ("PASS", "")
    verificar("Modelos", "M13", "Parametros de los eventos simulados (retiros de AFP, bonos, covid, Nino): verificados en fuente", eventos)

    def calidad_datos():
        t = leer("data/QUALITY.md")
        return pf(bool(t) and "Trazabilidad" in t and not re.search(r"(?i)\bfalla\b|no cumple", t), "informe de calidad presente con trazabilidad (semilla, huella de parametros)", "falta data/QUALITY.md o reporta una falla")
    verificar("Modelos", "M14", "Datos sinteticos: informe de calidad y trazabilidad presentes y sin fallas reportadas", calidad_datos)


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
    verificar("Conexiones", "C9", "Google Cloud Translation", lambda: ("NOT RUN", "no hay GOOGLE_TRANSLATE_API_KEY (la clave de Gemini no se usa con otras APIs de Google). Se traduce con Gemini.") if not os.environ.get("GOOGLE_TRANSLATE_API_KEY") else ("PASS", "clave presente"))
    verificar("Conexiones", "C10", "Calidad del quechua revisada por un hablante nativo", lambda: ("NOT RUN", "no hay revision de un hablante nativo; el aviso al usuario lo dice"))

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
        return pf(not mal and r["tokens_gemini"]["entrada"] < 80_000, f"Gemini real: perfil {r['perfil_ok']}, adversas {r['adversas_ok']}, datos vivos y idiomas OK, {r['tokens_gemini']['llamadas']} llamadas y {r['tokens_gemini']['entrada']:,} tokens de entrada", f"{mal}")
    verificar("Agente", "G2", "QA con Gemini real (una sola corrida): perfil, calendario, premisa falsa, datos vivos, idiomas y adversarios", qa)

    def diagramas():
        d = J("metricas_agente_plantillas.json")["diagramas"]
        return pf(all(not os.path.isabs(v) and os.path.isfile(os.path.join(RAIZ, v)) for v in d.values()), "los dos diagramas de nodos existen y se citan con ruta relativa", f"{d}")
    verificar("Agente", "G3", "Diagramas de nodos del agente generados, con rutas relativas", diagramas)

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
        propios = [f for f in texto if f.startswith(("src/", "eval/", "tests/", "data/parametros/", "models/", "docs/RESUMEN", "docs/EVALUACION", "docs/comparativa", "docs/QA", "notebooks/"))]
        pat = re.compile(r"[A-Za-z]:\\{1,2}(?:Users|hackathon)|/Users/[A-Za-z]|C:/hackathon")
        # la propia prueba que busca rutas absolutas las nombra: se excluye esta puerta y las pruebas
        hallados = [f for f in propios if pat.search(leer(f)) and not f.startswith("tests/") and f != "eval/puerta_de_calidad.py"]
        return pf(not hallados, f"{len(propios)} archivos propios sin rutas absolutas", f"rutas absolutas en: {hallados[:6]}")
    verificar("Seguridad", "S3", "Sin rutas absolutas de ninguna laptop en codigo, parametros, metricas ni documentos", rutas)

    def marca():
        propios = [f for f in texto if f.startswith(("src/", "eval/", "tests/", "data/parametros/", "docs/RESUMEN", "docs/EVALUACION", "docs/comparativa", "docs/QA", "data/catalogo", "models/")) and f != "eval/puerta_de_calidad.py"]
        pat = re.compile(r"(?i)\bbbva\b|interbank|scotiabank|banco de cr[eé]dito|\bBCP\b")
        hallados = [f for f in propios if pat.search(leer(f))]
        return pf(not hallados, "ninguna mencion a un banco real en lo propio (la entidad es inventada: Banco Kawsay)", f"menciones en: {hallados[:6]}")
    verificar("Seguridad", "S4", "Ninguna mencion a un banco real en codigo, datos, metricas ni documentos propios", marca)

    def pesados():
        grandes = [(f, os.path.getsize(os.path.join(RAIZ, f)) // 2 ** 20) for f in tracked if os.path.getsize(os.path.join(RAIZ, f)) > 50 * 2 ** 20]
        generados = [f for f in tracked if f.startswith("data/generado/")]
        return pf(not grandes and not generados, "ningun archivo de mas de 50 MB ni datos generados versionados", f"grandes: {grandes}; generados: {generados[:3]}")
    verificar("Seguridad", "S5", "Sin archivos pesados ni datos generados en el repositorio (solo data/sample)", pesados)


# ------------------------------------------------------------------------------------------------------------------------------------ reproducibilidad y frescura
def area_reproducibilidad():
    def dependencias():
        stdlib = set(sys.stdlib_module_names)
        usados = set()
        for carpeta in ("src", "eval", "tests"):
            for ruta in glob.glob(os.path.join(RAIZ, carpeta, "**", "*.py"), recursive=True):
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
        def mt(rutas):
            fs = [f for r in rutas for f in glob.glob(os.path.join(RAIZ, r), recursive=True)]
            return max(os.path.getmtime(f) for f in fs)
        codigo_agente = mt(["src/agente_analitico/*.py", "src/models/calendario_laboral.py", "src/models/recomendador.py", "data/parametros/normas_laborales.yaml", "src/rag/*.py", "src/bcrp/*.py"])
        codigo_rag = mt(["src/rag/*.py", "docs/rag/indice/*", "data/parametros/preguntas_rag.yaml"])
        viejos = []
        for nombre, dep in (("metricas_qa_agente.json", codigo_agente), ("metricas_agente_plantillas.json", codigo_agente), ("metricas_rag.json", codigo_rag)):
            if os.path.getmtime(os.path.join(MODELOS, nombre)) < dep:
                viejos.append(nombre)
        metricas = max(os.path.getmtime(f) for f in glob.glob(os.path.join(MODELOS, "metricas*.json")))
        for doc in ("docs/RESUMEN_DIEGO.md", "docs/EVALUACION_ANALITICA.md", "docs/comparativa_modelos.md"):
            if not os.path.isfile(os.path.join(RAIZ, doc)) or os.path.getmtime(os.path.join(RAIZ, doc)) < metricas:
                viejos.append(doc)
        return ("WARN", f"anteriores al codigo o a las metricas de las que dependen (regenerar): {viejos}") if viejos else ("PASS", "metricas y documentos son posteriores al codigo y a los datos de los que dependen")
    verificar("Reproducibilidad", "R2", "Nada desfasado: metricas posteriores al codigo del agente y del RAG, y documentos posteriores a las metricas", frescura)

    def fuentes():
        filas = [r for r in csv.DictReader(open(os.path.join(DOCS_RAG, "fuentes.csv"), encoding="utf-8")) if r["archivo"]]
        fechas = [datetime.fromisoformat(r["fecha_consulta"]).date() for r in filas]
        dias = (reloj.hoy() - max(fechas)).days
        return pf(dias <= 30, f"{len(filas)} fuentes del RAG, ultima consulta hace {dias} dias", f"las fuentes se consultaron hace {dias} dias")
    verificar("Reproducibilidad", "R3", "Las fuentes oficiales del RAG se consultaron en los ultimos 30 dias", fuentes)


NO_VERIFICADO = [
    "Calidad del quechua: no la revisó un hablante nativo; la respuesta lleva un aviso.",
    "Google Cloud Translation: no hay clave propia (la de Gemini no se usa con otras APIs); se traduce con Gemini.",
    "Datos reales de un banco: todo se evaluó con datos sintéticos; con datos reales las métricas serán otras.",
    "Sentimiento: no hay un set independiente de frases etiquetadas por personas (solo 24 escritas a mano por el equipo).",
    "Parámetros de los eventos simulados (retiros de AFP, bonos, covid, Niño): solo 1 de 18 está marcado como verificado; el resto son parciales o supuestos del equipo.",
    "Serie diaria del pronóstico: el modelo está calibrado en el día 30 y en el día de riesgo; una serie de 30 días con banda al 80 % por día no está entrenada ni validada.",
    "Redacción con juez LLM: JUEZ_LLM está apagado por ahorro de tokens; la verificación de cifras es determinista, y la calidad de redacción de Gemini se revisó en una sola corrida de QA.",
    "Carga en producción: se midió el costo por consulta en esta laptop, no el rendimiento con miles de usuarios simultáneos.",
    "Fuente de la libre disposición de la CTS después de 2026: se verificó la Ley 32322 (texto oficial); cualquier cambio posterior a 2026-11-14 no se conoce hasta volver a contrastarla.",
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
    lineas += ["## Lo que NO se pudo verificar", "", "Esta lista nunca va vacía: lo que no se verificó se dice.", ""] + [f"- {x}" for x in NO_VERIFICADO] + [""]
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
