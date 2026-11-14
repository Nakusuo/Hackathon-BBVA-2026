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
| 6 | Impacto en el usuario | Menos días en rojo y más colchón que «no hacer nada» y que «apartar 10 % fijo», en S/ con intervalo |
| 7 | Costo | Demo a S/ 0; se reporta el % de respuestas del chat por plantilla |

## Impacto y negocio (D16, simulado)

Se calculan repitiendo las decisiones de Lucas (tomadas con datos hasta el mes 9) sobre las transacciones reales de los meses 10 a 12 de la población sintética, con adherencia 100 % y simulada; nunca con el pronóstico que eligió las acciones. Son **simulación**, no resultados de clientes reales. Detalle en [../reglas/rentabilidad-impacto.md](../reglas/rentabilidad-impacto.md).

| Métrica | Lucas | Baseline | Unidad |
|---|---|---|---|
| Días en rojo evitados | Sigue las recomendaciones | No hacer nada / 10 % fijo | días por cliente al mes |
| Colchón a 3 meses | Sueldo Lucas y metas | 10 % fijo | S/ por cliente |
| Intereses evitados | Hueco cubierto con colchón en vez de deuda | Hueco cubierto con deuda a TCEA supuesta | S/ por cliente al mes |
| Sube de cuadrante | Metas y avisos | No hacer nada | % de clientes en 6 meses |
| S/ apartados (entrada de la calculadora del banco) | Metas y Sueldo Lucas | 10 % fijo | S/ por cliente al mes |
| Respuestas por plantilla | Chat | — | % de respuestas sin llamar al LLM |

Cada supuesto (TCEA, márgenes del banco) va en `config/supuestos.yaml` y se muestra junto al resultado.

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
| Matriz ahorro × gasto | Perfil derivado de K-Prototypes | Umbrales fijos | Estabilidad mes a mes, acuerdo con etiquetas sembradas |
| Metas de ahorro | Aporte quincenal con banda del pronóstico | 10 % fijo | Probabilidad de cumplir a fin de año, días en rojo |
| Ofertas por cuadrante | Necesidad + cuadrante + idoneidad | Lo más popular para todos | Precision@3 sobre necesidades sembradas, 0 violaciones de idoneidad |
| Memoria y aprendizaje | Pesos que se ajustan con «útil / no me sirve» | Recomendador sin memoria | Tasa simulada de aceptación |
| RAG por módulos | Búsqueda filtrada por módulo | Búsqueda en todos los documentos | % de citas válidas, exactitud en preguntas fijas |
| Datos sin sesgo | Generación estratificada + bootstrap | Generación libre | Proporción por estrato, ningún estrato vacío |

Todas las métricas se reportan con **intervalo de confianza por bootstrap por cliente**.

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

## Métricas de pruebas (ISTQB)

| Métrica | Meta para entregar |
|---|---|
| Casos críticos que pasan | 100 % |
| Casos altos que pasan | ≥ 90 % |
| Defectos críticos o altos abiertos | 0 |
| Requisitos DEBE con al menos un caso | 100 % |
| Cobertura de código en `src/models` y `src/recommender` | ≥ 70 % |
| Vulnerabilidades altas en dependencias (`pip-audit`) | 0 |

Resultados por ciclo en `.claude/planes/pruebas.md`.
