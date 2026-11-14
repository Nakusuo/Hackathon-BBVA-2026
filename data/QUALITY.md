# Calidad de los datos sinteticos

Generado por `src/generador/reporte.py` a partir de las tablas de `generado`. Todos los numeros salen de los datos; la configuracion esta en `data/parametros/`.

## 1. Trazabilidad
| Dato | Valor |
|---|---|
| Semilla | 2026 |
| Clientes | 500 |
| Ventana | 2019-01-01 a 2025-12-31 |
| Movimientos | 3,264,148 (incluye duplicados sembrados) |
| Mensajes | 44,924 |
| Tiempo de generacion | 39.9 s, lotes de 50 clientes |
| Python, numpy, pandas | 3.13.2, 2.5.4, 3.1.1 |
| Huella de parametros | `{'generador.yaml': 'f532ab0d7d20e4f4', 'eventos.yaml': '90b8415d9f9d66fa'}` |
| Perfiles semilla | parametrica |

Misma semilla y mismos parametros dan las mismas tablas (lo comprueba `tests/test_generador.py`).

## 2. Sesgo de muestreo: estratos y pesos
Cada cliente pertenece a un estrato arquetipo x perfil de ahorro x perfil de gasto. Ningun estrato baja del piso configurado (2%) y el peso muestral restituye la proporcion objetivo, de modo que se puede sobremuestrear un estrato pequeno sin que sesgue las metricas ponderadas.

|  | n | peso | participacion_muestra | participacion_objetivo |
|---|---|---|---|---|
| ('base_comision', 'ahorra', 'gasta_mucho') | 12.000 | 0.984 | 0.024 | 0.024 |
| ('base_comision', 'ahorra', 'gasta_poco') | 14.000 | 1.031 | 0.028 | 0.029 |
| ('base_comision', 'no_ahorra', 'gasta_mucho') | 22.000 | 0.997 | 0.044 | 0.044 |
| ('base_comision', 'no_ahorra', 'gasta_poco') | 27.000 | 0.993 | 0.054 | 0.054 |
| ('formal_quincena', 'ahorra', 'gasta_mucho') | 23.000 | 1.027 | 0.046 | 0.047 |
| ('formal_quincena', 'ahorra', 'gasta_poco') | 44.000 | 0.997 | 0.088 | 0.088 |
| ('formal_quincena', 'no_ahorra', 'gasta_mucho') | 29.000 | 0.996 | 0.058 | 0.058 |
| ('formal_quincena', 'no_ahorra', 'gasta_poco') | 54.000 | 0.993 | 0.108 | 0.107 |
| ('independiente', 'ahorra', 'gasta_mucho') | 20.000 | 1.000 | 0.040 | 0.040 |
| ('independiente', 'ahorra', 'gasta_poco') | 30.000 | 1.000 | 0.060 | 0.060 |
| ('independiente', 'no_ahorra', 'gasta_mucho') | 60.000 | 1.000 | 0.120 | 0.120 |
| ('independiente', 'no_ahorra', 'gasta_poco') | 90.000 | 1.000 | 0.180 | 0.180 |
| ('mixto', 'ahorra', 'gasta_mucho') | 10.000 | 0.900 | 0.020 | 0.018 |
| ('mixto', 'ahorra', 'gasta_poco') | 13.000 | 1.038 | 0.026 | 0.027 |
| ('mixto', 'no_ahorra', 'gasta_mucho') | 21.000 | 1.000 | 0.042 | 0.042 |
| ('mixto', 'no_ahorra', 'gasta_poco') | 31.000 | 1.016 | 0.062 | 0.063 |

Region (muestra frente a objetivo):

|  | muestra | objetivo |
|---|---|---|
| lima | 0.448 | 0.450 |
| norte | 0.182 | 0.180 |
| sur | 0.168 | 0.170 |
| centro | 0.122 | 0.120 |
| oriente | 0.080 | 0.080 |

Edad (muestra frente a objetivo):

|  | muestra | objetivo |
|---|---|---|
| 18-24 | 0.126 | 0.120 |
| 25-34 | 0.320 | 0.320 |
| 35-44 | 0.262 | 0.260 |
| 45-54 | 0.178 | 0.180 |
| 55+ | 0.114 | 0.120 |

## 3. Montos (S/)
| tipo | count | min | 1% | 50% | 99% | max |
|---|---|---|---|---|---|---|
| gasto | 2,611,898.0 | 0.0 | 0.6 | 10.4 | 485.0 | 18,079.7 |
| ingreso | 652,250.0 | 0.4 | 2.3 | 17.2 | 2,039.1 | 20,600.0 |

## 4. Calidad sembrada para probar el tratamiento
- Faltantes (fraccion de movimientos): glosa 1.99%, categoria 3.01%, saldo 1.50%, monto 0.20%.
- Duplicados y faltantes etiquetados en `etiquetas_calidad`: falta_categoria 97,758, falta_glosa 64,809, falta_saldo 48,770, duplicado_exacto 7,766, falta_monto 6,508, duplicado_cercano 5,164.
- Gastos atipicos: 0.205% de los movimientos. Salen del presupuesto del mes, de modo que el saldo no se desvia.
- Movimientos recurrentes: 9.6%. Clientes con una suscripcion duplicada: 36.

## 5. Contraste con una fuente oficial
Ingreso operativo mensual medio de 2025 por segmento (S/):

| seg | ingreso_2025 |
|---|---|
| base_comision | 2,409 |
| formal_quincena | 3,023 |
| independiente_diario | 1,405 |
| independiente_proyectos | 2,508 |
| mixto | 1,928 |

Ponderado por el peso muestral: **S/ 2,316**. Ancla INEI EPEN abr-2025 a mar-2026: S/ 1,925.9 nacional y S/ 2,093.7 urbano (cuadros 1.28 y 1.30). La poblacion objetivo es bancarizada y por eso queda algo por encima del promedio nacional.

## 6. Irregularidad y eventos
CV mensual del ingreso (sin los meses de gratificacion), mediana por segmento:

| segmento | cv |
|---|---|
| base_comision | 0.19 |
| formal_quincena | 0.07 |
| independiente_diario | 0.43 |
| independiente_proyectos | 0.73 |
| mixto | 0.57 |

Ingreso de abril de 2020 sobre el de febrero de 2020, por segmento:

| seg | abr/feb |
|---|---|
| base_comision | 0.66 |
| formal_quincena | 0.91 |
| independiente_diario | 0.39 |
| independiente_proyectos | 0.40 |
| mixto | 0.51 |

Dias con saldo negativo: por segmento

| seg | fraccion_de_dias |
|---|---|
| base_comision | 0.008 |
| formal_quincena | 0.006 |
| independiente_diario | 0.039 |
| independiente_proyectos | 0.091 |
| mixto | 0.063 |

y por anio

| fecha | fraccion_de_dias |
|---|---|
| 2019 | 0.025 |
| 2020 | 0.067 |
| 2021 | 0.055 |
| 2022 | 0.028 |
| 2023 | 0.032 |
| 2024 | 0.031 |
| 2025 | 0.025 |

Clientes con al menos un dia en rojo: 57%.

## 7. Texto
Reparto de sentimiento de los mensajes: neutro 38.0%, positivo 25.0%, preocupado 22.0%, negativo 15.0%. Fraccion con saldo en rojo ese dia: negativo 25.0%, neutro 0.0%, positivo 0.0%, preocupado 0.3%.

## 8. Controles automaticos
| Estado | Control |
|---|---|
| OK | Ningun estrato vacio |
| OK | Pesos muestrales entre 0,5 y 2 |
| OK | transaction_id unico salvo duplicados exactos etiquetados |
| OK | Montos en soles positivos donde existen |
| OK | Fechas dentro de la ventana |
| OK | Mas dias en rojo en independientes que en dependientes formales |
| OK | Efecto del confinamiento: el ingreso del independiente de comercio cae a menos de 0,7 del de feb-2020 |
| OK | Ingreso medio ponderado de 2025 dentro de +-35 % del ingreso urbano INEI |
| OK | Irregularidad: CV del ingreso por proyectos mayor que el del formal |
| OK | Saldo del ultimo movimiento coincide con el saldo diario (mediana de la diferencia < 1 sol) |
| OK | Sentimiento dentro de 5 puntos del reparto objetivo |
| OK | Faltantes dentro del 50 % relativo de lo configurado |
| OK | El mensaje negativo coincide con el saldo en rojo mas que el neutro |

## 9. Limites que hay que decir
- Los datos son sinteticos: un modelo puede descubrir lo que el generador sembro. Por eso cada modelo se evalua frente a un baseline y con pruebas de perturbacion.
- Las magnitudes de los eventos son supuestos del equipo, anclados en cifras publicas donde existen (estado `parcial` o `supuesto` en `data/parametros/eventos.yaml`).
- Los arquetipos, las regiones y las edades tienen pesos del equipo, no de una encuesta. Con microdatos de la ENAHO se pasa una tabla semilla y se regenera.
- El efectivo no observado esta modelado (fraccion por segmento) pero no hay datos reales para calibrarlo.
- Los atributos internos del simulador (`ingreso_base`, `gasto_ratio`, `fraccion_efectivo` y otros) no son observables: `src/models/columnas.py` define que puede ver un modelo.
