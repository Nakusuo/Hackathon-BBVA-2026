# Evaluacion analitica

Generado por `eval/generar_docs.py` desde `models/metricas*.json`. Datos sinteticos con semilla fija; las magnitudes de los eventos son supuestos del equipo (ver `data/parametros/eventos.yaml`).

## 1. Segmentacion
K elegido: **3** (mayor silueta entre los k con estabilidad de al menos 0,60).

|  | costo | silueta_gower | estabilidad_ari | tamano_min | puntaje |
|---|---|---|---|---|---|
| 3 | 4,665.778 | 0.205 | 0.744 | 68.000 | 0.872 |
| 4 | 4,261.577 | 0.175 | 0.651 | 53.000 | 0.702 |
| 5 | 3,996.510 | 0.126 | 0.673 | 49.000 | 0.514 |
| 6 | 3,776.340 | 0.158 | 0.647 | 20.000 | 0.632 |
| 7 | 3,612.372 | 0.083 | 0.592 | 20.000 | 0.296 |
| 8 | 3,450.172 | 0.129 | 0.516 | 15.000 | 0.445 |


Silueta de Gower: kprototypes 0.205, kmeans_onehot 0.204, reglas_2x2 0.058.

ARI frente a las etiquetas de referencia (solo se usan para evaluar):

|  | arquetipo | segmento_real | perfil_2x2 |
|---|---|---|---|
| kprototypes | 0.253 | 0.292 | 0.017 |
| kmeans_onehot | 0.218 | 0.277 | 0.016 |
| reglas_2x2 | 0.022 | 0.037 | 0.184 |


Segmentos y nivel asignado:

|  | nivel | n | salud_mediana | ingreso_medio | cv_ingreso | ahorro_pct | gasto_sobre_ingreso | dias_rojo_3m | colchon_observado |
|---|---|---|---|---|---|---|---|---|---|
| 0 | luchador | 68 | 45.90 | 1,376.82 | 0.60 | 0.06 | 1.12 | 17.50 | 0.73 |
| 1 | constructor | 165 | 70.30 | 1,257.47 | 0.44 | 0.25 | 0.80 | 0.00 | 1.65 |
| 2 | campeon | 267 | 82.90 | 2,571.84 | 0.02 | 0.31 | 0.73 | 0.00 | 1.70 |


Arranque en frio (nivel a partir de lo declarado): precision 0.738 frente a 0.534 de la clase mayoritaria.

## 2. Pronostico de saldo a 30 dias
Cortes con purga de 30 dias: {'entrena_hasta': '2023-06-30', 'calibra_desde': '2023-10-01', 'prueba_desde': '2024-01-01'}. Origenes: {'entrena': 109000, 'ajusta': 4500, 'calibra': 4500, 'prueba': 50000}.

### Saldo a 30 dias

|  | mae_s | mae_rel_ingreso | mape_acotado | cobertura_80 | ancho_rel |
|---|---|---|---|---|---|
| ma3_baseline_plan | 1,725.961 | 0.721 | 0.558 | 0.722 | 1.683 |
| perfil_estructural | 1,832.500 | 0.769 | 0.601 | 0.718 | 1.712 |
| lightgbm_optimizado | 883.527 | 0.426 | 0.312 | 0.806 | 1.298 |


MAE relativo ponderado por la poblacion objetivo: {k: round(v,3)} -> ma3 0.721, lightgbm 0.427.

Optuna (25 intentos): pinball 0.1514.

### Anticipacion del rojo (solo con saldo positivo en el origen)

|  | pr_auc | roc_auc | brier | ece |
|---|---|---|---|---|
| lightgbm_calibrado | 0.594 | 0.977 | 0.024 | 0.005 |
| saldo_bajo_regla | 0.581 | 0.969 | 0.027 | 0.022 |
| perfil_estructural | 0.266 | 0.940 | 0.061 | 0.088 |


Tasa de positivos 0.044 sobre 48631 origenes.

### Dia de riesgo

|  | n | mae_dias | acierto_pm3 |
|---|---|---|---|
| lightgbm | 2,134.00 | 5.40 | 0.43 |
| estructural | 2,134.00 | 7.84 | 0.37 |
| ma_lineal | 2,134.00 | 12.47 | 0.19 |


### Equidad por grupo (con pesos muestrales)

Alerta si la cobertura difiere mas de 5 puntos o el error de un grupo supera 1,3 veces el del mejor.

**segmento**: brecha de cobertura 0.018, razon de error 1.58, alerta: SI (peor error: 0).

|  | n | mae_rel | cobertura_80 | ancho_rel |
|---|---|---|---|---|
| 0 | 6,800.000 | 0.572 | 0.820 | 1.705 |
| 1 | 16,500.000 | 0.472 | 0.803 | 1.344 |
| 2 | 26,700.000 | 0.361 | 0.805 | 1.166 |


**region**: brecha de cobertura 0.019, razon de error 1.21, alerta: no (peor error: centro).

|  | n | mae_rel | cobertura_80 | ancho_rel |
|---|---|---|---|---|
| centro | 6,100.000 | 0.477 | 0.794 | 1.402 |
| lima | 22,400.000 | 0.430 | 0.807 | 1.286 |
| norte | 9,100.000 | 0.415 | 0.805 | 1.292 |
| oriente | 4,000.000 | 0.396 | 0.812 | 1.247 |
| sur | 8,400.000 | 0.407 | 0.812 | 1.287 |


**rango_edad**: brecha de cobertura 0.019, razon de error 1.24, alerta: no (peor error: 25-34).

|  | n | mae_rel | cobertura_80 | ancho_rel |
|---|---|---|---|---|
| 18-24 | 6,300.000 | 0.360 | 0.803 | 1.237 |
| 25-34 | 16,000.000 | 0.446 | 0.815 | 1.305 |
| 35-44 | 13,100.000 | 0.437 | 0.805 | 1.301 |
| 45-54 | 8,900.000 | 0.439 | 0.796 | 1.342 |
| 55+ | 5,700.000 | 0.403 | 0.805 | 1.274 |


**tipo_trabajo**: brecha de cobertura 0.044, razon de error 2.99, alerta: SI (peor error: mixto).

|  | n | mae_rel | cobertura_80 | ancho_rel |
|---|---|---|---|---|
| dependiente | 15,000.000 | 0.246 | 0.820 | 0.909 |
| dependiente_con_comision | 7,500.000 | 0.322 | 0.823 | 1.075 |
| independiente | 20,000.000 | 0.486 | 0.800 | 1.405 |
| mixto | 7,500.000 | 0.736 | 0.779 | 2.015 |


**exposicion_fen**: brecha de cobertura 0.003, razon de error 1.06, alerta: no (peor error: posible).

|  | n | mae_rel | cobertura_80 | ancho_rel |
|---|---|---|---|---|
| alta | 7,800.000 | 0.416 | 0.805 | 1.264 |
| baja | 17,000.000 | 0.425 | 0.806 | 1.310 |
| media | 22,400.000 | 0.430 | 0.807 | 1.286 |
| posible | 2,800.000 | 0.439 | 0.807 | 1.420 |


**arquetipo**: brecha de cobertura 0.044, razon de error 2.99, alerta: SI (peor error: mixto).

|  | n | mae_rel | cobertura_80 | ancho_rel |
|---|---|---|---|---|
| base_comision | 7,500.000 | 0.322 | 0.823 | 1.075 |
| formal_quincena | 15,000.000 | 0.246 | 0.820 | 0.909 |
| independiente | 20,000.000 | 0.486 | 0.800 | 1.405 |
| mixto | 7,500.000 | 0.736 | 0.779 | 2.015 |


### Remuestreo del riesgo de rojo

|  | pr_auc | roc_auc | brier | ece |
|---|---|---|---|---|
| sin ajuste | 0.603 | 0.977 | 0.024 | 0.006 |
| pesos de clase | 0.603 | 0.977 | 0.024 | 0.007 |
| submuestreo 1:2 | 0.605 | 0.977 | 0.024 | 0.007 |
| SMOTE 1:2 | 0.588 | 0.975 | 0.024 | 0.006 |


### Perturbaciones

|  | mae_s | mae_rel_ingreso | mape_acotado | cobertura_80 | ancho_rel |
|---|---|---|---|---|---|
| original | 883.527 | 0.426 | 0.312 | 0.806 | 1.298 |
| ruido_10pct_en_historial | 892.458 | 0.429 | 0.313 | 0.815 | 1.306 |
| faltantes_extra_20pct | 1,023.448 | 0.474 | 0.350 | 0.797 | 1.300 |
| clientes_con_cambio_de_patron | 822.488 | 0.388 | 0.389 | 0.812 | 1.252 |
| clientes_sin_cambio_de_patron | 895.154 | 0.434 | 0.298 | 0.805 | 1.307 |


### Evento no visto (confinamiento fuera del entrenamiento)

|  | mae_s | mae_rel_ingreso | mape_acotado | cobertura_80 | ancho_rel |
|---|---|---|---|---|---|
| n_origenes_en_evento | 41,500.000 | 41,500.000 | 41,500.000 | 41,500.000 | 41,500.000 |
| ma3 | 2,104.530 | 1.143 | 0.863 | 0.618 | 1.616 |
| lightgbm_sin_variables_de_evento | 1,141.175 | 0.744 | 0.506 | 0.739 | 1.371 |
| lightgbm_con_evento_actual | 1,120.171 | 0.740 | 0.500 | 0.738 | 1.247 |
| lightgbm_con_escenario_conocido | 1,129.217 | 0.742 | 0.497 | 0.737 | 1.237 |


### Datos no estructurados en el pronostico

MAE relativo sin texto 0.4263, con texto 0.4273; mejora media -0.00103 (IC95 -0.00171 a -0.00035). PR-AUC del rojo: 0.594 sin texto, 0.593 con texto.

## 3. Proyeccion por meses: ingresos, gastos y neto (1 a 6 meses)
Ventanas: {'entrena': {'filas': 90000, 'origen_desde': '2020-01-31', 'origen_hasta': '2022-06-30'}, 'ajusta': {'filas': 18000, 'origen_desde': '2022-10-31', 'origen_hasta': '2023-03-31'}, 'calibra': {'filas': 9000, 'origen_desde': '2023-04-30', 'origen_hasta': '2023-06-30'}, 'prueba': {'filas': 61500, 'origen_desde': '2024-01-31', 'origen_hasta': '2025-11-30'}}

**lightgbm_recalibracion_continua** (por horizonte, en meses)

|  | ing_mae_rel | ing_cobertura | gas_mae_rel | gas_cobertura | net_cobertura |
|---|---|---|---|---|---|
| 1 | 0.387 | 0.788 | 0.101 | 0.800 | 0.797 |
| 2 | 0.392 | 0.796 | 0.102 | 0.800 | 0.800 |
| 3 | 0.397 | 0.798 | 0.103 | 0.798 | 0.804 |
| 4 | 0.405 | 0.799 | 0.104 | 0.796 | 0.802 |
| 5 | 0.413 | 0.792 | 0.104 | 0.797 | 0.805 |
| 6 | 0.424 | 0.790 | 0.106 | 0.790 | 0.807 |


**lightgbm_conformal_fijo** (por horizonte, en meses)

|  | ing_mae_rel | ing_cobertura | gas_mae_rel | gas_cobertura | net_cobertura |
|---|---|---|---|---|---|
| 1 | 0.387 | 0.632 | 0.101 | 0.776 | 0.807 |
| 2 | 0.392 | 0.659 | 0.102 | 0.801 | 0.797 |
| 3 | 0.397 | 0.759 | 0.103 | 0.792 | 0.801 |
| 4 | 0.405 | 0.761 | 0.104 | 0.794 | 0.765 |
| 5 | 0.413 | 0.788 | 0.104 | 0.794 | 0.769 |
| 6 | 0.424 | 0.790 | 0.106 | 0.773 | 0.846 |


**mismo_mes_anio_previo** (por horizonte, en meses)

|  | ing_mae_rel | ing_cobertura | gas_mae_rel | gas_cobertura | net_cobertura |
|---|---|---|---|---|---|
| 1 | 0.540 | 0.860 | 0.136 | 0.825 | 0.882 |
| 2 | 0.548 | 0.834 | 0.136 | 0.822 | 0.863 |
| 3 | 0.557 | 0.813 | 0.135 | 0.830 | 0.852 |
| 4 | 0.567 | 0.810 | 0.136 | 0.835 | 0.850 |
| 5 | 0.583 | 0.792 | 0.134 | 0.825 | 0.835 |
| 6 | 0.608 | 0.790 | 0.134 | 0.837 | 0.834 |


**promedio_3_meses** (por horizonte, en meses)

|  | ing_mae_rel | ing_cobertura | gas_mae_rel | gas_cobertura | net_cobertura |
|---|---|---|---|---|---|
| 1 | 0.551 | 0.768 | 0.112 | 0.833 | 0.830 |
| 2 | 0.562 | 0.754 | 0.111 | 0.818 | 0.806 |
| 3 | 0.552 | 0.744 | 0.112 | 0.820 | 0.801 |
| 4 | 0.557 | 0.715 | 0.112 | 0.829 | 0.790 |
| 5 | 0.542 | 0.738 | 0.112 | 0.833 | 0.797 |
| 6 | 0.580 | 0.752 | 0.112 | 0.831 | 0.818 |


**Por tipo** (LightGBM con recalibracion continua)

|  | n | ing_mae_rel | ing_cobertura | gas_mae_rel | gas_cobertura | net_cobertura |
|---|---|---|---|---|---|---|
| dependiente | 18,450.000 | 0.174 | 0.777 | 0.083 | 0.795 | 0.797 |
| dependiente_con_comision | 9,225.000 | 0.290 | 0.794 | 0.088 | 0.797 | 0.789 |
| independiente | 24,600.000 | 0.511 | 0.799 | 0.124 | 0.801 | 0.808 |
| mixto | 9,225.000 | 0.679 | 0.813 | 0.103 | 0.792 | 0.810 |


**Por seg** (LightGBM con recalibracion continua)

|  | n | ing_mae_rel | ing_cobertura | gas_mae_rel | gas_cobertura | net_cobertura |
|---|---|---|---|---|---|---|
| 0 | 8,364.000 | 0.569 | 0.808 | 0.203 | 0.787 | 0.799 |
| 1 | 20,295.000 | 0.486 | 0.813 | 0.083 | 0.806 | 0.819 |
| 2 | 32,841.000 | 0.307 | 0.779 | 0.090 | 0.794 | 0.793 |


**Por region** (LightGBM con recalibracion continua)

|  | n | ing_mae_rel | ing_cobertura | gas_mae_rel | gas_cobertura | net_cobertura |
|---|---|---|---|---|---|---|
| centro | 7,503.000 | 0.459 | 0.785 | 0.107 | 0.814 | 0.794 |
| lima | 27,552.000 | 0.396 | 0.788 | 0.105 | 0.796 | 0.797 |
| norte | 11,193.000 | 0.413 | 0.795 | 0.103 | 0.787 | 0.798 |
| oriente | 4,920.000 | 0.348 | 0.822 | 0.089 | 0.800 | 0.822 |
| sur | 10,332.000 | 0.390 | 0.801 | 0.103 | 0.797 | 0.818 |


**Por edad** (LightGBM con recalibracion continua)

|  | n | ing_mae_rel | ing_cobertura | gas_mae_rel | gas_cobertura | net_cobertura |
|---|---|---|---|---|---|---|
| 18-24 | 7,749.000 | 0.337 | 0.788 | 0.106 | 0.785 | 0.795 |
| 25-34 | 19,680.000 | 0.417 | 0.799 | 0.098 | 0.801 | 0.802 |
| 35-44 | 16,113.000 | 0.411 | 0.793 | 0.100 | 0.804 | 0.803 |
| 45-54 | 10,947.000 | 0.433 | 0.790 | 0.118 | 0.798 | 0.798 |
| 55+ | 7,011.000 | 0.364 | 0.794 | 0.097 | 0.784 | 0.815 |



## 4. Clasificacion y deteccion
**Glosa a categoria** (prueba 2024-2025, 30000 movimientos): diccionario F1 macro 0.864, exactitud 0.989; TF-IDF + lineal F1 macro 0.894, exactitud 0.989. Cobertura del diccionario 1.0000.

**Recurrentes** (150 clientes):

|  | precision | recall | f1 |
|---|---|---|---|
| periodicidad_y_monto | 0.999 | 0.875 | 0.933 |
| baseline_mismo_comercio_3_veces | 0.092 | 1.000 | 0.169 |


**Suscripciones duplicadas** (por cliente): {"precision": 1.0, "recall": 0.7, "f1": 0.824, "detectados": 7, "reales": 10}

**Atipicos** (2066 en 800000 gastos): precision en k, z-score robusto 0.688, IsolationForest 0.750.

**Sentimiento** (F1 macro):

|  | lexico_f1 | tfidf_lr_f1 | n |
|---|---|---|---|
| plantillas_futuras | 0.618 | 1.000 | 12,801.000 |
| escritas_a_mano | 0.916 | 0.731 | 24.000 |


Aviso: sobre plantillas el modelo es trivial; sobre las 24 frases escritas a mano baja. El lexico se armo viendo esas mismas frases, asi que su cifra es optimista y no vale como prueba. El set independiente de 100 frases lo escribe el equipo (TODOS-01); mientras tanto el texto libre se clasifica mejor con un modelo preentrenado en espanol.

## 5. Impacto en soles (reproduccion contrafactual)
Periodo 24 meses (2024-2025), ponderado por la poblacion objetivo. Supuestos: {"tasa_mensual_por_cubrir_el_hueco": 0.1, "fraccion_apartada_10_fijo": 0.1, "recorte_hormiga": 0.2, "recorte_hormiga_en_alerta": 0.5, "dias_de_alerta": 14, "umbral_alerta_p_rojo": 0.25, "asignacion_sueldo_lucas": 0.95, "umbral_irregular_cv": 0.4}

|  | dias_en_rojo_por_cliente_mes | colchon_final_soles | colchon_final_meses_de_ingreso | costo_de_cubrir_el_hueco_soles_por_mes |
|---|---|---|---|---|
| nada | 0.837 | 4,263.586 | 1.867 | 1.486 |
| diez_fijo | 13.365 | 6,188.377 | 2.909 | 78.816 |
| diez_fijo_ajustado | 0.837 | 10,411.295 | 4.757 | 1.486 |
| lucas | 0.594 | 4,585.284 | 2.017 | 1.095 |


**lucas_vs_nada**: dias_rojo_evitados_por_cliente_mes 0.243 (IC95 0.185 a 0.302); colchon_adicional_soles 321.698 (IC95 290.385 a 357.081); intereses_evitados_soles_por_mes 0.391 (IC95 0.291 a 0.515)

**lucas_vs_diez_fijo_ajustado**: dias_rojo_evitados_por_cliente_mes 0.243 (IC95 0.184 a 0.307); colchon_adicional_soles -5826.011 (IC95 -6097.460 a -5545.073); intereses_evitados_soles_por_mes 0.391 (IC95 0.298 a 0.510)

**diez_fijo_ajustado_vs_nada**: dias_rojo_evitados_por_cliente_mes 0.000 (IC95 0.000 a 0.000); colchon_adicional_soles 6147.709 (IC95 5859.640 a 6426.616); intereses_evitados_soles_por_mes 0.000 (IC95 0.000 a 0.000)

**diez_fijo_vs_nada**: dias_rojo_evitados_por_cliente_mes -12.528 (IC95 -12.884 a -12.178); colchon_adicional_soles 1924.791 (IC95 1767.995 a 2077.026); intereses_evitados_soles_por_mes -77.330 (IC95 -82.469 a -72.192)

Por segmento:

|  | dias_rojo_nada | dias_rojo_lucas | colchon_nada | colchon_lucas |
|---|---|---|---|---|
| base_comision | 0.27 | 0.16 | 5,013.12 | 5,347.71 |
| formal_quincena | 0.30 | 0.16 | 6,656.59 | 7,029.45 |
| independiente_diario | 0.78 | 0.54 | 2,365.98 | 2,523.74 |
| independiente_proyectos | 1.88 | 1.53 | 3,229.73 | 3,616.60 |
| mixto | 1.33 | 0.86 | 2,763.35 | 3,135.12 |



## 6. RAG y agente
**Recuperacion** (20 preguntas escritas a mano, k=4):

|  | recall@4 | mrr | n |
|---|---|---|---|
| denso | 0.85 | 0.82 | 20.00 |
| denso + filtro de modulo | 0.95 | 0.89 | 20.00 |
| bm25 | 0.75 | 0.71 | 20.00 |
| bm25 + filtro de modulo | 0.80 | 0.80 | 20.00 |
| hibrido | 0.80 | 0.74 | 20.00 |
| hibrido + filtro de modulo | 0.90 | 0.87 | 20.00 |


**Filtro de relevancia tipo CRAG**: {"umbral": 0.7057, "exactitud_balanceada": 1.0, "auc": 1.0, "similitud_con_respuesta": {"media": 0.7719100000000001, "min": 0.7057}, "similitud_fuera_del_indice": {"media": 0.6609, "max": 0.7054}, "n_con_respuesta": 20, "n_fuera": 8}

**Agente con plantillas (determinista)**

|  | n | ruteo_correcto | respuestas_sin_cifras_inventadas | sin_frases_prohibidas | cierra_con_tu_decides | pedidos_prohibidos_rechazados | latencia_media_s | latencia_p95_s | llamadas_llm_por_respuesta | por_plantilla |
|---|---|---|---|---|---|---|---|---|---|---|
| agente_unico | 45.000 | 0.978 | 1.000 | 1.000 | 1.000 | 1.000 | 1.292 | 3.558 | 0.000 | 1.000 |
| multiagente | 45.000 | 0.978 | 1.000 | 1.000 | 1.000 | 1.000 | 1.271 | 3.496 | 0.000 | 1.000 |


Fallos de ruteo (agente unico): [['Explícame cómo funciona el crédito', 'educacion', 'ofertas']]

**Agente con Gemini con juez LLM (subconjunto)**

|  | n | ruteo_correcto | respuestas_sin_cifras_inventadas | sin_frases_prohibidas | cierra_con_tu_decides | pedidos_prohibidos_rechazados | latencia_media_s | latencia_p95_s | llamadas_llm_por_respuesta | por_plantilla |
|---|---|---|---|---|---|---|---|---|---|---|
| agente_unico | 10.000 | 0.900 | 1.000 | 1.000 | 1.000 | 0.000 | 12.082 | 38.291 | 1.100 | 0.100 |
| multiagente | 10.000 | 0.900 | 1.000 | 1.000 | 1.000 | 0.000 | 8.252 | 12.338 | 1.200 | 0.100 |


Fallos de ruteo (agente unico): [['Explícame cómo funciona el crédito', 'educacion', 'ofertas']]


## 7. Escalabilidad y valor
**Escalabilidad medida** (esta laptop, 500 clientes): {"clientes": 500, "carga_modelos_y_datos_s": 4.1, "contexto_por_cliente_ms": 3.32, "recomendaciones_por_cliente_ms": 0.43, "recomendaciones_por_segundo": 2319.0, "pico_memoria_gb": 0.81, "pronostico_30d_filas": 500, "pronostico_30d_ms_por_cliente": 0.084}

**Valor para la entidad** (escenario conservador, supuestos visibles): por cliente, colchon adicional S/ 322, 0.24 dias en rojo evitados al mes. Con 100,000 usuarios: margen por fondeo S/ 965,094, costo de puntos S/ 1,440,000, neto S/ -474,906 al anio. solo cuenta el fondeo de lo apartado; retencion, mora evitada y venta cruzada idonea no se valoran sin piloto.

Supuestos: {"margen_anual_sobre_saldo_apartado": 0.03, "usuarios_activos_escenario_conservador": 100000, "puntos_promedio_por_usuario_al_mes": 120, "aceptacion_de_la_recomendacion": "ya incluida: el impacto se simulo con la probabilidad de aceptacion de cada cliente", "retencion_y_mora": "no se asigna valor: no hay evidencia publica causal; lo mediria un piloto con grupo de control"}

