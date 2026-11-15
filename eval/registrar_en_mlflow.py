"""Seguimiento y versionamiento de los modelos con MLflow.
Registra, desde lo que ya se entreno y se midio (models/*.json y models/*.pkl), dos cosas:
1. Una corrida por CANDIDATO de cada problema (baseline, alternativas y el elegido) con la misma metrica y los mismos numeros de docs/comparativa_modelos.md: en la interfaz de MLflow se ve
   «partimos del baseline y nos quedamos con el ganador», y la grafica de cada problema va como artefacto.
2. Una corrida por MODELO DE PRODUCCION (pronostico a 30 dias, serie diaria, segmentacion, pronostico mensual, glosas, sentimiento) con sus hiperparametros, metricas, version del codigo (git), huella de los
   datos y el archivo del modelo, y lo REGISTRA en el Model Registry con el alias «produccion». Una version nueva solo se crea si el contenido del modelo cambio (hash).
Es idempotente: si las metricas no cambiaron (huella) no vuelve a registrar nada.
El entrenamiento NO depende de MLflow: esto se corre despues de entrenar y de correr eval/comparativa_modelos.py. El seguimiento va a una base local (SQLite) en data/generado/mlflow/ (no se versiona);
para usar el servidor del equipo basta definir MLFLOW_TRACKING_URI.
Uso: python eval/registrar_en_mlflow.py   (abrir la interfaz: mlflow ui --backend-store-uri sqlite:///data/generado/mlflow/lucas.db)
Salida: docs/presentacion/mlflow_resumen.md"""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import warnings

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
warnings.filterwarnings("ignore")

import joblib  # noqa: E402
import mlflow  # noqa: E402
from mlflow.tracking import MlflowClient  # noqa: E402

from src.comun import reloj  # noqa: E402
from src.comun.huella import METRICAS, huella  # noqa: E402
from src.comun.rutas import MODELOS  # noqa: E402

EXPERIMENTO = "lucas-analitica"
CARPETA = os.path.join(RAIZ, "data", "generado", "mlflow")
RESUMEN = os.path.join(RAIZ, "docs", "presentacion", "mlflow_resumen.md")


def uri_por_defecto() -> str:
    return os.environ.get("MLFLOW_TRACKING_URI") or "sqlite:///" + os.path.join(CARPETA, "lucas.db").replace(os.sep, "/")


def _comparativa():
    spec = importlib.util.spec_from_file_location("comparativa_modelos", os.path.join(RAIZ, "eval", "comparativa_modelos.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=RAIZ, capture_output=True, text=True, timeout=10).stdout.strip() or "desconocido"
    except (OSError, subprocess.SubprocessError):
        return "desconocido"


def _sha(ruta: str) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()[:16]


def _experimento(uri: str, artefactos: str | None) -> str:
    mlflow.set_tracking_uri(uri)
    c = MlflowClient()
    e = c.get_experiment_by_name(EXPERIMENTO)
    if e is None:
        raw = artefactos or os.path.join(CARPETA, "artifacts")
        os.makedirs(raw, exist_ok=True)
        return c.create_experiment(EXPERIMENTO, artifact_location=os.path.abspath(raw).replace(os.sep, "/") if "://" not in raw else raw)
    return e.experiment_id


def _planas(d: dict, prefijo: str = "") -> dict:
    """Numeros de un diccionario anidado a metricas planas (nombre con puntos) para que MLflow las grafique."""
    out = {}
    for k, v in d.items():
        k2 = f"{prefijo}{k}".replace(" ", "_").replace("+", "mas").replace(":", "").replace("%", "pct")
        if isinstance(v, dict):
            out.update(_planas(v, k2 + "."))
        elif isinstance(v, (int, float)) and not isinstance(v, bool) and v == v:
            out[k2] = float(v)
    return out


def _modelos_de_produccion() -> list[dict]:
    M = json.load(open(os.path.join(MODELOS, "metricas.json"), encoding="utf-8"))
    P = M["pronostico"]
    SD = json.load(open(os.path.join(MODELOS, "metricas_serie_diaria.json"), encoding="utf-8"))
    MEN = json.load(open(os.path.join(MODELOS, "metricas_pronostico_mensual.json"), encoding="utf-8"))
    CL = json.load(open(os.path.join(MODELOS, "metricas_clasificacion.json"), encoding="utf-8"))
    pk = joblib.load(os.path.join(MODELOS, "pronostico.pkl"))
    seg = M["segmentacion"]
    return [
        {"nombre": "lucas-pronostico-30d", "archivo": "pronostico.pkl", "familia": "LightGBM cuantil + conformal por segmento + clasificador isotonico de rojo",
         "params": {**{f"lgbm_{k}": v for k, v in pk["params"].items()}, "n_features": len(pk["features"]), "alfa_conformal": 0.2, "cortes": json.dumps(P["cortes"]), "datos_hasta": pk.get("datos_hasta", "")},
         "metricas": _planas({"saldo_30d": P["saldo_30d"]["lightgbm_optimizado"], "rojo": P["rojo_30d_anticipacion"]["lightgbm_calibrado"], "baseline_ma3": P["saldo_30d"]["ma3_baseline_plan"]})},
        {"nombre": "lucas-serie-diaria", "archivo": "serie_diaria.pkl", "familia": "LightGBM cuantil por horizontes + interpolacion + conformal por dia",
         "params": {"horizontes_entrenados": json.dumps(SD["horizontes_entrenados"]), "alfa_conformal": 0.2, "cortes": json.dumps(SD["cortes"])},
         "metricas": _planas({"serie": SD["serie_diaria"], "baseline_recta": SD["linea_base_recta_al_dia_30"], "baseline_ma3": SD["linea_base_promedio_movil_3_meses"]})},
        {"nombre": "lucas-segmentacion", "archivo": "segmentacion.pkl", "familia": "K-Prototypes (variables numericas y categoricas)",
         "params": {"k": seg["k"], "umbral_estabilidad": 0.60}, "metricas": _planas({"silueta_gower": seg["silueta_gower"], "ari_arquetipo": {k: v["arquetipo"] for k, v in seg["ari_vs_etiquetas"].items()}})},
        {"nombre": "lucas-pronostico-mensual", "archivo": "pronostico_mensual.pkl", "familia": "LightGBM con recalibracion continua por tipo de trabajo",
         "params": {"horizontes_meses": 6}, "metricas": _planas({"lightgbm": MEN["por_horizonte"]["lightgbm_recalibracion_continua"], "baseline_mismo_mes_anio_previo": MEN["por_horizonte"]["mismo_mes_anio_previo"]})},
        {"nombre": "lucas-glosa-a-categoria", "archivo": "glosa.pkl", "familia": "TF-IDF por caracteres + SGD lineal", "params": {"vectorizador": "tfidf_char", "clasificador": "sgd_lineal"},
         "metricas": _planas({"tfidf_sgd": CL["glosa_a_categoria"]["tfidf_char_sgd_lineal"], "baseline_diccionario": CL["glosa_a_categoria"]["diccionario"]})},
        {"nombre": "lucas-sentimiento", "archivo": "sentimiento.pkl", "familia": "TF-IDF + regresion logistica (no esta en produccion: el texto no mejora el pronostico)", "params": {"vectorizador": "tfidf_1_2gramas", "clasificador": "regresion_logistica"},
         "metricas": _planas(json.load(open(os.path.join(MODELOS, "metricas_sentimiento_independiente.json"), encoding="utf-8")) | {"procedencia": {}, "por_clase": {}, "lectura": ""})}]


def registrar(uri: str | None = None, artefactos: str | None = None, con_pickles: bool = True, resumen: str | None = RESUMEN) -> dict:
    uri = uri or uri_por_defecto()
    os.makedirs(CARPETA, exist_ok=True)
    eid = _experimento(uri, artefactos)
    c = MlflowClient()
    h = huella(METRICAS)
    meta = json.load(open(os.path.join(RAIZ, "data", "generado", "meta.json"), encoding="utf-8")) if os.path.isfile(os.path.join(RAIZ, "data", "generado", "meta.json")) else {}
    comun = {"datos": "sinteticos", "semilla_datos": str(meta.get("semilla", "")), "huella_parametros_datos": json.dumps(meta.get("huella_parametros", {})), "huella_metricas": h, "reloj": str(reloj.hoy()), "commit": _commit()}
    previas = c.search_runs([eid], filter_string=f"tags.huella_metricas = '{h}' and tags.origen = 'registrar_en_mlflow'", max_results=1)
    if previas:
        print(f"MLflow ya tiene este estado de las metricas ({h}): no se duplica nada")
    else:
        cm = _comparativa()
        for p in cm.problemas():
            figura = os.path.join(RAIZ, "docs", "presentacion", "modelos", f"{p['slug']}.png")
            for i, (nombre, valor) in enumerate(p["candidatos"]):
                with mlflow.start_run(experiment_id=eid, run_name=f"{p['slug']} | {nombre}"):
                    mlflow.set_tags({**comun, "origen": "registrar_en_mlflow", "tipo": "comparacion", "problema": p["titulo"], "rol": "elegido" if i == p["elegido"] else "baseline_o_alternativa",
                                     "por_que": p["por_que"][:4900], "limite": p["limite"][:4900]})
                    mlflow.log_params({"problema": p["slug"], "candidato": nombre, "metrica": p["metrica"], "mejor": p["mejor"]})
                    mlflow.log_metric("valor", float(valor))
                    if os.path.isfile(figura):
                        mlflow.log_artifact(figura, "grafica")
        for m in _modelos_de_produccion():
            ruta = os.path.join(MODELOS, m["archivo"])
            with mlflow.start_run(experiment_id=eid, run_name=f"produccion | {m['nombre']}") as run:
                mlflow.set_tags({**comun, "origen": "registrar_en_mlflow", "tipo": "modelo_de_produccion", "modelo": m["nombre"], "familia": m["familia"], "sha256_modelo": _sha(ruta)})
                mlflow.log_params({k: (str(v)[:500]) for k, v in m["params"].items()})
                mlflow.log_metrics(m["metricas"])
                if con_pickles:
                    mlflow.log_artifact(ruta, "modelo")
                mlflow.log_artifact(os.path.join(MODELOS, "metricas.json"), "metricas")
                if con_pickles:
                    _registrar_modelo(c, m, run.info.run_id, ruta, mlflow.get_artifact_uri("modelo") + "/" + m["archivo"], h)
    reg = _resumen(c, eid, h, resumen) if resumen else {}
    return {"experimento": eid, "uri": uri, "huella_metricas": h, **reg}


def _registrar_modelo(c: MlflowClient, m: dict, run_id: str, ruta: str, fuente: str, h: str) -> None:
    """Model Registry: una version nueva solo si el contenido del modelo cambio; el alias «produccion» apunta a la ultima."""
    sha = _sha(ruta)
    try:
        c.get_registered_model(m["nombre"])
    except mlflow.exceptions.MlflowException:
        c.create_registered_model(m["nombre"], description=m["familia"])
    existentes = c.search_model_versions(f"name = '{m['nombre']}'")
    previa = next((v for v in existentes if v.tags.get("sha256_modelo") == sha), None)
    v = previa or c.create_model_version(m["nombre"], source=fuente, run_id=run_id, tags={"sha256_modelo": sha, "huella_metricas": h, "familia": m["familia"]})
    c.set_registered_model_alias(m["nombre"], "produccion", v.version)


def _resumen(c: MlflowClient, eid: str, h: str, destino: str) -> dict:
    runs = c.search_runs([eid], filter_string=f"tags.huella_metricas = '{h}' and tags.origen = 'registrar_en_mlflow'", max_results=1000)
    comp = [r for r in runs if r.data.tags.get("tipo") == "comparacion"]
    prod = [r for r in runs if r.data.tags.get("tipo") == "modelo_de_produccion"]
    por_problema: dict = {}
    for r in comp:
        por_problema.setdefault(r.data.params["problema"], []).append(r)
    L = ["# Seguimiento de modelos con MLflow", "",
         f"Generado por `eval/registrar_en_mlflow.py` (huella de las metricas `{h}`). Experimento **{EXPERIMENTO}**; base local `data/generado/mlflow/lucas.db` (no se versiona) o el servidor definido en `MLFLOW_TRACKING_URI`. "
         "Abrir la interfaz: `mlflow ui --backend-store-uri sqlite:///data/generado/mlflow/lucas.db`.", "",
         "## Comparacion por problema: baseline frente al elegido", "",
         "Cada fila es una corrida de MLflow con la misma metrica y los mismos numeros de `docs/comparativa_modelos.md`; en la interfaz se pueden comparar las corridas de un mismo problema.", "",
         "| Problema | Metrica | Elegido | Valor del elegido | Baselines y alternativas |", "|---|---|---|---|---|"]
    for slug, rs in sorted(por_problema.items()):
        el = next(r for r in rs if r.data.tags["rol"] == "elegido")
        otros = "; ".join(f"{r.data.params['candidato']}: {r.data.metrics['valor']:.3g}" for r in rs if r is not el)
        L.append(f"| {el.data.tags['problema']} | {el.data.params['metrica']} ({el.data.params['mejor']} es mejor) | **{el.data.params['candidato']}** | {el.data.metrics['valor']:.3g} | {otros} |")
    L += ["", "## Modelos de produccion registrados (Model Registry)", "", "| Modelo | Familia | Version | Alias | Hash del archivo |", "|---|---|---|---|---|"]
    versiones = {}
    for r in prod:
        n = r.data.tags["modelo"]
        try:
            rm = c.get_registered_model(n)
            alias = rm.aliases.get("produccion")
            vs = c.search_model_versions(f"name = '{n}'")
            versiones[n] = len(vs)
            L.append(f"| `{n}` | {r.data.tags['familia']} | v{alias} de {len(vs)} | produccion | `{r.data.tags['sha256_modelo']}` |")
        except mlflow.exceptions.MlflowException:
            L.append(f"| `{n}` | {r.data.tags['familia']} | sin registrar | | `{r.data.tags['sha256_modelo']}` |")
    L += ["", "## Como se usa", "",
          "- **Versionar:** tras entrenar, correr `python eval/comparativa_modelos.py` y luego `python eval/registrar_en_mlflow.py`. Si el contenido de un modelo cambio, se crea una version nueva y el alias `produccion` pasa a ella; si no, no se duplica nada.",
          "- **Cargar el modelo en produccion:** `MlflowClient().get_model_version_by_alias('lucas-pronostico-30d', 'produccion')` da el origen del archivo; se carga con `joblib.load`.",
          "- **Servidor del equipo:** definir `MLFLOW_TRACKING_URI=http://servidor:5000` y volver a correr; las corridas y los modelos van al servidor central.",
          "- **Alcance:** el entrenamiento no esta instrumentado con autologging (los modelos son clases propias de LightGBM con calibracion conformal); el registro se hace desde las metricas y los archivos guardados, con la version del codigo (`commit`), la huella de los parametros de los datos y la semilla. Todo con datos sinteticos.", "",
          f"<!-- huella_metricas: {h} -->", ""]
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    return {"corridas_de_comparacion": len(comp), "problemas": len(por_problema), "modelos_de_produccion": len(prod), "versiones": versiones}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    r = registrar()
    print(json.dumps(r, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
