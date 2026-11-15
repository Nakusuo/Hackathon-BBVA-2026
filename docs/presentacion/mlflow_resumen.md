# Seguimiento de modelos con MLflow

Generado por `analitica/eval/registrar_en_mlflow.py` (huella de las metricas `89259a180d49264b`). Experimento **lucas-analitica**; base local `data/generado/mlflow/lucas.db` (no se versiona) o el servidor definido en `MLFLOW_TRACKING_URI`. Abrir la interfaz: `mlflow ui --backend-store-uri sqlite:///data/generado/mlflow/lucas.db`.

## Comparacion por problema: baseline frente al elegido

Cada fila es una corrida de MLflow con la misma metrica y los mismos numeros de `docs/comparativa_modelos.md`; en la interfaz se pueden comparar las corridas de un mismo problema.

| Problema | Metrica | Elegido | Valor del elegido | Baselines y alternativas |
|---|---|---|---|---|
| Segmentación de clientes | Silueta de Gower (mayor es mejor) | **K-Prototypes** | 0.205 | Reglas 2×2: 0.058; K-means (one-hot): 0.204 |
| Pronóstico del saldo a 30 días | Error medio / ingreso mensual (menor es mejor) | **LightGBM + bandas conformales** | 0.426 | Perfil estructural: 0.769; Promedio móvil de 3 meses: 0.721 |
| Alerta de saldo en rojo a 30 días | PR-AUC (evento raro) (mayor es mejor) | **LightGBM calibrado** | 0.594 | Perfil estructural: 0.266; Regla de saldo bajo: 0.581 |
| Día en que el saldo cae a rojo | Error medio en días (menor es mejor) | **LightGBM** | 5.4 | Tendencia lineal: 12.5; Perfil estructural: 7.84 |
| Proyección mensual de ingresos (1 a 6 meses) | Error medio / ingreso mensual (promedio de los 6 horizontes) (menor es mejor) | **LightGBM, recalibración continua** | 0.403 | Promedio de 3 meses: 0.557; Mismo mes del año previo: 0.567; LightGBM, calibración fija: 0.403 |
| Proyección mensual: cobertura de la banda al 80 % | Cobertura de ingresos (objetivo 0.80) (objetivo es mejor) | **LightGBM, recalibración continua** | 0.794 | Promedio de 3 meses: 0.745; Mismo mes del año previo: 0.816; LightGBM, calibración fija: 0.731 |
| Categoría de cada movimiento (glosa) | F1 macro (mayor es mejor) | **TF-IDF por caracteres + SGD lineal** | 0.894 | Diccionario de palabras: 0.864 |
| Gastos fijos y suscripciones | F1 (mayor es mejor) | **Periodicidad + estabilidad del monto** | 0.933 | «Mismo comercio 3 veces»: 0.169 |
| Movimientos atípicos | Precisión en los k más sospechosos (mayor es mejor) | **Isolation Forest** | 0.75 | Z-score robusto: 0.688 |
| Sentimiento de los mensajes | F1 macro en frases de un set independiente (mayor es mejor) | **TF-IDF + regresión logística** | 0.469 | Clase más frecuente (azar): 0.25; Léxico de palabras: 0.309 |
| Política de ahorro (reproducción contrafactual) | Días en rojo por cliente al mes (menor es mejor) | **Lucas + ahorro automático** | 0.594 | Apartar 10 % fijo, ajustado: 0.837; No hacer nada: 0.837; Lucas solo (alerta + Sueldo Lucas): 0.594 |
| Arquitectura del agente | Ruteo correcto (mayor es mejor) | **Agente único** | 1 | Multiagente (supervisor): 1 |
| Recuperación de fuentes (RAG) | Recall@4 con filtro de módulo (mayor es mejor) | **Denso + filtro de módulo** | 0.941 | Híbrido + partidas + MMR: 0.941; Híbrido + preguntas partidas: 0.941; Solo palabras (BM25) + filtro: 0.882; Híbrido + filtro de módulo: 0.941 |
| Pronóstico día por día (30 días con banda al 80 %) | Error medio / ingreso mensual (promedio de los 30 días) (menor es mejor) | **LightGBM por horizontes + banda por día** | 0.286 | Promedio móvil de 3 meses: 0.44; Recta al día 30: 0.334 |

## Modelos de produccion registrados (Model Registry)

| Modelo | Familia | Version | Alias | Hash del archivo |
|---|---|---|---|---|
| `lucas-sentimiento` | TF-IDF + regresion logistica (no esta en produccion: el texto no mejora el pronostico) | v1 de 1 | produccion | `8ab3dd3802a2994a` |
| `lucas-glosa-a-categoria` | TF-IDF por caracteres + SGD lineal | v1 de 1 | produccion | `d22e6f3997ed139b` |
| `lucas-pronostico-mensual` | LightGBM con recalibracion continua por tipo de trabajo | v1 de 1 | produccion | `e6255da9c051e072` |
| `lucas-segmentacion` | K-Prototypes (variables numericas y categoricas) | v1 de 1 | produccion | `c4a07801fe47f068` |
| `lucas-serie-diaria` | LightGBM cuantil por horizontes + interpolacion + conformal por dia | v1 de 1 | produccion | `457eaf7926f214ae` |
| `lucas-pronostico-30d` | LightGBM cuantil + conformal por segmento + clasificador isotonico de rojo | v1 de 1 | produccion | `d381f1ff430e1244` |

## Como se usa

- **Versionar:** tras entrenar, correr `python analitica/eval/comparativa_modelos.py` y luego `python analitica/eval/registrar_en_mlflow.py`. Si el contenido de un modelo cambio, se crea una version nueva y el alias `produccion` pasa a ella; si no, no se duplica nada.
- **Cargar el modelo en produccion:** `MlflowClient().get_model_version_by_alias('lucas-pronostico-30d', 'produccion')` da el origen del archivo; se carga con `joblib.load`.
- **Servidor del equipo:** definir `MLFLOW_TRACKING_URI=http://servidor:5000` y volver a correr; las corridas y los modelos van al servidor central.
- **Alcance:** el entrenamiento no esta instrumentado con autologging (los modelos son clases propias de LightGBM con calibracion conformal); el registro se hace desde las metricas y los archivos guardados, con la version del codigo (`commit`), la huella de los parametros de los datos y la semilla. Todo con datos sinteticos.

<!-- huella_metricas: 89259a180d49264b -->
