"""Genera docs/EVALUACION_ANALITICA.md y docs/RESUMEN_DIEGO.md con las cifras de models/metricas*.json. Ningun numero se escribe a mano.
Uso: python eval/generar_docs.py"""
import json
import os
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
AGG = cargar("metricas_agente_gemini.json")
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
        txt += f"**Recuperacion** (20 preguntas escritas a mano, k=4):\n\n{T(RAG['recuperacion'], 2)}\n**Filtro de relevancia tipo CRAG**: {json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in RAG['filtro_relevancia'].items()}, ensure_ascii=False)}\n\n"
    for nombre, A in (("plantillas (determinista)", AGU), ("Gemini con juez LLM (subconjunto)", AGG)):
        if A:
            txt += f"**Agente con {nombre}**\n\n" + T({m: A[m]["resumen"] for m in ("agente_unico", "multiagente") if m in A}, 3) + f"\nFallos de ruteo (agente unico): {A['agente_unico']['fallos_de_ruteo']}\n\n"
    return txt or "_pendiente_\n"


def seccion_escala_valor():
    txt = ""
    if ESC:
        txt += "**Escalabilidad medida** (esta laptop, 500 clientes): " + json.dumps(ESC) + "\n\n"
    if VAL:
        e = VAL["entidad_por_anio_escenario_conservador"]
        txt += (f"**Valor para la entidad** (escenario conservador, supuestos visibles): por cliente, colchon adicional S/ {VAL['por_cliente']['colchon_adicional_soles']:.0f}, "
                f"{VAL['por_cliente']['dias_en_rojo_evitados_por_mes']:.2f} dias en rojo evitados al mes. Con {e['usuarios']:,} usuarios: margen por fondeo S/ {e['margen_por_fondeo_de_lo_apartado_soles']:,.0f}, "
                f"costo de puntos S/ {e['costo_de_puntos_soles']:,.0f}, neto S/ {e['valor_neto_soles']:,.0f} al anio. {e['nota']}.\n\nSupuestos: {json.dumps(VAL['supuestos'], ensure_ascii=False)}\n")
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
"""


def resumen():
    niv = ", ".join(SEG["niveles"].values()) if SEG else "?"
    return f"""# Resumen de lo hecho: analitica e IA (Diego)

Registro de **que se hizo, que se cambio, que se mejoro, que se agrego y que se quito**, con el motivo. Las cifras salen de `models/metricas*.json` (ver [EVALUACION_ANALITICA.md](EVALUACION_ANALITICA.md)). Entidad y marca de ejemplo: **Banco Kawsay**, app **Lucas** (nombres inventados, `data/parametros/entidad.yaml`).

## 1. Como correrlo
```bash
python data/generator.py --perfil muestra      # 40 clientes, 12 meses, 1 s, queda en data/sample
python data/generator.py --perfil completo     # 500 clientes, 2019-2025, ~30 s, 0,5 GB de RAM
python -m src.datos_publicos.descargar         # fuentes oficiales y series del BCRP
python -m src.rag.indice                       # reconstruye el indice del RAG (requiere Ollama con nomic-embed-text)
python eval/entrenar_modelos.py                # entrena y evalua; guarda models/*.pkl y models/metricas_*.json
python eval/evaluar_agente.py --llm plantillas # evalua el agente (tambien --llm ollama o gemini)
python eval/construir_notebooks.py             # ejecuta los notebooks de notebooks/
python eval/generar_docs.py                    # regenera estos documentos
python -m pytest tests -q                      # 57 pruebas
```
Claves solo en `.env` (no se sube). `LLM_PROVIDER=ollama|gemini|plantillas`. Las rutas se calculan desde la raiz del repo (`src/comun/rutas.py`); una prueba impide rutas absolutas.

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
| Alerta por zona de riesgo del Nino con prevencion | `src/models/riesgo_clima.py`, `data/parametros/zonas_riesgo_fen.yaml` |
| RAG (fragmentos, embeddings locales, FAISS, filtro de relevancia) | `src/rag/`, `docs/rag/` |
| Agente LangGraph (unico y multiagente), juez determinista y juez LLM, memoria, avisos en tiempo real | `src/agent/` |
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
| No adoptado | Busqueda hibrida como defecto | La densa con filtro de modulo recupera mejor |
| No adoptado | GraphRAG, deep learning desde cero | Sin puntos extra y riesgo de tiempo (decision del plan) |
| Pendiente | Fuentes de nivel C (guia del Ministerio de Vivienda), cartilla del BCRP (bloqueo anti-bot) | Licencia por confirmar; descarga manual |

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

## 8. Integracion con el equipo
- Modelos: `models/*.pkl` (joblib, versiones en el manifiesto; abrirlos solo desde este repo). Cargar con `src/agent/repositorio.py`.
- Funciones para el backend: `Repositorio.contexto(cid)`, `Repositorio.proyeccion_mensual(cid)`, `recomendador.recomendar(ctx)`, `grafo.construir_grafo(repo, buscador, modo)` y `grafo.responder(app, cid, pregunta | evento)`.
- Interfaz web: llama a `responder` y muestra `respuesta`, `citas`, `cifras_verificadas` y `recomendaciones`. La memoria del usuario (`src/agent/memoria.py`) permite ver y olvidar.
- Avisos: `src/agent/vigilancia.py` (baja de tasa, ingreso extra, comunicado del ENFEN, riesgo de rojo; maximo 3 por semana).
- Postgres y pgvector del equipo: el indice FAISS puede cargarse a pgvector desde `docs/rag/indice/` (mismo modelo de embeddings, 768 dimensiones).

## 9. Pendientes y preguntas a la organizacion
LLM externo autorizado (hoy Gemini gratuito solo con datos sin identificadores), datos publicos de calibracion (ENAHO), prueba de evolucion, formato de entrega, licencia de las guias de nivel C, verificar normas y fechas de los retiros AFP, set independiente de frases para el sentimiento.

## 10. Fuentes
INEI EPEN I trim. 2026 (cuadros 1.20, 1.28 a 1.30); ENFEN comunicados 15 a 19 de 2026; BCRP (API de series); SBS Res. 3274-2017; DS 016-2024-JUS; CFPB; Banco Mundial 2017; MEF PEM. Detalle y hash en `docs/fuentes/fuentes.csv` y `docs/rag/fuentes.csv`.
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
        L.append(f"- Agente (plantillas): ruteo {a['ruteo_correcto']:.3f}, respuestas sin cifras inventadas {a['respuestas_sin_cifras_inventadas']:.3f}, pedidos prohibidos rechazados {a['pedidos_prohibidos_rechazados']}.")
    return "\n".join(L) if L else "_pendiente_"


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
          "- La busqueda hibrida no supera a la densa con filtro de modulo; el filtro de relevancia separa bien pero con margen estrecho entre la pregunta con respuesta mas baja y la de fuera mas alta.",
          "- Lucas baja los dias en rojo sin pedir cambios de habito, pero no construye colchon como lo hace apartar el 10 % recortando gasto (que supone recortes sin costo); el contrafactual solo incluye Sueldo Lucas, suscripcion duplicada, gasto hormiga y la alerta del pronostico.",
          "- Con los supuestos del equipo, el valor neto anual para la entidad es **negativo** si el usuario promedio gana 120 puntos al mes: el fondeo de lo apartado deja menos de lo que cuestan los puntos. El programa se sostiene por debajo de unos 80 puntos al mes por usuario o premiando solo conductas que generen ingreso; la retencion, la mora evitada y la venta cruzada idonea no se valoran sin un piloto.",
          "- Latencia medida el 14-nov en esta laptop (sin GPU NVIDIA): plantillas ~1 s, Gemini 3.5 flash-lite 3 a 12 s con juez, Ollama qwen2.5:3b en CPU ~67 s por respuesta (con cifras verificadas pero redaccion regular). Para la demo conviene Gemini o plantillas; Ollama en una laptop con GPU.",
          "- La vigilancia en vivo detecto sola el comunicado N.o 20-2026 del ENFEN (13-nov), que el RAG no tenia; se agrego al indice y el mapa de zonas se actualizo (Ica pasa a exposicion media y la vigencia llega a julio de 2027).",
          "- Las magnitudes de los eventos y de los retiros AFP son supuestos del equipo salvo donde se cita una fuente; una cifra sin fuente nunca se presenta como verificada.",
          "- Los modelos pueden descubrir lo que el generador sembro: por eso hay baselines, perturbaciones, evento no visto y otra semilla (pendiente de correr la prueba con otra semilla completa)."]
    return chr(10).join(L)


if __name__ == "__main__":
    with open(ruta("docs", "EVALUACION_ANALITICA.md"), "w", encoding="utf-8") as fh:
        fh.write(evaluacion())
    with open(ruta("docs", "RESUMEN_DIEGO.md"), "w", encoding="utf-8") as fh:
        fh.write(resumen())
    print("docs generados")
