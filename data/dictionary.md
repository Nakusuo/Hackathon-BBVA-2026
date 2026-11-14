# Diccionario de datos

Tablas que produce `python data/generator.py`. Cada tabla es una carpeta o un archivo Parquet en `data/generado/` (o `data/sample/`). Un test (`tests/test_generador.py`) comprueba que las columnas de este documento coinciden con las reales.

**Columna Uso:** `observable` lo ve un modelo; `etiqueta` es verdad de referencia solo para evaluar; `interna` describe como se genero el dato y nunca entra a un modelo (`src/models/columnas.py`). **Clasificacion** (ISO 27001, control 5.12): todo es dato sintetico, nivel interno; en un banco real `clientes` seria sensible.

## clientes
Un cliente por fila. Contrato de datos del plan (seguro.clientes) mas los parametros del simulador.

| Columna | Tipo | Uso | Descripcion |
|---|---|---|---|
| `customer_id` | texto | observable | Identificador ficticio |
| `rango_edad` | texto | observable | 18-24, 25-34, 35-44, 45-54, 55+ |
| `region` | texto | observable | lima, norte, sur, centro, oriente |
| `tipo_trabajo` | texto | observable | dependiente, dependiente_con_comision, independiente, mixto |
| `frecuencia_ingreso` | texto | observable | quincenal, mensual_mas_comision, diaria, irregular, mensual_mas_extra |
| `personas_a_cargo` | entero | observable | 0 a 5 |
| `deuda_total` | decimal | observable | Saldo de deuda en S/ |
| `n_creditos` | entero | observable | Creditos vigentes |
| `cuota_mensual` | decimal | observable | Cuota mensual en S/ |
| `tcea_promedio` | decimal | observable | Costo efectivo anual de la deuda, fraccion |
| `colchon_meses` | decimal | observable | Meses de ingreso que el cliente tiene ahorrados |
| `antiguedad_cliente_meses` | entero | observable | Meses como cliente |
| `meta_ahorro` | decimal | observable | Monto objetivo en S/ (0 si no tiene) |
| `paga_en_usd` | booleano | observable | Tiene un pago fijo en dolares |
| `arquetipo` | texto | etiqueta | formal_quincena, base_comision, independiente, mixto |
| `segmento` | texto | etiqueta | Arquetipo con el subtipo del independiente (diario o proyectos) |
| `subtipo` | texto | etiqueta | diario o proyectos para independientes |
| `perfil_ahorro_real` | texto | etiqueta | ahorra o no_ahorra |
| `perfil_gasto_real` | texto | etiqueta | gasta_poco o gasta_mucho |
| `necesidad_oculta` | texto | etiqueta | pago_usd, deuda_cara, ingreso_irregular o ninguna |
| `prob_acepta_reco` | decimal | etiqueta | Probabilidad de aceptar una recomendacion (para simular respuestas) |
| `cambio_patron` | booleano | etiqueta | Tiene un cambio estructural de ingreso a mitad del periodo |
| `ingreso_base` | decimal | interna | Ingreso mensual verdadero a precios de 2025-12 |
| `gasto_ratio` | decimal | interna | Parte del ingreso que consume |
| `ahorro_tasa` | decimal | interna | Parte del ingreso que aparta |
| `fraccion_efectivo` | decimal | interna | Parte del ingreso y gasto que se mueve en efectivo y no pasa por la cuenta |
| `traspaso_inflacion` | decimal | interna | Parte de la inflacion que llega al ingreso |
| `planilla` | booleano | interna | Tiene sueldo fijo en planilla |
| `tiene_alquiler` | booleano | interna | Paga alquiler |
| `alquiler_share` | decimal | interna | Alquiler como fraccion del ingreso |
| `tiene_deuda` | booleano | interna | Tiene cuota de prestamo |
| `cuota_share` | decimal | interna | Cuota como fraccion del ingreso |
| `saldo_inicial` | decimal | interna | Saldo liquido al inicio del periodo |
| `ahorro_inicial` | decimal | interna | Ahorro apartado al inicio |
| `acceso_credito_informal` | booleano | interna | Puede pedir un prestamo informal para cubrir un hueco |
| `tasa_credito_informal` | decimal | interna | Interes mensual de ese prestamo |
| `pos_cambio_patron` | decimal | interna | Posicion del cambio dentro del periodo (0 a 1) |
| `factor_cambio_ingreso` | decimal | interna | Multiplicador del ingreso tras el cambio |
| `heterogeneidad_consumo` | decimal | interna | Escala individual de la frecuencia de compra |
| `peso_muestral` | decimal | interna | Peso que restituye la proporcion poblacional del estrato; se usa como `sample_weight` al evaluar |
| `lote` | entero | interna | Lote de generacion |

## transacciones
Un movimiento por fila, con el problema de calidad sembrado (faltantes, duplicados, atipicos).

| Columna | Tipo | Uso | Descripcion |
|---|---|---|---|
| `customer_id` | categoria | observable | Cliente |
| `transaction_id` | texto | observable | Identificador del movimiento. Un duplicado exacto repite el id; uno cercano lleva el sufijo D |
| `fecha_hora` | fecha y hora | observable | Momento del movimiento |
| `monto` | decimal | observable | Monto en la moneda del movimiento (positivo) |
| `moneda` | categoria | observable | PEN o USD |
| `monto_pen` | decimal | observable | Monto en soles |
| `tipo` | categoria | observable | ingreso o gasto |
| `categoria` | categoria | observable | Categoria del movimiento (puede faltar) |
| `comercio` | categoria | observable | Comercio o contraparte ficticia |
| `glosa` | texto | observable | Texto del movimiento, con ruido de escritura (puede faltar) |
| `canal` | categoria | observable | yape, plin, tarjeta_debito, tarjeta_credito, transferencia, debito_automatico, cajero, deposito_efectivo |
| `saldo` | decimal | observable | Saldo despues del movimiento (puede faltar) |
| `es_recurrente` | booleano | etiqueta | Compromiso que se repite cada mes |
| `es_atipico` | booleano | etiqueta | Gasto fuera de patron |
| `es_suscripcion_duplicada` | booleano | etiqueta | Segunda suscripcion igual a otra activa |

## saldo_diario
Un dia por cliente, calculado sobre los movimientos limpios (sin duplicados ni faltantes).

| Columna | Tipo | Uso | Descripcion |
|---|---|---|---|
| `customer_id` | categoria | observable | Cliente |
| `fecha` | fecha | observable | Dia |
| `ingresos` | decimal | observable | Suma de ingresos del dia en S/ |
| `gastos` | decimal | observable | Suma de gastos del dia en S/ |
| `saldo_cierre` | decimal | observable | Saldo al cierre del dia |
| `en_rojo` | booleano | etiqueta | Saldo de cierre negativo |

## mensajes
Texto libre del usuario sobre su plata.

| Columna | Tipo | Uso | Descripcion |
|---|---|---|---|
| `customer_id` | categoria | observable | Cliente |
| `fecha_hora` | fecha y hora | observable | Momento del mensaje |
| `texto` | texto | observable | Mensaje |
| `sentimiento` | categoria | etiqueta | positivo, neutro, preocupado o negativo |

## etiquetas_calidad
Que movimientos se ensuciaron y como. Sirve para medir la limpieza.

| Columna | Tipo | Uso | Descripcion |
|---|---|---|---|
| `transaction_id` | texto | etiqueta | Movimiento afectado |
| `tipo_problema` | texto | etiqueta | falta_glosa, falta_categoria, falta_saldo, falta_monto, duplicado_exacto o duplicado_cercano |

## panel_mensual
Cliente por mes, agregado de los movimientos limpios. Es la entrada de la segmentacion.

| Columna | Tipo | Uso | Descripcion |
|---|---|---|---|
| `customer_id` | categoria | observable | Cliente |
| `mes` | texto | observable | AAAA-MM |
| `ingreso_operativo` | decimal | observable | Sueldo, gratificacion, comisiones, ventas, honorarios e ingreso extra |
| `ingreso_extraordinario` | decimal | observable | Bonos del Estado y retiros de fondos de pensiones |
| `ingreso_financiero` | decimal | observable | Retiros de ahorro, prestamos informales y transferencias recibidas |
| `ahorro_movido` | decimal | observable | Dinero llevado a ahorro |
| `gasto_fijo` | decimal | observable | Alquiler, servicios, suscripciones, colegio y seguro |
| `gasto_variable` | decimal | observable | Gasto cotidiano sin los gastos hormiga |
| `gasto_hormiga` | decimal | observable | Delivery y snacks |
| `gasto_deuda` | decimal | observable | Cuotas y pagos de creditos informales |
| `n_transacciones` | entero | observable | Movimientos del mes |
| `saldo_fin` | decimal | observable | Saldo al cierre del mes |
| `saldo_min` | decimal | observable | Saldo minimo del mes |
| `dias_en_rojo` | entero | etiqueta | Dias con saldo negativo en el mes |

## eventos
Catalogo de eventos aplicados. La magnitud de cada efecto esta en `data/parametros/eventos.yaml`.

| Columna | Tipo | Uso | Descripcion |
|---|---|---|---|
| `evento_id` | texto | observable | Identificador |
| `nombre` | texto | observable | Nombre |
| `tipo` | texto | observable | historico o prospectivo |
| `inicio` | texto | observable | Fecha de inicio |
| `fin` | texto | observable | Fecha de fin |
| `estado` | texto | observable | verificado, parcial o supuesto |
| `fuente` | texto | observable | Fuente y que parte es supuesto |

## contexto_diario
Calendario y fuerza de cada evento por dia (0 a 1).

| Columna | Tipo | Uso | Descripcion |
|---|---|---|---|
| `fecha` | fecha | observable | Dia |
| `dia_semana` | entero | observable | 0 lunes a 6 domingo |
| `dia_mes` | entero | observable | Dia del mes |
| `mes` | entero | observable | 1 a 12 |
| `fuerza_covid_confinamiento` | decimal | observable | Intensidad del evento |
| `fuerza_covid_reapertura` | decimal | observable | Intensidad del evento |
| `fuerza_covid_segunda_ola` | decimal | observable | Intensidad del evento |
| `fuerza_protestas_2022_2023` | decimal | observable | Intensidad del evento |
| `fuerza_nino_costero_2023` | decimal | observable | Intensidad del evento |

## macro_mensual
Series reales del BCRP (descargadas con `src/datos_publicos/descargar.py`, ver `docs/fuentes/bcrp_series.csv`).

| Columna | Tipo | Uso | Descripcion |
|---|---|---|---|
| `mes` | texto | observable | AAAA-MM |
| `ipc_var_mensual` | decimal | observable | Variacion mensual del IPC de Lima Metropolitana, % |
| `ipc_relativo` | decimal | observable | Precios relativos al ultimo mes real (2025-12 = 1) |
| `tasa_referencia_bcrp` | decimal | observable | Tasa de referencia de la politica monetaria, % |
| `tipo_cambio_venta` | decimal | observable | Tipo de cambio interbancario venta promedio del mes, S/ por US$ |
