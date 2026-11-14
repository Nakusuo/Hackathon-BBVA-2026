# Métricas y criterios de éxito

Regla: **cada técnica se compara con una alternativa sencilla**. Los resultados reales se registran abajo, en «Resultados», cuando `make eval` los produzca.

## Criterios de éxito del producto

| # | Criterio | Meta |
|---|---|---|
| 1 | Pronóstico de saldo a 30 días | MAE menor que el baseline (promedio móvil 3 meses) en test; bandas al 80 % cubren entre 75 % y 85 % |
| 2 | Groundedness del chat | 100 % de cifras rastreables a una tool |
| 3 | Tiempo hasta insight | < 60 s hasta el «día de riesgo» y una recomendación accionable |
| 4 | Recurrentes y duplicadas | F1 ≥ 0,85 sobre etiquetas sintéticas |
| 5 | Banda según tipo de ingreso | Más ancha para independientes que para dependientes, manteniendo cobertura |

## Técnica frente a baseline

| Módulo | Técnica | Baseline | Métrica |
|---|---|---|---|
| Recurrentes | Comercio + periodicidad (desviación de intervalos) + tolerancia de monto | «Mismo comercio ≥ 3 veces» | Precision, recall, F1 |
| Duplicadas | Recurrentes de igual categoría y cliente que se solapan | — | Precision |
| Pronóstico | Ingresos por calendario − fijos + variable (regresión/ETS); banda por bootstrap por bloques de residuos | Promedio móvil 3 meses | MAE, MAPE, cobertura |
| Salud financiera | Puntaje ponderado 0–100: colchón, deuda, fijo/ingreso, volatilidad, ahorro | — (transparente) | Monotonicidad en tests |
| Clasificación de gastos | Modelo/reglas | Diccionario de comercios | F1 por categoría |
| Perfiles (Debería) | K-Prototypes; k por codo, silueta y estabilidad | Reglas por umbral | Silueta, estabilidad, ARI contra arquetipo |
| Recomendador | Reglas → impacto × facilidad → perfil → seguridad | Top 3 fijo igual para todos | Ahorro simulado S/, % que evita día en rojo |
| Ahorro | Plan por quincena | Regla fija del 10 % | Probabilidad de cumplir la meta |
| Simulador | Reutiliza el pronóstico | Cálculo exacto en hoja de cálculo | Exactitud |
| Chat | 1 agente + tools | Plantillas | % cifras verificadas, exactitud en 20–30 preguntas fijas, tasa de bloqueo adversa |
| Atípicos (Podría) | Isolation Forest por cliente | z-score robusto | Precision, falsos positivos |
| F1 Avisos anticipados | Probabilidad de saldo < 0 según la banda del pronóstico | Alerta por saldo bajo un monto fijo | Precision, recall, días de anticipación |
| F2 Sueldo Lucas | Monto quincenal estable según banda baja del ingreso esperado | Apartar 10 % fijo / no hacer nada | Días en rojo simulados, colchón a 3 meses |
| A1 Lucas en 5 preguntas | Prior del perfil parecido + respuestas (arranque en frío) | Promedio de toda la población | MAE con 0, 1 y 3 meses de historia |
| F3 Plan grati/CTS | Reparto sugerido con impacto en el puntaje | Gasto como mes normal | Cambio del puntaje y de la deuda simulada |

## Particiones sin fuga

- Pronóstico: walk-forward temporal (entrena meses 1–9, valida 10, test 11–12).
- Recurrentes/atípicos: GroupKFold **por cliente**.
- Clusters: sin etiquetas; el arquetipo solo para ARI posterior.

## Honestidad con datos sintéticos

Los modelos pueden «descubrir» lo que sembramos. Por eso se reportan **pruebas con perturbaciones**: más ruido, otra semilla, cambio de patrón no visto en entrenamiento, faltantes extra. Se dice en README y pitch.

## Rendimiento

- Latencia: < 2 s por endpoint sin LLM; < 8 s con LLM local.
- `make test` en < 1 min.

## Resultados (rellenar con números reales de `make eval`)

| Fecha | Métrica | Baseline | Modelo | Nota |
|---|---|---|---|---|
| — | — | — | — | — |
