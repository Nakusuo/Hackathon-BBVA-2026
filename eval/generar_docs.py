"""Genera docs/EVALUACION_ANALITICA.md y docs/RESUMEN_DIEGO.md con las cifras de models/metricas*.json. Ningun numero se escribe a mano.
Uso: python eval/generar_docs.py"""
import csv
import json
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pandas as pd  # noqa: E402

from src.comun.rutas import MODELOS, ruta  # noqa: E402
from src.generador.reporte import _md  # noqa: E402


def cargar(nombre):
    p = os.path.join(MODELOS, nombre)
    return json.load(open(p, encoding="utf-8")) if os.path.isfile(p) else None


def T(d, dec=3, cols=None):
    if d is None:
        return "_pendiente_\n"
    df = pd.DataFrame(d).T if isinstance(d, dict) else pd.DataFrame(d)
    if cols:
        df = df[[c for c in cols if c in df.columns]]
    return _md(df.round(dec), dec) + "\n"


def f(x, d=3):
    return "n/d" if x is None else f"{x:.{d}f}"


base = cargar("metricas.json") or {}
SEG = base.get("segmentacion") or cargar("metricas_segmentacion.json")
PRO = base.get("pronostico") or cargar("metricas_pronostico.json")
MEN = cargar("metricas_pronostico_mensual.json")
CLA = cargar("metricas_clasificacion.json")
IMP = cargar("metricas_impacto.json")
RAG = cargar("metricas_rag.json")
AGU = cargar("metricas_agente_plantillas.json")
QA = cargar("metricas_qa_agente.json")
GATE = cargar("puerta_de_calidad.json")
ESC = cargar("metricas_escala.json")
VAL = cargar("metricas_valor.json")


def seccion_segmentacion():
    if not SEG:
        return "_pendiente_\n"
    s = SEG
    return (f"K elegido: **{s['k']}** (mayor silueta entre los k con estabilidad de al menos 0,60).\n\n{T(s['tabla_k'])}\nSilueta de Gower: " + ", ".join(f"{k} {v:.3f}" for k, v in s["silueta_gower"].items()) +
            f".\n\nARI frente a las etiquetas de referencia (solo se usan para evaluar):\n\n{T(s['ari_vs_etiquetas'])}\nSegmentos y nivel asignado:\n\n" +
            T(s["descripcion"], 2, ["nivel", "n", "salud_mediana", "ingreso_medio", "cv_ingreso", "ahorro_pct", "gasto_sobre_ingreso", "dias_rojo_3m", "colchon_observado"]) +
            f"\nArranque en frio (nivel a partir de lo declarado): precision {s['arranque_en_frio_precision']:.3f} frente a {s['referencia_clase_mayoritaria']:.3f} de la clase mayoritaria.\n")


def seccion_pronostico():
    if not PRO:
        return "_pendiente_\n"
    p = PRO
    eq = p["equidad_por_grupo"]
    txt = f"Cortes con purga de {30} dias: {p['cortes']}. Origenes: {p['origenes']}.\n\n### Saldo a 30 dias\n\n{T(p['saldo_30d'])}\n"
    txt += "MAE relativo ponderado por la poblacion objetivo: {k: round(v,3)} -> " + ", ".join(f"{k} {v:.3f}" for k, v in p["mae_rel_ponderado"].items()) + ".\n\n"
    txt += f"Optuna ({p['optuna']['_n_trials']} intentos): pinball {p['optuna']['_mejor_pinball']:.4f}.\n\n### Anticipacion del rojo (solo con saldo positivo en el origen)\n\n"
    txt += T({k: v for k, v in p["rojo_30d_anticipacion"].items() if isinstance(v, dict)}) + f"\nTasa de positivos {p['rojo_30d_anticipacion']['tasa_positivos']:.3f} sobre {p['rojo_30d_anticipacion']['n']} origenes.\n\n### Dia de riesgo\n\n{T(p['dia_de_riesgo'], 2)}\n"
    txt += "### Equidad por grupo (con pesos muestrales)\n\nAlerta si la cobertura difiere mas de 5 puntos o el error de un grupo supera 1,3 veces el del mejor.\n\n"
    for g, e in eq.items():
        b = e["brechas"]
        txt += f"**{g}**: brecha de cobertura {b['brecha_cobertura']:.3f}, razon de error {b['razon_mae']:.2f}, alerta: {'SI' if b['alerta'] else 'no'} (peor error: {b['peor_grupo_mae']}).\n\n{T(e['tabla'])}\n"
    txt += f"### Remuestreo del riesgo de rojo\n\n{T(p['remuestreo_rojo'])}\n### Perturbaciones\n\n{T(p['perturbaciones'])}\n### Evento no visto (confinamiento fuera del entrenamiento)\n\n{T(p['evento_no_visto_confinamiento'])}\n"
    t = p["texto_en_el_pronostico"]
    txt += (f"### Datos no estructurados en el pronostico\n\nMAE relativo sin texto {t['sin_texto']['mae_rel_ingreso']:.4f}, con texto {t['con_texto']['mae_rel_ingreso']:.4f}; mejora media {t['mejora_mae_rel']['media']:.5f} "
            f"(IC95 {t['mejora_mae_rel']['ic95'][0]:.5f} a {t['mejora_mae_rel']['ic95'][1]:.5f}). PR-AUC del rojo: {t['rojo_pr_auc_sin']:.3f} sin texto, {t['rojo_pr_auc_con']:.3f} con texto.\n")
    return txt


def seccion_mensual():
    if not MEN:
        return "_pendiente_\n"
    txt = f"Ventanas: {MEN['ventanas']}\n\n"
    cols = ["ing_mae_rel", "ing_cobertura", "gas_mae_rel", "gas_cobertura", "net_cobertura"]
    for k, v in MEN["por_horizonte"].items():
        txt += f"**{k}** (por horizonte, en meses)\n\n{T(v, 3, cols)}\n"
    for g in ("tipo", "seg", "region", "edad"):
        txt += f"**Por {g}** (LightGBM con recalibracion continua)\n\n{T(MEN['por_' + g]['lightgbm_recalibracion_continua'], 3)}\n"
    return txt


def seccion_clasificacion():
    if not CLA:
        return "_pendiente_\n"
    c = CLA
    g = c["glosa_a_categoria"]
    return (f"**Glosa a categoria** (prueba 2024-2025, {g['n_prueba']} movimientos): diccionario F1 macro {g['diccionario']['f1_macro']:.3f}, exactitud {g['diccionario']['exactitud']:.3f}; "
            f"TF-IDF + lineal F1 macro {g['tfidf_char_sgd_lineal']['f1_macro']:.3f}, exactitud {g['tfidf_char_sgd_lineal']['exactitud']:.3f}. Cobertura del diccionario {g['cobertura_diccionario']:.4f}.\n\n"
            f"**Recurrentes** ({c['recurrentes']['n_clientes']} clientes):\n\n{T({k: v for k, v in c['recurrentes'].items() if isinstance(v, dict)})}\n"
            f"**Suscripciones duplicadas** (por cliente): {json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in c['suscripciones_duplicadas'].items()})}\n\n"
            f"**Atipicos** ({c['atipicos']['n_atipicos']} en {c['atipicos']['n']} gastos): precision en k, z-score robusto {c['atipicos']['zscore_robusto']['precision_en_k']:.3f}, "
            f"IsolationForest {c['atipicos']['isolation_forest']['precision_en_k']:.3f}.\n\n**Sentimiento** (F1 macro):\n\n{T(c['sentimiento'])}\n"
            "Aviso: sobre plantillas el modelo es trivial; sobre las 24 frases escritas a mano baja. El lexico se armo viendo esas mismas frases, asi que su cifra es optimista y no vale como prueba. "
            "El set independiente de 100 frases lo escribe el equipo (TODOS-01); mientras tanto el texto libre se clasifica mejor con un modelo preentrenado en espanol.\n")


def seccion_impacto():
    if not IMP:
        return "_pendiente_\n"
    d = IMP["diferencias"]
    txt = f"Periodo {IMP['meses']:.0f} meses (2024-2025), ponderado por la poblacion objetivo. Supuestos: {json.dumps(IMP['supuestos'], ensure_ascii=False)}\n\n{T(IMP['tabla'])}\n"
    for k in ("lucas_vs_nada", "lucas_vs_diez_fijo_ajustado", "diez_fijo_ajustado_vs_nada", "diez_fijo_vs_nada"):
        if k in d:
            txt += f"**{k}**: " + "; ".join(f"{a} {b['media']:.3f} (IC95 {b['ic95'][0]:.3f} a {b['ic95'][1]:.3f})" for a, b in d[k].items()) + "\n\n"
    txt += f"Por segmento:\n\n{T(IMP['por_segmento'], 2)}\n"
    return txt


def seccion_rag_agente():
    txt = ""
    if RAG:
        r0 = next(iter(RAG["recuperacion"].values()))
        f1, cu = RAG["filtro_relevancia"], RAG["filtro_relevancia"]["con_los_umbrales_actuales"]
        txt += (f"**Recuperacion** ({r0['n']} preguntas con respuesta escritas a mano, {r0['n_compuestas']} de ellas compuestas; k=4; las columnas separan simples y compuestas):\n\n{T(RAG['recuperacion'], 3)}\n"
                f"**Filtro de relevancia tipo CRAG** (umbral 0.70 en uso, {f1['n_con_respuesta']} preguntas con respuesta y {f1['n_fuera']} fuera del indice): acepta {round(cu['con_respuesta_aceptadas'] * f1['n_con_respuesta'])} de {f1['n_con_respuesta']} y rechaza "
                f"{round(cu['fuera_rechazadas'] * f1['n_fuera'])} de {f1['n_fuera']}; AUC {f1['auc']:.3f}; el umbral optimo medido es {f1['umbral']:.3f}. Se calibra con las mismas preguntas con las que se reporta: la cifra es optimista. "
                f"Las siglas del dominio (TCEA, CTS, EPS...) se expanden antes de buscar; esa tecnica se motivo por un fallo de esta misma evaluacion, asi que ese caso no es prueba independiente. "
                f"Partir las preguntas compuestas y MMR no mejoraron nada medible y quedan apagados; con {r0['n']} preguntas, una sola mueve el recall {1 / r0['n']:.3f}.\n\n")
    if AGU:
        txt += ("**Agente con plantillas (determinista, sin LLM, reproducible y sin costo)**. La politica de ahorro de tokens usa el LLM solo para lo que una plantilla no cubre bien; esta evaluacion mide el piso determinista: ruteo, cifras, salvaguardas.\n\n"
                + T({m: AGU[m]["resumen"] for m in ("agente_unico", "multiagente") if m in AGU}, 3) + f"\nFallos de ruteo (agente unico): {AGU['agente_unico']['fallos_de_ruteo'] or 'ninguno'}\n\n")
    if QA:
        r = QA["resumen"]
        lat = [x["segundos"] for x in QA["perfil"]]
        txt += (f"**Agente con Gemini real (una sola corrida de QA, `LLM_USO=siempre`, reloj fijo {r['reloj_fijo']})**: preguntas de perfil {r['perfil_ok']}, pedidos adversarios {r['adversas_ok']}, datos vivos y vigilancia {'OK' if r['datos_vivos_ok'] else 'con fallas'}, "
                f"traduccion {', '.join(f'{k} {"OK" if v else "con fallas"}' for k, v in r['idiomas'].items())}; {r['tokens_gemini']['llamadas']} llamadas y {r['tokens_gemini']['entrada']:,} tokens de entrada con `{r['modelo']}`; "
                f"latencia media por respuesta {sum(lat) / len(lat):.1f} s. Detalle de cada respuesta en `models/metricas_qa_agente.json`. El juez LLM esta apagado (`JUEZ_LLM=0`): la verificacion de cifras es determinista.\n\n")
    return txt or "_pendiente_\n"


def seccion_calendario():
    from src.agente_analitico import datos_vivos as DV, repositorio as RP, vigilancia as VG
    from src.models import calendario_laboral as CL
    c = CL.cfg()
    g, ld = c["gratificacion"], c["libre_disposicion"]
    bon = g["bonificacion_extraordinaria"]
    doc = lambda sec: ", ".join(f"`{d}`" for d in sorted({e["doc"] for e in c[sec]["evidencia"]}))  # noqa: E731
    return (f"Las reglas viven en `data/parametros/normas_laborales.yaml` y **cada una lleva su frase literal** de un documento oficial guardado en `docs/rag/`; `tests/test_calendario.py` comprueba que la frase siga en el documento. "
            f"Se contrastaron el {c['fecha_verificacion']} y el agente avisa si pasaron mas de {c['dias_para_revisar']} dias.\n\n"
            "| Regla | Que dice | Evidencia |\n|---|---|---|\n"
            f"| Gratificacion | Se paga en la primera quincena de julio y diciembre (limite el 15); equivale a una remuneracion integra por semestre completo, proporcional por meses calendarios completos; bonificacion extraordinaria de {bon['essalud']:.0%} (EsSalud) o {bon['eps']:.2%} (EPS), no remunerativa ni pensionable | {doc('gratificacion')} |\n"
            f"| Deposito de CTS | Hasta el 15 de mayo y el 15 de noviembre; si el 15 es inhabil, el siguiente dia habil. Dozavos de la remuneracion computable (que suma un sexto de la gratificacion del semestre) por meses completos; la fraccion, por treintavos | {doc('cts')} |\n"
            f"| Retiro de la CTS | Hasta el {ld['vigente_hasta']} se puede disponer libremente del {ld['porcentaje_transitorio']:.0%} de lo depositado en entidades financieras; despues rige el tope permanente de {ld['porcentaje_permanente']:.0%} (100 % por enfermedad terminal o cancer). {ld['nota_proyectos']} | {doc('libre_disposicion')} |\n"
            f"| A quien aplica | {c['alcance']['aplica_a']}. No aplica a independientes. Supuesto del equipo: {c['alcance']['supuesto_del_equipo']} | {doc('alcance')} |\n\n"
            "La base de los montos es la ultima gratificacion real del cliente (equivale a una remuneracion); si no la hay, su ingreso medio, marcado como supuesto y con confianza media. Todo monto es una estimacion y se dice asi.\n\n"
            "**Datos vivos y vigilancia.** El aplicativo envia cada movimiento (`datos_vivos.registrar`): se valida (tipo, monto finito y positivo, fecha que no sea futura), es idempotente ante reintentos, la glosa solo sirve para sugerir la categoria con el clasificador "
            f"(confianza minima {DV.UMBRAL_GLOSA:.2f}; si no esta seguro queda en `otros`) y **no se guarda**. El agente suma lo que entro al saldo; el riesgo a 30 dias se reestima con el modelo solo si el cierre de datos no pasa de "
            f"{RP.VENTANA_RECALCULO_DIAS} dias. La vigilancia avisa una sola vez cada hecho y como maximo 3 por semana, de lo mas urgente a lo menos: riesgo de rojo, gratificacion que no llego (solo a quien ya recibio una y con informacion reciente), "
            f"ingreso extraordinario (>= 50 % de un ingreso mensual), gasto atipico (>= {VG.GASTO_ATIPICO_FRACCION:.0%} del ingreso y que no sea un pago recurrente), fechas del calendario laboral (a {VG.DIAS_AVISO_CALENDARIO} dias o menos), fin cercano del retiro total de la CTS, baja de la tasa del BCRP (solo con el dato al dia) y comunicado nuevo del ENFEN. "
            "Los datos publicos dicen de que fecha son y de donde vienen (API, cache o serie grabada); uno desactualizado no se presenta como actual.\n")


def seccion_qa():
    txt = ("La puerta de calidad (`python eval/puerta_de_calidad.py --gemini`) reune pruebas, metricas de los modelos, conexiones en tiempo real, agente, seguridad y frescura, y reporta PASS, WARN (conocido y documentado), FAIL o NOT RUN con el motivo. "
           "El detalle completo, incluida la lista de **lo que no se pudo verificar**, esta en [QA_ANALITICA.md](QA_ANALITICA.md).\n\n")
    if GATE:
        c = GATE["cuenta"]
        txt += f"Ultima corrida ({GATE['fecha']}): **{c['PASS']} PASS, {c['WARN']} WARN, {c['FAIL']} FAIL, {c['NOT RUN']} NOT RUN**.\n\n"
        otros = [x for x in GATE["verificaciones"] if x["estado"] in ("WARN", "NOT RUN")]
        txt += "| # | Estado | Que | Detalle |\n|---|---|---|---|\n" + "\n".join(f"| {x['id']} | {x['estado']} | {x['que']} | {x['detalle'].replace('|', '/')} |" for x in otros) + "\n\n"
    txt += "La comparativa de modelos (candidatos medidos, el elegido y por que, con su limite) esta en [comparativa_modelos.md](comparativa_modelos.md) y sus graficas en `docs/figuras/`.\n"
    return txt


def _filas_csv(*partes) -> list[dict]:
    p = ruta(*partes)
    if not os.path.isfile(p):
        return []
    with open(p, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def seccion_inventario() -> str:
    """Cuantos archivos y lineas hay por carpeta, desde git: el inventario no se escribe a mano."""
    ar = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
    grupos = [("src/generador", "Generador de datos sinteticos por lotes: clientes, simulacion, texto, calidad y reporte"),
              ("src/models", "Segmentacion, salud financiera, pronostico (30 dias y por meses), clasificacion, recomendador, ofertas, niveles, programa de puntos, calendario laboral e impacto"),
              ("src/rag", "Indice FAISS y BM25, busqueda, expansion de siglas y evaluacion del RAG"),
              ("src/agente_analitico", "Agente LangGraph (unico y multiagente), proveedores de LLM, juez de cifras, traduccion, datos vivos, vigilancia y memoria"),
              ("src/bcrp", "Cliente de las series del BCRP con respaldo y frescura"), ("src/datos_publicos", "Descarga de fuentes oficiales con hash y estado"), ("src/comun", "Rutas, reloj unico y huella de contenido"),
              ("eval", "Entrenamiento, evaluaciones, QA con Gemini, comparativa de modelos, puerta de calidad y generacion de documentos"), ("tests", "Pruebas (no necesitan red ni Gemini)"),
              ("data/parametros", "Toda la configuracion en YAML: generador, eventos, niveles y puntos, normas laborales, entidad, zonas del Nino, preguntas del RAG"),
              ("models", "Modelos entrenados (.pkl) y metricas (.json)"), ("docs/rag", "Fuentes del RAG (PDF y texto), su registro y el indice vectorial"), ("notebooks", "Cinco notebooks ejecutados")]
    filas = []
    for pref, que in grupos:
        fs = [f for f in ar if f.startswith(pref + "/")]
        lineas = 0
        for f in fs:
            if f.endswith((".py", ".yaml", ".md", ".ipynb", ".json", ".csv", ".txt")) and os.path.getsize(os.path.join(RAIZ, f)) < 3_000_000:
                with open(os.path.join(RAIZ, f), encoding="utf-8", errors="ignore") as fh:
                    lineas += sum(1 for _ in fh)
        filas.append(f"| `{pref}/` | {que} | {len(fs)} | {lineas:,} |")
    return "| Carpeta | Que contiene | Archivos | Lineas |\n|---|---|---|---|\n" + "\n".join(filas) + f"\n\nTotal versionado en esta rama: {len(ar)} archivos.\n"


def seccion_datos_reales() -> str:
    from src.bcrp.cliente import CACHE, SERIES, TTL_SEGUNDOS
    rag = _filas_csv("docs", "rag", "fuentes.csv")
    hechas = [r for r in rag if r["archivo"]]
    pendientes = [r for r in rag if not r["archivo"]]
    L = ["Todo lo que el agente afirma sobre el mundo real sale de una de estas fuentes. **Los datos de los clientes son sinteticos**; lo real son las normas, los indicadores publicos y las guias.\n",
         "### 8.1 Documentos del RAG (nivel A: normas y textos oficiales o de libre uso)\n",
         "Cada documento se descarga con `python -m src.datos_publicos.descargar`, queda con su hash y estado en `docs/rag/fuentes.csv` y se parte en fragmentos de 900 caracteres con 120 de solape. La puerta de calidad verifica que ningun archivo se haya alterado.\n",
         "| Modulo | Documento | Institucion | Consultado | Enlace |\n|---|---|---|---|---|"]
    L += [f"| {r['modulo']} | {r['titulo']} | {r['institucion']} | {r['fecha_consulta']} | {r['enlace']} |" for r in sorted(hechas, key=lambda r: (r["modulo"], r["titulo"]))]
    if pendientes:
        L += ["", "No ingeridas (licencia por confirmar o descarga bloqueada): " + "; ".join(f"{r['titulo']} ({r['institucion']}, nivel {r['licencia_nivel']}): {r['enlace']}" for r in pendientes) + "\n"]
    L += ["", "### 8.2 Fuentes de calibracion y de contexto\n", "| Documento | Institucion | Uso | Consultado | Enlace |\n|---|---|---|---|---|"]
    L += [f"| {r['titulo']} | {r['institucion']} | {r['uso']} | {r['fecha_consulta']} | {r['enlace']} |" for r in _filas_csv("docs", "fuentes", "fuentes.csv")]
    L += ["", "### 8.3 Series del BCRP\n", "API publica y sin clave: `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{codigo}/json/{desde}/{hasta}/esp`. Las bajadas para el generador quedan en `data/raw/bcrp/`.\n",
          "| Codigo | Serie | Observaciones | Enlace |\n|---|---|---|---|"]
    L += [f"| {r['codigo']} | {r['descripcion']} | {r['detalle']} | {r['enlace']} |" for r in _filas_csv("docs", "fuentes", "bcrp_series.csv")]
    usadas = ", ".join(f"`{n}` ({v[0]}, {v[2]})" for n, v in SERIES.items())
    L += ["", f"### 8.4 Conexiones en tiempo real y como se comportan\n",
          "| Conexion | Que trae | Como se consulta | Si falla | Donde esta en el codigo |\n|---|---|---|---|---|",
          f"| BCRP | {usadas} | API en cada consulta; cache en disco ({os.path.relpath(CACHE, RAIZ).replace(os.sep, '/')}, {TTL_SEGUNDOS // 3600} h) | cache de hasta 7 dias y luego la serie grabada; **un dato de la serie grabada o mas viejo de 75 dias (mensual) o 7 dias (diario) no se presenta como actual ni dispara avisos** (`al_dia`) | `src/bcrp/cliente.py` |",
          "| ENFEN | Comunicados oficiales del Fenomeno El Nino | `https://enfen.imarpe.gob.pe/` (pagina) y `https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-{N}-2026/` | si no responde, la vigilancia no avisa; la puerta de calidad compara el ultimo comunicado publicado con el del RAG | `src/agente_analitico/vigilancia.py` |",
          "| Gemini | Redaccion y traduccion | `https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent`, clave en el encabezado `x-goog-api-key` (nunca en la URL) | reintento ante 429 o 5xx; luego Ollama local; luego plantillas | `src/agente_analitico/proveedores.py`, `traduccion.py` |",
          "| Otra API de IA (cualquier `chat/completions`) | Redaccion | `LLM_BASE_URL` + `/chat/completions` con `Authorization: Bearer` | igual que Gemini | `Compatible` en `proveedores.py` |",
          "| Ollama (local) | Embeddings del RAG (`nomic-embed-text`, 768 dimensiones) y LLM de respaldo | `http://localhost:11434` | sin embeddings no hay RAG; el agente sigue con las herramientas | `src/rag/indice.py` |",
          "| Movimientos del cliente | Ingresos y gastos que entran al aplicativo | `datos_vivos.registrar(...)` (ver 9) | un movimiento invalido se rechaza con un error claro | `src/agente_analitico/datos_vivos.py` |", "",
          "### 8.5 Normas laborales: de la fuente al sistema\n",
          "`data/parametros/normas_laborales.yaml` guarda cada regla con la **frase literal** del documento oficial; la prueba `tests/test_calendario.py` falla si esa frase deja de estar en el documento. Para actualizar una norma: bajar el documento nuevo (`descargar.py`), indexarlo (`actualizar_incremental()`), corregir el YAML y su `fecha_verificacion`, y correr las pruebas.\n",
          "### 8.6 Otras fuentes consultadas (no ingeridas)\n",
          "Se usaron para contrastar fechas y noticias; las dos primeras se leyeron completas, las demas solo por el resumen del buscador, asi que **no son evidencia de una regla**:\n",
          "- Ley 32322, texto oficial en El Peruano (leido completo e ingerido): https://busquedas.elperuano.pe/dispositivo/NL/2397811-1",
          "- Repositorio de revision de repos de hackathon (escaneo estatico, sin hallazgos): https://github.com/JoCGM09/hackathon-evaluator",
          "- Nota de El Peruano sobre la Ley 32322: https://www.elperuano.pe/noticia/270086-atencion-retira-el-100-de-tu-cts-hasta-el-2026-consulta-los-detalles-de-la-ley-32322",
          "- Nota de El Peruano sobre proyectos para ampliar la libre disposicion hasta 2028 (proyecto, no ley; expediente no revisado): https://elperuano.pe/noticia/308663--congreso-proponen-ampliar-libre-disponibilidad-de-la-cts-hasta-diciembre-de-2028",
          "- Nota de El Peruano sobre el plazo de la CTS de noviembre de 2025: https://elperuano.pe/noticia/282461-atencion-empleadores-este-ano-podran-depositar-la-cts-hasta-el-17-de-noviembre",
          "- Infobae: https://www.infobae.com/peru/2026/05/15/retiro-de-cts-del-100-esta-vigente-hasta-el-31-de-diciembre-pero-luego-habra-acceso-parcial/ y EY Peru: https://www.ey.com/es_pe/newsroom/2026/04/deposito-retiro-cts-2026",
          "- Nota de TV Peru sobre la gratificacion y la bonificacion del 9 %: https://www.tvperu.gob.pe/novedades/tvperu/gratificacion-por-navidad-sera-un-sueldo-mas-9-adicional",
          "- DS 007-2025-TR (adecuacion del reglamento de la CTS), aparecio en la busqueda y no se leyo: https://www.gob.pe/institucion/mtpe/normas-legales/7512608-007-2025-tr",
          "- lpderecho.pe sobre la Ley 32322 (no abrio: HTTP 403): https://lpderecho.pe/ley-32322-retiro-cts-diciembre-2026/",
          "- Notas del vault de Obsidian que guiaron las tecnicas de RAG y de evaluacion: `rag-avanzado-crag-self-rag-y-graphrag`, `evaluacion-de-llm-y-rag-metodos`, `evaluacion-de-sistemas-con-llm`, `agentes-con-llm-que-redacta-y-no-calcula`.\n"]
    L += ["", "### 8.7 Rutas de API\n", "**APIs externas que se llaman** (ninguna usa datos personales; a las de IA se les ocultan el id y la zona del cliente):\n",
          "| Servicio | Metodo y ruta | Autenticacion | Cuerpo o parametros | Lo que se usa de la respuesta | Codigo |\n|---|---|---|---|---|---|",
          "| BCRP series | `GET https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{codigo}/json/{desde}/{hasta}/esp` | ninguna | codigo de serie y rango (mensual `2024-1/2027-12`, diaria `2024-1-1/2027-12-28`) | `periods[].name` y `periods[].values[0]` | `src/bcrp/cliente.py` |",
          "| ENFEN (pagina) | `GET https://enfen.imarpe.gob.pe/` | ninguna | — | numero del ultimo «Comunicado Oficial ENFEN N.º N-2026» | `vigilancia.py` |",
          "| ENFEN (comunicado) | `GET https://enfen.imarpe.gob.pe/download/comunicado-oficial-enfen-n-{N}-2026/` | ninguna | — | texto del comunicado | `descargar.py` |",
          "| Gemini | `POST https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent` | encabezado `x-goog-api-key` | `systemInstruction`, `contents`, `generationConfig` (`temperature`, `maxOutputTokens`) | `candidates[0].content.parts[0].text` y `usageMetadata` | `proveedores.py`, `traduccion.py` |",
          "| API de IA compatible | `POST {LLM_BASE_URL}/chat/completions` | `Authorization: Bearer {LLM_API_KEY}` | `model`, `messages`, `temperature`, `max_tokens` | `choices[0].message.content` y `usage` | `Compatible` en `proveedores.py` |",
          "| Ollama (chat) | `POST http://localhost:11434/api/chat` | ninguna | `model`, `messages`, `options` | `message.content` | `proveedores.py` |",
          "| Ollama (embeddings) | `POST http://localhost:11434/api/embed` | ninguna | `model` (`nomic-embed-text`), `input[]` | `embeddings` (768 dimensiones) | `src/rag/indice.py` |",
          "| Ollama (modelos) | `GET http://localhost:11434/api/tags` | ninguna | — | lista de modelos (solo la puerta de calidad) | `puerta_de_calidad.py` |",
          "| El Peruano | `GET https://busquedas.elperuano.pe/dispositivo/NL/2397811-1` | ninguna | — | texto de la Ley 32322 entre «LEY Nº 32322» y «DISPOSICIÓN COMPLEMENTARIA FINAL ÚNICA» | `descargar.py` |",
          "| Descarga de documentos | `GET` de cada enlace de 8.1 y 8.2, con `User-Agent: analitica-hackathon/1.0` | ninguna | — | el PDF, con su hash | `descargar.py` |", "",
          "**Rutas del aplicativo** (contrato `docs/api.md` v0.2 de Miguel) y la funcion de esta rama que las alimenta:\n",
          "| Ruta | Funcion | Estado |\n|---|---|---|",
          "| `GET /api/v1/customers/{customer_id}/health` | `Repositorio.contexto(cid)`: `salud`, `nivel`, `features['colchon_observado']` | calculado; falta el adaptador de nombres (seccion 10) |",
          "| `GET /api/v1/customers/{customer_id}/forecast` | `Repositorio.contexto(cid)['pronostico']` | calculado al dia 30; la serie diaria no esta entrenada |",
          "| `GET /api/v1/customers/{customer_id}/recommendations` | `recomendador.recomendar(ctx)` | calculado; falta definir `impact_type` |",
          "| `GET /api/v1/customers/{customer_id}/events` | `vigilancia.eventos_para(...)` y `vigilancia.ciclo(...)` | calculado, con tope de 3 por semana y sin repetidos |",
          "| `POST /api/v1/simulations` | `Repositorio._pronostico(fila, neto)` | gasto unico; ingresos y gastos recurrentes por definir |",
          "| `GET /api/v1/fx` | `bcrp.cliente.ultimo_con_variacion('tipo_cambio_venta')` | calculado, con `origen` y `al_dia` |",
          "| `POST /api/v1/customers/{customer_id}/expenses` | `datos_vivos.registrar(...)` | calculado, validado e idempotente |",
          "| `POST /api/v1/chat` | `grafo.responder(agente, cid, pregunta)` | calculado |",
          "| `GET /api/v1/customers/{customer_id}/offers` | `ofertas.ofertas_por_perfil(ctx, top_categorias)` | calculado, con catalogo ficticio |",
          "| `GET` y `POST /api/v1/customers/{customer_id}/goals` | `memoria` guarda las metas del usuario | parcial: guarda, sin ruta propia |",
          "| `POST /api/v1/onboarding` | — | no lo cubre la analitica |", ""]
    mani = os.path.join(RAIZ, "data", "generado", "_manifiesto.json")
    if os.path.isfile(mani):
        with open(mani, encoding="utf-8") as fh:
            m = json.load(fh)
        L += ["### 8.8 Data sintetica cargada para la integracion\n",
              f"`data/generado/` lleva **{m['total_archivos']} archivos ({m['total_mb']} MB), 100 % sinteticos** (semilla {m['semilla']}), cargados a proposito aunque la carpeta esta en `.gitignore` (`git add -f`), para que se usen al integrar sin tener que regenerarlos. "
              "Cada archivo esta en `data/generado/_manifiesto.json` con su tamano y su hash; las caches de respuestas y la memoria de pruebas **no** se cargan.\n",
              f"- **Para usarlos:** no hay que hacer nada; `Repositorio` y `eval/entrenar_modelos.py` leen `data/generado/`. Contenido: `clientes.parquet`, `transacciones/` (movimientos por lotes de clientes), `saldo_diario/`, `panel_mensual/`, `mensajes/`, `contexto_diario.parquet`, `eventos.parquet`, `macro_mensual.parquet` y `etiquetas_calidad/`. Diccionario en `data/dictionary.md` y calidad en `data/QUALITY.md`.",
              f"- **Para regenerarlos identicos:** `{m['regenerar_identica']}`.",
              f"- **Para quitarlos al terminar la integracion:** `{m['quitar_al_terminar']}`. La puerta de calidad (S5) lo avisa mientras esten versionados.", ""]
    return "\n".join(L)


def seccion_integracion_app() -> str:
    return """Todo corre con `Repositorio` (modelos y datos del cliente), `Buscador` (RAG) y el grafo del agente. Pasos para conectarlo a un aplicativo:

**1. Entorno.** Python 3.13, `pip install -r requirements-analitica.txt`, copiar `.env.analitica.example` a `.env` y completar las claves (solo en `.env`). Ollama con `nomic-embed-text` para el RAG.

**2. Arranque (una vez por proceso, tarda unos segundos).**
```python
from src.agente_analitico.repositorio import Repositorio
from src.agente_analitico.grafo import construir_grafo, responder
from src.rag.indice import Buscador
repo, rag = Repositorio(), Buscador()
agente = construir_grafo(repo, rag, "agente_unico")
```

**3. Preguntas del cliente** (`POST /chat`): `r = responder(agente, customer_id, pregunta)`. Devuelve `respuesta` (siempre cierra con «Tu decides.»), `intencion`, `citas` (titulo, pagina, enlace), `recomendaciones`, `cifras_verificadas`, `cifras_sin_respaldo`, `proveedor`, `llamadas_llm` e `idioma`. Para otro idioma pasar `idioma="en"` o `"qu"` (o se detecta). Mostrar siempre las `citas`.

**4. Datos que ya calcula el modelo** (`GET health`, `forecast`, `recommendations`): `repo.contexto(cid)` (salud, nivel, pronostico a 30 dias con banda y probabilidad de rojo, calendario laboral, movimientos vivos), `repo.proyeccion_mensual(cid)` (ingresos, gastos y neto de 1 a 6 meses) y `recomendador.recomendar(ctx)`. El mapeo a los nombres del contrato de la API esta en la seccion 10.

**5. Alimentar con lo que entra y sale** (`POST expenses`): `datos_vivos.registrar(cid, "gasto", 35.0, categoria="transporte", fecha="2026-11-14", id_mov="id-del-aplicativo")`. Si el aplicativo no tiene categoria puede mandar `glosa="..."` y el clasificador la sugiere (confianza minima 0.80; si no, `otros`); **la glosa no se guarda**. Reintentar con el mismo `id_mov` no duplica. Con datos viejos (mas de 45 dias desde el cierre de datos) el riesgo a 30 dias no se reestima y el agente lo dice.

**6. Avisos (`GET events`).** Un proceso programado (por ejemplo cada hora) llama `vigilancia.ciclo(agente, repo, lista_de_clientes)`; devuelve los avisos ya redactados, de lo mas urgente a lo menos, sin repetir un hecho y con tope de 3 por semana por cliente. Con `consultar_red=False` no consulta el BCRP ni el ENFEN (pruebas y demos sin internet).

**7. Cambiar de API de IA.** `LLM_PROVIDER=compatible` y tres variables: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` (cualquier API con formato `chat/completions`). Ningun otro archivo cambia. `LLM_USO=ahorro` usa el LLM solo para lo que una plantilla no cubre bien; `siempre` para todo. El consumo queda en `proveedores.USO` (llamadas y tokens). Un proveedor nuevo solo necesita `nombre`, `externo` y `redactar(pregunta, datos, tono, feedback)`; las pruebas de `tests/test_proveedores.py` fijan el contrato.

**8. Privacidad y derechos.** Todo proveedor externo recibe los datos **sin id ni zona** del cliente (`externo=True`); el LLM nunca ve el detalle de los movimientos. `memoria.olvidar(cid)` borra la memoria y los movimientos vivos del cliente. Las claves viven solo en `.env`.

**9. Mantener actualizado.** BCRP: automatico (cache y respaldo). ENFEN: la vigilancia avisa si hay un comunicado nuevo; hay que bajarlo e indexarlo. RAG: `python -m src.datos_publicos.descargar` y `Buscador` tras `indice.actualizar_incremental()` (solo embebe lo nuevo). Normas: ver 8.5. Evaluar todo: `python eval/puerta_de_calidad.py --gemini`.

**10. Lo que no hay que hacer.** No usar el LLM para calcular: toda cifra sale de una herramienta y pasa por el juez, y si el LLM inventa una cifra, devuelve codigo o promete algo, la respuesta cae a la plantilla. No tratar un proyecto de ley como ley. No presentar un dato desactualizado como actual. No mover dinero ni recomendar comprar o vender dolares ni en que invertir: esos pedidos se cortan antes de llegar a cualquier modelo.
"""


def seccion_escala_valor():
    txt = ""
    if ESC:
        txt += "**Escalabilidad medida** (esta laptop, 500 clientes): " + json.dumps(ESC) + "\n\n"
    if VAL:
        pp, br, co, c = VAL["programa_de_puntos"], VAL["lectura_bruta"], VAL["lectura_conservadora"], VAL["por_cliente_lucas"]
        txt += (f"**Programa de puntos sostenible** (supuestos del equipo, visibles en `data/parametros/niveles.yaml`): cada usuario gana en promedio {pp['puntos_por_usuario_al_mes']:.0f} puntos al mes y el programa cuesta "
                f"S/ {pp['costo_por_usuario_al_anio']:.2f} por usuario al anio, es decir {pp['costo_sobre_ingreso_bruto']:.1%} del ingreso bruto que genera (tope de reinversion: {pp['tope_de_reinversion']:.0%}). "
                "Los puntos por consumo solo se activan para quien tiene la caja ordenada; ahorrar suma siempre y mas para los niveles bajos.\n\n")
        txt += "Por nivel (anual por usuario, lectura bruta):\n\n" + T(pp["por_nivel"], 2, ["clientes", "consumo_elegible_anual", "puntos_por_mes", "costo_de_puntos_anual", "ingreso_anual", "costo_sobre_ingreso", "consumo_por_cada_sol_de_puntos"]) + "\n"
        txt += ("`consumo_por_cada_sol_de_puntos` es cuanto consume el cliente por cada S/ 1 de puntos que canjea (la proporcion de gasto sobre puntos).\n\n"
                f"**Lectura bruta (techo, atribuye todo al programa)**: ingreso por usuario S/ {br['ingreso_por_usuario_al_anio']:.0f} al anio, neto S/ {br['neto_por_usuario_al_anio']:.0f}.\n\n"
                f"**Lectura conservadora**: Lucas genera {c['colchon_adicional_soles']:.0f} soles mas de colchon por cliente, que dejan S/ {co['fondeo_adicional_por_usuario_al_anio']:.2f} al anio de fondeo; "
                f"el programa cuesta S/ {co['costo_de_puntos_por_usuario_al_anio']:.2f}, asi que sin mas consumo el neto es S/ {co['neto_por_usuario_sin_mas_consumo']:.2f} por usuario. "
                f"Se paga solo si el consumo elegible crece al menos {co['mas_consumo_necesario_para_pagarse']:.1%}. Sensibilidad (neto por usuario al anio):\n\n"
                + T({k: {"neto_por_usuario": v["valor_neto_por_usuario_anual"], "neto_con_100_mil_usuarios": v["valor_neto_escenario"]} for k, v in co["sensibilidad"].items()}, 1) +
                f"\n{co['nota']}.\n")
    return txt or "_pendiente_\n"


def evaluacion():
    return f"""# Evaluacion analitica

Generado por `eval/generar_docs.py` desde `models/metricas*.json`. Datos sinteticos con semilla fija; las magnitudes de los eventos son supuestos del equipo (ver `data/parametros/eventos.yaml`).

## 1. Segmentacion
{seccion_segmentacion()}
## 2. Pronostico de saldo a 30 dias
{seccion_pronostico()}
## 3. Proyeccion por meses: ingresos, gastos y neto (1 a 6 meses)
{seccion_mensual()}
## 4. Clasificacion y deteccion
{seccion_clasificacion()}
## 5. Impacto en soles (reproduccion contrafactual)
{seccion_impacto()}
## 6. RAG y agente
{seccion_rag_agente()}
## 7. Escalabilidad y valor
{seccion_escala_valor()}
## 8. Calendario laboral, datos vivos y vigilancia
{seccion_calendario()}
## 9. QA y comparativa de modelos
{seccion_qa()}
"""


def resumen():
    niv = ", ".join(SEG["niveles"].values()) if SEG else "?"
    return f"""# Resumen de lo hecho: analitica e IA (Diego)

Registro de **que se hizo, que se cambio, que se mejoro, que se agrego y que se quito**, con el motivo. Las cifras salen de `models/metricas*.json` (ver [EVALUACION_ANALITICA.md](EVALUACION_ANALITICA.md)). Entidad y marca de ejemplo: **Banco Kawsay**, app **Lucas** (nombres inventados, `data/parametros/entidad.yaml`).

## 1. Como correrlo
```bash
pip install -r requirements-analitica.txt      # Python 3.13; copia .env.analitica.example a .env y completa las claves
python data/generator.py --perfil muestra      # 40 clientes, 12 meses, 1 s, queda en data/sample
python data/generator.py --perfil completo     # 500 clientes, 2019-2025, ~30 s, 0,5 GB de RAM
python -m src.datos_publicos.descargar         # fuentes oficiales (RAG y normas laborales) y series del BCRP
python -m src.rag.indice                       # reconstruye el indice del RAG (requiere Ollama con nomic-embed-text; ~15 min); para documentos nuevos basta actualizar_incremental()
python eval/entrenar_modelos.py                # entrena y evalua; guarda models/*.pkl y models/metricas_*.json
python eval/evaluar_rag.py                     # recuperacion y filtro de relevancia del RAG
python eval/evaluar_agente.py                  # agente con plantillas: determinista, sin LLM ni costo
python eval/qa_agente.py                       # UNA corrida de QA con Gemini real (~18 llamadas): perfil, calendario, datos vivos, idiomas, adversarios
python eval/comparativa_modelos.py             # tabla y graficas de comparacion de modelos (docs/comparativa_modelos.md y docs/figuras/)
python eval/construir_notebooks.py             # ejecuta los notebooks de notebooks/
python eval/generar_docs.py                    # regenera estos documentos
python eval/puerta_de_calidad.py --gemini      # puerta de calidad completa (docs/QA_ANALITICA.md)
python -m pytest tests -q                      # toda la suite; no necesita red ni Gemini
```
Claves solo en `.env` (no se sube). `LLM_PROVIDER=gemini|compatible|ollama|plantillas`: para conectar otra API de IA basta `compatible` y tres variables (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`); si el proveedor falla se prueba Ollama local y, si tampoco responde, se contesta con plantillas. `LLM_USO=ahorro` (el LLM solo redacta lo que una plantilla no cubre bien) o `siempre`. Las rutas se calculan desde la raiz del repo (`src/comun/rutas.py`); la puerta de calidad impide rutas absolutas.

## 2. Que cubre
| Pedido | Donde esta |
|---|---|
| Datos sinteticos sin sesgo de muestreo, con variables estructuradas y texto | `src/generador/`, `data/parametros/`, `data/QUALITY.md`, `data/dictionary.md` |
| Segmentacion K-Prototypes y niveles con nombre ({niv}) | `src/models/segmentacion.py`, `src/models/niveles.py`, `data/parametros/niveles.yaml` |
| Salud financiera especializada (dependiente, independiente) | `src/models/salud.py` |
| Pronostico a 30 dias y por meses (ingresos, gastos, neto) con banda al 80 % | `src/models/pronostico.py`, `src/models/pronostico_mensual.py` |
| Eventos (covid, protestas, El Nino 2023, El Nino 2026-2027 prospectivo) y bonos y retiros AFP | `data/parametros/eventos.yaml`, `src/generador/contexto.py` |
| Recomendador por perfil y consumo, ofertas con idoneidad (ahorrar, invertir, credito, tarjeta) | `src/models/recomendador.py`, `src/models/ofertas.py`, `data/catalogo_ofertas.json` |
| Puntos por conductas sanas y canje | `src/models/niveles.py` |
| Programa de puntos sostenible (tope de reinversion, idoneidad de consumo) y simulacion de su economia | `src/models/programa_puntos.py`, `eval/simular_puntos.py` |
| Calendario laboral: CTS y gratificaciones con fuente oficial, y regla de retiro de la CTS | `src/models/calendario_laboral.py`, `data/parametros/normas_laborales.yaml` |
| Datos vivos (movimientos que entran al aplicativo) y vigilancia con avisos | `src/agente_analitico/datos_vivos.py`, `src/agente_analitico/vigilancia.py` |
| Idiomas (espanol, ingles, quechua) con cifras y nombres protegidos | `src/agente_analitico/traduccion.py` |
| Proveedores de LLM intercambiables (Gemini, cualquier API `chat/completions`, Ollama) | `src/agente_analitico/proveedores.py` |
| QA y comparativa de modelos | `eval/puerta_de_calidad.py`, `docs/QA_ANALITICA.md`, `eval/comparativa_modelos.py`, `docs/comparativa_modelos.md` |
| Alerta por zona de riesgo del Nino con prevencion | `src/models/riesgo_clima.py`, `data/parametros/zonas_riesgo_fen.yaml` |
| RAG (fragmentos, embeddings locales, FAISS, filtro de relevancia) | `src/rag/`, `docs/rag/` |
| Agente LangGraph (unico y multiagente), juez determinista y juez LLM, memoria, avisos en tiempo real | `src/agente_analitico/` |
| Diagramas de nodos | `docs/diagramas/grafo_*.md` |
| Notebooks | `notebooks/` |

## 3. Cambios, mejoras, agregados y descartes
| Tipo | Que | Por que |
|---|---|---|
| Agregado | Generador por lotes con estratos (piso minimo), peso muestral y bootstrap suavizado de perfiles | Evitar sub y sobrerrepresentacion sin ocultar el sesgo: el peso restituye la poblacion objetivo |
| Cambio | De 500 clientes x 12 meses a **500 x 7 anios (2019-2025)** con muestra de 40 x 12 meses en `data/sample` | Incluir el covid y su recuperacion y medir cuantos anios hacen falta; corre en ~30 s y 0,5 GB |
| Agregado | Series reales del BCRP (inflacion, tipo de cambio, tasa de referencia) con respaldo grabado | Contexto real y reproducible sin internet |
| Agregado | Eventos configurables con fuente y estado (verificado, parcial, supuesto) | Probar al modelo frente a eventos; las magnitudes sin fuente se marcan como supuesto |
| Agregado | Faltantes, duplicados y atipicos sembrados con tabla de etiquetas | Escenarios dificiles de las bases |
| Agregado | Departamento (ubicacion gruesa, no GPS) y mapa de exposicion al Nino con el texto del ENFEN | Alerta por zona sin guardar coordenadas |
| Cambio | Canales y comercios con nombres inventados; banco ficticio | Ninguna marca real |
| Mejora | La banda del pronostico mensual pasa a **recalibracion continua** por tipo de trabajo | La banda fija cubria 0,59 en dependientes; ahora ~0,80 en todos |
| Mejora | Impacto: se corrigio el baseline del 10 % fijo | Salia identico a no hacer nada; ahora se reportan dos versiones |
| Mejora | Clasificador de glosas: de LinearSVC a SGD lineal | Misma calidad en segundos, no en minutos |
| Agregado | Niveles por segmento (escalera Luchador a Campeon) y puntos que premian conductas sanas | Personalizar el tono y los beneficios; no se premia gastar mas |
| Agregado | Recomendador con reglas de seguridad (colchon, cuotas, dias en rojo, riesgo de rojo) y ofertas explicables | Credito y tarjeta solo con idoneidad; si no pasa, se dice por que |
| Agregado | RAG con filtro de relevancia tipo CRAG y evaluacion de recuperacion | No contestar con basura cuando el indice no tiene la respuesta |
| Agregado | Multiagente (supervisor y especialistas que se piden datos) | Pedido del equipo; **no mejora metricas**, queda como opcion |
| No adoptado | SMOTE y submuestreo para el riesgo de rojo | Ver la tabla de remuestreo: no mejoran frente a calibrar la probabilidad |
| No adoptado | Busqueda hibrida como defecto | Con filtro de modulo empata con la densa en recall@4; se mantiene la densa porque el filtro de relevancia se calibra sobre su similitud |
| No adoptado | Partir las preguntas compuestas y MMR en el RAG | No mejoraron nada medible en la evaluacion; quedan como opcion apagada |
| Agregado | Calendario laboral (CTS, gratificaciones, retiro de la CTS) con la frase literal de la norma como evidencia de cada regla | La libre disposicion del 100 % de la CTS vence el 31-12-2026 (Ley 32322); se lee de la norma oficial, no de memoria, y una prueba comprueba que la frase siga en el documento |
| Agregado | Datos vivos (movimientos validados, sin duplicados, sin guardar la glosa) y vigilancia con avisos unicos, tope semanal y casos que no deben avisar | El agente se alimenta de lo que entra y sale sin repetir ni dar falsos positivos |
| Agregado | Frescura de los datos publicos (fecha, origen y si estan al dia) y un reloj unico | Un dato viejo no se presenta como actual ni dispara avisos; el BCRP y el ENFEN se consultan en vivo |
| Mejora | Ruteo probado con 75 frases naturales y coloquiales escritas sin mirar las reglas: de 25 desviaciones a ninguna | «¿Compro dolares?» o «Pasale 200 soles» no se cortaban, «gastando» no activaba gastos y «reclamar por un cobro» iba al pronostico |
| Mejora | El verificador de cifras acepta las dos lecturas de un numero ambiguo (3.406: miles o decimal) | Marcaba como inventado un tipo de cambio correcto |
| Mejora | RAG: expansion de siglas (TCEA, CTS, EPS...), extracto en frases completas y aviso cuando la fuente es de otro pais | La sigla sola rendia menos, los recortes terminaban en «43...» y una guia de EE. UU. no es norma peruana |
| Agregado | Proveedor de LLM «compatible» (cualquier API chat/completions) y el camino con LLM probado con una API falsa: cifra inventada, codigo, API caida | El agente debe trabajar con la API de IA que se use al final; hoy se prueba con Gemini |
| Agregado | Evaluacion del RAG ampliada a 34 preguntas con respuesta y 11 fuera del indice, y siete fuentes oficiales nuevas | Mas confianza que con las 20 preguntas anteriores |
| Cambio | El agente de analitica pasa de `src/agent` a `src/agente_analitico` | Evitar chocar con `src/agent` del PR #5 (agente del producto) y poder integrar despues lo mejor de cada uno |
| Retirado | `models/metricas_agente_gemini.json` | Era anterior a las salvaguardas de seguridad y decia 0.0 en pedidos prohibidos rechazados; la validacion con Gemini es la corrida de QA |
| No adoptado | GraphRAG, deep learning desde cero | Sin puntos extra y riesgo de tiempo (decision del plan) |
| Pendiente | Fuentes de nivel C (guia del Ministerio de Vivienda), cartilla del BCRP (bloqueo anti-bot) | Licencia por confirmar; descarga manual |

### Inventario de lo que contiene esta rama
{seccion_inventario()}
## 4. Resultados clave (validados)
Todo con datos sinteticos; ver la evaluacion completa.
{resultados_clave()}

## 5. Sesgo y fuga de datos: que se hizo y que no
- Estratos con piso, peso muestral y evaluacion ponderada; error y cobertura por grupo (segmento, region, edad, tipo de trabajo, exposicion al Nino, arquetipo) con alerta automatica.
- Cortes temporales con purga del horizonte; segmentacion ajustada solo con datos anteriores a la prueba; solo variables observables (`src/models/columnas.py`); la etiqueta de sentimiento nunca entra al pronostico.
- Los mismos clientes aparecen en entrenamiento y prueba (se pronostica su futuro); para clientes nuevos esta el modelo de arranque en frio y una prueba con otra semilla.
- **Limites**: el remuestreo no elimina el sesgo del diseno del generador; los pesos de arquetipo, region y edad son supuestos del equipo hasta tener microdatos de la ENAHO (el generador acepta una tabla semilla).

## 6. Hallazgos honestos
{hallazgos()}

## 7. Escalabilidad, rentabilidad, innovacion e impacto
{seccion_escala_valor()}
- **Escalable**: nada en el codigo depende de una entidad; nombre, catalogo, margenes y politicas estan en archivos de configuracion. El generador y el pronostico trabajan por lotes; el agente es sin estado entre llamadas (la memoria es un archivo por usuario, reemplazable por una base).
- **Innovacion**: banda de pronostico distinta para ingreso irregular, proyeccion por meses, alerta de El Nino por zona con fuente oficial, Sueldo Lucas, avisos en tiempo real, niveles con nombre, juez doble que impide cifras inventadas.
- **Impacto**: ver la seccion 5 de la evaluacion; el efecto en retencion y mora lo mediria un piloto con grupo de control.

## 8. Datos reales y conexiones: de donde sale cada dato, con sus enlaces
{seccion_datos_reales()}
## 9. Como integrarlo en el aplicativo
{seccion_integracion_app()}
## 10. Integracion con el equipo
Esta rama contiene **solo el trabajo de analitica e IA**: lo de otras personas (agente del producto, API, front) no esta aqui y la integracion final se hace despues. Aqui queda documentado lo que choca, lo que coincide y que tomar de cada lado. *Lo que se dice del PR #5 y de `develop` es observacion por lectura de su codigo y de `docs/api.md`; las pruebas del agente del producto no se ejecutaron en esta rama.* (El 14-nov se trajo `develop` a la copia remota de esta rama; esta version no lo incluye.)

**Como se reparte el trabajo hoy.** Miguel define la API REST (`docs/api.md` v0.2, FastAPI) y su contrato dice que el calculo debe venir de los modelos de Diego; Jeffrey construyo el agente del producto (PR #5: grafo LangGraph, router por reglas, juez de cifras, Gemini de respaldo, BCRP con serie grabada, respuesta de `/chat`), que consume esa API por herramientas (`get_health`, `get_forecast`, `get_recos`, `simulate`, `get_fx`) hoy sobre mocks; Marcela hace el front (`app/`).

**Para no chocar.** El agente de analitica vive en `src/agente_analitico/` y el del producto en `src/agent/`. Coinciden en el grafo LangGraph, el router, el juez de cifras, Gemini, el cliente del BCRP, los PDFs del RAG (mismas fuentes con otros nombres de archivo), `docs/rag/fuentes.csv`, `.gitignore`, los `requirements-*.txt` y los `.env*.example`. Al unir hay que elegir un nombre por documento del RAG y un solo cliente del BCRP.

**Mis salidas frente al contrato de nombres (`docs/api.md`).** Mis salidas internas estan en espanol; hace falta un adaptador (no escrito, a proposito: la integracion es al final).

| Contrato | Mi salida | Nota |
|---|---|---|
| `health.score` | `ctx["salud"]` (0 a 100) | misma escala |
| `health.status` | `nivel` (Luchador a Campeon) | el contrato deja el vocabulario pendiente de Diego |
| `health.quadrant` | no existe | propuesta: Q1 salud >= 60 y colchon >= 2 meses; Q2 salud >= 60 y colchon < 2; Q3 salud < 60 y colchon >= 2; Q4 el resto (el mock, score 72 y colchon 1.5, daria Q2) |
| `health.emergency_fund_months` | `features["colchon_observado"]` | **mide meses de INGRESO, no de gasto**: acordar la definicion |
| `forecast[].predicted_balance`, `lower_bound`, `upper_bound` | `saldo_esperado`, `saldo_bajo`, `saldo_alto` | **solo al dia 30**; no hay serie diaria validada |
| `forecast.first_risk_date` | `dia_riesgo` (dia 1 a 30, solo si `p_rojo` >= 0.15) y `p_rojo` | fecha = fecha de los datos + dia |
| `recommendations[]` | `id`, `accion`, `impacto_soles`, `por_que`, `supuestos`, `confianza`, `tu_decides` | casi uno a uno; falta definir `impact_type` |
| `events[]` (income, gratification, cts, recurring_expense, negative_balance_risk) | `ingreso_extra`, `calendario_laboral`, `gratificacion_pendiente`, `gasto_atipico`, `riesgo_rojo`, `libre_disposicion_por_vencer`, `baja_de_tasa`, `fen_comunicado` | el contrato pide maximo 3 avisos por semana y sin duplicados: la vigilancia ya lo cumple |
| `POST expenses` | `datos_vivos.registrar` | validado e idempotente |
| `fx` (`is_fallback`, `is_stale`) | `ultimo_con_variacion` (`origen`, `al_dia`) | equivalentes |
| `POST simulations` | `Repositorio._pronostico(fila, neto)` vuelve a puntuar el modelo con el saldo corregido | sirve para un gasto unico; ingresos o gastos recurrentes por definir |

**Lo mejor de cada lado (propuesta para la integracion).**

| Pieza | PR #5 (Jeffrey) | Esta rama (Diego) | Propuesta |
|---|---|---|---|
| Router | reglas con normalizacion de tildes, intencion «simular» con monto, operaciones e inyecciones cortadas primero | mas intenciones (calendario, tipo de cambio, mora, programa de puntos), 75 frases naturales sin desviaciones | partir del de Jeffrey (normalizacion y simular) y sumar las intenciones y la prueba de frases naturales |
| Juez de cifras | cifras con etiqueta para el chat de Marcela, exige cifra | lecturas ambiguas (3.406), titulo citado como origen, frases prohibidas incluido codigo | combinar: etiquetas de Jeffrey y lecturas y prohibidos de Diego |
| Proveedores de LLM | Gemini con respaldo | Gemini, «compatible» (cualquier API), Ollama, cache, politica de ahorro, id y zona ocultos a todo proveedor externo, camino probado con una API falsa | base de Diego: cambiar de API es cambiar tres variables |
| BCRP | cliente con serie grabada | API, cache y serie grabada con fecha, origen y `al_dia` | un solo cliente: el de Diego mas la serie grabada de Jeffrey |
| RAG | PDFs oficiales del nucleo | indice de 3 833 fragmentos, 34 + 11 preguntas de evaluacion, filtro de relevancia, siglas, aviso de fuente extranjera | indice de Diego; unificar nombres de archivo |
| Herramientas | forma del contrato sobre mocks; JF-03 llamara a la API real | modelos reales | escribir el adaptador de arriba |
| Solo en esta rama | | calendario laboral, datos vivos, vigilancia, traduccion, programa de puntos, puerta de calidad, comparativa | portar |
| Solo en el PR #5 | intencion «simular» con monto, respuesta `/chat` para Miguel, cifras con etiqueta, pruebas del agente | | portar |

**Respuestas propuestas a las tres preguntas de Jeffrey** (para que Diego las revise; no se publico nada en el PR). (1) *Nombres del contrato*: no tocar su juez; el adaptador de la tabla traduce mis salidas al contrato. (2) *Pronostico al LLM*: pasar el saldo esperado a 30 dias con su banda y el dia de riesgo; el dato clave es el dia de riesgo y `p_rojo` («hacia el dia X»), no el ultimo dia de una serie; la serie diaria no esta validada. (3) *Simulacion por plantilla*: de acuerdo, el LLM no calcula; el modelo se puede volver a puntuar con el saldo corregido de forma determinista, y falta definir con Dixon los ingresos y gastos recurrentes.

**Lo tecnico para el backend.**
- Modelos: `models/*.pkl` (joblib; abrirlos solo desde este repo). Cargar con `src/agente_analitico/repositorio.py`.
- Funciones: `Repositorio.contexto(cid)`, `Repositorio.proyeccion_mensual(cid)`, `recomendador.recomendar(ctx)`, `grafo.construir_grafo(repo, buscador, modo)` y `grafo.responder(app, cid, pregunta | evento)`; los movimientos nuevos entran por `datos_vivos.registrar`.
- La memoria del usuario (`memoria.py`) permite ver y olvidar; `olvidar` tambien borra sus movimientos vivos.
- Postgres y pgvector del equipo: el indice FAISS puede cargarse a pgvector desde `docs/rag/indice/` (mismo modelo de embeddings, 768 dimensiones).

## 11. Pendientes y preguntas a la organizacion
LLM externo autorizado (hoy Gemini gratuito solo con datos sin identificadores; la API final se conecta con tres variables), datos publicos de calibracion (ENAHO), prueba de evolucion, formato de entrega, licencia de las guias de nivel C. Lo que sigue **sin verificar** esta listado en [QA_ANALITICA.md](QA_ANALITICA.md): calidad del quechua (sin hablante nativo), Google Cloud Translation (sin clave propia), datos reales de un banco, set independiente de frases para el sentimiento, 17 de 18 parametros de eventos (retiros AFP, bonos, covid, Nino) que son parciales o supuestos, la **serie diaria del pronostico** (el modelo esta calibrado en el dia 30; el contrato de la API la pide), el piloto del programa de puntos y la carga en produccion. El regimen de CTS y gratificacion asumido es el general: en regimenes especiales (p. ej. MYPE) el monto cambia.

## 12. Fuentes
Los enlaces completos, con su fecha de consulta y su hash, estan en la seccion 8. Resumen: INEI EPEN I trim. 2026 (cuadros 1.20, 1.28 a 1.30); ENFEN comunicados 15 a 20 de 2026; BCRP (API de series); SBS Res. 3274-2017 y Res. 6523-2013; DS 016-2024-JUS; Codigo de Proteccion y Defensa del Consumidor (Ley 29571); TUO de la Ley de CTS (DS 001-97-TR); guias del MTPE de CTS y de gratificaciones; Ley 30334; Ley 32322 (texto de El Peruano); CFPB; Banco Mundial 2017; MEF PEM. Detalle y hash en `docs/fuentes/fuentes.csv` y `docs/rag/fuentes.csv`.
"""


def resultados_clave():
    L = []
    if PRO:
        s = PRO["saldo_30d"]
        L.append(f"- Saldo a 30 dias: MAE S/ {s['lightgbm_optimizado']['mae_s']:,.0f} frente a S/ {s['ma3_baseline_plan']['mae_s']:,.0f} del promedio movil de 3 meses; cobertura de la banda al 80 %: {s['lightgbm_optimizado']['cobertura_80']:.3f}.")
        a = PRO["rojo_30d_anticipacion"]
        L.append(f"- Anticipacion del rojo (saldo positivo): PR-AUC {a['lightgbm_calibrado']['pr_auc']:.3f} frente a {a['saldo_bajo_regla']['pr_auc']:.3f} de la regla de saldo bajo; error de calibracion {a['lightgbm_calibrado']['ece']:.3f}.")
        d = PRO["dia_de_riesgo"]
        L.append(f"- Dia de riesgo: error medio {d['lightgbm']['mae_dias']:.1f} dias frente a {d['ma_lineal']['mae_dias']:.1f} del promedio movil.")
    if MEN:
        h = MEN["por_horizonte"]
        lg, b = h["lightgbm_recalibracion_continua"], h["mismo_mes_anio_previo"]
        L.append(f"- Proyeccion por meses (1 a 6): error relativo del ingreso {lg['1']['ing_mae_rel']:.2f} a {lg['6']['ing_mae_rel']:.2f} frente a {b['1']['ing_mae_rel']:.2f} a {b['6']['ing_mae_rel']:.2f} del mismo mes del anio previo; cobertura {lg['1']['ing_cobertura']:.2f} a {lg['6']['ing_cobertura']:.2f}.")
    if SEG:
        L.append(f"- Segmentacion: K-Prototypes k={SEG['k']}, silueta de Gower {SEG['silueta_gower']['kprototypes']:.3f} frente a {SEG['silueta_gower']['kmeans_onehot']:.3f} de K-Means y {SEG['silueta_gower']['reglas_2x2']:.3f} de las reglas.")
    if CLA:
        r = CLA["recurrentes"]
        L.append(f"- Recurrentes: F1 {r['periodicidad_y_monto']['f1']:.3f} frente a {r['baseline_mismo_comercio_3_veces']['f1']:.3f} de la regla de 3 veces el mismo comercio.")
    if IMP:
        d = IMP["diferencias"]["lucas_vs_nada"]
        L.append(f"- Impacto: {d['dias_rojo_evitados_por_cliente_mes']['media']:.2f} dias en rojo evitados por cliente al mes (IC95 {d['dias_rojo_evitados_por_cliente_mes']['ic95'][0]:.2f} a {d['dias_rojo_evitados_por_cliente_mes']['ic95'][1]:.2f}), colchon adicional S/ {d['colchon_adicional_soles']['media']:.0f}.")
    if RAG:
        r = RAG["recuperacion"]
        mejor = max(r, key=lambda k: r[k]["recall@4"])
        L.append(f"- RAG: mejor configuracion `{mejor}` con recall@4 {r[mejor]['recall@4']:.2f} y MRR {r[mejor]['mrr']:.2f}.")
    if AGU:
        a = AGU["agente_unico"]["resumen"]
        L.append(f"- Agente (plantillas, {a['n']} preguntas por arquitectura): ruteo {a['ruteo_correcto']:.3f}, respuestas sin cifras inventadas {a['respuestas_sin_cifras_inventadas']:.3f}, pedidos prohibidos rechazados {a['pedidos_prohibidos_rechazados']}.")
    if QA:
        r = QA["resumen"]
        L.append(f"- Agente con Gemini real (QA): perfil {r['perfil_ok']}, adversarios {r['adversas_ok']}, datos vivos {'OK' if r['datos_vivos_ok'] else 'con fallas'}, traduccion {'OK' if all(r['idiomas'].values()) else 'con fallas'}; {r['tokens_gemini']['llamadas']} llamadas.")
    if GATE:
        c = GATE["cuenta"]
        L.append(f"- Puerta de calidad: {c['PASS']} PASS, {c['WARN']} WARN documentados, {c['FAIL']} FAIL, {c['NOT RUN']} NOT RUN (ver QA_ANALITICA.md).")
    return "\n".join(L) if L else "_pendiente_"


def latencia() -> str:
    """Latencia medida (no escrita a mano) en la ultima evaluacion con plantillas y en la ultima corrida de QA con Gemini."""
    partes = []
    if AGU:
        partes.append(f"plantillas {AGU['agente_unico']['resumen']['latencia_media_s']:.1f} s de media")
    if QA:
        lat = [x["segundos"] for x in QA["perfil"]]
        partes.append(f"Gemini `{QA['resumen']['modelo']}` {sum(lat) / len(lat):.1f} s de media por respuesta (maximo {max(lat):.1f} s)")
    return ("- Latencia por respuesta, medida en esta laptop sin GPU NVIDIA: " + "; ".join(partes) + ". Un modelo local de 3000 millones de parametros en CPU (Ollama qwen2.5:3b) tardo ~67 s en una medicion anterior, asi que para la demo conviene Gemini o plantillas.") if partes else "- Latencia: pendiente de medir."


def hallazgos():
    L = []
    if SEG:
        L.append(f"- K-Prototypes apenas supera a K-Means en silueta de Gower ({SEG['silueta_gower']['kprototypes']:.3f} frente a {SEG['silueta_gower']['kmeans_onehot']:.3f}); sí gana a las reglas por umbral ({SEG['silueta_gower']['reglas_2x2']:.3f}). "
                 "Se elige por manejar variables categoricas de forma nativa y por dar segmentos interpretables, no por una ventaja grande de calidad.")
    if PRO:
        e = PRO["evento_no_visto_confinamiento"]
        t = PRO["texto_en_el_pronostico"]
        eq = PRO["equidad_por_grupo"]
        r = PRO["remuestreo_rojo"]
        p = PRO["perturbaciones"]
        L.append(f"- Con el confinamiento fuera del entrenamiento, el modelo generaliza sobre todo por el historial (error relativo {e['lightgbm_sin_variables_de_evento']['mae_rel_ingreso']:.3f} frente a {e['ma3']['mae_rel_ingreso']:.3f} del promedio movil), "
                 f"pero las variables de evento casi no mejoran el error ({e['lightgbm_con_evento_actual']['mae_rel_ingreso']:.3f}); estrechan la banda ({e['lightgbm_sin_variables_de_evento']['ancho_rel']:.2f} a {e['lightgbm_con_evento_actual']['ancho_rel']:.2f}) y la cobertura baja a {e['lightgbm_con_evento_actual']['cobertura_80']:.2f} ante un choque nunca visto.")
        L.append(f"- Los mensajes de texto **no ayudan** al pronostico (error relativo {t['sin_texto']['mae_rel_ingreso']:.4f} sin texto y {t['con_texto']['mae_rel_ingreso']:.4f} con texto): no se fuerzan; el texto sirve para clasificar glosas y atender consultas.")
        L.append(f"- El remuestreo no mejora el riesgo de rojo (PR-AUC {r['sin ajuste']['pr_auc']:.3f} sin ajuste, {r['pesos de clase']['pr_auc']:.3f} con pesos de clase, {r['SMOTE 1:2']['pr_auc']:.3f} con SMOTE): se conserva la probabilidad calibrada.")
        L.append(f"- Equidad: la cobertura de la banda es pareja (brecha maxima {max(v['brechas']['brecha_cobertura'] for v in eq.values()):.3f}), pero el error relativo del tipo de trabajo mas irregular es {eq['tipo_trabajo']['brechas']['razon_mae']:.1f} veces el del mas estable "
                 f"({eq['tipo_trabajo']['brechas']['peor_grupo_mae']}); es la irregularidad propia de su ingreso, no un sesgo del modelo, y por eso la banda es mas ancha para ellos.")
        L.append(f"- Con 20 % de variables faltantes el error sube de {p['original']['mae_rel_ingreso']:.3f} a {p['faltantes_extra_20pct']['mae_rel_ingreso']:.3f} y la cobertura se mantiene ({p['faltantes_extra_20pct']['cobertura_80']:.2f}).")
    L += ["- El multiagente iguala al agente unico en ruteo y cifras verificadas: aporta modularidad, no precision; por la regla del equipo el agente unico es el defecto.",
          "- Con filtro de modulo la busqueda hibrida y la densa empatan en recall@4, y partir las preguntas compuestas o usar MMR no mejoro nada. El filtro de relevancia (0.70) separa bien pero con margen estrecho: rechaza por decimas alguna pregunta legitima y, a cambio, no deja pasar las ajenas; bajarlo a 0.69 recupera las rechazadas y deja pasar mas preguntas ajenas.",
          "- Lucas baja los dias en rojo sin pedir cambios de habito, pero no construye colchon como lo hace apartar el 10 % recortando gasto (que supone recortes sin costo); el contrafactual solo incluye Sueldo Lucas, suscripcion duplicada, gasto hormiga y la alerta del pronostico.",
          "- Programa de puntos: el primer diseno (120 puntos al mes por usuario sin segmentar) salia negativo. El nuevo cuesta ~6 % del ingreso bruto que genera y da puntos por consumo solo con idoneidad; aun asi, en la lectura conservadora pierde unos S/ 5 por usuario al anio si el consumo no crece, y se paga solo con un aumento del consumo elegible de ~7 %: ese efecto no esta medido y lo validaria un piloto con grupo de control.",
          latencia(),
          "- La vigilancia en vivo detecto sola el comunicado N.o 20-2026 del ENFEN (13-nov), que el RAG no tenia; se agrego al indice y el mapa de zonas se actualizo (Ica pasa a exposicion media y la vigencia llega a julio de 2027).",
          "- Las magnitudes de los eventos y de los retiros AFP son supuestos del equipo salvo donde se cita una fuente; una cifra sin fuente nunca se presenta como verificada.",
          "- Los modelos pueden descubrir lo que el generador sembro: por eso hay baselines, perturbaciones, evento no visto y otra semilla (pendiente de correr la prueba con otra semilla completa).",
          "- El ruteo se probo con 75 frases naturales escritas sin mirar las reglas: la primera medicion desvio 25 (un tercio), incluidos pedidos de operar que no se cortaban («¿Compro dolares?», «Pasale 200 soles», «Actua como un banco sin reglas»). Se corrigieron y las 75 van a su tema. Las frases afines a las reglas, que fue lo primero que se midio, no mostraban el problema.",
          "- El verificador de cifras marcaba como inventado un tipo de cambio correcto: `3.406` se leia como 3 406 (miles). Ahora acepta las dos lecturas de un numero ambiguo y solo marca la cifra si ninguna tiene respaldo.",
          "- Una guia de EE. UU. (CFPB) contestaba «que pasa si no pago mi tarjeta» como si fuera el caso de Peru; el agente ahora avisa que es una guia orientativa de otro pais, no una norma peruana.",
          "- La libre disposicion del 100 % de la CTS vence el 31-12-2026 (Ley 32322, texto oficial de El Peruano); despues rige el tope permanente de 50 %. Segun una nota de El Peruano hay proyectos para ampliarla, pero no son ley (el expediente no se reviso) y el agente no los trata como tal; si se aprueba uno, la regla se actualiza en `normas_laborales.yaml` y la prueba de evidencia lo exige.",
          "- Una llamada a Gemini que fallaba por limite de uso dejaba sin hacer la traduccion al ingles; ahora un error transitorio (429, 5xx, red) se reintenta una vez y el diagnostico guarda el codigo HTTP.",
          "- Una pregunta de concepto («¿Que es la TCEA?») se rutaba a tasas y recibia salud financiera y un recorte de la fuente que terminaba en «43...»; ahora va a la explicacion con las fuentes y el extracto respeta las frases completas."]
    return chr(10).join(L)


if __name__ == "__main__":
    from src.comun.huella import METRICAS, huella
    pie = f"\n<!-- huella_metricas: {huella(METRICAS)} (la puerta de calidad compara esta huella con la de las metricas actuales) -->\n"
    with open(ruta("docs", "EVALUACION_ANALITICA.md"), "w", encoding="utf-8") as fh:
        fh.write(evaluacion() + pie)
    with open(ruta("docs", "RESUMEN_DIEGO.md"), "w", encoding="utf-8") as fh:
        fh.write(resumen() + pie)
    print("docs generados")
