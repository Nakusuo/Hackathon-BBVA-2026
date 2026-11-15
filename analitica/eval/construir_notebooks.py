"""Arma y ejecuta los notebooks de analitica a partir de los modulos y de models/metricas*.json. Uso: python analitica/eval/construir_notebooks.py [nombre ...]"""
import os
import sys
import warnings

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "backend"))
warnings.filterwarnings("ignore")

import nbformat as nbf  # noqa: E402
from nbclient import NotebookClient  # noqa: E402

from src.comun.rutas import ruta  # noqa: E402

ARRANQUE = '''import os, sys, json, warnings
warnings.filterwarnings("ignore")
RAIZ = os.path.abspath(os.path.join(os.getcwd(), "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "backend"))
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from IPython.display import display
pd.set_option("display.width", 160); pd.set_option("display.max_columns", 30)
from src.comun.rutas import DATA_GENERADO, MODELOS
M = json.load(open(os.path.join(MODELOS, "metricas.json"), encoding="utf-8")) if os.path.isfile(os.path.join(MODELOS, "metricas.json")) else {}
for f in os.listdir(MODELOS):
    if f.startswith("metricas_") and f.endswith(".json") and not f.startswith(("metricas_rag", "metricas_agente")):
        M[f[len("metricas_"):-5]] = json.load(open(os.path.join(MODELOS, f), encoding="utf-8"))
def tabla(d, dec=3):
    return pd.DataFrame(d).T.round(dec) if isinstance(d, dict) else pd.DataFrame(d)
'''

NOTEBOOKS = {
    "01_calidad_de_datos": [
        ("md", "# 01. Calidad de los datos sintéticos\n\nQué se generó, con qué semilla, cómo se evitó el sesgo de muestreo y qué controles pasan. Todo sale de `data/QUALITY.md` y de las tablas."),
        ("code", "meta = json.load(open(os.path.join(DATA_GENERADO, 'meta.json'), encoding='utf-8')); meta"),
        ("code", "from src.generador.reporte import calcular\nr = calcular(DATA_GENERADO)\nprint({k: ('OK' if v else 'FALLA') for k, v in r['controles'].items()})"),
        ("md", "## Estratos y pesos muestrales\nCada estrato (arquetipo × ahorro × gasto) tiene un piso; el peso restituye la proporción objetivo."),
        ("code", "r['estratos'].round(3)"),
        ("md", "## Ingreso por segmento y efecto del confinamiento"),
        ("code", "print(r['ingreso_2025'].round(0).to_dict()); print('abr-2020 / feb-2020:', r['covid'].round(2).to_dict()); print('ponderado 2025:', round(r['ingreso_2025_ponderado']), '| INEI urbano 2093,7')"),
        ("code", "fig, ax = plt.subplots(1, 2, figsize=(11, 3.2))\nr['rojo_anio'].plot(ax=ax[0], marker='o'); ax[0].set_title('Fracción de días con saldo negativo por año')\nr['rojo_seg'].plot.bar(ax=ax[1]); ax[1].set_title('Por segmento'); plt.tight_layout(); plt.savefig(os.path.join(MODELOS, 'fig_rojo.png'), dpi=110); plt.show()"),
    ],
    "02_segmentacion": [
        ("md", "# 02. Segmentación con K-Prototypes y nombres por nivel\n\nK-Prototypes (variables mixtas) frente a K-Means y a reglas por umbral. El nombre de cada segmento sale del ranking de su salud financiera mediana."),
        ("code", "S = M['segmentacion']; print('k elegido:', S['k']); tabla(S['tabla_k'])"),
        ("code", "print('Silueta de Gower:', S['silueta_gower']); tabla(S['ari_vs_etiquetas'])"),
        ("md", "## Los segmentos y su nombre"),
        ("code", "d = tabla(S['descripcion'], 2); d[['nivel', 'n', 'salud_mediana', 'ingreso_medio', 'cv_ingreso', 'ahorro_pct', 'gasto_sobre_ingreso', 'dias_rojo_3m', 'colchon_observado']]"),
        ("md", "## Composición de los niveles por grupo (control de sesgo)\nSi un nivel estuviera dominado por una región o una edad, sería una señal de sesgo."),
        ("code", "for g, t in S['composicion_de_niveles_por_grupo'].items():\n    print(g); display(tabla(t, 2))"),
        ("md", "**Arranque en frío** (predecir el nivel solo con lo declarado): precisión de validación cruzada frente a la clase mayoritaria."),
        ("code", "print(round(S['arranque_en_frio_precision'], 3), 'frente a', round(S['referencia_clase_mayoritaria'], 3))"),
    ],
    "03_pronostico": [
        ("md", "# 03. Pronóstico: saldo a 30 días y proyección por meses\n\nSaldo esperado con banda al 80 %, probabilidad de quedar en rojo, día de riesgo y, por mes, ingresos, gastos y neto de los próximos 6 meses."),
        ("md", "## Saldo a 30 días frente a sus baselines"),
        ("code", "P = M['pronostico']; tabla(P['saldo_30d'])"),
        ("code", "print('MAE relativo ponderado por la población objetivo:', {k: round(v, 3) for k, v in P['mae_rel_ponderado'].items()})\nprint('Optuna:', {k: (round(v, 4) if isinstance(v, float) else v) for k, v in P['optuna'].items()})"),
        ("md", "## Anticipación del rojo (solo clientes con saldo positivo en el origen)"),
        ("code", "pd.DataFrame({k: v for k, v in P['rojo_30d_anticipacion'].items() if isinstance(v, dict)}).T.round(3)"),
        ("code", "tabla(P['dia_de_riesgo'])"),
        ("md", "## Equidad: error y cobertura por grupo\nUna brecha de cobertura mayor a 5 puntos o un error 1,3 veces mayor en un grupo enciende la alerta."),
        ("code", "for g, e in P['equidad_por_grupo'].items():\n    print(g, '->', {k: (round(v, 3) if isinstance(v, float) else v) for k, v in e['brechas'].items()}); display(tabla(e['tabla'], 3))"),
        ("md", "## Remuestreo del riesgo de rojo (clase rara)"),
        ("code", "tabla(P['remuestreo_rojo'])"),
        ("md", "## Perturbaciones y evento no visto"),
        ("code", "tabla(P['perturbaciones'])"),
        ("code", "tabla({k: v for k, v in P['evento_no_visto_confinamiento'].items() if isinstance(v, dict)})"),
        ("md", "## ¿Ayuda el texto de los mensajes?"),
        ("code", "P['texto_en_el_pronostico']['mejora_mae_rel'], P['texto_en_el_pronostico']['rojo_pr_auc_sin'], P['texto_en_el_pronostico']['rojo_pr_auc_con']"),
        ("md", "## Proyección por meses (ingreso, gasto, neto)"),
        ("code", "PM_ = M['pronostico_mensual']; print(PM_['ventanas'])\nfor k, v in PM_['por_horizonte'].items():\n    print(k); display(tabla(v, 3))"),
        ("code", "for g in ('tipo', 'seg', 'region', 'edad'):\n    print('por', g); display(tabla(PM_[f'por_{g}']['lightgbm_recalibracion_continua'], 3))"),
        ('md', '## Serie diaria: los 30 días con banda al 80 % (contrato `/forecast`)\nMismo corte temporal con embargo; cobertura medida en cada día frente a dos baselines.'),
        ('code', "S = M['serie_diaria']\nprint({k: round(v, 3) for k, v in S['serie_diaria'].items()})\nprint('recta al día 30:', {k: round(v, 3) for k, v in S['linea_base_recta_al_dia_30'].items()})\nprint('promedio móvil 3 meses:', {k: round(v, 3) for k, v in S['linea_base_promedio_movil_3_meses'].items()})\ndisplay(pd.DataFrame(S['por_dia']['serie_diaria']).set_index('dia').iloc[::3].round(3))"),
        ('md', '## Otra muestra del generador, sin reentrenar\nSi el pronóstico solo hubiera aprendido el ruido de la semilla 2026, aquí se caería.'),
        ('code', "O = M['otra_semilla']\nprint({k: v for k, v in O.items() if k in ('semilla_de_entrenamiento', 'semilla_de_la_muestra_nueva', 'clientes', 'sin_reentrenar')})\ndisplay(tabla(O['saldo_30d_en_la_muestra_nueva']))\nprint('rojo', O['rojo_30d_en_la_muestra_nueva']); print('serie diaria', O['serie_diaria_en_la_muestra_nueva']); print('segmentación', O['segmentacion'])"),
    ],
    "04_clasificacion_y_recomendacion": [
        ("md", "# 04. Clasificación, recurrentes, atípicos, sentimiento y recomendador\n\nCada técnica frente a su alternativa sencilla."),
        ("code", "C = M['clasificacion']; print(json.dumps(C['glosa_a_categoria'], indent=1)); print(json.dumps(C['recurrentes'], indent=1)); print(json.dumps(C['suscripciones_duplicadas'], indent=1))"),
        ("code", "print(json.dumps(C['atipicos'], indent=1)); print(json.dumps(C['sentimiento'], indent=1))"),
        ("md", "## Impacto en soles de seguir a Lucas (reproducción contrafactual 2024–2025)"),
        ("code", "I = M['impacto']; display(tabla(I['tabla'])); print(json.dumps(I['diferencias'], indent=1)); display(tabla(I['por_segmento'])); I['supuestos']"),
        ("md", "## Recomendaciones y ofertas para tres perfiles"),
        ("code", "os.environ['LLM_PROVIDER'] = 'plantillas'\nfrom src.agente_analitico.repositorio import Repositorio\nrepo = Repositorio()\nsys.path.insert(0, os.path.join(RAIZ, 'analitica', 'eval'))\nfrom evaluar_agente import clientes_de_prueba\nids = clientes_de_prueba(repo)\nfrom src.models import recomendador as R\nfor nombre, cid in ids.items():\n    c = repo.contexto(cid); print(nombre, cid, c['nivel'], 'salud', c['salud'])\n    for r in R.recomendar(c, 4): print('  -', r['id'], '|', r['accion'][:110])"),
        ('md', '## Sentimiento en un set independiente\nLa medición anterior con frases de quien armó el léxico lo favorecía (0.92); en frases nuevas escritas sin verlo, el modelo entrenado gana.'),
        ('code', "SI = M['sentimiento_independiente']\nprint({k: SI[k] for k in ('frases_generadas', 'frases_con_consenso', 'coincidencia_generacion_vs_etiquetado_ciego', 'exactitud_de_la_clase_mayoritaria')})\nprint('léxico', SI['lexico']); print('TF-IDF + regresión logística', SI['tfidf_lr'])\ndisplay(tabla(SI['por_clase']))"),
        ('md', '## Quechua frente a FLORES-200 (quechua de Ayacucho)\nchrF frente a un piso: copiar el texto de origen sin traducir. No sustituye a un hablante nativo.'),
        ('code', "Q = M['quechua']\nprint(Q['fuente']); print('oraciones:', Q['n'])\nfor d in ('es_a_qu', 'qu_a_es'):\n    print(d, {k: (round(v, 1) if isinstance(v, float) else v) for k, v in Q[d].items() if k in ('chrf', 'chrf_mas_mas', 'piso_copiar_el_origen_chrf', 'oraciones_que_cayeron_al_texto_original')}, 'IC95', [round(x, 1) for x in Q[d]['ic95_chrf']])"),
        ('md', '## Programa de puntos a futuro y política de ahorro\nProyección a 5 años con supuestos del equipo (sin piloto) y comparación de políticas con el mismo supuesto.'),
        ('code', "V = M['valor']['proyeccion_a_futuro']\nfor k, e in V['escenarios'].items():\n    print(k, 'se paga en el año', e['se_paga_en_el_anio'], [round(x['neto_acumulado'], 1) for x in e['por_anio']])\nprint('ahorro adicional para pagarse en el año 1:', round(V['ahorro_adicional_necesario_para_pagarse_en_el_anio_1'], 4))\ndisplay(tabla(M['impacto']['tabla']))"),
    ],
    "05_rag_y_agente": [
        ("md", "# 05. RAG y agente\n\nRecuperación evaluada por separado, filtro de relevancia tipo CRAG, agente único frente a multiagente y juez doble."),
        ("code", "R_ = json.load(open(os.path.join(MODELOS, 'metricas_rag.json'), encoding='utf-8')); tabla(R_['recuperacion'])"),
        ("code", "R_['filtro_relevancia']"),
        ("code", "A = json.load(open(os.path.join(MODELOS, 'metricas_agente_plantillas.json'), encoding='utf-8'))\npd.DataFrame({m: A[m]['resumen'] for m in ('agente_unico', 'multiagente')}).round(3)"),
        ("code", "A['agente_unico']['fallos_de_ruteo'], A['multiagente']['fallos_de_ruteo']"),
        ("code", "print(open(os.path.join(RAIZ, 'docs', 'presentacion', 'diagramas', 'grafo_multiagente.md'), encoding='utf-8').read()[:1800])"),
        ("md", "## Demo del agente"),
        ("code", "os.environ['LLM_PROVIDER'] = 'plantillas'\nfrom src.agente_analitico.repositorio import Repositorio\nfrom src.agente_analitico.grafo import construir_grafo, responder\nfrom src.rag.indice import Buscador\nsys.path.insert(0, os.path.join(RAIZ, 'analitica', 'eval'))\nfrom evaluar_agente import clientes_de_prueba\nrepo = Repositorio(); ids = clientes_de_prueba(repo); app = construir_grafo(repo, Buscador(), 'agente_unico')\nr = responder(app, ids['independiente_en_zona_del_nino'], '¿Estoy en riesgo por el Fenómeno El Niño?')\nprint(r['respuesta']); print(r['trazas'], r['cifras_verificadas'], r['rag_estado'])"),
        ('md', '## Validación del RAG: chunks, embeddings e índice\nQue los vectores se hicieron con el prefijo correcto, están normalizados, alineados con los textos y que no hay duplicados.'),
        ('code', "RV = json.load(open(os.path.join(MODELOS, 'metricas_rag_validacion.json'), encoding='utf-8'))\nprint(RV['comprobaciones']); print('embeddings', {k: v for k, v in RV['embeddings'].items() if k in ('modelo', 'dimension_del_indice', 'vectores', 'fragmentos', 'tipo_de_indice')})\nprint('chunks', RV['chunks']['largo'], 'duplicados', RV['chunks']['duplicados_exactos']); print('autorrecuperación', RV['autorrecuperacion'])"),
        ('md', '## Seguimiento con MLflow\nCada comparación (baseline frente a elegido) y cada modelo de producción quedan como corridas y versiones; el resumen se genera con `analitica/eval/registrar_en_mlflow.py`.'),
        ('code', "print(open(os.path.join(RAIZ, 'docs', 'presentacion', 'mlflow_resumen.md'), encoding='utf-8').read()[:2500])"),
    ],
}


def construir(nombre, celdas, ejecutar=True):
    nb = nbf.v4.new_notebook()
    nb.cells.append(nbf.v4.new_code_cell(ARRANQUE))
    for tipo, src in celdas:
        nb.cells.append(nbf.v4.new_markdown_cell(src) if tipo == "md" else nbf.v4.new_code_cell(src))
    destino = ruta("analitica", "notebooks", f"{nombre}.ipynb")
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    if ejecutar:
        NotebookClient(nb, timeout=900, kernel_name="python3", resources={"metadata": {"path": ruta("analitica", "notebooks")}}).execute()
    nbf.write(nb, destino)
    return destino


if __name__ == "__main__":
    solo = sys.argv[1:] or list(NOTEBOOKS)
    for n in solo:
        print("construyendo", n, flush=True)
        print(construir(n, NOTEBOOKS[n]), flush=True)
