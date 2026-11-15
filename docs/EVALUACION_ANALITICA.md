# Evaluacion analitica

Generado por `analitica/eval/generar_docs.py` desde `models/metricas*.json`. Datos sinteticos con semilla fija; las magnitudes de los eventos son supuestos del equipo (ver `data/parametros/eventos.yaml`).

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

### Serie diaria: los 30 dias con banda al 80 % (lo que pide el contrato de la API)

Se entrenan los mismos cuantiles (10, 50 y 90) en los horizontes [5, 10, 15, 20, 25, 30] dias, se interpola entre ellos y la banda se **recalibra dia por dia** con datos de calibracion que el modelo no uso para entrenar (conformal por dia). El dia 0 es el saldo de hoy (sin incertidumbre) y el dia 30 es exactamente el pronostico validado: el esperado es identico, y la banda solo se ensancha donde los cuantiles se cruzaban (0.16% de los casos), nunca se estrecha. Validacion con el mismo corte temporal con embargo (prueba 2024 a 2025, 50,000 origenes que el modelo no vio).

| Metodo | Cobertura media | Minima | Maxima | Error medio / ingreso | Ancho relativo |
|---|---|---|---|---|---|
| serie diaria (elegida) | 0.815 | 0.791 | 0.860 | 0.286 | 0.86 |
| recta al dia 30 (baseline) | 0.685 | 0.616 | 0.806 | 0.334 | 0.89 |
| promedio movil de 3 meses (baseline) | 0.759 | 0.722 | 0.857 | 0.440 | 1.06 |

Los dias entre horizontes no se entrenan, se interpolan, y aun asi se miden: cobertura 0.817 en los dias intermedios y 0.808 en los entrenados.

Cobertura por tipo de trabajo (equidad):

| Tipo de trabajo | n | Dia 7 | Dia 15 | Dia 30 |
|---|---|---|---|---|
| independiente | 20,000 | 0.802 | 0.802 | 0.800 |
| dependiente | 15,000 | 0.794 | 0.842 | 0.820 |
| mixto | 7,500 | 0.803 | 0.780 | 0.779 |
| dependiente_con_comision | 7,500 | 0.823 | 0.837 | 0.823 |

Se sirve con `backend/src/agente_analitico/contrato.py` (`pronostico_contrato(repo, customer_id, dias=30)`), con la forma del endpoint `GET /api/v1/customers/{customer_id}/forecast`: `customer_id`, `currency`, `horizon_days`, `confidence_level` (0.8), `forecast[]` (`date`, `predicted_balance`, `lower_bound`, `upper_bound`), `first_risk_date`, `model`, `data_as_of`, `risk_probability` y `synthetic_data`. `first_risk_date` solo aparece si la probabilidad de quedar en rojo es de al menos 15 %.

### Prueba con otra muestra del generador (semilla 2027, sin reentrenar)

Los modelos se entrenaron con la semilla 2026. Se generaron 500 clientes nuevos con otra semilla (mismos parametros, otro azar) y se evaluaron **sin reentrenar** en la ventana 2024 a 2025 (50,000 origenes). Mide si el pronostico solo aprendio el ruido de una muestra: no demuestra nada sobre datos reales, porque la muestra nueva comparte los supuestos del generador.

| Medida | Muestra de entrenamiento | Muestra nueva |
|---|---|---|
| Cobertura de la banda al 80 % a 30 dias | 0.806 | 0.772 |
| Error a 30 dias / ingreso mensual | 0.426 | 0.417 (promedio movil 0.707, perfil estructural 0.749) |
| PR-AUC del rojo a 30 dias | 0.594 | 0.870 (tasa de positivos 0.086) |
| Serie diaria: cobertura por dia | 0.791 a 0.860 | 0.750 a 0.806 |
| Segmentacion: ARI con los arquetipos | 0.253 | 0.268 |

Lectura: gana a los dos baselines tambien en una muestra nueva; la cobertura baja unos tres puntos (la calibracion conformal se hizo con la muestra de entrenamiento), sigue cerca del 80 %. El PR-AUC del rojo no es comparable punto a punto porque cambia la tasa de positivos de una muestra a otra.

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


Aviso: sobre plantillas el modelo es trivial. Con las 24 frases escritas a mano el lexico parecia mejor (0.92), pero las escribio quien armo el lexico: no era una prueba independiente. **Set independiente**: 140 frases de trabajadores peruanos que Gemini escribio sin ver el lexico ni las plantillas, mas una segunda pasada ciega que las etiqueto sin ver la clase pedida (coincidencia 100%; guardadas en `data/evaluacion/sentimiento_independiente.json` con su procedencia). F1 macro: TF-IDF + regresion logistica 0.47 (IC95 0.38 a 0.54), lexico 0.31 (0.23 a 0.38), clase mas frecuente 0.25. Conclusion: el modelo entrenado generaliza mejor que el lexico, y el lexico estaba inflado. Ambos son debiles y el sentimiento no esta en produccion (el texto no mejora el pronostico). Limite: el set lo escribio un modelo de lenguaje, no personas.

## 5. Impacto en soles (reproduccion contrafactual)
Periodo 24 meses (2024-2025), ponderado por la poblacion objetivo. Supuestos: {"tasa_mensual_por_cubrir_el_hueco": 0.1, "fraccion_apartada_10_fijo": 0.1, "recorte_hormiga": 0.2, "recorte_hormiga_en_alerta": 0.5, "dias_de_alerta": 14, "umbral_alerta_p_rojo": 0.25, "asignacion_sueldo_lucas": 0.95, "umbral_irregular_cv": 0.4, "dias_de_gasto_que_deben_quedar_en_caja_para_apartar": 7, "fraccion_del_excedente_que_se_aparta": 0.5}

|  | dias_en_rojo_por_cliente_mes | colchon_final_soles | colchon_final_meses_de_ingreso | costo_de_cubrir_el_hueco_soles_por_mes |
|---|---|---|---|---|
| nada | 0.837 | 4,263.586 | 1.867 | 1.486 |
| diez_fijo | 13.365 | 6,188.377 | 2.909 | 78.816 |
| diez_fijo_ajustado | 0.837 | 10,411.295 | 4.757 | 1.486 |
| lucas | 0.594 | 4,585.284 | 2.017 | 1.095 |
| lucas_mas_ahorro_ajustado | 0.594 | 10,732.993 | 4.908 | 1.095 |
| lucas_ahorro_guiado | 6.241 | 5,095.895 | 2.343 | 30.586 |


Politicas comparadas: **nada** (no hacer nada); **10 % fijo** (aparta el 10 % de cada ingreso sin recortar el gasto); **10 % fijo ajustado** (aparta y el gasto baja en lo mismo, sin costo y con adopcion total: un techo ideal); **Lucas** (alerta del pronostico, Sueldo Lucas, suscripcion duplicada y gasto hormiga, con la probabilidad de aceptacion de cada cliente); **Lucas + ahorro automatico** (Lucas mas el apartado del 10 % con el mismo supuesto ideal que el ajustado, para comparar de igual a igual); **Lucas + ahorro guiado** (prueba de estres: aparta la mitad del excedente estructural de 90 dias, solo sin alerta y con 7 dias de gasto en caja, sin recortar el gasto y bloqueado). Las politicas de Lucas usan los mismos sorteos de aceptacion para que la diferencia sea solo el ahorro.

**lucas_vs_nada**: dias_rojo_evitados_por_cliente_mes 0.243 (IC95 0.185 a 0.302); colchon_adicional_soles 321.698 (IC95 290.385 a 357.081); intereses_evitados_soles_por_mes 0.391 (IC95 0.291 a 0.515)

**lucas_vs_diez_fijo_ajustado**: dias_rojo_evitados_por_cliente_mes 0.243 (IC95 0.184 a 0.307); colchon_adicional_soles -5826.011 (IC95 -6097.460 a -5545.073); intereses_evitados_soles_por_mes 0.391 (IC95 0.298 a 0.510)

**diez_fijo_ajustado_vs_nada**: dias_rojo_evitados_por_cliente_mes 0.000 (IC95 0.000 a 0.000); colchon_adicional_soles 6147.709 (IC95 5859.640 a 6426.616); intereses_evitados_soles_por_mes 0.000 (IC95 0.000 a 0.000)

**diez_fijo_vs_nada**: dias_rojo_evitados_por_cliente_mes -12.528 (IC95 -12.884 a -12.178); colchon_adicional_soles 1924.791 (IC95 1767.995 a 2077.026); intereses_evitados_soles_por_mes -77.330 (IC95 -82.469 a -72.192)

**lucas_mas_ahorro_ajustado_vs_diez_fijo_ajustado**: dias_rojo_evitados_por_cliente_mes 0.243 (IC95 0.184 a 0.295); colchon_adicional_soles 321.698 (IC95 291.003 a 356.111); intereses_evitados_soles_por_mes 0.391 (IC95 0.295 a 0.504)

**lucas_mas_ahorro_ajustado_vs_nada**: dias_rojo_evitados_por_cliente_mes 0.243 (IC95 0.191 a 0.303); colchon_adicional_soles 6469.407 (IC95 6167.888 a 6791.521); intereses_evitados_soles_por_mes 0.391 (IC95 0.290 a 0.490)

**lucas_ahorro_guiado_vs_nada**: dias_rojo_evitados_por_cliente_mes -5.404 (IC95 -5.803 a -4.955); colchon_adicional_soles 832.309 (IC95 734.474 a 951.439); intereses_evitados_soles_por_mes -29.100 (IC95 -32.984 a -25.716)

**Lectura.** Lucas evita dias en rojo (0.59 frente a 0.84 al mes) pero no obliga a apartar, por eso forma 2.0 meses de colchon frente a 4.8 del 10 % ajustado. Esa ventaja del ajustado depende de un supuesto ideal (recortar el gasto sin costo, con adopcion total): sin el, apartar dinero bloqueado deja 13.4 dias en rojo al mes (10 % fijo) y 6.2 (ahorro guiado por el excedente). **Decision de diseno:** Lucas no bloquea ahorro; usa una reserva que se puede usar (Sueldo Lucas) y metas voluntarias. Y la politica recomendada, Lucas + ahorro automatico, forma 4.9 meses de colchon con 0.59 dias en rojo: gana en las dos cosas al 10 % ajustado con el mismo supuesto.

Por segmento:

|  | dias_rojo_nada | dias_rojo_lucas | colchon_nada | colchon_lucas |
|---|---|---|---|---|
| base_comision | 0.27 | 0.16 | 5,013.12 | 5,347.71 |
| formal_quincena | 0.30 | 0.16 | 6,656.59 | 7,029.45 |
| independiente_diario | 0.78 | 0.54 | 2,365.98 | 2,523.74 |
| independiente_proyectos | 1.88 | 1.53 | 3,229.73 | 3,616.60 |
| mixto | 1.33 | 0.86 | 2,763.35 | 3,135.12 |



## 6. RAG y agente
**Recuperacion** (34 preguntas con respuesta escritas a mano, 6 de ellas compuestas; k=4; las columnas separan simples y compuestas):

|  | recall@4 | mrr | documentos_distintos_en_top | n | recall@4_simples | recall@4_compuestas | n_compuestas |
|---|---|---|---|---|---|---|---|
| denso | 0.794 | 0.725 | 2.118 | 34.000 | 0.750 | 1.000 | 6.000 |
| denso + filtro de modulo | 0.941 | 0.831 | 1.971 | 34.000 | 0.929 | 1.000 | 6.000 |
| bm25 | 0.824 | 0.789 | 2.382 | 34.000 | 0.821 | 0.833 | 6.000 |
| bm25 + filtro de modulo | 0.882 | 0.860 | 1.971 | 34.000 | 0.857 | 1.000 | 6.000 |
| hibrido | 0.882 | 0.804 | 2.265 | 34.000 | 0.857 | 1.000 | 6.000 |
| hibrido + filtro de modulo | 0.941 | 0.892 | 2.059 | 34.000 | 0.929 | 1.000 | 6.000 |
| hibrido + multiconsulta | 0.853 | 0.789 | 2.235 | 34.000 | 0.857 | 0.833 | 6.000 |
| hibrido + multiconsulta + filtro de modulo | 0.941 | 0.892 | 2.088 | 34.000 | 0.929 | 1.000 | 6.000 |
| hibrido + multiconsulta + MMR | 0.853 | 0.787 | 2.176 | 34.000 | 0.857 | 0.833 | 6.000 |
| hibrido + multiconsulta + MMR + filtro de modulo | 0.941 | 0.892 | 2.029 | 34.000 | 0.929 | 1.000 | 6.000 |


**Filtro de relevancia tipo CRAG** (umbral 0.70 en uso, 34 preguntas con respuesta y 11 fuera del indice): acepta 33 de 34 y rechaza 10 de 11; AUC 0.979; el umbral optimo medido es 0.706. Se calibra con las mismas preguntas con las que se reporta: la cifra es optimista. Las siglas del dominio (TCEA, CTS, EPS...) se expanden antes de buscar; esa tecnica se motivo por un fallo de esta misma evaluacion, asi que ese caso no es prueba independiente. Partir las preguntas compuestas y MMR no mejoraron nada medible y quedan apagados; con 34 preguntas, una sola mueve el recall 0.029.

**Agente con plantillas (determinista, sin LLM, reproducible y sin costo)**. La politica de ahorro de tokens usa el LLM solo para lo que una plantilla no cubre bien; esta evaluacion mide el piso determinista: ruteo, cifras, salvaguardas.

|  | n | ruteo_correcto | respuestas_sin_cifras_inventadas | sin_frases_prohibidas | cierra_con_tu_decides | pedidos_prohibidos_rechazados | latencia_media_s | latencia_p95_s | llamadas_llm_por_respuesta | por_plantilla |
|---|---|---|---|---|---|---|---|---|---|---|
| agente_unico | 69.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.869 | 2.850 | 0.000 | 1.000 |
| multiagente | 69.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.310 | 1.022 | 0.000 | 1.000 |


Fallos de ruteo (agente unico): ninguno

**Agente con Gemini real (una sola corrida de QA, `LLM_USO=siempre`, reloj fijo 2026-11-14)**: preguntas de perfil 11/11, pedidos adversarios 16/16, datos vivos y vigilancia OK, traduccion ingles OK, quechua OK; 51 llamadas y 140,543 tokens de entrada con `gemini-3.5-flash-lite`; latencia media por respuesta 3.7 s. Detalle de cada respuesta en `models/metricas_qa_agente.json`. El juez LLM esta apagado (`JUEZ_LLM=0`): la verificacion de cifras es determinista.

**QA conversacional con Gemini real**: conversaciones de varias preguntas seguidas 14/14 (sin cortarse ni repetirse), preguntas-trampa con datos que no existen 9/9 (sin inventar ni prometer), mensajes de apertura («hola», «oye», «ayudame», contar como se siente) 25/25 y botones 8/8; los saludos no gastan tokens: si; mayor tiempo de respuesta 7 s; reintentos por cuota agotada del plan gratuito: 0. Diseno y detalle en el informe 9.10.


## 7. Escalabilidad y valor
**Escalabilidad medida** (esta laptop, 500 clientes): {"clientes": 500, "serie_diaria_30_dias_ms_por_cliente": 0.257, "carga_modelos_y_datos_s": 3.1, "contexto_por_cliente_ms": 1.35, "recomendaciones_por_cliente_ms": 0.12, "recomendaciones_por_segundo": 8004.0, "pico_memoria_gb": 0.82, "pronostico_30d_filas": 500, "pronostico_30d_ms_por_cliente": 0.056}

**Programa de puntos sostenible** (supuestos del equipo, visibles en `data/parametros/niveles.yaml`): cada usuario gana en promedio 181 puntos al mes y el programa cuesta S/ 15.17 por usuario al anio, es decir 6.2% del ingreso bruto que genera (tope de reinversion: 30%). Los puntos por consumo solo se activan para quien tiene la caja ordenada; ahorrar suma siempre y mas para los niveles bajos.

Por nivel (anual por usuario, lectura bruta):

|  | clientes | consumo_elegible_anual | puntos_por_mes | costo_de_puntos_anual | ingreso_anual | costo_sobre_ingreso | consumo_por_cada_sol_de_puntos |
|---|---|---|---|---|---|---|---|
| aprendiz | 13.00 | 4,197.80 | 82.65 | 6.94 | 136.31 | 0.05 | 423.27 |
| campeon | 228.00 | 9,415.68 | 254.52 | 21.38 | 335.47 | 0.06 | 308.29 |
| constructor | 153.00 | 5,045.42 | 110.19 | 9.26 | 151.55 | 0.06 | 381.55 |
| luchador | 58.00 | 7,177.83 | 48.00 | 4.03 | 98.35 | 0.04 | 1,246.22 |
| maestro | 48.00 | 12,289.43 | 239.12 | 20.09 | 323.17 | 0.06 | 428.28 |


`consumo_por_cada_sol_de_puntos` es cuanto consume el cliente por cada S/ 1 de puntos que canjea (la proporcion de gasto sobre puntos).

**Lectura bruta (techo, atribuye todo al programa)**: ingreso por usuario S/ 245 al anio, neto S/ 230.

**Lectura conservadora**: Lucas genera 322 soles mas de colchon por cliente, que dejan S/ 9.65 al anio de fondeo; el programa cuesta S/ 15.17, asi que sin mas consumo el neto es S/ -5.52 por usuario. Se paga solo si el consumo elegible crece al menos 6.9%. Sensibilidad (neto por usuario al anio):

|  | neto_por_usuario | neto_con_100_mil_usuarios |
|---|---|---|
| 0 % mas de consumo | -5.5 | -551,707.7 |
| 5 % mas de consumo | -1.5 | -153,720.3 |
| 10 % mas de consumo | 2.4 | 244,267.1 |
| 15 % mas de consumo | 6.4 | 642,254.5 |
| 20 % mas de consumo | 10.4 | 1,040,241.9 |


retencion, mora evitada y venta cruzada idonea no se valoran sin un piloto con grupo de control.

**Ingresos a futuro del programa de puntos (proyeccion a 5 anios, por usuario que entra).** Pregunta: si el programa no se paga el primer anio, ¿genera ingresos despues? Cada anio suma el fondeo medido del colchon de Lucas, el margen del consumo adicional con tarjeta o QR, el margen del ahorro adicional (el saldo apartado **se acumula**: saldo final = saldo inicial x (1 - retiro) + aporte del anio) y el valor de los usuarios que el programa retiene de mas, y resta el costo de los puntos. Supuestos generales del equipo: abandono anual base 20%, retiro anual de lo apartado 30%. **Los porcentajes de conducta son supuestos del equipo, sin evidencia publica ni piloto**: sirven para ver cuando se paga y que debe cumplirse, no para prometer un resultado.

| Escenario | Mas consumo | Mas ahorro | Menos abandono | Neto acumulado anio 1 (S/) | Neto acumulado anio 2 (S/) | Neto acumulado anio 3 (S/) | Neto acumulado anio 4 (S/) | Neto acumulado anio 5 (S/) | Se paga en el anio |
|---|---|---|---|---|---|---|---|---|---|
| Solo lo medido (sin efecto de conducta) | 0% | 0% | 0% | -5.5 | -9.9 | -13.5 | -16.3 | -18.5 | no se paga |
| Prudente | 2% | 5% | 5% | 4.4 | 24.6 | 54.9 | 90.4 | 127.6 | 1 |
| Base | 5% | 10% | 10% | 15.0 | 61.1 | 126.9 | 203.2 | 283.1 | 1 |
| Optimista | 10% | 20% | 20% | 35.6 | 134.0 | 274.3 | 438.3 | 611.8 | 1 |

El primer anio de «solo lo medido» es exactamente la lectura conservadora de arriba (S/ -5.52): la proyeccion arranca donde termina el calculo de un anio. Sin ningun efecto de conducta nunca se paga; para pagarse en el primer anio basta **3.3% mas de ahorro apartado** o 6.9% mas de consumo elegible. Lo que decide el piloto con grupo de control es si el programa de puntos causa ese comportamiento adicional.

## 8. Calendario laboral, datos vivos y vigilancia
Las reglas viven en `data/parametros/normas_laborales.yaml` y **cada una lleva su frase literal** de un documento oficial guardado en `docs/rag/`; `backend/tests/test_calendario.py` comprueba que la frase siga en el documento. Se contrastaron el 2026-11-14 y el agente avisa si pasaron mas de 120 dias.

| Regla | Que dice | Evidencia |
|---|---|---|
| Gratificacion | Se paga en la primera quincena de julio y diciembre (limite el 15); equivale a una remuneracion integra por semestre completo, proporcional por meses calendarios completos; bonificacion extraordinaria de 9% (EsSalud) o 6.75% (EPS), no remunerativa ni pensionable | `laboral/ley_30334_bonificacion_extraordinaria.pdf`, `laboral/mtpe_guia_gratificaciones.pdf` |
| Deposito de CTS | Hasta el 15 de mayo y el 15 de noviembre; si el 15 es inhabil, el siguiente dia habil. Dozavos de la remuneracion computable (que suma un sexto de la gratificacion del semestre) por meses completos; la fraccion, por treintavos | `laboral/tuo_cts_ds_001_97_tr.pdf` |
| Retiro de la CTS | Hasta el 2026-12-31 se puede disponer libremente del 100% de lo depositado en entidades financieras; despues rige el tope permanente de 50% (100 % por enfermedad terminal o cancer). Hay un proyecto de ley en el Congreso para ampliar ese plazo; se esta evaluando y todavia no es ley: por ahora solo rige lo que dice la Ley 32322. | `laboral/ley_32322_cts_libre_disposicion.txt` |
| A quien aplica | personas dependientes en planilla del regimen laboral general con jornada de cuatro horas o mas. No aplica a independientes. Supuesto del equipo: el agente asume regimen general y semestre completo trabajado; en regimenes especiales o con menos meses el monto cambia y el aviso lo dice | `laboral/tuo_cts_ds_001_97_tr.pdf` |

La base de los montos es la ultima gratificacion real del cliente (equivale a una remuneracion); si no la hay, su ingreso medio, marcado como supuesto y con confianza media. Todo monto es una estimacion y se dice asi.

**Datos vivos y vigilancia.** El aplicativo envia cada movimiento (`datos_vivos.registrar`): se valida (tipo, monto finito y positivo, fecha que no sea futura), es idempotente ante reintentos, la glosa solo sirve para sugerir la categoria con el clasificador (confianza minima 0.80; si no esta seguro queda en `otros`) y **no se guarda**. El agente suma lo que entro al saldo; el riesgo a 30 dias se reestima con el modelo solo si el cierre de datos no pasa de 45 dias. La vigilancia avisa una sola vez cada hecho y como maximo 3 por semana, de lo mas urgente a lo menos: riesgo de rojo, gratificacion que no llego (solo a quien ya recibio una y con informacion reciente), ingreso extraordinario (>= 50 % de un ingreso mensual), gasto atipico (>= 30% del ingreso y que no sea un pago recurrente), fechas del calendario laboral (a 7 dias o menos), fin cercano del retiro total de la CTS, baja de la tasa del BCRP (solo con el dato al dia) y comunicado nuevo del ENFEN. Los datos publicos dicen de que fecha son y de donde vienen (API, cache o serie grabada); uno desactualizado no se presenta como actual.

## 9. QA y comparativa de modelos
La puerta de calidad (`python analitica/eval/puerta_de_calidad.py --gemini`) reune pruebas, metricas de los modelos, conexiones en tiempo real, agente, seguridad y frescura, y reporta PASS, WARN (conocido y documentado), FAIL o NOT RUN con el motivo. El detalle completo, incluida la lista de **lo que no se pudo verificar**, esta en [QA_ANALITICA.md](QA_ANALITICA.md).

Ultima corrida (2026-11-14T23:27:27): **52 PASS, 3 WARN, 0 FAIL, 3 NOT RUN**.

| # | Estado | Que | Detalle |
|---|---|---|---|
| P1b | NOT RUN | Pruebas del agente del producto (PR #5, Jeffrey): no estan en esta rama; se corren en la rama develop al integrar todo (proximo paso) | no hay pruebas del agente del producto en esta rama |
| M6 | WARN | Equidad por segmento: brecha de cobertura <= 0.05 y razon de error entre segmentos | la cobertura es pareja (brecha 0.018) pero el error del peor segmento (0) es 1.58 veces el del mejor: el ingreso irregular es mas dificil de pronosticar. Documentado. |
| M12 | WARN | Programa de puntos: rentable sin depender de consumo nuevo | solo con lo medido pierde S/ 5.52 por usuario al anio y no se paga nunca; se paga con 6.9% mas de consumo o con 3.3% mas de ahorro apartado. Proyeccion a 5 anios (supuestos del equipo): se paga en el anio 1 (prudente), 1 (base) y 1 (optimista). Aceptado por el equipo: lo decide un piloto con grupo de control. |
| C9b | NOT RUN | Google Cloud Translation: llamada real con clave (proximo paso) | proximo paso: no hay GOOGLE_TRANSLATE_API_KEY propia (una clave de Gemini da 401 en esa API). El contrato esta probado con respuestas simuladas y se traduce con Gemini. |
| C10b | NOT RUN | Calidad del quechua revisada por un hablante nativo (proximo paso) | proximo paso: hay evidencia objetiva (FLORES-200) pero la revision de un hablante nativo queda para despues; el aviso al usuario lo dice |
| S5 | OK | Sin archivos pesados ni datos generados en el repositorio (solo data/sample) | data/generado/ esta en .gitignore y se regenera con python data/generator.py --semilla 2026 |

La comparativa de modelos (candidatos medidos, el elegido y por que, con su limite) esta en [comparativa_modelos.md](comparativa_modelos.md) y sus graficas en `docs/presentacion/`.

## 10. Idiomas: quechua y Google Cloud Translation
Que idioma entiende el agente y que tan bien lo hace, con la evidencia objetiva que se pudo reunir sin un hablante nativo y sin clave de Google Cloud.

### Quechua frente a un benchmark publico (FLORES-200, quechua de Ayacucho)

Fuente: FLORES-200 devtest, par spa_Latn / quy_Latn (quechua de Ayacucho); Meta AI, NLLB Team; CC BY-SA 4.0. Se tomaron 60 oraciones al azar (semilla 20261114) y se tradujeron con el mismo flujo del agente (cifras y nombres protegidos, Gemini). Metrica: chrF (a nivel de caracteres, apropiada para lenguas con mucha morfologia) con IC95 por remuestreo de oraciones, frente a un piso: copiar el texto de origen sin traducir.

| Direccion | chrF | IC95 | chrF++ | Piso (copiar el origen) | Oraciones que cayeron al texto original | Devueltas sin traducir |
|---|---|---|---|---|---|---|
| espanol a quechua | 34.2 | 31.6 a 36.3 | 28.6 | 18.5 | 0 de 60 | 0 |
| quechua a espanol | 33.4 | 30.9 a 35.9 | 31.3 | 17.7 | 1 de 60 | 1 |

Un chrF por encima del piso de copiar el origen muestra que la salida se parece a una traduccion humana mas que el propio texto sin traducir; no demuestra que un hablante la entienda. Las referencias de FLORES estan en la ortografia del quechua de Ayacucho: diferencias de escritura (por ejemplo entre variedades) bajan el chrF aunque la traduccion sea correcta. **Limite:** No hay hablante nativo que la revise. FLORES es texto de noticias y enciclopedia: no es el lenguaje de las finanzas personales. Quechua sureno (Cusco-Collao y Ayacucho-Chanka); el agente lo declara como no validado.

### Google Cloud Translation (proveedor opcional)

No hay clave propia y la de Gemini no se usa contra otras APIs de Google. Lo que si se verifico: (1) el pedido y la respuesta del proveedor contra la documentacion oficial de la API v2 (`POST https://translation.googleapis.com/language/translate/v2`, cuerpo `q`, `source`, `target`, `format`, respuesta `data.translations[].translatedText`; el quechua `qu` esta en la lista de idiomas; la clave puede ir en la cabecera `X-goog-api-key` y la documentacion desaconseja ponerla en la URL); (2) siete pruebas con respuestas simuladas en `backend/tests/test_traduccion.py` (forma del pedido, clave solo en cabecera, sin clave no hay pedido, marcadores espaciados por Google, marcador perdido se descarta, errores 429 y 5xx se reintentan y 403 y 400 no, respuesta mal formada, caida a Gemini). **No se probo** una llamada real: cuando haya una clave, basta definir `GOOGLE_TRANSLATE_API_KEY` y correr la puerta de calidad.


## 11. Modulos de reglas
Ofertas (`backend/src/models/ofertas.py`), recomendador (`recomendador.py`), programa de puntos (`programa_puntos.py`), riesgo por clima (`riesgo_clima.py`), campanas (`campanas.py`) y calendario laboral (`calendario_laboral.py`) son reglas o catalogos, no modelos entrenados: no tienen baseline porque no hay nada que aprender. Se comprueban con pruebas de reglas en `backend/tests`: `test_modelos.py` (recomendador, idoneidad del credito, puntos y su tope, aviso de El Nino), `api/test_offers.py` (ofertas) y `test_calendario.py` (calendario laboral, con la frase literal de la norma). `campanas.py` no tiene prueba propia hoy.

<!-- huella_metricas: 89259a180d49264b (la puerta de calidad compara esta huella con la de las metricas actuales) -->
