"""Comparativa de modelos para la presentacion: para cada problema, los candidatos que se midieron, cual se eligio y por que, con una tabla y una grafica.
Todo sale de models/*.json (nada escrito a mano): las cifras de la explicacion se toman de los mismos archivos que la grafica, asi no se pueden desalinear.
Salidas: docs/comparativa_modelos.md, docs/comparativa_modelos.csv, docs/figuras/comparativa_modelos.png (panel general) y docs/figuras/comparativa/<problema>.png (una por diapositiva).
Uso: python eval/comparativa_modelos.py"""
import csv
import json
import os
import sys
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELOS, DOCS = os.path.join(RAIZ, "models"), os.path.join(RAIZ, "docs")
# Paleta de referencia validada (contraste >= 3:1 y separacion para daltonismo): el elegido en azul con textura; los descartados en gris neutro. Texto siempre en tinta, nunca en el color de la serie.
SUPERFICIE, TINTA, TINTA_2, AZUL, GRIS, AZUL_CLARO = "#fcfcfb", "#0b0b0b", "#52514e", "#2a78d6", "#8c8b86", "#a9c8f0"


def J(nombre: str) -> dict:
    with open(os.path.join(MODELOS, nombre), encoding="utf-8") as f:
        return json.load(f)


def _media_horizonte(PM: dict, modelo: str, clave: str) -> float:
    return float(np.mean([PM["por_horizonte"][modelo][h][clave] for h in "123456"]))


def problemas() -> list[dict]:
    M, PM, C, IM, AG, R = J("metricas.json"), J("metricas_pronostico_mensual.json"), J("metricas_clasificacion.json"), J("metricas_impacto.json"), J("metricas_agente_plantillas.json"), J("metricas_rag.json")
    P = []
    # 1. Segmentacion -------------------------------------------------------------------------------------------------------------------------------
    seg = M["segmentacion"]
    s, a, tk = seg["silueta_gower"], seg["ari_vs_etiquetas"], seg["tabla_k"][str(seg["k"])]
    P.append(dict(slug="01_segmentacion", titulo="Segmentación de clientes", metrica="Silueta de Gower", mejor="mayor", fmt=".3f", fuente="metricas.json",
                  candidatos=[("K-Prototypes", s["kprototypes"]), ("K-means (one-hot)", s["kmeans_onehot"]), ("Reglas 2×2", s["reglas_2x2"])], elegido=0,
                  por_que=(f"Mezcla variables numéricas y categóricas sin convertirlas a ceros y unos. En silueta de Gower empata con K-means ({s['kprototypes']:.3f} frente a {s['kmeans_onehot']:.3f}) y supera a las reglas 2×2 ({s['reglas_2x2']:.3f}); "
                           f"donde se separa es en recuperar los arquetipos reales de la población simulada (ARI {a['kprototypes']['arquetipo']:.3f} frente a {a['kmeans_onehot']['arquetipo']:.3f} y {a['reglas_2x2']['arquetipo']:.3f}). "
                           f"Se eligen k={seg['k']} segmentos: es el de mayor puntaje entre los k con estabilidad de remuestreo ≥ 0.60 (silueta {tk['silueta_gower']:.3f}, estabilidad ARI {tk['estabilidad_ari']:.3f}, segmento más chico de {tk['tamano_min']} clientes)."),
                  limite="La silueta de K-Prototypes y K-means es casi la misma: la ventaja está en los arquetipos recuperados, no en la silueta."))
    # 2. Pronostico de saldo a 30 dias --------------------------------------------------------------------------------------------------------------
    sd = M["pronostico"]["saldo_30d"]
    lg, ma, es = sd["lightgbm_optimizado"], sd["ma3_baseline_plan"], sd["perfil_estructural"]
    P.append(dict(slug="02_saldo_30_dias", titulo="Pronóstico del saldo a 30 días", metrica="Error medio / ingreso mensual", mejor="menor", fmt=".2f", fuente="metricas.json",
                  candidatos=[("LightGBM + bandas conformales", lg["mae_rel_ingreso"]), ("Promedio móvil de 3 meses", ma["mae_rel_ingreso"]), ("Perfil estructural", es["mae_rel_ingreso"])], elegido=0,
                  por_que=(f"Error de {lg['mae_rel_ingreso']:.2f} veces el ingreso mensual frente a {ma['mae_rel_ingreso']:.2f} del promedio móvil y {es['mae_rel_ingreso']:.2f} del perfil estructural ({1 - lg['mae_rel_ingreso'] / ma['mae_rel_ingreso']:.0%} menos error que el promedio móvil). "
                           f"La banda al 80 % cubre {lg['cobertura_80']:.3f} de los casos (objetivo 0.80) con una banda más angosta ({lg['ancho_rel']:.2f} frente a {ma['ancho_rel']:.2f}); el promedio móvil cubre solo {ma['cobertura_80']:.3f}. "
                           f"Hiperparámetros con Optuna ({M['pronostico']['optuna']['_n_trials']} pruebas) y calibración conformal por segmento, validado en 2024 a 2025 sin haberlo visto al entrenar."),
                  limite="Está calibrado en el día 30. Una serie diaria con banda al 80 % para cada uno de los 30 días no está entrenada ni validada."))
    # 3. Alerta de saldo en rojo ---------------------------------------------------------------------------------------------------------------------
    rj = M["pronostico"]["rojo_30d_anticipacion"]
    P.append(dict(slug="03_alerta_rojo", titulo="Alerta de saldo en rojo a 30 días", metrica="PR-AUC (evento raro)", mejor="mayor", fmt=".3f", fuente="metricas.json",
                  candidatos=[("LightGBM calibrado", rj["lightgbm_calibrado"]["pr_auc"]), ("Regla de saldo bajo", rj["saldo_bajo_regla"]["pr_auc"]), ("Perfil estructural", rj["perfil_estructural"]["pr_auc"])], elegido=0,
                  por_que=(f"PR-AUC {rj['lightgbm_calibrado']['pr_auc']:.3f} frente a {rj['saldo_bajo_regla']['pr_auc']:.3f} de la regla simple y {rj['perfil_estructural']['pr_auc']:.3f} del perfil estructural; el azar daría {rj['tasa_positivos']:.3f}. "
                           f"La ventaja real es la calibración: error de calibración (ECE) de {rj['lightgbm_calibrado']['ece']:.3f} frente a {rj['saldo_bajo_regla']['ece']:.3f} de la regla, así que el «p_rojo» que ve la persona se puede leer como una probabilidad. ROC-AUC {rj['lightgbm_calibrado']['roc_auc']:.3f}."),
                  limite=f"La ventaja sobre la regla simple en PR-AUC es modesta ({rj['lightgbm_calibrado']['pr_auc'] - rj['saldo_bajo_regla']['pr_auc']:.3f}); lo que justifica el modelo es la calibración. Evento raro: {rj['tasa_positivos']:.1%} de los casos."))
    # 4. Dia de riesgo -------------------------------------------------------------------------------------------------------------------------------
    dr = M["pronostico"]["dia_de_riesgo"]
    P.append(dict(slug="04_dia_de_riesgo", titulo="Día en que el saldo cae a rojo", metrica="Error medio en días", mejor="menor", fmt=".1f", fuente="metricas.json",
                  candidatos=[("LightGBM", dr["lightgbm"]["mae_dias"]), ("Perfil estructural", dr["estructural"]["mae_dias"]), ("Tendencia lineal", dr["ma_lineal"]["mae_dias"])], elegido=0,
                  por_que=(f"Se equivoca en promedio {dr['lightgbm']['mae_dias']:.1f} días frente a {dr['estructural']['mae_dias']:.1f} del perfil estructural y {dr['ma_lineal']['mae_dias']:.1f} de la tendencia lineal; "
                           f"acierta dentro de ±3 días el {dr['lightgbm']['acierto_pm3']:.0%} de las veces (contra {dr['estructural']['acierto_pm3']:.0%} y {dr['ma_lineal']['acierto_pm3']:.0%})."),
                  limite=f"Es la parte más débil del pronóstico: menos de la mitad de los días de riesgo cae a ±3 días. Por eso la app dice «hacia el día X», no una fecha exacta. Casos con día de riesgo: {dr['lightgbm']['n']}."))
    # 5. Proyeccion mensual --------------------------------------------------------------------------------------------------------------------------
    modelos_m = [("lightgbm_recalibracion_continua", "LightGBM, recalibración continua"), ("lightgbm_conformal_fijo", "LightGBM, calibración fija"), ("mismo_mes_anio_previo", "Mismo mes del año previo"), ("promedio_3_meses", "Promedio de 3 meses")]
    mae = [(n, _media_horizonte(PM, k, "ing_mae_rel")) for k, n in modelos_m]
    cob = [(n, _media_horizonte(PM, k, "ing_cobertura")) for k, n in modelos_m]
    gas = _media_horizonte(PM, "lightgbm_recalibracion_continua", "gas_mae_rel")
    P.append(dict(slug="05_proyeccion_mensual_error", titulo="Proyección mensual de ingresos (1 a 6 meses)", metrica="Error medio / ingreso mensual (promedio de los 6 horizontes)", mejor="menor", fmt=".2f", fuente="metricas_pronostico_mensual.json",
                  candidatos=mae, elegido=0,
                  por_que=(f"Error de ingresos de {mae[0][1]:.2f} veces el ingreso mensual frente a {mae[2][1]:.2f} (mismo mes del año previo) y {mae[3][1]:.2f} (promedio de 3 meses); en gastos el error es de solo {gas:.2f}. "
                           f"Con la misma predicción puntual, la recalibración continua corrige la banda: cubre {cob[0][1]:.3f} de los ingresos (objetivo 0.80) y la calibración fija {cob[1][1]:.3f}."),
                  limite="El ingreso de independientes y mixtos es mucho más difícil de proyectar que el de dependientes: el error depende del tipo de trabajo (ver tabla por tipo en docs/EVALUACION_ANALITICA.md)."))
    P.append(dict(slug="06_proyeccion_mensual_cobertura", titulo="Proyección mensual: cobertura de la banda al 80 %", metrica="Cobertura de ingresos (objetivo 0.80)", mejor="objetivo", objetivo=0.80, fmt=".3f", fuente="metricas_pronostico_mensual.json",
                  candidatos=cob, elegido=0, por_que=f"La banda debería contener el ingreso real el 80 % de las veces. La recalibración continua queda en {cob[0][1]:.3f}; la calibración fija se desajusta con el tiempo ({cob[1][1]:.3f}) y el promedio de 3 meses queda corto ({cob[3][1]:.3f}). "
                                                      f"El mismo mes del año previo cubre {cob[2][1]:.3f} pero con un error mucho mayor ({mae[2][1]:.2f} frente a {mae[0][1]:.2f}).",
                  limite="Cubrir más que el objetivo no es mejor: una banda demasiado ancha deja de ser útil."))
    # 6. Glosas --------------------------------------------------------------------------------------------------------------------------------------
    g = C["glosa_a_categoria"]
    P.append(dict(slug="07_glosas", titulo="Categoría de cada movimiento (glosa)", metrica="F1 macro", mejor="mayor", fmt=".3f", fuente="metricas_clasificacion.json",
                  candidatos=[("TF-IDF por caracteres + SGD lineal", g["tfidf_char_sgd_lineal"]["f1_macro"]), ("Diccionario de palabras", g["diccionario"]["f1_macro"])], elegido=0,
                  por_que=(f"F1 macro de {g['tfidf_char_sgd_lineal']['f1_macro']:.3f} frente a {g['diccionario']['f1_macro']:.3f} del diccionario, con la misma exactitud ({g['tfidf_char_sgd_lineal']['exactitud']:.3f}) sobre {g['n_prueba']:,} movimientos: "
                           f"con igual exactitud, un F1 macro mayor indica que acierta mejor en las categorías poco frecuentes. Se descartó LinearSVC por tiempo de entrenamiento (más de 13 minutos en esta laptop sin terminar)."),
                  limite="El generador usa plantillas de glosa: con glosas reales de un banco la métrica será menor. En el agente, una glosa desconocida cae a «otros» si la confianza es menor de 0.80."))
    # 7. Recurrentes ---------------------------------------------------------------------------------------------------------------------------------
    r = C["recurrentes"]
    P.append(dict(slug="08_gastos_recurrentes", titulo="Gastos fijos y suscripciones", metrica="F1", mejor="mayor", fmt=".3f", fuente="metricas_clasificacion.json",
                  candidatos=[("Periodicidad + estabilidad del monto", r["periodicidad_y_monto"]["f1"]), ("«Mismo comercio 3 veces»", r["baseline_mismo_comercio_3_veces"]["f1"])], elegido=0,
                  por_que=(f"Precisión de {r['periodicidad_y_monto']['precision']:.3f} y F1 de {r['periodicidad_y_monto']['f1']:.3f}. La regla «mismo comercio tres veces» recupera todo ({r['baseline_mismo_comercio_3_veces']['recall']:.2f} de recall) pero con precisión de "
                           f"{r['baseline_mismo_comercio_3_veces']['precision']:.3f}: marca como fijo cualquier compra repetida y llenaría de falsas alertas. Evaluado en {r['n_clientes']} clientes."),
                  limite=f"Recall de {r['periodicidad_y_monto']['recall']:.2f}: se le escapan algunos recurrentes con montos o fechas irregulares."))
    # 8. Atipicos ------------------------------------------------------------------------------------------------------------------------------------
    at = C["atipicos"]
    P.append(dict(slug="09_atipicos", titulo="Movimientos atípicos", metrica="Precisión en los k más sospechosos", mejor="mayor", fmt=".3f", fuente="metricas_clasificacion.json",
                  candidatos=[("Isolation Forest", at["isolation_forest"]["precision_en_k"]), ("Z-score robusto", at["zscore_robusto"]["precision_en_k"])], elegido=0,
                  por_que=(f"Isolation Forest acierta {at['isolation_forest']['precision_en_k']:.1%} de los marcados frente a {at['zscore_robusto']['precision_en_k']:.1%} del z-score robusto, sobre {at['n']:,} movimientos con {at['n_atipicos']:,} atípicos sembrados por el generador. "
                           f"Detecta combinaciones raras de variables, no solo montos altos."),
                  limite="Los atípicos son sembrados por el generador: en datos reales la precisión será distinta y hay que revisarla con casos etiquetados por analistas."))
    # 9. Sentimiento ---------------------------------------------------------------------------------------------------------------------------------
    sn = C["sentimiento"]
    P.append(dict(slug="10_sentimiento", titulo="Sentimiento de los mensajes", metrica="F1 en frases escritas a mano", mejor="mayor", fmt=".3f", fuente="metricas_clasificacion.json",
                  candidatos=[("Léxico (provisional)", sn["escritas_a_mano"]["lexico_f1"]), ("TF-IDF + regresión logística", sn["escritas_a_mano"]["tfidf_lr_f1"])], elegido=0,
                  por_que=(f"Sin ganador definitivo. El modelo entrenado aprende las plantillas del generador (F1 {sn['plantillas_futuras']['tfidf_lr_f1']:.2f} contra {sn['plantillas_futuras']['lexico_f1']:.2f} del léxico) pero cae a {sn['escritas_a_mano']['tfidf_lr_f1']:.2f} "
                           f"con {sn['escritas_a_mano']['n']} frases escritas a mano, donde el léxico llega a {sn['escritas_a_mano']['lexico_f1']:.2f}. Se toma el léxico como referencia hasta tener un set independiente."),
                  limite=f"Solo {sn['escritas_a_mano']['n']} frases escritas a mano: el resultado es indicativo. Además el texto no mejora el pronóstico (ver comparación de texto en docs/EVALUACION_ANALITICA.md), así que el sentimiento no está en producción."))
    # 10. Politica de ahorro -------------------------------------------------------------------------------------------------------------------------
    t, dl = IM["tabla"], IM["diferencias"]["lucas_vs_nada"]
    rj_l, rj_n, rj_f, rj_a = (t[k]["dias_en_rojo_por_cliente_mes"] for k in ("lucas", "nada", "diez_fijo", "diez_fijo_ajustado"))
    P.append(dict(slug="11_politica_de_ahorro", titulo="Política de ahorro (reproducción contrafactual)", metrica="Días en rojo por cliente al mes", mejor="menor", fmt=".2f", fuente="metricas_impacto.json",
                  candidatos=[("Lucas (alerta + Sueldo Lucas)", rj_l), ("No hacer nada", rj_n), ("Apartar 10 % fijo, ajustado", rj_a)], elegido=0,
                  nota=f"No se muestra «apartar 10 % fijo sin ajustar»: {rj_f:.1f} días en rojo al mes (aparta aunque no haya saldo).",
                  por_que=(f"Es la única política que reduce los días en rojo: {rj_l:.2f} por cliente al mes frente a {rj_n:.2f} sin hacer nada ({1 - rj_l / rj_n:.0%} menos; {dl['dias_rojo_evitados_por_cliente_mes']['media']:.2f} días evitados, IC95 {dl['dias_rojo_evitados_por_cliente_mes']['ic95'][0]:.2f} a {dl['dias_rojo_evitados_por_cliente_mes']['ic95'][1]:.2f}) "
                           f"y deja S/ {dl['colchon_adicional_soles']['media']:.0f} más de colchón (IC95 {dl['colchon_adicional_soles']['ic95'][0]:.0f} a {dl['colchon_adicional_soles']['ic95'][1]:.0f}). "
                           f"Apartar un 10 % fijo sin ajustar deja {rj_f:.1f} días en rojo al mes; con el ajuste solo iguala a no hacer nada ({rj_a:.2f})."),
                  limite=f"El 10 % fijo ajustado forma más colchón ({t['diez_fijo_ajustado']['colchon_final_meses_de_ingreso']:.1f} meses frente a {t['lucas']['colchon_final_meses_de_ingreso']:.1f} de Lucas): Lucas gana en días en rojo, no en colchón. Es un hallazgo abierto. Reproducción sobre datos sintéticos."))
    # 11. Agente -------------------------------------------------------------------------------------------------------------------------------------
    u, m = AG["agente_unico"]["resumen"], AG["multiagente"]["resumen"]
    P.append(dict(slug="12_agente", titulo="Arquitectura del agente", metrica="Ruteo correcto", mejor="mayor", fmt=".3f", fuente="metricas_agente_plantillas.json",
                  candidatos=[("Agente único", u["ruteo_correcto"]), ("Multiagente (supervisor)", m["ruteo_correcto"])], elegido=0,
                  por_que=(f"Mismo ruteo correcto ({u['ruteo_correcto']:.3f}), misma latencia media ({u['latencia_media_s']:.2f} s frente a {m['latencia_media_s']:.2f} s) y ninguno inventa cifras en {u['n']} preguntas: el multiagente no aporta una mejora medible. "
                           f"Se usa el agente único por ser más simple y fácil de auditar; el multiagente queda como arquitectura demostrable."),
                  limite="Evaluado con plantillas (sin LLM) sobre preguntas escritas por el equipo: mide el ruteo y las salvaguardas, no la calidad de redacción de un LLM."))
    # 12. RAG ----------------------------------------------------------------------------------------------------------------------------------------
    rc, fr = R["recuperacion"], R["filtro_relevancia"]
    ks = [("denso + filtro de modulo", "Denso + filtro de módulo"), ("hibrido + filtro de modulo", "Híbrido + filtro de módulo"), ("bm25 + filtro de modulo", "Solo palabras (BM25) + filtro"),
          ("hibrido + multiconsulta + filtro de modulo", "Híbrido + preguntas partidas"), ("hibrido + multiconsulta + MMR + filtro de modulo", "Híbrido + partidas + MMR")]
    cu = fr["con_los_umbrales_actuales"]
    P.append(dict(slug="13_rag", titulo="Recuperación de fuentes (RAG)", metrica="Recall@4 con filtro de módulo", mejor="mayor", fmt=".3f", fuente="metricas_rag.json",
                  candidatos=[(n, rc[k]["recall@4"]) for k, n in ks], elegido=0,
                  por_que=(f"Con filtro de módulo, denso e híbrido empatan en recall@4 ({rc[ks[0][0]]['recall@4']:.3f}); partir las preguntas y MMR no mejoraron nada medible. Se mantiene el denso porque el filtro de relevancia (umbral 0.70) se calibra sobre su similitud: "
                           f"acepta {round(cu['con_respuesta_aceptadas'] * fr['n_con_respuesta'])} de {fr['n_con_respuesta']} preguntas con respuesta y rechaza {round(cu['fuera_rechazadas'] * fr['n_fuera'])} de {fr['n_fuera']} ajenas (AUC {fr['auc']:.3f})."),
                  limite=f"Con {rc[ks[0][0]]['n']} preguntas, una sola mueve el recall {1 / rc[ks[0][0]]['n']:.3f}: diferencias de una pregunta no son concluyentes. La expansión de siglas se motivó por un fallo de esta misma evaluación, así que ese caso no es prueba independiente."))
    return P


# ---------------------------------------------------------------------------------------------------------------------------------- graficas
def dibujar(ax, p: dict, tam: int = 10, completo: bool = False) -> None:
    """completo=True: panel del resumen general, con barras del mismo grosor en todos los paneles (5 casillas) y nota corta. Falso: una imagen para una diapositiva."""
    nombres = ["\n".join(textwrap.wrap(n, 24)) for n, _ in p["candidatos"]]
    valores = [v for _, v in p["candidatos"]]
    n = len(valores)
    y = (4 - np.arange(n)) if completo else np.arange(n)[::-1]
    barras = ax.barh(y, valores, height=0.56, color=[AZUL if i == p["elegido"] else GRIS for i in range(n)], linewidth=0, zorder=2)
    barras[p["elegido"]].set_hatch("////")
    barras[p["elegido"]].set_edgecolor(AZUL_CLARO)
    tope = max(max(valores), p.get("objetivo", 0)) * 1.62   # sitio para el valor y la etiqueta «elegido» sin que se corten
    ax.set_xlim(0, tope)
    abajo = float(y.min()) - 0.62
    ax.set_ylim(abajo - (0.7 if p.get("objetivo") is not None else 0.0) if not completo else -0.6 - (0.7 if p.get("objetivo") is not None else 0.0), float(y.max()) + 0.62)
    if p.get("objetivo") is not None:
        ax.axvline(p["objetivo"], color=TINTA_2, linewidth=1.2, linestyle=(0, (4, 3)), zorder=1)
        ax.text(p["objetivo"], float(y.min()) - 0.5, f"objetivo {p['objetivo']:.2f}", ha="center", va="top", fontsize=tam - 1, color=TINTA_2, zorder=3, bbox=dict(facecolor=SUPERFICIE, edgecolor="none", pad=2))
    for i, (b, v) in enumerate(zip(barras, valores)):   # el fondo del texto evita que la linea del objetivo lo atraviese
        ax.text(v + tope * 0.015, b.get_y() + b.get_height() / 2, f"{v:{p['fmt']}}" + ("  ← elegido" if i == p["elegido"] else ""), va="center", ha="left", fontsize=tam, color=TINTA,
                fontweight="bold" if i == p["elegido"] else "normal", zorder=3, bbox=dict(facecolor=SUPERFICIE, edgecolor="none", pad=1.2))
    if completo and p.get("nota"):
        ax.text(0, float(y.min()) - 0.55, "\n".join(textwrap.wrap(p["nota"], 52)), fontsize=tam - 2, color=TINTA_2, va="top")
    ax.set_yticks(y)
    ax.set_yticklabels(nombres, fontsize=tam, color=TINTA)
    flecha = {"mayor": "mayor es mejor", "menor": "menor es mejor", "objetivo": "más cerca del objetivo es mejor"}[p["mejor"]]
    ax.set_title(p["titulo"], loc="left", fontsize=tam + 3, fontweight="bold", color=TINTA, pad=22 if not completo else 20)
    ax.text(0, 1.03, f"{p['metrica']} · {flecha}", transform=ax.transAxes, fontsize=tam - 1, color=TINTA_2, va="bottom")
    for lado in ("top", "right", "bottom"):   # los valores van escritos junto a cada barra: no hace falta un eje x
        ax.spines[lado].set_visible(False)
    ax.spines["left"].set_color("#c9c8c2")
    ax.set_xticks([])
    ax.tick_params(axis="y", length=0)
    ax.set_facecolor(SUPERFICIE)


def guardar_figuras(P: list[dict]) -> None:
    os.makedirs(os.path.join(DOCS, "figuras", "comparativa"), exist_ok=True)
    plt.rcParams["hatch.linewidth"] = 1.4
    for p in P:   # una imagen por problema, para pegar en una diapositiva
        fig, ax = plt.subplots(figsize=(9.2, 4.9), dpi=200, facecolor=SUPERFICIE)
        dibujar(ax, p, tam=12)
        fig.text(0.01, 0.015, f"Datos sintéticos · fuente: models/{p['fuente']} · azul rayado = modelo elegido, gris = descartado", fontsize=8.5, color=TINTA_2)
        fig.subplots_adjust(left=0.30, right=0.97, top=0.78, bottom=0.2 if not p.get("nota") else 0.27)
        if p.get("nota"):
            fig.text(0.01, 0.075, "\n".join(textwrap.wrap(p["nota"], 120)), fontsize=9, color=TINTA_2)
        fig.savefig(os.path.join(DOCS, "figuras", "comparativa", f"{p['slug']}.png"), facecolor=SUPERFICIE)
        plt.close(fig)
    columnas = 4
    filas = int(np.ceil((len(P) + 1) / columnas))
    fig, axs = plt.subplots(filas, columnas, figsize=(25, 4.0 * filas), dpi=130, facecolor=SUPERFICIE)
    axs = axs.ravel()
    for ax, p in zip(axs, P):
        dibujar(ax, p, tam=10, completo=True)
    leyenda = axs[len(P)]
    leyenda.axis("off")
    leyenda.text(0, 0.95, "Cómo leer este panel", fontsize=14, fontweight="bold", color=TINTA, va="top")
    leyenda.add_patch(plt.Rectangle((0, 0.62), 0.12, 0.1, facecolor=AZUL, hatch="////", edgecolor=AZUL_CLARO, linewidth=0, transform=leyenda.transAxes))
    leyenda.text(0.16, 0.67, "modelo elegido", fontsize=12, color=TINTA, va="center")
    leyenda.add_patch(plt.Rectangle((0, 0.44), 0.12, 0.1, facecolor=GRIS, linewidth=0, transform=leyenda.transAxes))
    leyenda.text(0.16, 0.49, "alternativa descartada", fontsize=12, color=TINTA, va="center")
    leyenda.text(0, 0.30, "Cada panel compara con la misma métrica a los modelos\nque se midieron para ese problema. La explicación de la\nelección y su límite están en docs/comparativa_modelos.md.\nTodo sale de models/*.json con datos sintéticos.", fontsize=10.5, color=TINTA_2, va="top", linespacing=1.5)
    for ax in axs[len(P) + 1:]:
        ax.axis("off")
    fig.subplots_adjust(left=0.1, right=0.985, top=0.95, bottom=0.03, hspace=0.62, wspace=0.85)
    fig.savefig(os.path.join(DOCS, "figuras", "comparativa_modelos.png"), facecolor=SUPERFICIE)
    plt.close(fig)


def escribir_documentos(P: list[dict]) -> None:
    filas = []
    for p in P:
        res = " · ".join(f"{'**' if i == p['elegido'] else ''}{n}: {v:{p['fmt']}}{'**' if i == p['elegido'] else ''}" for i, (n, v) in enumerate(p["candidatos"]))
        filas.append(f"| {p['titulo']} | {p['metrica']} ({p['mejor'] if p['mejor'] != 'objetivo' else 'cerca de 0.80'} es mejor) | {res} | **{p['candidatos'][p['elegido']][0]}** | {p['por_que']} | {p['limite']} |")
    texto = ("# Comparativa de modelos: qué se midió, qué se eligió y por qué\n\n"
             "Generado por `eval/comparativa_modelos.py` solo a partir de `models/*.json`. Datos sintéticos con semilla fija. En negrita, el modelo elegido en cada problema. "
             "Cada fila trae también el límite de la comparación: lo que no demuestra.\n\n"
             "![Comparativa de modelos](figuras/comparativa_modelos.png)\n\n"
             "Una imagen por problema para las diapositivas: `docs/figuras/comparativa/`.\n\n"
             "| Problema | Métrica | Resultados (elegido en negrita) | Elegido | Por qué se eligió | Límite |\n|---|---|---|---|---|---|\n" + "\n".join(filas) + "\n")
    with open(os.path.join(DOCS, "comparativa_modelos.md"), "w", encoding="utf-8") as f:
        f.write(texto)
    with open(os.path.join(DOCS, "comparativa_modelos.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["problema", "metrica", "mejor", "candidato", "valor", "elegido"])
        for p in P:
            for i, (n, v) in enumerate(p["candidatos"]):
                w.writerow([p["titulo"], p["metrica"], p["mejor"], n, round(v, 6), "si" if i == p["elegido"] else "no"])


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    P = problemas()
    guardar_figuras(P)
    escribir_documentos(P)
    print(f"{len(P)} problemas comparados -> docs/comparativa_modelos.md, .csv y docs/figuras/")
    for p in P:
        print(f"  {p['titulo']}: elegido {p['candidatos'][p['elegido']][0]} ({p['candidatos'][p['elegido']][1]:{p['fmt']}}) de {len(p['candidatos'])}")


if __name__ == "__main__":
    main()
